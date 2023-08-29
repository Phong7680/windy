import sqlite3, pickledb, time

systemdb = pickledb.load("system.db", False)
data = sqlite3.connect('DATA')
db = data.cursor()

#データベースが存在するかどうかチェック
db.execute("SELECT COUNT(*) FROM sqlite_master"
          "    WHERE TYPE = 'table' AND name = 'tweet'")
row = db.fetchone()

if row[0] != 1:
    db.execute("CREATE TABLE tweet(id int, user name, tweet text, date text)")


now = time.strftime('%Y/%m/%d %H:%M')
sql = "INSERT INTO tweet VALUES(" + str(2) + ",'" + systemdb.get("_login") + "','" + "contents" + "','" + now + "')"
db.execute(sql)
data.commit()

for row in db.execute('SELECT * FROM tweet'):
    print(row)

for row in db.execute("SELECT MAX(id) from tweet"):
    print(row)
    print(row[0])

row = db.execute("SELECT MAX(id) from tweet")
print("number =", row[0])

data.close()