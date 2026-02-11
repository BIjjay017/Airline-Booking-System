
from flask import Blueprint, render_template, request
from flights.config import get_db_connection
from datetime import date, timedelta

flights_bp = Blueprint("flights", __name__)

@flights_bp.route("/search", methods=["GET", "POST"])
def search_flights():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch airport codes + names for dropdowns
    cur.execute("SELECT code, name FROM airports ORDER BY code;")
    airports = cur.fetchall()  # [(code, name), ...]

    flights = None  # default: no search yet

    if request.method == "POST":
        origin = request.form["origin"]
        destination = request.form["destination"]
        date_selected = request.form["date"]
        tickets = int(request.form["tickets"])

        query = """
            SELECT f.flight_id, f.flight_number, ao.code AS origin_code, ao.name AS origin_name,
                   ad.code AS dest_code, ad.name AS dest_name,
                   f.departure_time, f.duration,
                   f.total_seats, f.available_seats, f.price
            FROM flights f
            JOIN airports ao ON f.origin_id = ao.airport_id
            JOIN airports ad ON f.destination_id = ad.airport_id
            WHERE ao.code = %s
              AND ad.code = %s
              AND DATE(f.departure_time) = %s
              AND f.available_seats >= %s
            ORDER BY f.departure_time;
        """
        cur.execute(query, (origin, destination, date_selected, tickets))
        flights = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "search_flights.html",
        airports=airports,
        flights=flights,
        today=date.today().isoformat()
    )