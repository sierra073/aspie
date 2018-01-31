from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter
from bokeh.models.callbacks import CustomJS
from bokeh.models.tools import HoverTool, BoxZoomTool, WheelZoomTool, PanTool, ResetTool, SaveTool
from bokeh.models.widgets import Div, DataTable, TableColumn, Select, CheckboxGroup, DateRangeSlider
from bokeh.layouts import layout
from bokeh.plotting import figure
from datetime import datetime, date
from math import radians
from bokeh.layouts import row, column, widgetbox
import sys
sys.path.append('/Users/sierra/Documents/Other/aspie/get_data/')
from initialize_data import *
import psycopg2

HOST = '127.0.0.1'
USER = 'sierra'
PASSWORD = 'cryptofund'
DB = 'cryptometrics'

conn = psycopg2.connect( host=HOST, user=USER, password=PASSWORD, dbname=DB , port=5431)
cur = conn.cursor()

div_style = """
    <link rel="stylesheet" type="text/css" href="//fonts.googleapis.com/css?family=Open+Sans" />
    <style>
        .sans-font {
            font-family: "Open Sans"; }
    </style>
"""
####################################
## Helper Functions
####################################
def get_data(name):
    cur.execute('select * from ' + name +';')
    names = [x[0] for x in cur.description]
    rows = cur.fetchall()
    data = pd.DataFrame(rows, columns=names)

    colors = protocols[['protocol','color']]
    data = data.merge(colors,how='inner',on='protocol')

    if name == 'github_stars':
        data = data[data.protocol!='Bitcoin']
    if name == 'stackoverflow_questions':
        data = data[['protocol','date','question_count','color']]

    data.columns = ['protocol','date','count','color']
    return data

# List of protocols
protocols_list = list(protocols['protocol'])

#dictionary to store time series lines
keys = ["l" + str(i) for i in range(0,len(protocols_list))]

#create figures
def build_figure(figname):
    f=figure(x_axis_type='datetime',plot_width=800, plot_height=500, 
        background_fill_color = "grey", background_fill_alpha = .1, 
        title = figname, name = figname, 
        tools=['box_zoom','wheel_zoom','pan','reset','save'], active_scroll='wheel_zoom', active_drag='pan', toolbar_location=None)
    f.title.text_font = "verdana"
    f.xaxis.axis_label = "Date"
    f.yaxis.axis_label = "Count"
    f.left[0].formatter.use_scientific = False
    f.xaxis.major_label_orientation=radians(90)
    f.min_border_right = 65
    f.min_border_bottom = 0
    return f

#add all time series lines
def build_line(fig,source_data,n):
    #select subset of source (workaround to get Hover to work)
    name = protocols_list[n]
    d = pd.DataFrame(source_data)
    d = d[d.protocol==name]
    if d.shape[0] > 1 and str(d['date'].iloc[0]) != 'nan':
        #construct line
        d['date'] = pd.to_datetime(d['date'])
        source_sub = ColumnDataSource(
            data = dict(
            protocol=d['protocol'],
            date=d['date'],
            count=d['count'],
            color=d['color'],
            date_formatted = d['date'].apply(lambda d: d.strftime('%Y-%m-%d'))
        ))
        #format legend
        fig.legend.spacing = 1
        fig.legend.label_text_font_size = '8pt'
        fig.legend.padding = 1
        fig.legend.background_fill_color = "grey"
        fig.legend.background_fill_alpha = 0.015   
        # add line 
        val = fig.line('date', 'count', source=source_sub, line_color=source_sub.data['color'].iloc[0], legend=name, line_width=2, line_alpha=0.7)
        #set Hover
        fig.add_tools(HoverTool(renderers=[val],  show_arrow=True, point_policy='follow_mouse',  
            tooltips=[('Name', name),('Date', '@date_formatted'),('Count', '@count')],
            mode = "vline"))
        
        return val
    else:
        return None

