
"""
services.py
ბიზნეს ლოგიკის ფენა -- აკავშირებს models.py-ის კლასებს და decorators.py-ის დეკორატორებს.
იყენებს: decorators (log_action, require_role, validate_*, timer), datetime, მარტივი მათემატიკა.
"""

import datetime
from Models import Admin, Staff, Customer, Car, Station, Booking
from decorators import log_action, require_role, validate_email, validate_phone, validate_plate, timer
import email_service
import database

# ============================================================
# Security & Verification Services
# ============================================================

def initiate_email_verification(user):
    code = email_service.generate_code()
    user.verification_code = code
    database.save_user(user)
    email_service.send_verification_code(user.email, code)
    return code

def verify_email(user, code):
    if user.verification_code == code:
        user.is_verified = True
        user.verification_code = None
        database.save_user(user)
        return True
    return False

def initiate_2fa(user):
    if not user.is_2fa_enabled:
        return None
    code = email_service.generate_code()
    user.two_fa_secret = code # Using two_fa_secret to store current login code for simplicity
    database.save_user(user)
    email_service.send_2fa_code(user.email, code)
    return code

def verify_2fa(user, code):
    if user.two_fa_secret == code:
        user.two_fa_secret = None
        database.save_user(user)
        return True
    return False

def request_password_recovery(users, email):
    user = next((u for u in users if u.email.lower() == email.lower()), None)
    if user:
        code = email_service.generate_code()
        user.recovery_code = code
        database.save_user(user)
        email_service.send_recovery_code(user.email, code)
        return True
    return False

def reset_password(user, code, new_password):
    if user.recovery_code == code:
        user.password = new_password
        user.recovery_code = None
        database.save_user(user)
        return True
    return False


# ============================================================
# ფასები და წესები
# ============================================================

SERVICE_PRICES = {
    "staff_wash": 25.0,
    "self_service": 12.0,
}

LATE_CANCEL_FEE = 5.0


def calculate_booking_price(booking):
    """საბაზისო ფასი + ლოიალურობის ფასდაკლება ქულების მიხედვით."""
    base_price = SERVICE_PRICES[booking.booking_type]
    customer = booking.customer
    
    discount_rate = customer.get_loyalty_discount()
    discount = base_price * discount_rate
    base_price -= discount

    return round(base_price, 2)


def calculate_cancellation_fee(booking):
    """თუ ჯავშნამდე 1 საათზე ნაკლები დარჩა, ჯარიმდება გაუქმება (ლოიალურობის ფასდაკლებით)."""
    booking_datetime = datetime.datetime.combine(booking.date, booking.time)
    time_remaining = booking_datetime - datetime.datetime.now()

    if time_remaining < datetime.timedelta(hours=1):
        fee = LATE_CANCEL_FEE
        customer = booking.customer
        discount_rate = customer.get_loyalty_discount()
        fee -= (fee * discount_rate)
        return round(fee, 2)
    return 0.0


# ============================================================
# რეგისტრაცია
# ============================================================

@log_action
@validate_email
@validate_phone
def register_customer(name, email, phone, password):
    return Customer(name=name, email=email, phone=phone, password=password)


@log_action
@validate_email
@validate_phone
def register_staff(name, email, phone, password, station_id):
    return Staff(name=name, email=email, phone=phone, password=password, station_id=station_id)


@log_action
@validate_plate
def register_car(customer, plate, make, model, color):
    car = Car(plate=plate, model=model, color=color, make=make)
    customer.add_car(car)   # თუ დუბლირებული plate-ია, customer.add_car() თავად ისვრის ValueError-ს
    
    # Save to database
    import database
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (customer.email,))
    row = cursor.fetchone()
    if row:
        database.save_car(row['id'], car)
    conn.close()
    
    return car


