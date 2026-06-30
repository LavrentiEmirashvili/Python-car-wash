"""
models.py
ავთვიმრეცხის აპლიკაციის ძირითადი კლასები: User (Admin/Staff/Customer), Car, Station, Booking.
იყენებს: ABC, Inheritance, Dunder methods, @property, datetime
"""

import datetime
from abc import ABC, abstractmethod


class User(ABC):
    """
    აბსტრაქტული კლასი — ყველა მომხმარებლის ტიპის "blueprint".
    ვერ შექმნი User-ის ობიექტს პირდაპირ — მხოლოდ Admin, Staff ან Customer.
    """

    def __init__(self, name, email, phone, password):
        self.name = name
        self._email = None
        self._phone = None
        self.email = email      # გადის @property setter-ში ვალიდაციისთვის
        self.phone = phone      # გადის @property setter-ში ვალიდაციისთვის
        self.password = password
        self.role = None        # child კლასი დააყენებს
        self.created_at = datetime.datetime.now()
        
        # Email Verification & Security
        self.is_verified = False
        self.verification_code = None
        self.is_2fa_enabled = False
        self.two_fa_secret = None
        self.recovery_code = None

        # New fields
        self.points = 0
        self.balance = 0.0
        self.profile_picture = None # Path to image

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if "@" not in value or "." not in value:
            raise ValueError(f"არასწორი ელ-ფოსტის ფორმატი: {value}")
        self._email = value

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value):
        value = str(value)
        if not (value.startswith("5") and len(value) == 9 and value.isdigit()):
            raise ValueError(f"არასწორი ტელეფონის ფორმატი: {value}")
        self._phone = value

    @abstractmethod
    def get_dashboard(self):
        """ყველა child კლასმა უნდა განსაზღვროს, რას აბრუნებს მისი dashboard"""
        pass

    def __str__(self):
        return f"{self.name} ({self.role})"

    def __repr__(self):
        return f"User(name={self.name!r}, role={self.role!r}, email={self.email!r})"

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.email == other.email


class Admin(User):
    def __init__(self, name, email, phone, password):
        super().__init__(name, email, phone, password)
        self.role = "admin"

    def get_dashboard(self):
        return "ადმინის პანელი: სადგურების მართვა, პერსონალი, ყველა ჯავშანი, რეპორტები"


class Staff(User):
    def __init__(self, name, email, phone, password, station_id):
        super().__init__(name, email, phone, password)
        self.role = "staff"
        self.station_id = station_id  # რომელ სადგურზე მუშაობს

    def get_dashboard(self):
        return f"პერსონალის პანელი: დღევანდელი ჯავშნები სადგურზე #{self.station_id}"


class Customer(User):
    def __init__(self, name, email, phone, password):
        super().__init__(name, email, phone, password)
        self.role = "customer"
        self.registered_at = datetime.date.today()
        self.cars = []

    def get_dashboard(self):
        return f"კლიენტის პანელი: {len(self.cars)} მანქანა, {self.points} ქულა, ბალანსი: {self.balance}₾"

    def get_loyalty_tier(self):
        if self.points >= 1000:
            return "Gold"
        elif self.points >= 750:
            return "Silver"
        elif self.points >= 500:
            return "Bronze"
        return "None"

    def get_loyalty_info(self):
        """Returns (current_tier, next_tier, min_pts, max_pts, current_pts)"""
        pts = self.points
        if pts >= 1000:
            return "Gold", "Max", 1000, 1000, pts
        elif pts >= 750:
            return "Silver", "Gold", 750, 1000, pts
        elif pts >= 500:
            return "Bronze", "Silver", 500, 750, pts
        else:
            return "None", "Bronze", 0, 500, pts

    def get_loyalty_discount(self):
        tier = self.get_loyalty_tier()
        discounts = {
            "Gold": 0.20,
            "Silver": 0.15,
            "Bronze": 0.10,
            "None": 0.0
        }
        return discounts.get(tier, 0.0)

    def add_car(self, car):
        if not isinstance(car, Car):
            raise TypeError("მხოლოდ Car ობიექტის დამატება შესაძლებელია")
        if car in self.cars:
            raise ValueError(f"მანქანა {car.plate} უკვე დამატებულია")
        self.cars.append(car)

    def years_as_customer(self):
        today = datetime.date.today()
        return (today - self.registered_at).days / 365.25


