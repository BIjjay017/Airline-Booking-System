"""
Standalone Flight Price Prediction App
Runs separately from the main flights booking app
"""

from flask import Flask, render_template, request, flash
import os
import sys
from datetime import date

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.ml_model import predict_from_form, load_error, validate_prediction_input
from config import get_db_connection

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "prediction-secret-key")


def get_lookup_data():
    """Fetch lookup data from database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get airports
    cur.execute("SELECT airport_id, code, city FROM airports ORDER BY code")
    airports = cur.fetchall()
    
    # Get aircraft types
    cur.execute("SELECT aircraft_id, code, name FROM aircraft_types ORDER BY code")
    aircraft_types = cur.fetchall()
    
    # Get flight classes
    cur.execute("SELECT class_id, code, description FROM flight_classes ORDER BY code")
    flight_classes = cur.fetchall()
    
    # Get baggage options
    cur.execute("SELECT baggage_id, allowance, weight_kg FROM baggage_options ORDER BY weight_kg")
    baggage_options = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return airports, aircraft_types, flight_classes, baggage_options


@app.route("/", methods=["GET", "POST"])
def predict():
    price = None
    
    # Get lookup data from database
    airports, aircraft_types, flight_classes, baggage_options = get_lookup_data()
    
    if request.method == "POST":
        # Build form data for the ML model
        form_data = {
            "aircraft_type": request.form.get("aircraft_type", "ATR72"),
            "departure_airport": request.form.get("departure_airport", "KTM"),
            "arrival_airport": request.form.get("arrival_airport", "PKR"),
            "departure_time": request.form.get("departure_time", "09:00"),
            "arrival_time": request.form.get("arrival_time", "09:30"),
            "flight_class": request.form.get("flight_class", "E1"),
            "baggage_allowance": request.form.get("baggage_allowance", "15KG + 5KG"),
            "refundable_status": request.form.get("refundable_status", "NonRefundable"),
            "date": request.form.get("date", date.today().strftime("%Y-%m-%d"))
        }
        
        # Validate input
        errors = validate_prediction_input(form_data)
        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            try:
                price = predict_from_form(form_data)
                if price:
                    flash("Prediction successful!", "success")
                else:
                    flash("Could not generate prediction", "warning")
            except Exception as e:
                flash(f"Prediction error: {str(e)}", "danger")
                print(f"Error: {e}")
    
    return render_template(
        "predict.html",
        price=price,
        load_error=load_error,
        airports=airports,
        aircraft_types=aircraft_types,
        flight_classes=flight_classes,
        baggage_options=baggage_options,
        today=date.today().isoformat()
    )


if __name__ == "__main__":
    print("🚀 Starting Flight Price Prediction Server...")
    print("📍 Access at: http://127.0.0.1:5001")
    app.run(debug=True, host="127.0.0.1", port=5001)
