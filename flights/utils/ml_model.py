import os
import re
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone

# -----------------------
# CONFIG
# -----------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_FILENAME = os.path.join(BASE_DIR, "..", "models", "optimized_flight_price_model.pkl")

# -----------------------
# GLOBALS
# -----------------------
model = None
encoder = None
scaler = None
feature_names = None
load_error = None


# -----------------------
# UTILITY FUNCTIONS
# -----------------------
def time_to_minutes(t):
    if pd.isna(t):
        return 0
    t = str(t).strip()
    m = re.match(r'^\s*(\d{1,2})[:\-\.](\d{1,2})\s*$', t)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    try:
        dt = pd.to_datetime(t)
        return dt.hour * 60 + dt.minute
    except:
        return 0


def baggage_to_kg(b):
    b = str(b).upper().strip()
    if b in ['NAN', '']:
        return 0
    if "+" in b:
        nums = re.findall(r"(\d+\.?\d*)\s*KG", b)
        return sum(float(x) for x in nums) if nums else 0
    if "LUGGAGE" in b or "HAND" in b:
        nums = re.findall(r"(\d+\.?\d*)\s*KG", b)
        return sum(float(x) for x in nums) if nums else 0
    if "KG" in b:
        num = re.findall(r"(\d+\.?\d*)", b)
        return float(num[0]) if num else 0
    if "PIECE" in b:
        pcs = re.findall(r"(\d+)", b)
        return int(pcs[0]) * 23 if pcs else 0
    num = re.findall(r"(\d+\.?\d*)", b)
    return float(num[0]) if num else 0


def get_season(month):
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    else:
        return 'Fall'


def is_weekend(day_of_week):
    return 1 if day_of_week >= 5 else 0


