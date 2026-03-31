# Flight Booking System - Setup & Installation Guide

## Quick Start

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package installer)
- Virtual environment manager (venv or conda)

### Step 1: Clone & Setup Virtual Environment

```bash
# Navigate to project directory
cd FYP

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

### Step 2: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

### Step 3: Environment Configuration

Create a `.env` file in the project root:

```env
# Flask Configuration
FLASK_APP=flights
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database Configuration
DB_NAME=flights_db
DB_USER=postgres
DB_PASS=your_password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration (using Mailtrap for development)
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=587
MAIL_USERNAME=your_mailtrap_username
MAIL_PASSWORD=your_mailtrap_password
MAIL_USE_TLS=True
MAIL_USE_SSL=False

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:5000,http://127.0.0.1:5000

# Application Settings
DEBUG=False
TESTING=False
```

**Important**: Never commit `.env` to version control. Add to `.gitignore`:
```
.env
.venv/
*.pyc
__pycache__/
*.log
security.log
```

### Step 4: Database Setup

```bash
# Database creation (using psql)
psql -U postgres

# In psql:
CREATE DATABASE flights_db;
\q

# Run migrations (if any)
# python flights/migrate.py
```

### Step 5: Train ML Model

```bash
# Generate and train the improved model
python -m flights.utils.train_improved_model

# This creates: flights/models/improved_flight_price_model.pkl
```

### Step 6: Initialize Application

```bash
# For initial data setup
python flights/seed.py
```

### Step 7: Run Development Server

```bash
# Start Flask development server
python flights/app.py

# Or using Flask CLI:
flask run

# Application accessible at: http://localhost:5000
```

---

## Production Deployment

### Using Gunicorn

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn (4 workers)
gunicorn -w 4 -b 0.0.0.0:5000 flights.app:create_app()
```

### Using Docker (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment
ENV FLASK_APP=flights
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "flights.app:create_app()"]
```

Build and run:
```bash
docker build -t flightbooking:latest .
docker run -p 5000:5000 --env-file .env flightbooking:latest
```

---

## Security Best Practices

### 1. Secret Key Generation
Generate a secure random secret key:
```python
import os
print(os.urandom(24).hex())
```

### 2. HTTPS Configuration
In production, always enable HTTPS:
```env
SESSION_COOKIE_SECURE=True
PREFERRED_URL_SCHEME=https
```

### 3. Rate Limiting
The system includes built-in rate limiting for login attempts:
- Max 5 attempts per 5 minutes
- Configurable in `flights/utils/security.py`

### 4. CSRF Protection
All forms automatically include CSRF tokens via Flask-WTF.

### 5. Password Requirements
Users must create passwords with:
- Minimum 8 characters
- One uppercase letter
- One lowercase letter
- One number
- One special character (@$!%*?&)

### 6. Security Headers
All responses include security headers:
- X-Content-Type-Options: nosniff
- X-Frame-Options: SAMEORIGIN
- Strict-Transport-Security
- X-XSS-Protection
- And more...

---

## Project Structure

```
FYP/
├── flights/
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Database configuration
│   ├── migrate.py             # Database migrations
│   ├── predict_app.py         # Prediction application
│   ├── seed.py                # Database seeding
│   ├── models/                # ML models
│   │   ├── optimized_flight_price_model.pkl
│   │   └── improved_flight_price_model.pkl
│   ├── routes/
│   │   ├── admin.py          # Admin routes
│   │   ├── auth.py           # Authentication routes
│   │   ├── bookings.py       # Booking routes
│   │   └── flights.py        # Flight routes (ENHANCED)
│   ├── templates/
│   │   ├── base.html         # Base template (ENHANCED)
│   │   ├── login_enhanced.html   # Enhanced login
│   │   ├── search_flights_enhanced.html # Enhanced search
│   │   └── ... (other templates)
│   └── utils/
│       ├── ml_model.py       # ML prediction utilities
│       ├── pricing_engine.py # Dynamic pricing (NEW)
│       ├── security.py       # Security utilities (NEW)
│       ├── train_improved_model.py # Model training (NEW)
│       └── __init__.py
├── .env                       # Environment variables (create this)
├── requirements.txt           # Dependencies (NEW)
├── UPGRADE_DOCUMENTATION.md   # Detailed upgrade docs (NEW)
├── SETUP_GUIDE.md            # This file (NEW)
└── README.md
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution**:
```bash
# Ensure virtual environment is activated
# Then reinstall dependencies
pip install -r requirements.txt
```

