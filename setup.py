import sqlite3
# conn = sqlite3.connect('launcbot.db')
conn = sqlite3.connect(':memory:')


c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS servers(
    sid INTEGER NOT NULL PRIMARY KEY,
    prefix TEXT (16),
    notifyrole INTEGER
) WITHOUT ROWID;""")

c.execute("""CREATE TABLE IF NOT EXISTS channels(
    cid INTEGER NOT NULL PRIMARY KEY,
    alert INTEGER,
    disabled INTEGER
) WITHOUT ROWID;""")

c.execute("""CREATE TABLE IF NOT EXISTS launches(
    lid INTEGER NOT NULL PRIMARY KEY,
    name TEXT,
    description TEXT,
    photo TEXT
) WITHOUT ROWID;""")

conn.commit()
conn.close()
