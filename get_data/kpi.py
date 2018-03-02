from initialize_data import *
import pandas as pd


conn = psycopg2.connect( host=HOST, user=USER, password=PASSWORD, dbname=DB , port=5432)
cur = conn.cursor()

cur.execute('''delete from protocols_activity_hist;''')

queryfile=open('kpi.sql', 'r')
query = queryfile.read()
queryfile.close()
cur.execute('insert into protocols_activity_hist ' + query)

cur.close()
conn.commit()
conn.close()

print("kpi done")