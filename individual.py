from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, NumeralTickFormatter 
from bokeh.models.callbacks import CustomJS
from bokeh.models.tools import HoverTool, BoxZoomTool, WheelZoomTool, PanTool, ResetTool, SaveTool
from bokeh.models.widgets import Div, DataTable, TableColumn, Select, CheckboxGroup, DateRangeSlider
from bokeh.models.layouts import Spacer
from bokeh.layouts import layout
from bokeh.plotting import figure
from datetime import datetime, date
from math import radians
from bokeh.layouts import row, column, widgetbox
from initialize_data import *
import psycopg2
from functools import partial

#### Variables

HOST = '159.89.155.200'
USER = 'sbbw'
PASSWORD = 'cryptofund'
DB = 'cryptometrics'

div_style = """
    <link rel="stylesheet" type="text/css" href="//fonts.googleapis.com/css?family=Open+Sans" />
    <style>
        .sans-font {
            font-family: "Open Sans"; }
        *{
            border: 0; 
            margin: 0; 
            margin: 0; }
    </style>
"""

conn = psycopg2.connect( host=HOST, user=USER, password=PASSWORD, dbname=DB , port=5432)
cur = conn.cursor()

protocols_list = list(protocols['protocol'])

#### Set up widgets, figures, static titles
protocolSelect = Select(title="Select a protocol:", value='Ethereum', options=protocols_list)
protocolTitle = Div(text=div_style + '<div class="sans-font"><h1></h1></div>')
Price = Div(text=div_style + '<div class="sans-font"><h3>Price (USD)</h3></div>')  
Pricev = Div(text=div_style + '<div class="sans-font"><p></p></div>')     
Algorithm = Div(text=div_style + '<div class="sans-font"><h3>Algorithm</h3></div>')  
Algorithmv = Div(text=div_style + '<div class="sans-font"><p></p></div>')                                                   
BlockNumber =  Div(text=div_style + '<div class="sans-font"><h3>Block Number</h3></div>')    
BlockNumberv = Div(text=div_style + '<div class="sans-font"><p></p></div>')                                                
BlockReward =  Div(text=div_style + '<div class="sans-font"><h3>Block Reward</h3></div>')   
BlockRewardv = Div(text=div_style + '<div class="sans-font"><p></p></div>')                                                                
NetHashesPerSecond = Div(text=div_style + '<div class="sans-font"><h3>Net Hashes per Second</h3></div>')  
NetHashesPerSecondv = Div(text=div_style + '<div class="sans-font"><p></p></div>')                                   
ProofType = Div(text=div_style + '<div class="sans-font"><h3>Proof Type</h3></div>')      
ProofTypev = Div(text=div_style + '<div class="sans-font"><p></p></div>')                                                       
TotalCoinsMined = Div(text=div_style + '<div class="sans-font"><h3>Total Coins Mined</h3></div>')  
TotalCoinsMinedv = Div(text=div_style + '<div class="sans-font"><p></p></div>')                                            
NumberofExchanges = Div(text=div_style + '<div class="sans-font"><h3>Number of Exchanges</h3></div>') 
NumberofExchangesv = Div(text=div_style + '<div class="sans-font"><p></p></div>')                                                         
AdditionalSocialData = Div(text=div_style + '<div class="sans-font"><h3>Additional Social Data</h3></div>')

asosource = ColumnDataSource(dict(twitter_statuses=[],reddit_comments_per_day=[],facebook_likes=[]))
asocolumns = [
        TableColumn(field="twitter_statuses", title="Twitter Statuses"),
        TableColumn(field="reddit_comments_per_day", title="Reddit Comments per Day"),
        TableColumn(field="facebook_likes", title="Facebook Likes")
    ]
asostats = DataTable(source=asosource, columns=asocolumns, fit_columns=True, row_headers=False, width=540, height=100)
           
tmetric = Select(value='Total Volume', options=['Total Volume', 'Market Cap', 'Average Daily Price'])
gmetric = Select(value='Commits', options=['Commits', 'Stars', 'StackOverflow Questions'])
sometric = Select(value='Search Interest', options=['Reddit Posts', 'Reddit Subscribers', 'Twitter Followers', 'Search Interest', 'HackerNews Stories'])

