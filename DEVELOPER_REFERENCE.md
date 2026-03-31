# Flight Booking System - Developer Quick Reference

## 🚀 Quick Start

```bash
# 1. Setup
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 2. Install
pip install -r requirements.txt

# 3. Configure
# Create .env file with required variables

# 4. Train Model
python -m flights.utils.train_improved_model

# 5. Run
python flights/app.py
```

---

## 📁 Key Files & Their Purpose

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `flights/app.py` | Main Flask app | `create_app()` |
| `flights/utils/pricing_engine.py` | Dynamic pricing | `DynamicPricingEngine` |
| `flights/utils/security.py` | Security utilities | `InputValidator`, `RateLimiter` |
| `flights/utils/train_improved_model.py` | ML training | `ImprovedFlightPriceModel` |
| `flights/routes/flights.py` | Flight endpoints | API routes |
| `flights/templates/base.html` | Base template | Security headers, CSRF |

---

## 🔐 Security Quick Reference

### Add CSRF Token to Forms
```html
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <!-- form fields -->
</form>
```

### Validate User Input
```python
from flights.utils.security import InputValidator

errors = InputValidator.validate_email(email)
errors = InputValidator.validate_flight_booking_data(data)
```

### Rate Limit a Function
```python
from flights.utils.security import RateLimiter

if not RateLimiter.check_rate_limit(user_email):
    flash("Too many attempts. Try again later.", "danger")
```

### Check Password Strength
```python
pwd_validation = InputValidator.validate_password(password)
if isinstance(pwd_validation, list):
    errors.extend(pwd_validation)
```

---

## 💰 Dynamic Pricing Quick Reference

### Get Dynamic Price
```python
from flights.utils.pricing_engine import get_pricing_engine

pricing_engine = get_pricing_engine()
result = pricing_engine.get_dynamic_price({
    'departure_airport': 'KTM',
    'arrival_airport': 'PKR',
    'flight_class': 'E1',
    'baggage_allowance': '15KG',
    'refundable_status': 'NonRefundable',
    'date': '2025-04-15'
})

price = result['final_price']
confidence = result['confidence']
breakdown = result['breakdown']
```

### Pricing Factors
```python
# Class: E1(1.0x), E2(1.15x), B(1.35x), B2(1.55x)
# Baggage: <20kg(1.0x), 20-30kg(1.05x), >30kg(1.15x)
# Time: Early(1.0x), Peak(1.2x-1.25x), Night(0.85x)
# Advance: 30+days(0.8x), 7days(0.95x), <7days(1.0x)
# Season: Peak(1.4x), High(1.2x), Standard(1.0x)
# Occupancy: >90%(1.35x), 50%(1.0x), <50%(0.9x)
# Refundable: Yes(1.15x), No(1.0x)
```

---

## 🤖 ML Model Quick Reference

### Train Model
```bash
python -m flights.utils.train_improved_model
```

### Load & Predict
```python
from flights.utils.ml_model import load_model, predict_from_form

# Load on app startup
load_model()

# Make prediction
price = predict_from_form({
    'flight_class': 'E1',
    'departure_airport': 'KTM',
    'arrival_airport': 'PKR',
    'departure_time': '09:00',
    'arrival_time': '09:30',
    'baggage_allowance': '15KG',
    'refundable_status': 'NonRefundable',
    'date': '2025-04-15'
})
```

### Model Accuracy
- **MAE**: < रु500
- **R²**: > 0.85
- **Features**: 14 engineered features
- **Training**: 5,000+ samples

---

## 🎨 UI Components Quick Reference

### Simple Button
```html
<button class="btn btn-primary">Click Me</button>
```

### Flight Search Form
```html
<form method="POST" id="searchForm">
    <select name="origin" required></select>
    <select name="destination" required></select>
    <input type="date" name="date" required>
    <button type="submit">Search</button>
</form>
```

### Price Display
```html
<div class="price-display">
    <strong class="text-primary fs-5">रु {{ price }}</strong>
    <small class="text-muted">Confidence: {{ confidence }}%</small>
</div>
```

### Loading Spinner
```html
<span class="spinner-border spinner-border-sm" id="spinner" 
      style="display:none;"></span>
```

---

## 🔌 API Endpoints Quick Reference

### Dynamic Price
```bash
POST /flights/api/flights/price
Content-Type: application/json

{
  "departure_airport": "KTM",
  "arrival_airport": "PKR",
  "flight_class": "E1",
  "baggage_allowance": "15KG",
  "refundable_status": "NonRefundable",
  "date": "2025-04-15"
}
```

### Price Trends
```bash
POST /flights/api/price-trends
Content-Type: application/json

{
  "origin": "KTM",
  "destination": "PKR"
}
```

