from src.db import get_db_connection
def create_table():
    conn = get_db_connection()
    cur = conn.cursor()

    # Products table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            data XML
        );
    """)

    # Commands table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id SERIAL PRIMARY KEY,
            data XML
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Tables 'products' and 'commands' created.")

if __name__ == "__main__":
    create_table()
