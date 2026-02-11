from config import get_db_connection
from datetime import datetime, timedelta

def seed_airports():
    airports = [
        ('KTM', 'Tribhuvan International Airport', 'Kathmandu'),
        ('PKR', 'Pokhara International Airport', 'Pokhara'),
        ('BWA', 'Gautam Buddha International Airport', 'Bhairahawa'),
        ('BDP', 'Bhadrapur Airport', 'Jhapa'),
        ('BIR', 'Biratnagar Airport', 'Biratnagar'),
        ('LUK', 'Tenzing-Hillary Airport', 'Solukhumbu'),
        ('BJU', 'Bajura Airport', 'Bajura'),
        ('KEP', 'Nepalgunj Airport', 'Banke'),
        ('RHP', 'Ramechhap Airport', 'Ramechhap'),
    ]

    conn = get_db_connection()
    cur = conn.cursor()

    for code, name, city in airports:
        cur.execute(
            """
            INSERT INTO airports (code, name, city) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (code) DO NOTHING
            """,
            (code, name, city),
        )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Airports seeded successfully!")


def seed_flights():
    conn = get_db_connection()
    cur = conn.cursor()

    # flights = [
    #     (DA'KTM', 'PKR', datetime.now() + timedelta(days=1, hours=9), datetime.now() + timedelta(days=1, hours=10), 100),
    #     ('PKR', 'KTM', datetime.now() + timedelta(days=1, hours=15), datetime.now() + timedelta(days=1, hours=16), 100),
    #     ('KTM', 'BWA', datetime.now() + timedelta(days=2, hours=8), datetime.now() + timedelta(days=2, hours=9), 120),
    #     ('BWA', 'KTM', datetime.now() + timedelta(days=2, hours=17), datetime.now() + timedelta(days=2, hours=18), 120),
    #     ('KTM', 'BIR', datetime.now() + timedelta(days=3, hours=7), datetime.now() + timedelta(days=3, hours=8), 150),
    # ]
    #
    # for dep_code, arr_code, dep_time, arr_time, price in flights:
    #     # Look up airport IDs by code
    #     cur.execute("SELECT airport_id FROM airports WHERE code = %s", (dep_code,))
    #     dep_id = cur.fetchone()[0]
    #
    #     cur.execute("SELECT airport_id FROM airports WHERE code = %s", (arr_code,))
    #     arr_id = cur.fetchone()[0]
    #
    #     cur.execute(
    #         """
    #         INSERT INTO flights (flight_number,destination_id, origin_id, departure_time, arrival_time, price)
    #         VALUES (%s, %s, %s, %s, %s)
    #         ON CONFLICT DO NOTHING
    #         """,
    #         (dep_id, arr_id, dep_time, arr_time, price),
    #     )
    #
    # conn.commit()
    # cur.close()
    # conn.close()
    # print("✅ Flights seeded successfully!")


if __name__ == "__main__":
    seed_airports()
    # seed_flights()
    print("🎉 Database seeding completed!")
