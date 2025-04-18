from src.db import get_db_connection

def create_table():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            data XML
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Table 'products' created.")

if __name__ == "__main__":
    create_table()
