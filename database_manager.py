import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Establish a connection to the Neon database."""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Create appointments table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            contact TEXT NOT NULL,
            service TEXT NOT NULL,
            doctor TEXT NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def add_appointment(name, contact, service, doctor, date, time):
    """Add a new appointment to the database."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO appointments (name, contact, service, doctor, date, time)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (name, contact, service, doctor, date, time))
    
    conn.commit()
    cur.close()
    conn.close()

def get_all_appointments():
    """Retrieve all appointments from the database."""
    conn = get_connection()
    # Use RealDictCursor to return results as dictionaries
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT * FROM appointments ORDER BY created_at DESC")
    appointments = cur.fetchall()
    
    cur.close()
    conn.close()
    return appointments

# Initialize the DB if this script is run directly
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