#add all time series as bar charts
def build_circle(fig,source_data,n):
    #select subset of source (workaround to get Hover to work)
    name = protocols_list[n]
    d = pd.DataFrame(source_data)
    d = d[d.protocol==name]
    if d.shape[0] > 0 and d.protocol.iloc[0] != 'Bitcoin' and d['date'].iloc[0] != None:
        #construct line
        d['date'] = pd.to_datetime(d['date'])
        source_sub = ColumnDataSource(
            data = dict(
            protocol=d['protocol'],
            date=d['date'],
            count=d['count'],
            color=d['color'],
            date_formatted = d['date'].apply(lambda d: d.strftime('%Y-%m-%d'))
        ))
        #format legend
        fig.legend.spacing = 1
        fig.legend.label_text_font_size = '8pt'
        fig.legend.padding = 1
        fig.legend.background_fill_color = "grey"
        fig.legend.background_fill_alpha = 0.015  
        # add line
        val = fig.circle_cross('date', 'count', source=source_sub, size=14, 
            fill_color=source_sub.data['color'].iloc[0], fill_alpha=0.3, 
            line_color=source_sub.data['color'].iloc[0], line_alpha=1,legend=name)
        #set Hover
        fig.add_tools(HoverTool(renderers=[val],  show_arrow=True, point_policy='follow_mouse',  
            tooltips=[('Name', name),('Date', '@date_formatted'),('Count', '@count')]))

        return val
    else:
        return None

############
## GitHub, StackOverflow
############
# Data
commits = get_data('github_commits')
stars = get_data('github_stars')
questions = get_data('stackoverflow_questions')

# import PreText data (static table)
github_data_total = pd.read_csv("data/output/github_data_total.csv")
# add column for StackOverflow question count to date
questions_total = questions[['protocol','count']].groupby(['protocol']).sum().reset_index()
github_data_total = github_data_total.merge(questions_total,how='inner',on='protocol')
github_data_total = github_data_total.fillna("") 

#create ColumnDataSources
#source = ColumnDataSource(data=dict(protocol=[], date=[], count=[], color=[]))
gsource_stats = ColumnDataSource(data=dict())
gsource_stats.data = gsource_stats.from_df(github_data_total)

f_commits = build_figure("Commits")
f_stars = build_figure("Stars")
f_questions = build_figure("Questions")

lines_dict_commits = dict.fromkeys(keys)
lines_dict_stars = dict.fromkeys(keys)
lines_dict_questions = dict.fromkeys(keys)

#set up widgets
gsection_title = Div(text=div_style + '<div class="sans-font">' + '<h2>GitHub and StackOverflow Activity</h2></div>')
gcolumns = [
        TableColumn(field="protocol", title="Protocol"),
        TableColumn(field="total_commits_past_year", title="Total Commits"),
        TableColumn(field="total_forks_count", title="Total Forks"),
        TableColumn(field="total_stars_count", title="Total Stars"),
        TableColumn(field="created_at", title="GitHub Created"),
        TableColumn(field="count", title="StackOverflow")
    ]
gstats = DataTable(source=gsource_stats, columns=gcolumns, fit_columns=True, row_headers=False, width=502, height=685)
gcomments = Div(text=div_style + '''<div class="sans-font" style="width:700px;">''' 
    + "<font size='1'>\
    <ul><li>Commits are only available at a weekly basis for the last 12 months, hence why the data starts end of January 2017</li>\
    <li>StackOverflow questions counted since January 2017. Questions are aggregated by protocol by searching for those that contain the term(s) specified in our input data in their title OR for those tagged as the term(s). Thus, it's possible for questions to be double counted if the term is contained in the question title AND question tag, but highly unlikely based on the data observed.</li>\
    </ul></font></div>")

#controls
gprotocolSelect = CheckboxGroup(labels=protocols_list, active=[0,1,2], width=100)
gmetric = Select(value='Commits', options=['Commits', 'Stars', 'StackOverflow Questions'])

