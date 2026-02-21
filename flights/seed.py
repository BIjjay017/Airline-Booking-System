from config import get_db_connection


def seed_airports():
    """Seed airports table with Nepal airport data"""
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


if __name__ == "__main__":
    seed_airports()
    print("🎉 Database seeding completed!")