### Flight Availability
```bash
POST /flights/api/flights/availability
Content-Type: application/json

{
  "origin": "KTM",
  "destination": "PKR",
  "date": "2025-04-15"
}
```

---

## 📊 Database Quick Reference

### Key Tables
- `users` - User accounts
- `flights` - Flight information
- `airports` - Airport data
- `bookings` - User bookings
- `airlines` - Airline details

### Common Queries

**Get available flights:**
```sql
SELECT * FROM flights 
WHERE origin_id IN (SELECT airport_id FROM airports WHERE code = 'KTM')
  AND destination_id IN (SELECT airport_id FROM airports WHERE code = 'PKR')
  AND DATE(departure_time) = '2025-04-15'
  AND available_seats > 0
ORDER BY departure_time;
```

**Get flight statistics:**
```sql
SELECT 
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM flights
WHERE origin_id = 1 AND destination_id = 2;
```

---

## 🧪 Testing Quick Reference

### Install Test Dependencies
```bash
pip install pytest pytest-cov
```

### Run Tests
```bash
pytest tests/ -v
pytest tests/ --cov=flights
```

### Test Security Input
```python
from flights.utils.security import InputValidator

# Test email
assert InputValidator.validate_email("user@example.com")
assert not InputValidator.validate_email("invalid-email")

# Test airport code
assert InputValidator.validate_airport_code("KTM")
assert not InputValidator.validate_airport_code("INVALID")

# Test flight data
errors = InputValidator.validate_flight_booking_data({
    'origin': 'KTM',
    'destination': 'KTM'  # Invalid
})
assert len(errors) > 0
```

---

## 🐛 Debugging Tips

### Enable Debug Mode
```python
# In app.py
app.run(debug=True)
```

### Check Logs
```bash
# Application logs
tail -f flask.log

# Security logs
tail -f security.log
```

### Debug Template Issues
```python
# In route
print(f"Template context: {locals()}")
```

### Debug ML Model
```python
from flights.utils.ml_model import load_error
if load_error:
    print(f"Model error: {load_error}")
```

---

## 📈 Performance Tips

### Optimize Database Queries
```python
# Good - with index
cur.execute("""
    SELECT * FROM flights 
    WHERE origin_id = %s AND destination_id = %s
""", (origin_id, dest_id))

# Bad - full table scan
cur.execute("SELECT * FROM flights WHERE price > 5000")
```

### Cache Results
```python
# In pricing engine
if not hasattr(get_pricing_engine, 'cache'):
    get_pricing_engine.cache = {}

route_key = (origin, destination)
if route_key in cache:
    return cache[route_key]
```

### Use Connection Pooling
```python
# In production
# pip install psycopg2-pool
from psycopg2 import pool
```

---

## 🚀 Deployment Quick Reference

### Environment Variables
```env
SECRET_KEY=your-secret-key
FLASK_ENV=production
DEBUG=False
DB_NAME=flights_db
DB_USER=postgres
DB_PASS=password
DB_HOST=localhost
MAIL_SERVER=smtp.gmail.com
```

### Run with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 flights.app:create_app()
```

### Docker Deployment
```bash
docker build -t flightbooking .
docker run -p 5000:5000 --env-file .env flightbooking
```

---

## 📚 Common Code Patterns

### Route with Database Query
```python
@app.route('/flights/search', methods=['POST'])
def search_flights():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM flights WHERE ...", params)
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('results.html', flights=results)
```

### Form with CSRF Protection
```python
@app.route('/book', methods=['POST'])
def book_flight():
    # CSRF token validated automatically by Flask-WTF
    flight_id = request.form.get('flight_id')
    # Process booking
    return redirect(url_for('confirmation'))
```

### API Endpoint with JSON
```python
@app.route('/api/price', methods=['POST'])
def get_price():
    data = request.get_json()
    engine = get_pricing_engine()
    result = engine.get_dynamic_price(data)
    return jsonify(result)
```

---

## ⚡ Useful Commands

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install/Update dependencies
pip install -r requirements.txt
pip install --upgrade Flask

# Run tests
pytest -v

# Format code
black flights/

# Check code quality
flake8 flights/

# Generate database backup
pg_dump flights_db > backup.sql

# Start development server
python flights/app.py

# Train ML model
python -m flights.utils.train_improved_model

# View logs
tail -f security.log
```

---

## 📞 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError" | Run `pip install -r requirements.txt` |
| "Database connection failed" | Check DB credentials in `.env` |
| "CSRF token missing" | Add `{{ csrf_token() }}` to form |
| "Model not found" | Run `python -m flights.utils.train_improved_model` |
| "Rate limit exceeded" | Wait 5 minutes or check RateLimiter settings |
| "Price incorrect" | Verify database occupancy data |

---

**Last Updated**: March 2025  
**Version**: 2.0.0  
**Status**: Production Ready ✅