gfig=figure()
sofig=figure()
tfig=figure()

gsection_title = Div(text=div_style + '<div class="sans-font">' + '<h3>GitHub and StackOverflow Activity</h3></div>')
sosection_title = Div(text=div_style + '<div class="sans-font">' + '<h3>Social Media and Search Activity</h3></div>')
tsection_title = Div(text=div_style + '<div class="sans-font">' + '<h3>Marketplace Activity</h3></div>')

#### Helper Functions

def get_hdata(tablename, col):
    protocol = protocolSelect.value
    if tablename != 'market_cap_volume':
        cur.execute('''select * from %s where protocol = '%s' ;''' %(tablename, protocol))
    else:
        cur.execute('''select protocol, date, %s from %s where protocol = '%s' ;''' %(col, tablename, protocol))
    names = [x[0] for x in cur.description]
    rows = cur.fetchall()
    data = pd.DataFrame(rows, columns=names)

    if tablename != 'github_data_total':
        colors = protocols[['protocol','color']]
        data = data.merge(colors,how='inner',on='protocol')

    if tablename == 'stackoverflow_questions':
        data = data[['protocol','date','question_count','color']]
    if tablename != 'market_cap_volume':
        data.columns = ['protocol','date','count','color']
    else:
        data.columns = ['protocol','date','value','color']

    return data

def get_price_data(protocol):
    cur.execute('''select close from (select *, row_number() over (partition by protocol order by date desc) as row_number from market_cap_volume) as rows where row_number = 1 and protocol = '%s';''' %(protocol))
    names = [x[0] for x in cur.description]
    rows = cur.fetchall()
    data = pd.DataFrame(rows, columns=names)

    return data

def extract_asodata(protocol):
    id = protocols[protocols.protocol==protocol].id_cc.item()

    if str(id) != 'nan':
        url = 'https://www.cryptocompare.com/api/data/socialstats/?id=' + str(int(id))
        r = requests.get(url,headers=REQUEST_HEADERS)
        alldata = json.loads(r.content)

        if len(alldata['Data']['Twitter']) > 1:
            socialdata = pd.Series(alldata['Data']['Twitter']['statuses'], index=['twitter_statuses'])
        else: 
            socialdata = pd.Series(0, index=['twitter_statuses'])
        if len(alldata['Data']['Reddit']) > 2:
            socialdata['reddit_comments_per_day'] = alldata['Data']['Reddit']['comments_per_day']
        else:
            socialdata['reddit_comments_per_day'] = 0     
        if len(alldata['Data']['Facebook']) > 1:
            socialdata['facebook_likes'] = alldata['Data']['Facebook']['likes']
        else:
            socialdata['facebook_likes'] = 0
        return pd.DataFrame(socialdata).transpose()

    return pd.DataFrame([])

def extract_alldata(protocol):
    symbol = protocols[protocols.protocol==protocol].ticker_cc.item()

    if str(symbol) != 'nan':
        if symbol == 'MKR' or symbol == 'FIL' or symbol == 'RDN*':
            url = 'https://www.cryptocompare.com/api/data/coinsnapshot/?fsym='+ symbol + '&tsym=USDT'
        else:
            url = 'https://www.cryptocompare.com/api/data/coinsnapshot/?fsym='+ symbol + '&tsym=USD'

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

def build_figure(figname,type):
    f=figure(x_axis_type='datetime',plot_width=600, plot_height=320, 
        background_fill_color = "grey", background_fill_alpha = .1, 
        tools=['box_zoom','wheel_zoom','pan','reset','save'], active_scroll='wheel_zoom', active_drag='pan', toolbar_location=None)
    f.xaxis.axis_label = "Date"
    if type==1:
        f.yaxis.axis_label = "Count"
        f.left[0].formatter.use_scientific = False
    else:
        f.yaxis.axis_label = "Value"
        f.yaxis.formatter = NumeralTickFormatter(format='($ 0.00 a)')
    f.xaxis.major_label_orientation=radians(90)
    f.min_border_right = 25
    f.min_border_bottom = 1
    f.min_border_top = 1
    return f

