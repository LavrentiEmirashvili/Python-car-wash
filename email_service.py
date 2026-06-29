import logging
import random
import string
import smtplib
from email.mime.text import MIMEText

# ============================================================
# SMTP Configuration (Fill these to enable real email sending)
# ============================================================
# For Gmail: 
# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 587
# SMTP_USER = "your-email@gmail.com"
# SMTP_PASSWORD = "your-app-password"  # Use an App Password, not your regular password
# ============================================================

SMTP_SERVER = "pro.eu.turbo-smtp.com"
SMTP_PORT = 587
SMTP_USER = "c88c20ffaeb430f3a89d"
SMTP_PASSWORD = ""
FROM_EMAIL = ""  # Defaults to SMTP_USER if empty

# Configure email logger
email_logger = logging.getLogger('email_service')
email_logger.setLevel(logging.INFO)
handler = logging.FileHandler('email.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
email_logger.addHandler(handler)

def send_email(to_email, subject, body):
    """Sends a real email if SMTP is configured, otherwise simulates."""
    # Always log to email.log for development visibility
    log_entry = f"To: {to_email}\nSubject: {subject}\nBody: {body}\n{'-'*30}"
    email_logger.info(log_entry)

    # Check if real SMTP is configured
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
    """Generates a random numeric code."""
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