############
## Reddit, Twitter, Search
############
sosection_title = Div(text=div_style + '<div class="sans-font">' + '<h2>Social Media and Search Activity</h2></div>')

# Data
reddit_posts = get_data('reddit_posts')
reddit_subscribers = get_data('reddit_subscribers')
twitter_followers = get_data('twitter_followers')
searchinterest = get_data('search_interest')

# import PreText data (static table)
reddit_posts_total = reddit_posts[['protocol','count']].groupby(['protocol']).sum().reset_index()
reddit_subscribers_total = reddit_subscribers[['protocol','count']].groupby(['protocol']).max().reset_index()
twitter_followers_total = twitter_followers[['protocol','count']].groupby(['protocol']).max().reset_index()
reddit_data_total = reddit_posts_total.merge(reddit_subscribers_total,how='outer',on='protocol')
social_data_total = reddit_data_total.merge(twitter_followers_total,how='outer',on='protocol')
social_data_total.columns = ['Protocol','Reddit Posts','Reddit Subscribers', 'Twitter Followers']
social_data_total = social_data_total.fillna("") 

sosource_stats = ColumnDataSource(data=dict())
sosource_stats.data = sosource_stats.from_df(social_data_total)

f_rposts = build_figure("Reddit Posts")
f_rsubs = build_figure("Reddit Subscribers")
f_tfoll = build_figure("Twitter Followers")
f_search = build_figure("Search Interest")

lines_dict_rposts = dict.fromkeys(keys)
lines_dict_rsubs = dict.fromkeys(keys)
lines_dict_tfoll = dict.fromkeys(keys)
lines_dict_search = dict.fromkeys(keys)

#set up widgets
socolumns = [
        TableColumn(field="Protocol",title="Protocol"),
        TableColumn(field="Reddit Posts",title="Reddit Posts"),
        TableColumn(field="Reddit Subscribers",title="Reddit Subscribers"),
        TableColumn(field="Twitter Followers",title="Twitter Followers")
    ]
sostats = DataTable(source=sosource_stats, columns=socolumns, fit_columns=True, row_headers=False, width=380, height=685)

#controls
soprotocolSelect = CheckboxGroup(labels=protocols_list, active=[0,1,2], width=100)
sometric = Select(value='Search Interest', options=['Reddit Posts', 'Reddit Subscribers', 'Twitter Followers', 'Search Interest'])

####################################
## Updates
####################################
def add_lines(fig):
    i = 0
    if fig=='Commits':
        for l in lines_dict_commits:
            lines_dict_commits[l] = build_line(f_commits,commits,i)
            i+=1
    if fig=="Stars":
        for l in lines_dict_stars:
            lines_dict_stars[l] = build_line(f_stars,stars,i)
            i+=1
    if fig=="StackOverflow Questions":
        for l in lines_dict_questions:
            lines_dict_questions[l] = build_line(f_questions,questions,i)
            i+=1
    if fig=="Reddit Posts":
        for l in lines_dict_rposts:
            lines_dict_rposts[l] = build_line(f_rposts,reddit_posts,i)
            i+=1
    if fig=="Reddit Subscribers":
        for l in lines_dict_rsubs:
            lines_dict_rsubs[l] = build_circle(f_rsubs,reddit_subscribers,i)
            i+=1
    if fig=="Twitter Followers":
        for l in lines_dict_tfoll:
            lines_dict_tfoll[l] = build_circle(f_tfoll,twitter_followers,i)
            i+=1
    if fig=="Search Interest":
        for l in lines_dict_search:
            lines_dict_search[l] = build_line(f_search,searchinterest,i)
            i+=1
def g_lineupdate():
    i = 0
    #get the select value
    gfig = gmetric.value

    if gfig=='Commits':
        for l in lines_dict_commits:
            l1 = lines_dict_commits[l]
            if l1 != None:
                l1.visible = i in gprotocolSelect.active
            i+=1
    if gfig=='Stars':
        for l in lines_dict_stars:
            l2 = lines_dict_stars[l]
            if l2 != None:
                l2.visible = i in gprotocolSelect.active
            i+=1
    if gfig=='StackOverflow Questions':
        for l in lines_dict_questions:
            l3 = lines_dict_questions[l]
            if l3 != None:
                l3.visible = i in gprotocolSelect.active
            i+=1