class Car:
    def __init__(self, plate, model, color):
        self.plate = plate.upper()
        self.model = model
        self.color = color

    def __str__(self):
        return f"{self.plate} | {self.model} | {self.color}"

    def __repr__(self):
        return f"Car(plate={self.plate!r}, model={self.model!r})"

    def __eq__(self, other):
        if not isinstance(other, Car):
            return NotImplemented
        return self.plate == other.plate

    def __hash__(self):
        return hash(self.plate)


class Station:
    def __init__(self, name, address, district, has_self_service=True):
        self.name = name
        self.address = address
        self.district = district
        self.has_self_service = has_self_service
        self.bookings = []

    def __str__(self):
        return f"{self.name} — {self.district}, {self.address}"

    def __repr__(self):
        return f"Station(name={self.name!r}, district={self.district!r})"

    def is_available(self, date, time):
        for booking in self.bookings:
            if booking.date == date and booking.time == time and booking.status != "cancelled":
                return False
        return True

    def add_booking(self, booking):
        self.bookings.append(booking)

    def bookings_for_date(self, date):
        return [b for b in self.bookings if b.date == date]


class Booking:
    VALID_TYPES = ("staff_wash", "self_service")
    VALID_STATUSES = ("pending", "confirmed", "completed", "cancelled")

    def __init__(self, customer, station, car, date, time, booking_type):
        if booking_type not in self.VALID_TYPES:
            raise ValueError(f"არასწორი ჯავშნის ტიპი: {booking_type}")
        if booking_type == "self_service" and not station.has_self_service:
            raise ValueError(f"{station.name} არ აქვს თვითმომსახურების ოპცია")

        self.customer = customer
        self.station = station
        self.car = car
        self.date = date              # datetime.date
        self.time = time              # datetime.time
        self.booking_type = booking_type
        self.status = "pending"
        self.created_at = datetime.datetime.now()

    def __str__(self):
        return (f"{self.customer.name} — {self.car.plate} — "
                f"{self.date} {self.time} — {self.booking_type} ({self.status})")

    def __repr__(self):
        return f"Booking(customer={self.customer.name!r}, date={self.date!r}, status={self.status!r})"

    def __lt__(self, other):
        """შედარება თარიღით — საშუალებას გვაძლევს sorted()-ით დავალაგოთ ჯავშნები"""
        if not isinstance(other, Booking):
            return NotImplemented
        return (self.date, self.time) < (other.date, other.time)

    def confirm(self):
        self.status = "confirmed"

    def cancel(self):
        if self.status == "completed":
            raise ValueError("დასრულებული ჯავშნის გაუქმება შეუძლებელია")
        self.status = "cancelled"

    def complete(self):
        self.status = "completed"

    def time_since_created(self):
        delta = datetime.datetime.now() - self.created_at
        return delta.total_seconds()


if __name__ == "__main__":
    admin = Admin("ნიკა", "nika@carwash.ge", "555111222", "pass123")
    customer = Customer("გიორგი", "giorgi@gmail.com", "555123456", "pass456")

    car = Car("AA-123-BB", "Toyota Camry", "თეთრი")
    customer.add_car(car)

    station = Station("საბურთალო", "ვაჟა-ფშაველას 12", "საბურთალო", has_self_service=True)

    booking = Booking(
        customer=customer,
        station=station,
        car=car,
        date=datetime.date(2026, 6, 20),
        time=datetime.time(14, 0),
        booking_type="staff_wash"
    )
    station.add_booking(booking)

    print(admin)
    print(admin.get_dashboard())
    print(customer)
    print(customer.get_dashboard())
    print(car)
    print(station)
    print(booking)
