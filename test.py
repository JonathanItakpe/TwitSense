#
# Small script to show PostgreSQL and Pyscopg together
#

import psycopg2

try:
    conn = psycopg2.connect(database='twitsense', user='postgres', password='C@ntH@ck', host='localhost')
except:
    print "I am unable to connect to the database"

cur = conn.cursor()

cur.execute("""SELECT tweet_text, sentiment from extend_train""")

rows = cur.fetchall()

print rows

for row in rows:
    print "   ", row[0]
