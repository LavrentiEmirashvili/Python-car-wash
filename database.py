import sqlite3
import datetime
from Models import Admin, Staff, Customer, Car, Station, Booking

DB_NAME = "carwash.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create Stations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            address TEXT NOT NULL,
            district TEXT NOT NULL,
            has_self_service BOOLEAN NOT NULL
        )
    """)

    # Create Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_verified BOOLEAN DEFAULT 0,
            verification_code TEXT,
            is_2fa_enabled BOOLEAN DEFAULT 0,
            two_fa_secret TEXT,
            recovery_code TEXT,
            registered_at TEXT, -- For Customers
            station_id INTEGER, -- For Staff
            FOREIGN KEY (station_id) REFERENCES stations (id)
        )
    """)

    # Create Cars table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            plate TEXT UNIQUE NOT NULL,
            model TEXT NOT NULL,
            color TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES users (id)
        )
    """)

    # Create Bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            station_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            booking_type TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES users (id),
            FOREIGN KEY (station_id) REFERENCES stations (id),
            FOREIGN KEY (car_id) REFERENCES cars (id),
            UNIQUE(customer_id, station_id, date, time)
        )
    """)

    conn.commit()
    conn.close()

def save_user(user):
    conn = get_connection()
    cursor = conn.cursor()
    
    registered_at = getattr(user, 'registered_at', None)
    if registered_at and isinstance(registered_at, (datetime.date, datetime.datetime)):
        registered_at = registered_at.isoformat()
        
    station_id = getattr(user, 'station_id', None)
    
    try:
        cursor.execute("""
            INSERT INTO users (role, name, email, phone, password, created_at, is_verified, 
                               verification_code, is_2fa_enabled, two_fa_secret, recovery_code, 
                               registered_at, station_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                name=excluded.name,
                phone=excluded.phone,
                password=excluded.password,
                is_verified=excluded.is_verified,
                verification_code=excluded.verification_code,
                is_2fa_enabled=excluded.is_2fa_enabled,
                two_fa_secret=excluded.two_fa_secret,
                recovery_code=excluded.recovery_code,
                registered_at=excluded.registered_at,
                station_id=excluded.station_id
        """, (
            user.role, user.name, user.email, user.phone, user.password, 
            user.created_at.isoformat(), int(user.is_verified),
            user.verification_code, int(user.is_2fa_enabled), user.two_fa_secret, user.recovery_code,
            registered_at, station_id
        ))
        conn.commit()
    finally:
        conn.close()

def save_station(station):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO stations (name, address, district, has_self_service)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                address=excluded.address,
                district=excluded.district,
                has_self_service=excluded.has_self_service
        """, (station.name, station.address, station.district, int(station.has_self_service)))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def save_car(customer_id, car):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO cars (customer_id, plate, model, color)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(plate) DO UPDATE SET
                model=excluded.model,
                color=excluded.color
        """, (customer_id, car.plate, car.model, car.color))
        conn.commit()
    finally:
        conn.close()

def save_booking(booking):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users WHERE email = ?", (booking.customer.email,))
        customer_row = cursor.fetchone()
        if not customer_row: return
        customer_id = customer_row['id']
        
        cursor.execute("SELECT id FROM stations WHERE name = ?", (booking.station.name,))
        station_row = cursor.fetchone()
        if not station_row: return
        station_id = station_row['id']
        
        cursor.execute("SELECT id FROM cars WHERE plate = ?", (booking.car.plate,))
        car_row = cursor.fetchone()
        if not car_row: return
        car_id = car_row['id']

        cursor.execute("""
            INSERT INTO bookings (customer_id, station_id, car_id, date, time, booking_type, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(customer_id, station_id, date, time) DO UPDATE SET
                status=excluded.status
        """, (
            customer_id, station_id, car_id, 
            booking.date.isoformat(), booking.time.isoformat(), 
            booking.booking_type, booking.status, booking.created_at.isoformat()
        ))
        conn.commit()
    finally:
        conn.close()

def load_all_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Load Stations
    cursor.execute("SELECT * FROM stations")
    station_rows = cursor.fetchall()
    stations = []
    station_map = {} # id -> station object
    for row in station_rows:
        s = Station(row['name'], row['address'], row['district'], bool(row['has_self_service']))
        stations.append(s)
        station_map[row['id']] = s
        
    # Load Users
    cursor.execute("SELECT * FROM users")
    user_rows = cursor.fetchall()
    users = []
    user_map = {} # id -> user object
    for row in user_rows:
        role = row['role']
        if role == 'admin':
            u = Admin(row['name'], row['email'], row['phone'], row['password'])
        elif role == 'staff':
            u = Staff(row['name'], row['email'], row['phone'], row['password'], row['station_id'])
        else: # customer
            u = Customer(row['name'], row['email'], row['phone'], row['password'])
            if row['registered_at']:
                u.registered_at = datetime.date.fromisoformat(row['registered_at'])
        
        u.created_at = datetime.datetime.fromisoformat(row['created_at'])
        u.is_verified = bool(row['is_verified'])
        u.verification_code = row['verification_code']
        u.is_2fa_enabled = bool(row['is_2fa_enabled'])
        u.two_fa_secret = row['two_fa_secret']
        u.recovery_code = row['recovery_code']
        
        users.append(u)
        user_map[row['id']] = u

    # Load Cars
    cursor.execute("SELECT * FROM cars")
    car_rows = cursor.fetchall()
    for row in car_rows:
        c = Car(row['plate'], row['model'], row['color'])
        customer = user_map.get(row['customer_id'])
        if customer and isinstance(customer, Customer):
            customer.add_car(c)

    # Load Bookings
    cursor.execute("""
        SELECT b.*, c.plate 
        FROM bookings b 
        JOIN cars c ON b.car_id = c.id
    """)
    booking_rows = cursor.fetchall()
    for row in booking_rows:
        customer = user_map.get(row['customer_id'])
        station = station_map.get(row['station_id'])
        if not customer or not station:
            continue
            
        car = next((c for c in customer.cars if c.plate == row['plate']), None)
        
        if car:
            b = Booking(
                customer, station, car, 
                datetime.date.fromisoformat(row['date']), 
                datetime.time.fromisoformat(row['time']), 
                row['booking_type']
            )
            b.status = row['status']
            b.created_at = datetime.datetime.fromisoformat(row['created_at'])
            station.add_booking(b)

    conn.close()
    return users, stations

def update_booking_status(booking):
    save_booking(booking)
