import logging
import random
import string
import smtplib
from email.mime.text import MIMEText


SMTP_SERVER = "smtp.hostinger.com"
SMTP_PORT = 587
SMTP_USER = "carwash@emirashvili.xyz"
SMTP_PASSWORD = "Lavrenti123."
FROM_EMAIL = "carwash@emirashvili.xyz"

# Configure email logger
email_logger = logging.getLogger('email_service')
email_logger.setLevel(logging.INFO)
handler = logging.FileHandler('email.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
email_logger.addHandler(handler)

def send_email(to_email, subject, body):
    """აგზავნის ნამდვილ მეილს თუ smtp დაკონფიგურებულია"""
    # ინახავს ლოგებს email.log-ში
    log_entry = f"To: {to_email}\nSubject: {subject}\nBody: {body}\n{'-'*30}"
    email_logger.info(log_entry)

    # ამოწმებს smtp დაკონფიგურებულია თუ არა
    if all([SMTP_SERVER, SMTP_USER, SMTP_PASSWORD]):
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = FROM_EMAIL or SMTP_USER
            msg['To'] = to_email

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()  # Secure the connection
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"SUCCESS: Real email sent to {to_email}")
        except Exception as e:
            print(f"ERROR: Failed to send real email: {e}")
            print(f"NOTICE: Simulation fallback used. Check 'email.log' for details.")
    else:
        # Simulation Mode
        print(f"SIMULATION: Email to {to_email} logged in 'email.log'.")
        print(f"DEBUG: Subject: {subject} | Body: {body}")

def generate_code(length=6):
    """ქმნის რანდომ 6 ნიშნა კოდს."""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_code(email, code):
    subject = "Account Verification Code"
    body = f"Your verification code is: {code}"
    send_email(email, subject, body)

def send_2fa_code(email, code):
    subject = "2FA Login Code"
    body = f"Your 2FA login code is: {code}"
    send_email(email, subject, body)

def send_recovery_code(email, code):
    subject = "Password Recovery Code"
    body = f"Your password recovery code is: {code}"
    send_email(email, subject, body)
