from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from flights.config import get_db_connection
from decimal import Decimal
from datetime import datetime, timedelta

bookings_bp = Blueprint("bookings", __name__)


# ---------------------------
# 🔹 View Booking History
# ---------------------------
@bookings_bp.route("/history")
def view_history():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
       SELECT b.booking_id,
        f.flight_number, 
       ao.code AS origin_code,
        ad.code AS dest_code,
       f.departure_time, 
       (f.departure_time + f.duration) AS arrival_time,
       b.booking_date,
       b.refund_amount, 
       b.status,
       f.duration
FROM booking_history b
JOIN flights f ON b.flight_id = f.flight_id
JOIN airports ao ON f.origin_id = ao.airport_id
JOIN airports ad ON f.destination_id = ad.airport_id
WHERE b.user_id = %s
ORDER BY b.booking_date DESC
 """, (session["user_id"],))
    bookings = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("booking_history.html", bookings=bookings)


# ---------------------------
# 🔹 Book Flight
# ---------------------------
@bookings_bp.route("/book/<int:flight_id>", methods=["POST", "GET"])
def book_flight(flight_id):
    if "user_id" not in session:
        flash("You must log in to book a flight.", "warning")
        return redirect(url_for("auth.login", next=url_for("bookings.book_flight", flight_id=flight_id)))

    tickets = request.form.get("tickets") or request.args.get("tickets") or 1
    tickets = int(tickets)

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    # Check availability
    cur.execute("SELECT available_seats FROM flights WHERE flight_id = %s", (flight_id,))
    flight = cur.fetchone()

    if not flight or flight[0] < tickets:
        flash("Not enough seats available.", "danger")
        cur.close()
        conn.close()
        return redirect(url_for("flights.search_flights"))

    # Create booking with "pending" status (no seat deduction yet)
    cur.execute("""
        INSERT INTO booking_history (user_id, flight_id, booking_date, status, last_modified, tickets)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING booking_id
    """, (user_id, flight_id, datetime.now(), "pending", datetime.now(), tickets))

    booking_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    # Redirect to mock payment page
    return redirect(url_for("bookings.mock_payment", booking_id=booking_id))

@bookings_bp.route("/pay/<int:booking_id>", methods=["GET", "POST"])
def mock_payment(booking_id):
    if "user_id" not in session:
        flash("Please log in to complete payment.", "warning")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Get booking + flight details
    cur.execute("""
        SELECT b.booking_id, b.status, b.tickets, f.flight_id, f.flight_number, f.price, f.available_seats
        FROM booking_history b
        JOIN flights f ON b.flight_id = f.flight_id
        WHERE b.booking_id = %s AND b.user_id = %s
    """, (booking_id, session["user_id"]))
    booking = cur.fetchone()

    if not booking:
        cur.close()
        conn.close()
        flash("Booking not found.", "danger")
        return redirect(url_for("bookings.view_history"))

    booking_id, status, tickets, flight_id, flight_number, price, available_seats = booking

    if request.method == "POST":
        action = request.form.get("action")

        if action == "pay":
            # Check seats again before confirming
            if available_seats < tickets:
                flash("Payment failed: Not enough seats available.", "danger")
                cur.close()
                conn.close()
                return redirect(url_for("bookings.view_history"))

            # Mark booking confirmed + deduct seats
            cur.execute("UPDATE booking_history SET status = %s, last_modified = %s WHERE booking_id = %s",
                        ("confirmed", datetime.now(), booking_id))
            cur.execute("UPDATE flights SET available_seats = available_seats - %s WHERE flight_id = %s",
                        (tickets, flight_id))

            conn.commit()
            cur.close()
            conn.close()

            flash("Payment successful! Booking confirmed.", "success")
            return redirect(url_for("bookings.view_history"))

        elif action == "cancel":
            # Cancel booking
            cur.execute("UPDATE booking_history SET status = %s, last_modified = %s WHERE booking_id = %s",
                        ("cancelled", datetime.now(), booking_id))
            conn.commit()
            cur.close()
            conn.close()

            flash("Payment cancelled. Booking not completed.", "warning")
            return redirect(url_for("bookings.view_history"))

    cur.close()
    conn.close()

    # Render mock payment page
    return render_template("mock_payment.html", booking=booking)

# ---------------------------
# 🔹 Cancel Booking + Refund
# ---------------------------

@bookings_bp.route("/cancel/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    if "user_id" not in session:
        flash("Please log in to cancel a booking.")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch booking details
    cur.execute("""
        SELECT b.booking_id, b.booking_date, b.status, f.price
        FROM booking_history b
        JOIN flights f ON b.flight_id = f.flight_id
        WHERE b.booking_id = %s AND b.user_id = %s
    """, (booking_id, session["user_id"]))
    booking = cur.fetchone()

    if not booking:
        cur.close()
        conn.close()
        flash("Booking not found.")
        return redirect(url_for("bookings.view_history"))

    booking_id, booking_time, status, price = booking
    price = Decimal(price)

    # Prevent cancelling twice
    if status == "cancelled":
        cur.close()
        conn.close()
        flash("This booking is already cancelled.")
        return redirect(url_for("bookings.view_history"))

    # Check cancellation window (24 hrs from booking_time)
    booking_time = booking_time.replace(tzinfo=None)  # strip timezone if present
    now = datetime.now()
    if now > booking_time + timedelta(hours=24):
        cur.close()
        conn.close()
        flash("Cancellation window (24 hours) has expired.")
        return redirect(url_for("bookings.view_history"))

    # Refund calculation (80%)
    refund_rate = Decimal("0.8")
    refund_amount = price * refund_rate

    # Update status instead of deleting
    cur.execute("UPDATE booking_history SET status = %s WHERE booking_id = %s", ("cancelled", booking_id))
    conn.commit()

    cur.close()
    conn.close()

    flash(f"Booking {booking_id} has been cancelled. Refund amount: ${refund_amount:.2f}")
    return redirect(url_for("bookings.view_history"))

