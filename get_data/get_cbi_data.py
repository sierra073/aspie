import urllib2
from bs4 import BeautifulSoup
import json
import pandas as pd
link = "https://am.coinbase.com/index"
from initialize_data import *

r = urllib2.urlopen(link)
soup = BeautifulSoup(r,'html.parser')

alldata = soup.find_all(id = "coinbase_chart_data")
data = json.loads(alldata[0].getText())

df = pd.DataFrame(data, columns=['date','price'])   
df['date'] = pd.to_datetime(df['date'],unit='ms').dt.date

insert_db(df, 'cbi_data')


