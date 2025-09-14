import sqlite3

def main():
    con = sqlite3.connect('buaran.db')
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS sensor(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER,
        voltage REAL,
        temp REAL,
        humid REAL
    )""")
    con.commit()
    cur.execute('DELETE FROM sensor')
    con.commit()
    cur.execute('VACUUM')
    con.commit()
    con.close()
    print('CLEARED buaran.db:sensor')

if __name__ == '__main__':
    main()

