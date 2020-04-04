import sqlite3
"""
Здесь будет город-сад.
"""
def ctrate_base():
    con = sqlite3.connect('base.db')
    cur = con.cursor()
    cur.execute('DROP TABLE IF EXISTS human')

    cur.execute("""CREATE TABLE IF NOT EXISTS human (
    	id INTEGER PRIMARY KEY,
    	genome INTEGER AUTOINCREMENT)""")
