import sys
import sqlite3

def clear_db(db_path: str):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS sensor(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER,
        voltage REAL,
        temp REAL,
        humid REAL
    )"""
    )
    con.commit()
    cur.execute('DELETE FROM sensor')
    con.commit()
    cur.execute('VACUUM')
    con.commit()
    con.close()
    print(f'CLEARED {db_path}:sensor')

if __name__ == '__main__':
    db = sys.argv[1] if len(sys.argv) > 1 else 'sensor.db'
    clear_db(db)

