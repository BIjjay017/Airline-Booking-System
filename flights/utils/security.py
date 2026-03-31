"""
Security utilities for input validation, sanitization, and protection
"""

import re
import bleach
from functools import wraps
from flask import request, jsonify, session
from datetime import datetime, timedelta


class InputValidator:
    """
    Comprehensive input validation for flight booking system
    """
    
    # Allowed HTML tags for sanitization
    ALLOWED_TAGS = []
    ALLOWED_ATTRIBUTES = {}

    @staticmethod
    def sanitize_input(text):
        """Remove any potentially dangerous characters"""
        if not isinstance(text, str):
            return str(text)
        
        # Clean HTML
        text = bleach.clean(text, tags=InputValidator.ALLOWED_TAGS, 
                           attributes=InputValidator.ALLOWED_ATTRIBUTES, strip=True)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254

    @staticmethod
    def validate_airport_code(code):
        """Validate airport code (3 uppercase letters)"""
        return bool(re.match(r'^[A-Z]{3}$', code.upper()))

    @staticmethod
    def validate_date(date_str):
        """Validate date format"""
        patterns = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']
        for pattern in patterns:
            try:
                dt = datetime.strptime(date_str, pattern)
                # Ensure date is not in the past
                if dt.date() >= datetime.now().date():
                    return True
            except ValueError:
                continue
        return False

    @staticmethod
    def validate_phone(phone):
        """Validate phone number"""
        # Supports formats like +977-1234567890 or 1234567890
        pattern = r'^(\+\d{1,3}[-.\s]?)?\d{9,14}$'
        return bool(re.match(pattern, phone.replace(' ', '').replace('-', '').replace('.', '')))

    @staticmethod
    def validate_password(password):
        """
        Validate password strength
        Requirements: 8+ chars, uppercase, lowercase, number, special char
        """
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[@$!%*?&]', password):
            errors.append("Password must contain at least one special character (@$!%*?&)")
        
        return errors if errors else True

    @staticmethod
    def validate_flight_booking_data(data):
        """Validate complete flight booking data"""
        errors = []
        
        # Origin airport
        if not data.get('origin'):
            errors.append("Origin airport is required")
        elif not InputValidator.validate_airport_code(data['origin']):
            errors.append("Invalid origin airport code")
        
        # Destination airport
        if not data.get('destination'):
            errors.append("Destination airport is required")
        elif not InputValidator.validate_airport_code(data['destination']):
            errors.append("Invalid destination airport code")
        
        # Same airport check
        if data.get('origin') and data.get('destination'):
            if data['origin'].upper() == data['destination'].upper():
                errors.append("Origin and destination must be different")
        
        # Date validation
        if not data.get('date'):
            errors.append("Departure date is required")
        elif not InputValidator.validate_date(data['date']):
            errors.append("Invalid or past departure date")
        
        # Passengers
        try:
            passengers = int(data.get('tickets', 1))
            if passengers < 1 or passengers > 6:
                errors.append("Number of passengers must be between 1 and 6")
        except:
            errors.append("Invalid number of passengers")
        
        return errors

    @staticmethod
    def validate_user_data(data):
        """Validate user registration/profile data"""
        errors = []
        
        # Name
        if not data.get('name'):
            errors.append("Name is required")
        elif len(data['name']) < 2 or len(data['name']) > 100:
            errors.append("Name must be between 2 and 100 characters")
        
        # Email
        if not data.get('email'):
            errors.append("Email is required")
        elif not InputValidator.validate_email(data['email']):
            errors.append("Invalid email format")
        
        # Password
        if 'password' in data:
            pwd_validation = InputValidator.validate_password(data['password'])
            if isinstance(pwd_validation, list):
                errors.extend(pwd_validation)
        
        return errors


class SecurityHeaders:
    """
    Security header utilities
    """
    
    @staticmethod
    def set_security_headers(response):
        """Set security headers for response"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response


class RateLimiter:
    """
    Simple rate limiting for login attempts and sensitive operations
    """
    
    # Store rate limit data in memory (use Redis in production)
    _limits = {}
    
    @staticmethod
    def check_rate_limit(key, max_attempts=5, window_seconds=300):
        """
        Check if rate limit exceeded
        key: unique identifier (e.g., IP address, email)
        max_attempts: maximum attempts allowed
        window_seconds: time window in seconds
        """
        now = datetime.now()
        
        if key not in RateLimiter._limits:
            RateLimiter._limits[key] = []
        
        # Remove old entries outside the window
        RateLimiter._limits[key] = [
            timestamp for timestamp in RateLimiter._limits[key]
            if (now - timestamp).total_seconds() < window_seconds
        ]
        
        # Check limit
        if len(RateLimiter._limits[key]) >= max_attempts:
            return False
        
        # Add current attempt
        RateLimiter._limits[key].append(now)
        return True

    @staticmethod
    def reset_limit(key):
        """Reset rate limit for a key"""
        if key in RateLimiter._limits:
            RateLimiter._limits[key] = []


def require_login(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


def validate_form_data(schema):
    """
    Decorator to validate form data against schema
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            errors = InputValidator.validate_flight_booking_data(request.form.to_dict())
            if errors:
                from flask import flash
                for error in errors:
                    flash(error, 'danger')
                return f(*args, **kwargs)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_request_data(data_dict):
    """Sanitize all string values in a dictionary"""
    sanitized = {}
    for key, value in data_dict.items():
        if isinstance(value, str):
            sanitized[key] = InputValidator.sanitize_input(value)
        else:
            sanitized[key] = value
    return sanitized


# SQL Injection Prevention Helpers
class SQLHelper:
    """Helper functions for safe SQL operations"""
    
    @staticmethod
    def safe_like_escape(search_term):
        """Escape special characters in LIKE queries"""
        return search_term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


# CSRF Token Management
class CSRFManager:
    """Manage CSRF tokens for forms"""
    
    @staticmethod
    def generate_csrf_token():
        """Generate a new CSRF token (uses Flask-WTF)"""
        from flask_wtf.csrf import generate_csrf
        return generate_csrf()

    @staticmethod
    def inject_csrf_token():
        """Inject CSRF token into template context"""
        from flask_wtf.csrf import generate_csrf
        return {'csrf_token': generate_csrf()}


# Logging Security Events
import logging
from datetime import datetime

logger = logging.getLogger('security')
logger.setLevel(logging.WARNING)

# File handler
handler = logging.FileHandler('security.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def log_security_event(event_type, details, severity='WARNING'):
    """
    Log security events
    """
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'details': details,
        'severity': severity,
        'ip_address': request.remote_addr if request else 'unknown'
    }
    
    if severity == 'CRITICAL':
        logger.critical(str(log_entry))
    elif severity == 'WARNING':
        logger.warning(str(log_entry))
    else:
        logger.info(str(log_entry))
