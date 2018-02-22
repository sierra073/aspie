from initialize_data import *
from datetime import datetime
import coinmarketcap_usd_history

market_cap_volume =  get_table_from_db('select * from market_cap_volume;')

market_cap_volume_data = pd.DataFrame([])

for index, row in protocols.iterrows():
    if str(row['ticker_symbol']) != 'nan':
        p = row['protocol']
        if p=='Raiden':
            p='Raiden-Network-Token'
        if p=='Bitcoin Cash':
            p='Bitcoin-Cash'
        if p=='Raiblocks':
            p='nano'
        df = coinmarketcap_usd_history.main([p,'2017-01-01',str(datetime.now().date()),'--dataframe'])
        df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'market_cap','avg']
        df['protocol'] = row['protocol']
        print(row['protocol'])
        market_cap_volume_data = market_cap_volume_data.append(df)

cols = market_cap_volume_data.columns.tolist()
cols = cols[-1:] + cols[:-1]
market_cap_volume_data = market_cap_volume_data[cols]

# export to Postgres
insert_db(market_cap_volume_data,'market_cap_volume')