import random
from faker import Faker
from Models import Customer, Staff, Car
import database

def generate_georgian_phone():
    """Generates a valid Georgian mobile number (starts with 5, 9 digits)."""
    return "5" + "".join([str(random.randint(0, 9)) for _ in range(8)])

def generate_georgian_plate():
    """Generates a fake car plate in XX-000-XX format."""
    letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ" # Avoiding I to be safe, though not strictly necessary
    return f"{random.choice(letters)}{random.choice(letters)}-{random.randint(100, 999)}-{random.choice(letters)}{random.choice(letters)}"

def populate(num_customers=10, num_staff_per_station=2):
    fake = Faker()
    database.init_db()
    
    # Ensure there are stations in the database
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM stations")
    station_rows = cursor.fetchall()
    conn.close()
    
    if not station_rows:
        print("No stations found in the database. Seeding initial data first...")
        from store import AppStore
        AppStore() # This will trigger the initial seed
        
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM stations")
        station_rows = cursor.fetchall()
        conn.close()
        
    if not station_rows:
        print("Still no stations found. Aborting.")
        return

    print(f"Populating {num_customers} customers with cars...")
    for _ in range(num_customers):
        name = fake.name()
        email = fake.unique.email()
        phone = generate_georgian_phone()
        password = "password123"
        
        customer = Customer(name, email, phone, password)
        customer.is_verified = True
        database.save_user(customer)
        
        # Get the ID to save a car
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        c_id = row['id']
        conn.close()
        
        # Add 1-2 fake cars per customer
        for _ in range(random.randint(1, 2)):
            plate = generate_georgian_plate()
            model = f"{fake.company()} {random.choice(['Model S', 'Civic', 'Camry', 'X5', 'Golf', 'Corolla', 'A4'])}"
            color = fake.color_name()
            car = Car(plate, model, color)
            try:
                database.save_car(c_id, car)
            except Exception as e:
                print(f"  Could not save car {plate}: {e}")
    
    print(f"Populating {num_staff_per_station} staff per station...")
    for station_row in station_rows:
        s_id = station_row['id']
        s_name = station_row['name']
        print(f"  Adding staff for station: {s_name}")
        for _ in range(num_staff_per_station):
            name = fake.name()
            email = fake.unique.email()
            phone = generate_georgian_phone()
            password = "staffpassword"
            
            staff = Staff(name, email, phone, password, station_id=s_id)
            staff.is_verified = True
            database.save_user(staff)

    print("Population complete.")

if __name__ == "__main__":
    populate()
