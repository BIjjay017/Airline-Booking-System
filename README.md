# Flight Booking System

A full-featured airline booking web application built with Flask and PostgreSQL, featuring user authentication, flight search, booking management, admin dashboard, and ML-powered price prediction.

## Features

### User Features
- **User Authentication** - Secure signup/login with password validation and hashing
- **Password Recovery** - Email-based password reset functionality
- **Flight Search** - Search flights by origin, destination, and date
- **Booking Management** - Book flights, view booking history, and cancel bookings
- **Mock Payment** - Simulated payment processing for bookings

### Admin Features
- **Dashboard** - Overview of system statistics
- **User Management** - View and delete users
- **Flight Management** - Add, edit, and delete flights
- **Booking Management** - View and manage all bookings
- **ML Price Prediction** - AI-powered flight price suggestions when adding flights

## Tech Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL
- **Authentication**: Werkzeug Security (password hashing)
- **Email**: Flask-Mail with Mailtrap
- **ML**: Scikit-learn, Pandas, NumPy, Joblib
- **Frontend**: HTML, Jinja2 Templates

## Project Structure

```
flights/
├── app.py                 # Application factory and Flask app setup
├── config.py              # Database configuration
├── seed.py                # Database seeding script
├── models/
│   └── optimized_flight_price_model.pkl  # Trained ML model
├── routes/
│   ├── admin.py           # Admin panel routes
│   ├── auth.py            # Authentication routes
│   ├── bookings.py        # Booking management routes
│   └── flights.py         # Flight search routes
├── templates/             # Jinja2 HTML templates
│   ├── admin_*.html       # Admin panel templates
│   ├── base.html          # Base template
│   ├── login.html         # User login
│   ├── signup.html        # User registration
│   ├── search_flights.html
│   ├── booking_history.html
│   └── ...
└── utils/
    └── ml_model.py        # ML model utilities for price prediction
```

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/flight-booking-system.git
   cd flight-booking-system
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-mail psycopg2-binary werkzeug itsdangerous pandas numpy scikit-learn joblib
   ```

4. **Configure the database**
   
   Set environment variables or update `config.py`:
   ```bash
   set DB_NAME=flights
   set DB_USER=postgres
   set DB_PASS=your_password
   set DB_HOST=localhost
   set DB_PORT=5432
   ```

5. **Create database tables**
   
   Create a PostgreSQL database named `flights` and set up the required tables:
   - `users` - User accounts
   - `airports` - Airport information
   - `flights` - Flight schedules
   - `booking_history` - Booking records

6. **Seed the database**
   ```bash
   cd flights
   python seed.py
   ```

7. **Run the application**
   ```bash
   python -m flights.app
   ```

   The application will be available at `http://localhost:5000`

## Usage

### User Access
1. Navigate to `http://localhost:5000`
2. Create an account or log in
3. Search for flights by selecting origin, destination, and date
4. Book available flights and complete mock payment

### Admin Access
1. Navigate to `http://localhost:5000/admin/login`
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin123`
3. Manage users, flights, and bookings from the dashboard

## API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/auth/signup` | GET, POST | User registration |
| `/auth/login` | GET, POST | User login |
| `/auth/logout` | GET | User logout |
| `/auth/forgot_password` | GET, POST | Password reset request |
| `/flights/search` | GET, POST | Search available flights |
| `/bookings/book/<id>` | POST | Book a flight |
| `/bookings/history` | GET | View booking history |
| `/admin/` | GET | Admin dashboard |
| `/admin/users` | GET | List all users |
| `/admin/flights` | GET | List all flights |
| `/admin/bookings` | GET | List all bookings |

## ML Price Prediction

The system includes a machine learning model for predicting flight prices. The model considers:
- Departure and arrival times
- Flight duration
- Baggage allowance
- Route information

The trained model is stored in `models/optimized_flight_price_model.pkl` and is used in the admin panel when adding new flights.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Flask documentation
- PostgreSQL documentation
- Scikit-learn for ML capabilities
