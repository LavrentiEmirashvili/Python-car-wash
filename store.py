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
        if not self.users:
            self._seed()

    def _seed(self):
        self.stations = [
            Station("საბურთალო", "ვაჟა-ფშაველას 12", "საბურთალო", has_self_service=True),
            Station("ვაკე", "ჭავჭავაძის 5", "ვაკე", has_self_service=True),
            Station("ისანი", "კახეთის გზატ 100", "ისანი", has_self_service=False),
        ]
        for s in self.stations:
            database.save_station(s)

        admin = Admin("ნიკა", "admin@carwash.ge", "555111222", "admin123")
        admin.is_verified = True
        database.save_user(admin)

        staff_saburtalo = Staff(
            "ლუკა", "luka@carwash.ge", "555222333", "staff123", station_id=1
        )
        staff_saburtalo.is_verified = True
        database.save_user(staff_saburtalo)

        staff_vake = Staff(
            "ანა", "ana@carwash.ge", "555333444", "staff123", station_id=2
        )
        staff_vake.is_verified = True
        database.save_user(staff_vake)

        customer = register_customer(
            "გიორგი", "giorgi@gmail.com", "555123456", "customer123"
        )
        customer.is_verified = True
        database.save_user(customer)

        self.users = [admin, staff_saburtalo, staff_vake, customer]

    def login(self, email: str, password: str):
        email = email.strip().lower()
        for user in self.users:
            if user.email.lower() == email and user.password == password:
                if not user.is_verified:
                    raise ValueError("გთხოვთ გაიაროთ ელ-ფოსტის ვერიფიკაცია")
                return user
        return None

    def logout(self):
        self.current_user = None

    def register_new_customer(self, name, email, phone, password):
        customer = register_customer(name, email, phone, password)
        database.save_user(customer)
        self.users.append(customer)
        return customer

    def register_new_staff(self, name, email, phone, password, station_id):
        staff = register_staff(name, email, phone, password, station_id)
        staff.is_verified = True  # პერსონალი დამატებულია ადმინის მიერ, ვერიფიცირებულია
        database.save_user(staff)
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