### Issue: "PostgreSQL connection error"

**Solution**:
```bash
# Verify PostgreSQL is running
# Windows: Check Services
# macOS: brew services list
# Linux: systemctl status postgresql

# Verify connection parameters in .env
# Test connection:
psql -U postgres -h localhost -d flights_db
```

### Issue: "Model not found" error

**Solution**:
```bash
# Retrain the model
python -m flights.utils.train_improved_model

# Verify file exists
# Windows: dir flights\models\
# macOS/Linux: ls -la flights/models/
```

### Issue: CSRF token validation fails

**Solution**:
1. Ensure all forms include the CSRF token input:
   ```html
   <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
   ```
2. Ensure `Flask-WTF` is installed: `pip install Flask-WTF`
3. Clear browser cache and cookies

### Issue: Rate limiting too strict

**Solution**:
In `flights/utils/security.py`, modify:
```python
# Change from 5 attempts per 300 seconds to custom:
if not RateLimiter.check_rate_limit(email, max_attempts=10, window_seconds=600):
    flash("Too many login attempts. Try again later.", "danger")
```

### Issue: Prices seem incorrect

**Solution**:
1. Check occupancy data in database
2. Verify date formatting (YYYY-MM-DD)
3. Verify ML model is loaded correctly
4. Check pricing_engine.py for any errors in logs

---

## Testing

### Run Unit Tests
```bash
# Using pytest
pytest tests/ -v

# With coverage
pytest tests/ --cov=flights
```

### Manual Testing Checklist

#### Security
- [ ] Test CSRF token on all forms
- [ ] Test rate limiting on login (5 attempts)
- [ ] Verify password validation requirements
- [ ] Test input sanitization
- [ ] Check security headers in response

#### ML Model
- [ ] Test price prediction accuracy
- [ ] Verify price bounds (80%-200% of base)
- [ ] Test with edge cases
- [ ] Verify confidence scores

#### UI/UX
- [ ] Test responsive design (mobile/tablet/desktop)
- [ ] Test all interactive elements (buttons, forms)
- [ ] Test sort and filter functionality
- [ ] Verify accessibility (keyboard navigation)
- [ ] Test form validation

#### API Endpoints
- [ ] Test `/flights/api/flights/price` endpoint
- [ ] Test `/flights/api/flights/availability` endpoint
- [ ] Test `/flights/api/price-trends` endpoint
- [ ] Verify error handling

---

## Monitoring & Logging

### Viewing Logs

```bash
# View application logs
tail -f flights.log

# View security logs
tail -f security.log

# On Windows PowerShell:
Get-Content security.log -Tail 10 -Wait
```

### Log Levels
- **INFO**: Normal application events
- **WARNING**: Security events, potential issues
- **CRITICAL**: Security breaches, system failures

---

## Performance Tips

1. **Database Indexing**: Create indexes on frequently queried columns
   ```sql
   CREATE INDEX idx_flights_route ON flights(origin_id, destination_id);
   CREATE INDEX idx_bookings_user ON bookings(user_id);
   ```

2. **Caching**: Use Redis for session and price data
   ```bash
   pip install redis flask-caching
   ```

3. **CDN**: Serve static files (CSS, JS, images) from CDN

4. **Database Connection Pooling**: Configure in production
   ```python
   # Use psycopg2 connection pool
   ```

---

## Updates & Maintenance

### Updating Dependencies
```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade Flask

# Update all packages
pip install --upgrade -r requirements.txt
```

### Backup Database
```bash
# PostgreSQL backup
pg_dump -U postgres flights_db > backup_$(date +%Y%m%d).sql

# Restore backup
psql -U postgres flights_db < backup_20250320.sql
```

---

## Support & Documentation

- **Main Documentation**: See `UPGRADE_DOCUMENTATION.md`
- **Security Guide**: See `flights/utils/security.py` docstrings
- **ML Model**: See `flights/utils/train_improved_model.py`
- **Pricing Engine**: See `flights/utils/pricing_engine.py`

---

## Version Information

- **Version**: 2.0.0
- **Python**: 3.8+
- **Flask**: 2.3.2+
- **Last Updated**: March 2025
- **Status**: Production Ready

---

**Questions or Issues?** Check the troubleshooting section or review log files for detailed error messages.
