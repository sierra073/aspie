import json
import pandas as pd
import time
import psycopg2
from datetime import datetime

# variables
HOST = '159.89.155.200'
USER = 'sbbw'
PASSWORD = 'cryptofund'
DB = 'cryptometrics'

# convert strings in the form of "[a,b]" to a list
def stringToList(string):
    string = string[1:len(string)-1]
    try:
        if len(string) != 0: 
            tempList = string.split(", ")
            newList = list(map(lambda x: str(x), tempList))
        else:
            newList = []
    except:
        newList = [-9999]
    return(newList)

# Execute a query on a Postgres database and populate a pandas dataframe
def get_table_from_db(query):
    conn = psycopg2.connect( host=HOST, user=USER, password=PASSWORD, dbname=DB , port=5432)
    cur = conn.cursor()
    cur.execute(query)

    names = [x[0] for x in cur.description]
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=names)

    conn.close()
    return df

# populate a Postgres table from a pandas dataframe
def insert_db(df,tablename):
    conn = psycopg2.connect( host=HOST, user=USER, password=PASSWORD, dbname=DB , port=5432)
    cur = conn.cursor()
    #empty the table
    if tablename != 'reddit_posts':
        cur.execute('delete from ' + tablename + ';')
    else:
        cur.execute('''delete from ''' + tablename + ''' where protocol != 'Bitcoin';''')

    columns_list = df.columns.values.tolist()
    columns = ', '.join(map(str, columns_list))
    #build query
    query = '(' + ','.join(["%s"] * len(columns.split(','))) + ')'
    df = df.fillna("NULL")
    final_query = ','.join(cur.mogrify(query, row.values.tolist()) for index, row in df.iterrows())
    final_query = final_query.replace("'NULL'",'NULL')
    #insert into table
    cur.execute('insert into ' + tablename + ' values ' + final_query)
    print("data inserted")

    cur.close()
    conn.commit()
    conn.close()

#### Import input data with Protocols info 
protocols = pd.read_csv("../../data/input/protocols.csv")

protocols['github_repos'] = protocols['github_repos'].apply(lambda x: stringToList(x))
protocols['subreddits'] = protocols['subreddits'].apply(lambda x: stringToList(x))
protocols['stackoverflow'] = protocols['stackoverflow'].apply(lambda x: stringToList(x))
protocols['twitter'] = protocols['twitter'].apply(lambda x: stringToList(x))
protocols['search'] = protocols['search'].apply(lambda x: stringToList(x))
