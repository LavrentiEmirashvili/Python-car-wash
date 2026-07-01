"""
In-memory application state: users, stations, and session helpers.
All mutations go through services.py so decorators stay in the call path.
"""

from Models import Admin, Staff, Station, Customer
from services import register_customer, register_staff
import database


class AppStore:
    def __init__(self):
        database.init_db()
        self.users, self.stations = database.load_all_data()
        self.current_user = None
        self._seed_stations()
        self._seed_users()
        self.users, self.stations = database.load_all_data()

    def _seed_stations(self):
        self.stations = [
            Station("საბურთალო", "ვაჟა-ფშაველას 12", "საბურთალო", has_self_service=True),
            Station("ვაკე", "ჭავჭავაძის 81", "ვაკე", has_self_service=True),
            Station("ისანი", "ნავთლუღის 20", "ისანი", has_self_service=False),
            Station("ვარკეთილი", "თრიალეთის 21", "ვარკეთილი", has_self_service=True),
            Station("გლდანი", "ვეკუას 15", "გლდანი", has_self_service=True),
            Station("ნაძალადევი", "დიმიტრი გულიაშვილის 3", "ნაძალადევი", has_self_service=True),
            Station("სამგორი", "მეველეს 24", "სამგორი", has_self_service=True),
        ]
        for s in self.stations:
            database.save_station(s)

    def _seed_users(self):
        if not any(getattr(u, "email", "").lower() == "admin@carwash.ge" for u in self.users):
            admin = Admin("ნიკა", "admin@carwash.ge", "555111222", "admin123")
            admin.is_verified = True
            database.save_user(admin)
            self.users.append(admin)

        if not any(getattr(u, "email", "").lower() == "luka@carwash.ge" for u in self.users):
            staff_saburtalo = Staff(
                "ლუკა", "luka@carwash.ge", "555222333", "staff123", station_id=1
            )
            staff_saburtalo.is_verified = True
            database.save_user(staff_saburtalo)
            self.users.append(staff_saburtalo)

        if not any(getattr(u, "email", "").lower() == "ana@carwash.ge" for u in self.users):
            staff_vake = Staff(
                "ანა", "ana@carwash.ge", "555333444", "staff123", station_id=2
            )
            staff_vake.is_verified = True
            database.save_user(staff_vake)
            self.users.append(staff_vake)

        if not any(getattr(u, "email", "").lower() == "giorgi@gmail.com" for u in self.users):
            customer = register_customer(
                "გიორგი", "giorgi@gmail.com", "555123456", "customer123"
            )
            customer.is_verified = True
            database.save_user(customer)
            self.users.append(customer)

    def login(self, email: str, password: str):
        email = email.strip().lower()
        password = password.strip()
        for user in self.users:
            if user.email.lower() == email:
                if user.password == password:
                    if not user.is_verified:
                        raise ValueError("გთხოვთ გაიაროთ ელ-ფოსტის ვერიფიკაცია")
                    return user
        return None

    def logout(self):
        self.current_user = None

    def register_new_customer(self, name, email, phone, password):
        password = password.strip()
        customer = register_customer(name, email, phone, password)
        database.save_user(customer)
        
        # Check if user already in memory list and update it, otherwise append
        existing = next((u for u in self.users if u.email.lower() == email.lower()), None)
        if existing:
            # Update existing object's attributes
            existing.name = name
            existing.phone = phone
            existing.password = password
            # customer might have other defaults but these are the main ones
            return existing
        else:
            self.users.append(customer)
            return customer

    def register_new_staff(self, name, email, phone, password, station_id):
        password = password.strip()
        staff = register_staff(name, email, phone, password, station_id)
        staff.is_verified = True  # პერსონალი დამატებულია ადმინის მიერ, ვერიფიცირებულია
        database.save_user(staff)
        
        # Check if user already in memory list
        existing = next((u for u in self.users if u.email.lower() == email.lower()), None)
        if existing:
            existing.name = name
            existing.phone = phone
            existing.password = password
            existing.role = "staff" # Might be changing role
            if hasattr(existing, 'station_id'):
                existing.station_id = station_id
            return existing
        else:
            self.users.append(staff)
            return staff

    def station_for_staff(self, user: Staff):
        idx = user.station_id - 1
        if 0 <= idx < len(self.stations):
            return self.stations[idx]
        return None

    def all_bookings(self):
        bookings = []
        for station in self.stations:
            bookings.extend(station.bookings)
        return sorted(bookings)
