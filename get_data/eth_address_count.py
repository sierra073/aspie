from initialize_data import *

r = requests.get('https://etherscan.io/chart/address?output=csv',headers=REQUEST_HEADERS,allow_redirects=True)
open('../data/output/ethaddresscount.csv', 'wb').write(r.content)

data = pd.read_csv('../data/output/ethaddresscount.csv')
data = data.drop('UnixTimeStamp',axis=1)
data.columns = ['date','count']
data['protocol']='Ethereum'

insert_db(data,'eth_address_count')