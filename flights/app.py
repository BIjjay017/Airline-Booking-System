from flask import Flask, redirect, url_for, render_template_string
from flask_mail import Mail
from flights.routes.admin import admin_bp
from flights.routes.auth import auth_bp
from flights.routes.flights import flights_bp
from flights.routes.bookings import bookings_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = "289102891728942"

    # Email config
    # Looking to send emails in production? Check out our Email API/SMTP product!
    app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = '1d38fb15116214'
    app.config['MAIL_PASSWORD'] = 'c90100fde4c206'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False

    mail = Mail(app)
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(flights_bp, url_prefix="/flights")
    app.register_blueprint(bookings_bp, url_prefix="/bookings")
    app.register_blueprint(admin_bp)

    # Home page redirects to login
    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    # Optional: simple navigation page for testing
    @app.route("/menu")
    def menu():
        return render_template_string("""
            <h1>Dummy Airline Booking System</h1>
            <ul>
                <li><a href="{{ url_for('auth.signup') }}">Signup</a></li>
                <li><a href="{{ url_for('auth.login') }}">Login</a></li>
                <li><a href="{{ url_for('flights.search_flights') }}">Search Flights</a></li>
                <li><a href="{{ url_for('bookings.view_history') }}">Booking History</a></li>
            </ul>
        """)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
