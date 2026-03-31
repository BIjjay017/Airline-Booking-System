
from flask import Blueprint, render_template, request, jsonify
from flights.config import get_db_connection
from flights.utils.pricing_engine import get_pricing_engine
from flights.utils.security import InputValidator, sanitize_request_data
from datetime import date

flights_bp = Blueprint("flights", __name__)

@flights_bp.route("/search", methods=["GET", "POST"])
def search_flights():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch airport codes + names for dropdowns
    cur.execute("SELECT code, name FROM airports ORDER BY code;")
    airports = cur.fetchall()  # [(code, name), ...]

    flights = None  # default: no search yet
    search_params = {}

    if request.method == "POST":
        form_data = sanitize_request_data(request.form.to_dict())
        origin = form_data.get("origin", "").upper()
        destination = form_data.get("destination", "").upper()
        date_selected = form_data.get("date", "")
        try:
            tickets = int(form_data.get("tickets", 1))
        except (TypeError, ValueError):
            tickets = 1

        search_params = {
            'origin': origin,
            'destination': destination,
            'date': date_selected,
            'tickets': tickets
        }

        validation_errors = InputValidator.validate_flight_booking_data(search_params)
        if validation_errors:
            cur.close()
            conn.close()
            return render_template(
                "search_flights_enhanced.html",
                airports=airports,
                flights=[],
                search_params=search_params,
                today=date.today().isoformat(),
                validation_errors=validation_errors
            )

        if origin and destination and date_selected:
            query = """
                SELECT f.flight_id, f.flight_number, ao.code AS origin_code, ao.name AS origin_name,
                       ad.code AS dest_code, ad.name AS dest_name,
                       f.departure_time, f.duration,
                       f.total_seats, f.available_seats, f.price,
                       a.name as airline_name
                FROM flights f
                JOIN airports ao ON f.origin_id = ao.airport_id
                JOIN airports ad ON f.destination_id = ad.airport_id
                LEFT JOIN airlines a ON f.airline_id = a.airline_id
                WHERE ao.code = %s
                  AND ad.code = %s
                  AND DATE(f.departure_time) = %s
                  AND f.available_seats >= %s
                ORDER BY f.departure_time;
            """
            cur.execute(query, (origin, destination, date_selected, tickets))
            flight_rows = cur.fetchall()

            # Add dynamic pricing so the UI reflects route/time demand in real-time.
            pricing_engine = get_pricing_engine()
            flights = []
            for row in flight_rows:
                booking_payload = {
                    "departure_airport": origin,
                    "arrival_airport": destination,
                    "departure_time": row[6].strftime("%H:%M") if hasattr(row[6], "strftime") else str(row[6]),
                    "date": date_selected,
                    "flight_class": "E1",
                    "baggage_allowance": "15KG + 5KG",
                    "refundable_status": "NonRefundable"
                }
                price_result = pricing_engine.get_dynamic_price(booking_payload)
                mutable_row = list(row)
                mutable_row[10] = price_result["final_price"]
                flights.append(tuple(mutable_row))

    cur.close()
    conn.close()

    return render_template(
        "search_flights_enhanced.html",
        airports=airports,
        flights=flights,
        search_params=search_params,
        today=date.today().isoformat()
    )


@flights_bp.route("/api/flights/price", methods=["POST"])
def get_dynamic_price():
    """
    AJAX endpoint for dynamic price calculation
    Accepts flight parameters and returns calculated price with breakdown
    """
    try:
        data = sanitize_request_data(request.get_json(silent=True) or {})
        
        pricing_engine = get_pricing_engine()
        price_result = pricing_engine.get_dynamic_price(data)
        
        return jsonify({
            'success': True,
            'price': price_result['final_price'],
            'base_price': price_result['base_price'],
            'confidence': price_result['confidence'],
            'breakdown': price_result['breakdown'],
            'currency': price_result['currency']
        }), 200
        
    except Exception as e:
        print(f"Price calculation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@flights_bp.route("/api/flights/availability", methods=["POST"])
def get_availability():
    """
    AJAX endpoint for real-time availability data
    """
    try:
        data = sanitize_request_data(request.get_json(silent=True) or {})
        origin = data.get('origin', '').upper()
        destination = data.get('destination', '').upper()
        date_selected = data.get('date', '')
        
        if not all([origin, destination, date_selected]):
            return jsonify({'error': 'Missing parameters'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT f.flight_id, f.flight_number,
                   f.available_seats, f.total_seats,
                   f.departure_time, f.price,
                   a.name as airline_name
            FROM flights f
            JOIN airports ao ON f.origin_id = ao.airport_id
            JOIN airports ad ON f.destination_id = ad.airport_id
            LEFT JOIN airlines a ON f.airline_id = a.airline_id
            WHERE ao.code = %s
              AND ad.code = %s
              AND DATE(f.departure_time) = %s
            ORDER BY f.departure_time;
        """
        
        cur.execute(query, (origin, destination, date_selected))
        flights = cur.fetchall()
        cur.close()
        conn.close()
        
        flight_list = []
        for f in flights:
            occupancy = (((f[3] - f[2]) / f[3]) * 100) if f[3] > 0 else 0
            flight_list.append({
                'flight_id': f[0],
                'flight_number': f[1],
                'available_seats': f[2],
                'total_seats': f[3],
                'occupancy_percent': round(occupancy, 1),
                'departure_time': str(f[4]),
                'base_price': f[5],
                'airline': f[6] or 'Unknown'
            })
        
        return jsonify({
            'success': True,
            'flights': flight_list,
            'timestamp': str(date.today())
        }), 200
        
    except Exception as e:
        print(f"Availability error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@flights_bp.route("/api/price-trends", methods=["POST"])
def get_price_trends():
    """
    AJAX endpoint for price trend analysis
    Shows how prices change over different metrics
    """
    try:
        data = sanitize_request_data(request.get_json(silent=True) or {})
        origin = data.get('origin', '').upper()
        destination = data.get('destination', '').upper()
        
        if not origin or not destination:
            return jsonify({'error': 'Missing parameters'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get price statistics for this route
        query = """
            SELECT 
                AVG(f.price) as avg_price,
                MIN(f.price) as min_price,
                MAX(f.price) as max_price,
                COUNT(*) as flight_count,
                AVG(f.available_seats) as avg_seats
            FROM flights f
            JOIN airports ao ON f.origin_id = ao.airport_id
            JOIN airports ad ON f.destination_id = ad.airport_id
            WHERE ao.code = %s
              AND ad.code = %s
        """
        
        cur.execute(query, (origin, destination))
        stats = cur.fetchone()
        cur.close()
        conn.close()
        
        if stats:
            return jsonify({
                'success': True,
                'stats': {
                    'average_price': round(stats[0], 2) if stats[0] else 0,
                    'minimum_price': round(stats[1], 2) if stats[1] else 0,
                    'maximum_price': round(stats[2], 2) if stats[2] else 0,
                    'flight_count': stats[3],
                    'avg_available_seats': round(stats[4], 1) if stats[4] else 0
                }
            }), 200
        
        return jsonify({'success': False, 'error': 'No flights found'}), 404
        
    except Exception as e:
        print(f"Trends error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