def try_parse_date(inp):
    if pd.isna(inp):
        return None
    s = str(inp).strip()
    patterns = ['%d-%b-%Y', '%d-%b', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%B-%Y']
    for p in patterns:
        try:
            dt = datetime.strptime(s, p)
            if p == '%d-%b' and dt.year == 1900:
                dt = dt.replace(year=datetime.now(timezone.utc).year)
            return dt
        except:
            continue
    try:
        return pd.to_datetime(s)
    except:
        return None


# -----------------------
# MODEL LOADING
# -----------------------
def load_model(path=MODEL_FILENAME):
    global model, encoder, scaler, feature_names, load_error
    try:
        if not os.path.exists(path):
            load_error = f"Model file not found: {path}"
            return
        data = joblib.load(path)
        if isinstance(data, dict):
            model = data.get('model') or data.get('best_model') or data.get('estimator')
            encoder = data.get('encoder') or data.get('onehot')
            scaler = data.get('scaler') or data.get('standardscaler')
            feature_names = data.get('feature_names') or data.get('features')
        else:
            model = data
        if model is None:
            load_error = "Model object not found in .pkl file"
            return
        load_error = None
        print("✅ Model loaded successfully!")
    except Exception as e:
        load_error = f"Failed to load model: {e}"
        print(f"⚠️ Model loading error: {load_error}")


# Load model immediately
load_model()


# -----------------------
# PREDICTION FUNCTION
# -----------------------
def normalize_key(key):
    """Normalize form data keys to handle different formats"""
    key_mapping = {
        'airline_name': 'airline_name',
        'airline name': 'airline_name',
        'Airline Name': 'airline_name',
        'aircraft_type': 'aircraft_type',
        'aircraft type': 'aircraft_type',
        'Aircraft Type': 'aircraft_type',
        'departure_airport': 'departure_airport',
        'departure airport': 'departure_airport',
        'Departure Airport': 'departure_airport',
        'arrival_airport': 'arrival_airport',
        'arrival airport': 'arrival_airport',
        'Arrival Airport': 'arrival_airport',
        'departure_time': 'departure_time',
        'departure time': 'departure_time',
        'Departure Time': 'departure_time',
        'arrival_time': 'arrival_time',
        'arrival time': 'arrival_time',
        'Arrival Time': 'arrival_time',
        'flight_class': 'flight_class',
        'class': 'flight_class',
        'Class': 'flight_class',
        'baggage_allowance': 'baggage_allowance',
        'baggage allowance': 'baggage_allowance',
        'Baggage Allowance': 'baggage_allowance',
        'refundable_status': 'refundable_status',
        'refund_type': 'refundable_status',
        'Refundable Status': 'refundable_status',
        'date': 'date',
        'Date': 'date',
    }
    return key_mapping.get(key, key.lower().replace(' ', '_'))


def validate_prediction_input(data):
    """Validate prediction input and return errors if any"""
    errors = []
    
    if not data.get('departure_airport'):
        errors.append("Departure airport is required")
    if not data.get('arrival_airport'):
        errors.append("Arrival airport is required")
    if data.get('departure_airport') == data.get('arrival_airport'):
        errors.append("Departure and arrival airports must be different")
    if not data.get('departure_time'):
        errors.append("Departure time is required")
    if not data.get('arrival_time'):
        errors.append("Arrival time is required")
    if not data.get('date'):
        errors.append("Flight date is required")
        
    return errors


def predict_from_form(form_data):
    """
    Predict flight price from form data.
    Handles multiple key formats for flexibility.
    
    Args:
        form_data: dict with flight details
        
    Returns:
        float: predicted price or fallback price
    """
    if model is None:
        print("DEBUG: ML model not loaded, using fallback")
    else:
        print("DEBUG: ML model loaded, using it for prediction")

    # Normalize keys and extract data
    normalized = {}
    for key, value in form_data.items():
        norm_key = normalize_key(key)
        if value is not None:
            normalized[norm_key] = str(value).strip() if value else ''
    
    # Build clean data dict with defaults
    data = {
        'Airline Name': normalized.get('airline_name', 'YETI AIRLINES'),
        'Aircraft Type': normalized.get('aircraft_type', 'ATR72'),
        'Departure Airport': normalized.get('departure_airport', 'KATHMANDU').upper(),
        'Arrival Airport': normalized.get('arrival_airport', 'POKHARA').upper(),
        'Departure Time': normalized.get('departure_time', '18:50'),
        'Arrival Time': normalized.get('arrival_time', '19:15'),
        'Class': normalized.get('flight_class', 'E1'),
        'Baggage Allowance': normalized.get('baggage_allowance', '15KG + 5KG'),
        'Refundable Status': normalized.get('refundable_status', 'NonRefundable'),
        'Date': normalized.get('date', '29-Aug')
    }
    
    print(f"DEBUG: Normalized prediction data: {data}")

    try:
        if model is not None:
            dep_minutes = time_to_minutes(data['Departure Time'])
            arr_minutes = time_to_minutes(data['Arrival Time'])
            flight_duration = arr_minutes - dep_minutes
            if flight_duration < 0:
                flight_duration += 1440
            baggage_kg = baggage_to_kg(data['Baggage Allowance'])
            refundable_binary = 1 if 'Refundable' in data['Refundable Status'] and 'Non' not in data['Refundable Status'] else 0
            parsed_date = try_parse_date(data['Date'])
            if parsed_date is None:
                parsed_date = datetime.now()

            basic_features = np.array([[dep_minutes, arr_minutes, baggage_kg, refundable_binary,
                                        parsed_date.day, parsed_date.month, flight_duration, dep_minutes // 60]])
            try:
                prediction = model.predict(basic_features)[0]
                if prediction > 0:
                    print(f"DEBUG: ML prediction successful: {prediction}")
                    return float(prediction)
            except Exception as e:
                print(f"DEBUG: Basic features prediction failed: {e}")

            # Enhanced fallback features
            weekend = is_weekend(parsed_date.weekday())
            season_map = {'Winter': 0, 'Spring': 1, 'Summer': 2, 'Fall': 3}
            season = season_map.get(get_season(parsed_date.month), 1)
            enhanced_features = np.array([[dep_minutes, arr_minutes, baggage_kg, refundable_binary,
                                           parsed_date.day, parsed_date.month, flight_duration, dep_minutes // 60,
                                           weekend, season, parsed_date.weekday(),
                                           1 if dep_minutes // 60 in [7, 8, 9, 17, 18, 19] else 0]])
            try:
                prediction = model.predict(enhanced_features)[0]
                if prediction > 0:
                    print(f"DEBUG: Enhanced ML prediction: {prediction}")
                    return float(prediction)
            except Exception as e:
                print(f"DEBUG: Enhanced features prediction failed: {e}")

        # If all else fails, use fallback
        fallback = get_fallback_prediction(data)
        print(f"DEBUG: Using fallback prediction: {fallback}")
        return fallback

    except Exception as e:
        print(f"[ML_MODEL] Prediction failed: {e}")
        return get_fallback_prediction(data)


def get_fallback_prediction(data):
    """Simple rule-based fallback for Nepal flights"""
    base_price = 4000
    baggage_kg = baggage_to_kg(data['Baggage Allowance'])
    base_price += 10 * baggage_kg
    if 'Refundable' in data['Refundable Status']:
        base_price *= 1.3
    # Add simple route adjustments
    routes = {('KATHMANDU', 'POKHARA'): 3895, ('POKHARA', 'KATHMANDU'): 3895}
    route_price = routes.get((data['Departure Airport'], data['Arrival Airport']))
    if route_price:
        base_price = route_price
    return float(base_price)
