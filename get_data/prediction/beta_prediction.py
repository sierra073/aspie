from initialize_data import * 

queryfile=open('prices_and_index_hist.sql', 'r')
query = queryfile.read()
queryfile.close()

data = get_table_from_db(query)