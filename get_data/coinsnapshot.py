from initialize_data import *

def get_all_data(protocol):
    symbol = protocols[protocols.protocol==protocol].ticker_cc.item()

    if str(symbol) != 'nan':
        if symbol == 'MKR' or symbol == 'FIL' or symbol == 'RDN*':
            url = 'https://www.cryptocompare.com/api/data/coinsnapshot/?fsym='+ symbol + '&tsym=USDT'
        else:
            url = 'https://www.cryptocompare.com/api/data/coinsnapshot/?fsym='+ symbol + '&tsym=USD'

        print "Requesting: " + url
        r = requests.get(url,headers=REQUEST_HEADERS)
        alldata = json.loads(r.content)
        alldata = pd.DataFrame(alldata)

        alldata = alldata['Data']
        alldata['nExchanges'] = len(alldata.loc['Exchanges'])
        alldata = pd.DataFrame(alldata).transpose()

        if 'Algorithm' not in alldata.columns:
            alldata['Algorithm'] = None
        if 'BlockNumber' not in alldata.columns:
            alldata['BlockNumber'] = 0
        if 'BlockReward' not in alldata.columns:
            alldata['BlockReward'] = 0
        if 'NetHashesPerSecond' not in alldata.columns:
            alldata['NetHashesPerSecond'] = 0
        if 'ProofType' not in alldata.columns:
            alldata['ProofType'] = None
        if 'TotalCoinsMined' not in alldata.columns:
            alldata['TotalCoinsMined'] = 0

        return alldata

    return pd.DataFrame([])

def get_social_data(protocol):
    id = protocols[protocols.protocol==protocol].id_cc.item()

    if str(id) != 'nan':
        url = 'https://www.cryptocompare.com/api/data/socialstats/?id=' + str(int(id))
        print "Requesting: " + url
        r = requests.get(url,headers=REQUEST_HEADERS)
        alldata = json.loads(r.content)

        if len(alldata['Data']['Twitter']) > 1:
            socialdata = pd.Series(alldata['Data']['Twitter']['statuses'], index=['twitter_statuses'])
        else: 
            socialdata = pd.Series(0, index=['twitter_statuses'])
        if len(alldata['Data']['Reddit']) > 2:
            socialdata['reddit_posts_per_day'] = alldata['Data']['Reddit']['posts_per_day']
            socialdata['reddit_comments_per_day'] = alldata['Data']['Reddit']['comments_per_day']
        else:
            socialdata['reddit_posts_per_day'] = 0
            socialdata['reddit_comments_per_day'] = 0     
        if len(alldata['Data']['Facebook']) > 1:
            socialdata['facebook_likes'] = alldata['Data']['Facebook']['likes']
        else:
            socialdata['facebook_likes'] = 0
        return pd.DataFrame(socialdata).transpose()

    return pd.DataFrame([])


protocols_list = list(protocols['protocol'])
for protocol in protocols_list:
    print(get_all_data(protocol))
    print(get_social_data(protocol))