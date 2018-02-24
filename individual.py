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
tmetric = Select(value='Total Volume', options=['Total Volume', 'Market Cap', 'Average Daily Price'])
gmetric = Select(value='Commits', options=['Commits', 'Stars', 'StackOverflow Questions'])
sometric = Select(value='Search Interest', options=['Reddit Posts', 'Reddit Subscribers', 'Twitter Followers', 'Search Interest', 'HackerNews Stories'])

gfig=figure()
sofig=figure()
tfig=figure()

gsection_title = Div(text=div_style + '<div class="sans-font">' + '<h3>GitHub and StackOverflow Activity</h3></div>')
sosection_title = Div(text=div_style + '<div class="sans-font">' + '<h3>Social Media and Search Activity</h3></div>')
tsection_title = Div(text=div_style + '<div class="sans-font">' + '<h3>Historical Transactions</h3></div>')

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

def divs_update():
    protocolTitle.text=div_style + '<div class="sans-font"><h1>' + protocolSelect.value +'</h1></div>'
    
protocolSelect.on_change('value', lambda attr, old, new: divs_update())

def t_update():
    if tmetric.value == 'Total Volume':
        col = 'volume'
    if tmetric.value == 'Market Cap':
        col = 'market_cap'
    if tmetric.value == 'Average Daily Price':
        col = 'average'

    data = get_hdata('market_cap_volume', col)

    tfig = build_figure(tmetric.value,2)
    build_line(tfig,data,2)

    tlayout.children[2] = row(tfig) #will change

protocolSelect.on_change('value', lambda attr, old, new: t_update())
tmetric.on_change('value', lambda attr, old, new: t_update())

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


protocolSelect.on_change('value', lambda attr, old, new: g_update())
gmetric.on_change('value', lambda attr, old, new: g_update())

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

protocolSelect.on_change('value', lambda attr, old, new: so_update())
sometric.on_change('value', lambda attr, old, new: so_update())

#### Layouts, Initialization
curdoc().add_root(column(protocolSelect,protocolTitle))

#GitHub & StackOverflow
glayout = column(gsection_title,row(gmetric,Spacer(width=300)),gfig)

#Social/Search
solayout = column(sosection_title, row(sometric,Spacer(width=300)),sofig)

#Transactions
tlayout = column(tsection_title, row(tmetric,Spacer(width=300)),tfig)

#All
hlayout = column(tlayout,row(glayout,solayout))

divs_update()
g_update()
so_update()
t_update()

curdoc().add_root(hlayout)

