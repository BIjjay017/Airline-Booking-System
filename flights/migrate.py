"""
Database Migration Script
Run this file to create all necessary database tables.
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )


def create_tables():
    """Create all required database tables"""
    
    conn = get_db_connection()
    cur = conn.cursor()

    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ Users table created/verified")

    # Create airports table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS airports (
            airport_id SERIAL PRIMARY KEY,
            code VARCHAR(10) UNIQUE NOT NULL,
            name VARCHAR(150) NOT NULL,
            city VARCHAR(100) NOT NULL
        );
    """)
    print("✅ Airports table created/verified")

    # Create flights table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            flight_id SERIAL PRIMARY KEY,
            flight_number VARCHAR(20) NOT NULL,
            origin_id INTEGER REFERENCES airports(airport_id) ON DELETE CASCADE,
            destination_id INTEGER REFERENCES airports(airport_id) ON DELETE CASCADE,
            departure_time TIMESTAMP NOT NULL,
            duration INTERVAL NOT NULL,
            total_seats INTEGER NOT NULL DEFAULT 100,
            available_seats INTEGER NOT NULL DEFAULT 100,
            price DECIMAL(10, 2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ Flights table created/verified")

    # Create booking_history table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS booking_history (
            booking_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
            flight_id INTEGER REFERENCES flights(flight_id) ON DELETE CASCADE,
            booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'pending',
            refund_amount DECIMAL(10, 2) DEFAULT 0,
            last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tickets INTEGER DEFAULT 1
        );
    """)
    print("✅ Booking history table created/verified")

    # Create airlines lookup table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS airlines (
            airline_id SERIAL PRIMARY KEY,
            code VARCHAR(10) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL
        );
    """)
    print("✅ Airlines table created/verified")

    # Create aircraft_types lookup table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aircraft_types (
            aircraft_id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100)
        );
    """)
    print("✅ Aircraft types table created/verified")

    # Create flight_classes lookup table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS flight_classes (
            class_id SERIAL PRIMARY KEY,
            code VARCHAR(10) UNIQUE NOT NULL,
            description VARCHAR(100)
        );
    """)
    print("✅ Flight classes table created/verified")

    # Create baggage_options lookup table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS baggage_options (
            baggage_id SERIAL PRIMARY KEY,
            allowance VARCHAR(50) UNIQUE NOT NULL,
            weight_kg INTEGER
        );
    """)
    print("✅ Baggage options table created/verified")

    # Seed default data for lookup tables
    seed_lookup_tables(cur)

    conn.commit()
    cur.close()
    conn.close()
    
    print("\n🎉 All database tables migrated successfully!")


def seed_lookup_tables(cur):
    """Seed lookup tables with default values"""
    
    # Airlines
    airlines = [
        ('YT', 'Yeti Airlines'),
        ('BG', 'Buddha Air'),
        ('SH', 'Shree Airlines'),
        ('TG', 'Tara Air'),
        ('SA', 'Saurya Airlines'),
        ('SM', 'Summit Air'),
        ('GK', 'Guna Airlines')
    ]
    for code, name in airlines:
        cur.execute("""
            INSERT INTO airlines (code, name) VALUES (%s, %s)
            ON CONFLICT (code) DO NOTHING
        """, (code, name))
    print("✅ Airlines seeded")

    # Aircraft Types
    aircraft_types = [
        ('ATR72', 'ATR 72-500'),
        ('ATR42', 'ATR 42-320'),
        ('CRJ200', 'Bombardier CRJ200'),
        ('Q400', 'De Havilland Q400'),
        ('A320', 'Airbus A320'),
        ('B737', 'Boeing 737-800')
    ]
    for code, name in aircraft_types:
        cur.execute("""
            INSERT INTO aircraft_types (code, name) VALUES (%s, %s)
            ON CONFLICT (code) DO NOTHING
        """, (code, name))
    print("✅ Aircraft types seeded")

    # Flight Classes
    flight_classes = [
        ('A', 'First Class Discounted'),
        ('B', 'Economy Plus'),
        ('C', 'Business Class'),
        ('D', 'Economy Discounted'),
        ('E', 'Economy'),
        ('E1', 'Economy Standard'),
        ('F', 'First Class'),
        ('G', 'Group Economy'),
        ('I', 'Business Discounted'),
        ('N', 'Normal'),
        ('S', 'Economy Saver'),
        ('T', 'Economy Promo'),
        ('Y', 'Economy Full')
    ]
    for code, desc in flight_classes:
        cur.execute("""
            INSERT INTO flight_classes (code, description) VALUES (%s, %s)
            ON CONFLICT (code) DO NOTHING
        """, (code, desc))
    print("✅ Flight classes seeded")

    # Baggage Options
    baggage_options = [
        ('15KG + 5KG', 20),
        ('20KG', 20),
        ('25KG', 25),
        ('30KG', 30),
        ('5KG', 5),
        ('10KG', 10),
        ('1 Piece (23KG)', 23),
        ('2 Pieces (46KG)', 46)
    ]
    for allowance, weight in baggage_options:
        cur.execute("""
            INSERT INTO baggage_options (allowance, weight_kg) VALUES (%s, %s)
            ON CONFLICT (allowance) DO NOTHING
        """, (allowance, weight))
    print("✅ Baggage options seeded")


def drop_tables():
    """Drop all tables (use with caution!)"""
    
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS booking_history CASCADE;")
    cur.execute("DROP TABLE IF EXISTS flights CASCADE;")
    cur.execute("DROP TABLE IF EXISTS airports CASCADE;")
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")
    cur.execute("DROP TABLE IF EXISTS airlines CASCADE;")
    cur.execute("DROP TABLE IF EXISTS aircraft_types CASCADE;")
    cur.execute("DROP TABLE IF EXISTS flight_classes CASCADE;")
    cur.execute("DROP TABLE IF EXISTS baggage_options CASCADE;")

    conn.commit()
    cur.close()
    conn.close()
    
    print("⚠️ All tables dropped!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        confirm = input("Are you sure you want to drop all tables? (yes/no): ")
        if confirm.lower() == "yes":
            drop_tables()
    else:
        create_tables()
