from flask import flash, Blueprint, render_template, request, redirect, url_for, session
from flights.config import get_db_connection
from datetime import datetime, date, timedelta
from flights.utils.ml_model import predict_from_form
import re


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Hardcoded admin credentials (can be moved to DB later)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ----------------------
# 🔹 Admin Authentication
# ----------------------
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin.dashboard"))
        else:
            error = "Invalid username or password"
    return render_template("admin_login.html", error=error)


@admin_bp.route("/")
def dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("admin.login"))
    return render_template("admin_dashboard.html")


@admin_bp.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin.login"))


# ----------------------
# 🔹 Users CRUD
# ----------------------
@admin_bp.route("/users")
def list_users():
    if not session.get("is_admin"):
        return redirect(url_for("admin.login"))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, name, email FROM users ORDER BY user_id")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin_users.html", users=users)


@admin_bp.route("/users/delete/<int:user_id>")
def delete_user(user_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin.login"))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin.list_users"))


# ----------------------
# 🔹 Flights CRUD
# ----------------------
@admin_bp.route("/flights")
def list_flights():
    if not session.get("is_admin"):
        return redirect(url_for("admin.login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.flight_id, f.flight_number,
       ao.code AS origin_code, ao.city AS origin_city,
       ad.code AS dest_code, ad.city AS dest_city,
       f.departure_time,
       f.departure_time + f.duration AS arrival_time,
       f.duration,
       f.total_seats, f.available_seats, f.price
FROM flights f
JOIN airports ao ON f.origin_id = ao.airport_id
JOIN airports ad ON f.destination_id = ad.airport_id

        ORDER BY f.departure_time;
    """)
    flights = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("admin_flights.html", flights=flights, now=datetime.now())


def baggage_to_kg(b):
    """Convert baggage allowance string to kg"""
    b = str(b).upper().strip()
    if "+" in b:  # e.g., "15KG + 5KG"
        nums = re.findall(r"(\d+\.?\d*)", b)
        return sum(float(x) for x in nums)
    if "KG" in b:
        nums = re.findall(r"(\d+\.?\d*)", b)
        return float(nums[0]) if nums else 0
    if "PIECE" in b:
        nums = re.findall(r"(\d+)", b)
        return int(nums[0]) * 23  # assume 1 piece = 23kg
    return 0



@admin_bp.route("/flights/add", methods=["GET", "POST"])
def add_flight():
    if not session.get("is_admin"):
        return redirect(url_for("admin.login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT airport_id, code, city FROM airports")
    airports = cur.fetchall()

    if request.method == "POST":
        flight_number = request.form["flight_number"]
        origin_id = request.form["origin_id"]
        destination_id = request.form["destination_id"]

        # Map IDs to airport codes
        origin_code = next((a[1] for a in airports if str(a[0]) == origin_id), "UNKNOWN")
        destination_code = next((a[1] for a in airports if str(a[0]) == destination_id), "UNKNOWN")

        departure_time_str = request.form["departure_time"]
        departure_time = datetime.strptime(departure_time_str, "%Y-%m-%dT%H:%M")

        duration_hours = int(request.form.get("duration_minutes", 0))
        duration_minutes = int(request.form.get("duration_minutes", 0))
        arrival_time = departure_time + timedelta(hours=duration_hours, minutes=duration_minutes)

        total_seats = int(request.form["total_seats"])
        flight_class = request.form["class"]
        baggage_allowance = request.form.get("baggage_allowance", "15KG + 5KG")  # keep string format
        refund_type = request.form["refund_type"]
        aircraft_type = request.form.get("aircraft_type", "ATR72")

        # --- Features for ML model ---
        form_data = {
            "Airline Name": "YETI AIRLINES",  # you can make dynamic later
            "Aircraft Type": aircraft_type.strip(),
            "Departure Airport": origin_code.strip().upper(),
            "Arrival Airport": destination_code.strip().upper(),
            "Departure Time": departure_time.strftime("%H:%M"),
            "Arrival Time": arrival_time.strftime("%H:%M"),
            "Class": flight_class.strip(),  # must match model keys exactly
            "Baggage Allowance": baggage_allowance.strip(),  # string format like "15KG + 5KG"
            "Refundable Status": refund_type.strip(),  # "Refundable" / "NonRefundable"
            "Date": departure_time.strftime("%d-%b-%Y")
        }

        # DEBUG: check features sent to ML
        print("DEBUG: Features sent to ML model:", form_data)

        price = predict_from_form(form_data)  # make sure this function expects exactly these keys

        # Prevent past flights
        if departure_time < datetime.now():
            flash("Cannot add a flight in the past!", "danger")
            cur.close()
            conn.close()
            return redirect(url_for("admin.add_flight"))

        duration_str = f"{duration_hours} hours {duration_minutes} minutes"

        # Insert into DB
        cur.execute(
            """
            INSERT INTO flights
                (flight_number, origin_id, destination_id, departure_time, duration,
                 total_seats, available_seats, class, baggage_allowance, refund_type, price)
            VALUES (%s, %s, %s, %s, %s::interval, %s, %s, %s, %s, %s, %s);
            """,
            (
                flight_number, origin_id, destination_id, departure_time, duration_str,
                total_seats, total_seats, flight_class, baggage_allowance, refund_type, price
            )
        )
        conn.commit()

        cur.close()
        conn.close()
        flash(f"Flight added successfully! Predicted price: {price:.2f}", "success")
        return redirect(url_for("admin.list_flights"))

    cur.close()
    conn.close()
    return render_template("admin_add_flight.html", airports=airports)



@admin_bp.route("/flights/edit/<int:flight_id>", methods=["GET", "POST"])
def edit_flight(flight_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin.login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT airport_id, code, city FROM airports")
    airports = cur.fetchall()

    cur.execute("""
       SELECT flight_id, flight_number, origin_id, destination_id, departure_time,
       duration, departure_time + duration AS arrival_time,
       total_seats, available_seats, price
FROM flights
WHERE flight_id = %s;

    """, (flight_id,))
    flight = cur.fetchone()

    # 🚫 Prevent editing past flights
    if flight and flight[4] < datetime.now():
        flash("Cannot edit past flights!", "danger")
        cur.close()
        conn.close()
        return redirect(url_for("admin.list_flights"))

    if request.method == "POST":
        flight_number = request.form["flight_number"]
        origin_id = request.form["origin_id"]
        destination_id = request.form["destination_id"]
        departure_time = datetime.fromisoformat(request.form["departure_time"])
        duration_hours = int(request.form["duration_hours"])
        duration_minutes = int(request.form.get("duration_minutes", 0))
        price = request.form["price"]
        total_seats = request.form["total_seats"]

        # 🚫 Prevent setting departure in the past
        if departure_time < datetime.now():
            flash("Departure time cannot be in the past!", "danger")
            cur.close()
            conn.close()
            return redirect(url_for("admin.edit_flight", flight_id=flight_id))

        # ✅ Recalculate arrival_time
        arrival_time = departure_time + timedelta(hours=duration_hours, minutes=duration_minutes)

        cur.execute("""
            UPDATE flights
SET flight_number = %s, origin_id = %s, destination_id = %s,
    departure_time = %s, duration = %s::interval,
    total_seats = %s, available_seats = %s, price = %s
WHERE flight_id = %s;

        """, (flight_number, origin_id, destination_id, departure_time, arrival_time, price,
              total_seats, total_seats, flight_id))

        conn.commit()
        flash("Flight updated successfully!", "info")
        cur.close()
        conn.close()
        return redirect(url_for("admin.list_flights"))

    cur.close()
    conn.close()
    return render_template("admin_edit_flight.html", flight=flight, airports=airports)


@admin_bp.route("/flights/delete/<int:flight_id>")
def delete_flight(flight_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin.login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT departure_time FROM flights WHERE flight_id = %s", (flight_id,))
    flight = cur.fetchone()

    if flight and flight[0] < datetime.now():
        flash("Cannot delete past flights!", "warning")
        cur.close()
        conn.close()
        return redirect(url_for("admin.list_flights"))

    cur.execute("DELETE FROM flights WHERE flight_id = %s", (flight_id,))
    conn.commit()
    flash("Flight deleted successfully!", "danger")
    cur.close()
    conn.close()
    return redirect(url_for("admin.list_flights", now=datetime.now()))


# ----------------------
# 🔹 Bookings Management
# ----------------------
@admin_bp.route("/bookings")
def list_bookings():
    if not session.get("is_admin"):
        return redirect(url_for("admin.login"))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.booking_id, u.name, f.flight_number, b.status, b.booking_date
        FROM booking_history b
        JOIN users u ON b.user_id = u.user_id
        JOIN flights f ON b.flight_id = f.flight_id
        ORDER BY b.booking_id
    """)
    bookings = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin_bookings.html", bookings=bookings)
