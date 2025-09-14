import sqlite3

RIVER_DBS = [
    'buaran.db',
    'cakung.db',
    'cilliwung.db',
    'kalimalang.db',
    'sunter.db',
]

def clear_sensor_table(db_path: str):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS sensor(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER,
            voltage REAL,
            temp REAL,
            humid REAL,
            ampere REAL,
            power REAL,
            co2e REAL
        )"""
    )
    con.commit()
    cur.execute('DELETE FROM sensor')
    con.commit()
    cur.execute('VACUUM')
    con.commit()
    con.close()
    print(f'CLEARED {db_path}: sensor')

def clear_prediction(db_path: str):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS prediction(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            text TEXT
        )"""
    )
    con.commit()
    cur.execute('DELETE FROM prediction')
    con.commit()
    cur.execute('VACUUM')
    con.commit()
    con.close()
    print(f'CLEARED {db_path}: prediction')

def main():
    for db in RIVER_DBS:
        try:
            clear_sensor_table(db)
        except Exception as e:
            print(f'ERROR clearing {db}: {e}')

    # central DB
    try:
        clear_sensor_table('sensor.db')
    except Exception as e:
        print(f'ERROR clearing sensor.db sensor: {e}')
    try:
        clear_prediction('sensor.db')
    except Exception as e:
        print(f'ERROR clearing sensor.db prediction: {e}')

if __name__ == '__main__':
    main()

