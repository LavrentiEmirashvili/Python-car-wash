import functools
import datetime
import re
import logging

logging.basicConfig(
    filename="carwash.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)


def log_action(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Starting {func.__name__} with args: {args}, kwargs: {kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"Finished {func.__name__}")
        return result
    return wrapper


def require_role(*roles):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # args[0] is 'self' if used in a class method, args[1] is the user
            # args[0] is the user if used in a regular function
            user = args[0] if hasattr(args[0], 'role') else args[1] if len(args) > 1 else None
            if user is None or not hasattr(user, 'role') or user.role not in roles:
                raise PermissionError(f"წვდომა აკრძალულია! საჭირო როლი: {roles}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_email(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        # FIX: check both kwargs AND positional args
        email = kwargs.get('email') or (args[1] if len(args) > 1 else None)
        if email and not re.match(pattern, str(email)):
            raise ValueError(f"არასწორი ელ-ფოსტის ფორმატი: {email}")
        return func(*args, **kwargs)
    return wrapper


def validate_phone(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pattern = r"^5\d{8}$"
        # FIX: check both kwargs AND positional args
        phone = kwargs.get('phone') or (args[2] if len(args) > 2 else None)
        if phone and not re.match(pattern, str(phone)):
            raise ValueError(f"არასწორი ტელეფონის ფორმატი: {phone}. მაგალითი: 555123456")
        return func(*args, **kwargs)
    return wrapper


def validate_plate(func):
    """NEW: validates Georgian car plate format — AA-123-BB"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pattern = r"^[A-Z]{2}-\d{3}-[A-Z]{2}$"
        plate = kwargs.get('plate') or (args[1] if len(args) > 1 else None)
        if plate and not re.match(pattern, str(plate).upper()):
            raise ValueError(f"არასწორი სანომრე ნიშნის ფორმატი: {plate}. სწორი ფორმატი: AA-123-BB")
        return func(*args, **kwargs)
    return wrapper


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        # FIX: :.4f formats to 4 decimal places — much cleaner output
        message = f"ფუნქცია '{func.__name__}' შესრულდა {duration:.4f} წამში."
        print(message)
        logging.info(message)
        return result
    return wrapper