def remove_car(customer, plate):
    """Remove a car from the customer's account and persist deletion."""
    # Find car in memory
    target = next((c for c in customer.cars if c.plate.upper() == plate.upper()), None)
    if not target:
        raise ValueError(f"მანქანა {plate} ვერ მოიძებნა")

    # Remove from in-memory list
    customer.cars = [c for c in customer.cars if c.plate.upper() != plate.upper()]

    # Persist in database
    database.delete_car(customer.email, plate)
    return True


# ============================================================
# ჯავშნის სამუშაო პროცესი
# ============================================================

@log_action
@timer
def create_booking(customer, station, car, date, time, booking_type):
    """
    Booking-ის constructor უკვე ამოწმებს booking_type-ს და self_service-ის
    ხელმისაწვდომობას -- ამიტომ აქ მხოლოდ დროის კონფლიქტს ვამოწმებთ.
    """
    booking_datetime = datetime.datetime.combine(date, time)
    if booking_datetime <= datetime.datetime.now():
        raise ValueError("ჯავშანი წარსულ დროში ვერ შეიქმნება")

    if not station.is_available(date, time):
        raise ValueError("ეს დროის სლოტი დაკავებულია, აირჩიეთ სხვა დრო")

    price = calculate_booking_price(Booking(
        customer=customer,
        station=station,
        car=car,
        date=date,
        time=time,
        booking_type=booking_type,
    ))
    if customer.balance < price:
        raise ValueError("ბალანსი არასაკმარისია ჯავშნის créationთვის")

    booking = Booking(
        customer=customer,
        station=station,
        car=car,
        date=date,
        time=time,
        booking_type=booking_type,
    )

    station.add_booking(booking)
    booking.confirm()

    # Earn points and deduct balance
    customer.points += 10  # +10 per reservation
    customer.balance -= price  # Deduct booking price from balance
    database.save_user(customer)

    database.save_booking(booking)

    return booking, price


@log_action
def cancel_booking(booking):
    """ჯარიმის გამოთვლა ხდება ჯავშნის სტატუსის შეცვლამდე."""
    fee = calculate_cancellation_fee(booking)
    booking.cancel()   # booking.cancel() თავად ისვრის ValueError-ს, თუ status == 'completed'
    database.update_booking_status(booking)

    # Deduct cancellation fee from customer's balance if any
    if fee and fee > 0:
        booking.customer.balance -= fee
        database.save_user(booking.customer)

    return fee


# ============================================================
# როლებზე დაცული ფუნქციები
# ============================================================

@require_role("staff", "admin")
@log_action
def complete_booking(user, booking):
    booking.complete()
    database.update_booking_status(booking)
    return booking


@require_role("admin")
def total_revenue(user, station):
    completed = [b for b in station.bookings if b.status == "completed"]
    return round(sum(calculate_booking_price(b) for b in completed), 2)


@require_role("admin", "staff")
def daily_booking_count(user, station, date=None):
    date = date or datetime.date.today()
    return len([b for b in station.bookings if b.date == date and b.status != "cancelled"])


@require_role("admin")
def most_popular_service(user, station):
    counts = {"staff_wash": 0, "self_service": 0}
    for b in station.bookings:
        if b.status != "cancelled":
            counts[b.booking_type] += 1
    return max(counts, key=counts.get)


# ============================================================
# ძებნა და სიების დაბრუნება (წაკითხვადი ოპერაციები -- დაცვა არ სჭირდება)
# ============================================================

def find_stations_by_district(stations, district):
    district_query = district.strip().lower()
    if not district_query:
        return list(stations)
    return [s for s in stations if district_query in s.district.lower()]


def find_self_service_stations(stations):
    return [s for s in stations if s.has_self_service]


def get_customer_upcoming_bookings(customer, station):
    now = datetime.datetime.now()
    upcoming = []
    for b in station.bookings:
        if b.customer == customer and b.status != "cancelled":
            booking_dt = datetime.datetime.combine(b.date, b.time)
            if booking_dt > now:
                upcoming.append(b)
    return sorted(upcoming)   # იყენებს Booking.__lt__-ს models.py-დან


def get_customer_history(customer, station):
    return [b for b in station.bookings if b.customer == customer and b.status == "completed"]