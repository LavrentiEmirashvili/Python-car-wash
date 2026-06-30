# Python Car Wash Management System

Finals project for programming in Python. A desktop application built with Python and PyQt5 for managing car wash operations, bookings, and user roles.

## Overview

This project provides a comprehensive solution for car wash businesses. It supports multiple user roles, including Admins, Staff, and Customers, each with their own dedicated dashboards and functionalities. The system handles car registration, booking management, automated price calculation with loyalty discounts, and secure user authentication with email verification and 2FA.

## Features

- **Multi-Role Dashboards**:
  - **Admin**: Manage stations, staff, view all bookings, and access reports.
  - **Staff**: View and complete bookings for assigned stations.
  - **Customer**: Manage personal cars, book wash sessions, and view booking history.
- **Booking System**: Real-time availability checking, support for both staff-managed wash and self-service options.
- **Security**: 
  - Email verification during registration.
  - Two-Factor Authentication (2FA) support.
  - Password recovery via email.
- **Automated Calculations**: 
  - Loyalty discounts for long-term customers.
  - Late cancellation fee calculation.
- **Logging**: Comprehensive action logging for debugging and audit trails (`carwash.log`).

## Technical Stack & Libraries

- **Language**: Python 3.x
- **GUI Framework**: [PyQt5](https://pypi.org/project/PyQt5/) - Used for building the cross-platform desktop interface and managing the event-driven UI.
- **Data Generation**: [Faker](https://pypi.org/project/Faker/) - Used in development to generate realistic test data like names, emails, and car plates for the database seeding script.
- **Database**: **SQLite** - Built-in Python support for lightweight, serverless persistent storage, used to store users, cars, stations, and bookings.
- **Email Service**: `smtplib` - Python's built-in library for SMTP communication, used for sending verification and recovery codes.
- **Logging**: `logging` - Used for tracking application events and email service history.

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`:
  - `PyQt5>=5.15.0`
  - `faker>=33.0.0`

## Setup and Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Python-car-wash
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the Database**:
   The database is automatically initialized when running the application for the first time or when running the population script.

## Running the Application

### Launch Main App
To start the PyQt5 GUI:
```bash
python main.py
```

### Seed Development Data
To populate the database with fake customers, cars, and staff for testing purposes:
```bash
python populate_fake_users.py
```

## Project Structure

- `main.py`: The entry point of the application.
- `gui.py`: Contains all PyQt5 window and widget definitions.
- `Models.py`: Core business objects using OOP principles (User, Customer, Staff, Admin, Car, Station, Booking).
- `database.py`: Handles SQLite connection and CRUD operations.
- `store.py`: Centralized state management and data loading logic.
- `services.py`: Business logic layer (price calculation, registration logic, etc.).
- `decorators.py`: Custom decorators for role-based access control, validation, and performance timing.
- `email_service.py`: Handles SMTP configurations and sending automated emails.
- `populate_fake_users.py`: A utility script for seeding the database with `Faker`.
- `carwash.db`: SQLite database file (generated after first run).
- `carwash.log`: Log file for application actions.
- `email.log`: Log file for email service history.

## Configuration & Environment Variables

- **Email Settings**: SMTP configurations (server, port, credentials) are currently hardcoded in `email_service.py`. 
- **TODO**: Move SMTP credentials to environment variables (`.env` file) for better security.

## Tests

- **TODO**: Implement comprehensive unit tests and integration tests. Currently, validation is performed through manual testing and the `populate_fake_users.py` script.

## License

- **TODO**: Add license information (e.g., MIT, Apache).