def build_line(fig,source_data,type):
    #select subset of source (workaround to get Hover to work)
    name = protocolSelect.value
    d = pd.DataFrame(source_data)

    if d.shape[0] > 1 and str(d['date'].iloc[0]) != 'nan':
        #construct line
        d['date'] = pd.to_datetime(d['date'])
        if type==1:
            source_sub = ColumnDataSource(
                data = dict(
                protocol=d['protocol'],
                date=d['date'],
                count=d['count'],
                color=d['color'],
                date_formatted = d['date'].apply(lambda d: d.strftime('%Y-%m-%d'))
            ))
        else:
            source_sub = ColumnDataSource(
                data = dict(
                protocol=d['protocol'],
                date=d['date'],
                value=d['value'].astype(float).round(2),
                color=d['color'],
                date_formatted = d['date'].apply(lambda d: d.strftime('%Y-%m-%d'))
            ))
        # add line 
        if type==1:
            val = fig.line('date', 'count', source=source_sub, line_color=source_sub.data['color'].iloc[0], line_width=2, line_alpha=0.7)
        else:
            val = fig.line('date', 'value', source=source_sub, line_color=source_sub.data['color'].iloc[0], line_width=2, line_alpha=0.7)
        #set Hover
        if type==1:
            fig.add_tools(HoverTool(renderers=[val],  show_arrow=True, point_policy='follow_mouse',  
                tooltips=[('Name', name),('Date', '@date_formatted'),('Count', '@count')],
                mode = "vline"))
        else:
            fig.add_tools(HoverTool(renderers=[val],  show_arrow=True, point_policy='follow_mouse',  
                tooltips=[('Name', name),('Date', '@date_formatted'),("Value", "@value{'$ 0.00 a'}")],
                mode = "vline"))

#### Updates

def title_update():
    protocolTitle.text=div_style + '<div class="sans-font"><h1>' + protocolSelect.value +'</h1></div>'

def divs_update():
    new_asodata = extract_asodata(protocolSelect.value)
    if (not new_asodata.empty):
        asosource.data=asosource.from_df(new_asodata)
    else:
        asosource.data = dict(twitter_statuses=[],reddit_comments_per_day=[],facebook_likes=[])

    new_alldata = extract_alldata(protocolSelect.value)
    if (not new_alldata.empty):
        Algorithmv.text = div_style + '<div class="sans-font"><p>' + str(new_alldata['Algorithm'].item()) +'</p></div>'
        BlockNumberv.text = div_style + '<div class="sans-font"><p>' + str(int(new_alldata['BlockNumber'])) +'</p></div>'
        BlockRewardv.text = div_style + '<div class="sans-font"><p>' + str(int(new_alldata['BlockReward'])) +'</p></div>'
        NetHashesPerSecondv.text = div_style + '<div class="sans-font"><p>' + str(int(new_alldata['NetHashesPerSecond'])) +'</p></div>'
        ProofTypev.text = div_style + '<div class="sans-font"><p>' + str(new_alldata['ProofType'].item()) +'</p></div>'
        TotalCoinsMinedv.text = div_style + '<div class="sans-font"><p>' + str(int(new_alldata['TotalCoinsMined'])) +'</p></div>'
        NumberofExchangesv.text = div_style + '<div class="sans-font"><p>' + str(int(new_alldata['nExchanges'])) +'</p></div>'
    else:
        Algorithmv.text = div_style + '<div class="sans-font"><p></p></div>'
        BlockNumberv.text = div_style + '<div class="sans-font"><p></p></div>'
        BlockRewardv.text = div_style + '<div class="sans-font"><p></p></div>'
        NetHashesPerSecondv.text = div_style + '<div class="sans-font"><p></p></div>'
        ProofTypev.text = div_style + '<div class="sans-font"><p></p></div>'
        TotalCoinsMinedv.text = div_style + '<div class="sans-font"><p></p></div>'
        NumberofExchangesv.text = div_style + '<div class="sans-font"><p></p></div>'