def so_lineupdate():
    i = 0
    #get the select value
    sofig = sometric.value

    if sofig=='Reddit Posts':
        for l in lines_dict_rposts:
            l4 = lines_dict_rposts[l]
            if l4 != None:
                l4.visible = i in soprotocolSelect.active
            i+=1
    if sofig=='Reddit Subscribers':
        for l in lines_dict_rsubs:
            l5 = lines_dict_rsubs[l]
            if l5!= None:
                l5.visible = i in soprotocolSelect.active
            i+=1
    if sofig=='Twitter Followers':
        for l in lines_dict_tfoll:
            l6 = lines_dict_tfoll[l]
            if l6!= None:
                l6.visible = i in soprotocolSelect.active
            i+=1
    if sofig=='Search Interest':
        for l in lines_dict_search:
            l7 = lines_dict_search[l]
            if l7!= None:
                l7.visible = i in soprotocolSelect.active
            i+=1

# Update checkbox controls
gprotocolSelect.on_change('active', lambda attr, old, new: g_lineupdate())
soprotocolSelect.on_change('active', lambda attr, old, new: so_lineupdate())

# Callback which either adds or removes a plot depending on what metric is selected
def g_selectCallback():
    # Either add or remove the second graph
    if  gmetric.value=='Stars':
        add_lines('Stars')
        glayout.children[1].children[0].children[1].children[1] = row(f_stars)
        g_lineupdate()
    if gmetric.value=='Commits':
        add_lines('Commits')
        glayout.children[1].children[0].children[1].children[1] = row(f_commits)
        g_lineupdate()
    if gmetric.value=='StackOverflow Questions':
        add_lines('StackOverflow Questions')
        glayout.children[1].children[0].children[1].children[1] = row(f_questions)
        g_lineupdate()
def so_selectCallback():
    # Either add or remove the second graph
    if sometric.value=='Reddit Posts':
        add_lines('Reddit Posts')
        solayout.children[1].children[0].children[1].children[1] = row(f_rposts)
        so_lineupdate()
    if sometric.value=='Reddit Subscribers':
        add_lines('Reddit Subscribers')
        solayout.children[1].children[0].children[1].children[1] = row(f_rsubs)
        so_lineupdate()
    if sometric.value=='Twitter Followers':
        add_lines('Twitter Followers')
        solayout.children[1].children[0].children[1].children[1] = row(f_tfoll)
        so_lineupdate()
    if sometric.value=='Search Interest':
        add_lines('Search Interest')
        solayout.children[1].children[0].children[1].children[1] = row(f_search)
        so_lineupdate()

# Update select controls
gmetric.on_change('value', lambda attr, old, new: g_selectCallback())
sometric.on_change('value', lambda attr, old, new: so_selectCallback())

####################################
## Layouts, Initialization
####################################
#GitHub & StackOverflow
glinesSelect = row(gprotocolSelect)
gfig = row(f_commits)
gfig_final = column(gmetric,gfig,gcomments)
gmain_col = row(glinesSelect,gfig_final)
gmain_elements = row(gmain_col, gstats)
glayout = column(gsection_title, gmain_elements, sizing_mode='scale_width')

#Social/Search
solinesSelect = row(soprotocolSelect)
sofig = row(f_search)
sofig_final = column(sometric,sofig)
somain_col = row(solinesSelect,sofig_final)
somain_elements = row(somain_col, sostats)
solayout = column(sosection_title,somain_elements, sizing_mode='scale_width')

# initialize
add_lines('Commits')
add_lines('Search Interest')
g_lineupdate()
so_lineupdate()

curdoc().add_root(glayout)
curdoc().add_root(solayout)