def price_update():
    new_price = get_price_data(protocolSelect.value)
    print new_price
    if (not new_price.empty):
        Pricev.text = div_style + '<div class="sans-font"><p>$' + str(new_price['close'].item()) +'</p></div>'
    else:
        Pricev.text = div_style + '<div class="sans-font"><p></p></div>'

def t_update():
    if tmetric.value == 'Total Volume':
        col = 'volume'
    if tmetric.value == 'Market Cap':
        col = 'market_cap'
    if tmetric.value == 'Average Daily Price':
        col = 'average'

    data = get_hdata('market_cap_volume', col)

    if not data.empty:
        tfig = build_figure(tmetric.value,2)
        build_line(tfig,data,2)
    else: 
        tfig = build_figure(tmetric.value,2)

    tlayout.children[2] = row(tfig) #will change

def g_update():
    if gmetric.value == 'Commits':
        tablename = 'github_commits'
    if gmetric.value == 'Stars':
        tablename = 'github_stars'
    if gmetric.value == 'StackOverflow Questions':
        tablename = 'stackoverflow_questions'

    data = get_hdata(tablename, "")

    gfig = build_figure(gmetric.value,1)
    build_line(gfig,data,1)

    glayout.children[2] = row(gfig) #will change

def so_update():
    if sometric.value == 'Reddit Posts':
        tablename = 'reddit_posts'
    if sometric.value == 'Reddit Subscribers':
        tablename = 'reddit_subscribers'
    if sometric.value == 'Twitter Followers':
        tablename = 'twitter_followers'
    if sometric.value == 'Search Interest':
        tablename = 'search_interest'
    if sometric.value == 'HackerNews Stories':
        tablename = 'hackernews_stories'

    data = get_hdata(tablename, "")

    sofig = build_figure(sometric.value,1)
    build_line(sofig,data,1)

    solayout.children[2] = row(sofig) #will change

#### On change
curdoc().hold()
protocolSelect.on_change('value', lambda attr, old, new: title_update())
protocolSelect.on_change('value', lambda attr, old, new: divs_update())
protocolSelect.on_change('value', lambda attr, old, new: price_update())
protocolSelect.on_change('value', lambda attr, old, new: g_update())
protocolSelect.on_change('value', lambda attr, old, new: t_update())
protocolSelect.on_change('value', lambda attr, old, new: so_update())
curdoc().unhold()
gmetric.on_change('value', lambda attr, old, new: g_update())
tmetric.on_change('value', lambda attr, old, new: t_update())
sometric.on_change('value', lambda attr, old, new: so_update())

#### Layouts, Initialization
curdoc().add_root(column(protocolSelect,protocolTitle))

#GitHub & StackOverflow
glayout = column(gsection_title,row(gmetric,Spacer(width=300)),gfig)
#Social/Search
solayout = column(sosection_title, row(sometric,Spacer(width=300)),sofig)
#Transactions
tlayout = column(tsection_title, row(tmetric,Spacer(width=300)),tfig)

#Divs
playout = column(Price, Pricev)  
alayout = column(Algorithm, Algorithmv)                                                  
blnlayout = column(BlockNumber, BlockNumberv)                                       
blrlayout = column(BlockReward, BlockRewardv)                                                            
nhlayout = column(NetHashesPerSecond, NetHashesPerSecondv)                              
prlayout = column(ProofType, ProofTypev)                                   
tclayout = column(TotalCoinsMined, TotalCoinsMinedv)                               
nelayout = column(NumberofExchanges, NumberofExchangesv) 

dlayout1 = column(playout,row(alayout,prlayout,blnlayout,blrlayout))
dlayout2 = row(nhlayout,tclayout,nelayout)
dlayout3 = column(AdditionalSocialData,asostats)
dlayout = column(dlayout1,dlayout2,dlayout3)

#All
layout = column(row(tlayout,dlayout),row(glayout,solayout))             

title_update()
divs_update()
price_update()
g_update()
so_update()
t_update()

#curdoc().add_periodic_callback(price_update, 2000)
curdoc().add_root(layout)

