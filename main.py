from bokeh.client import push_session
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter
from bokeh.models.tools import HoverTool, BoxZoomTool, WheelZoomTool, PanTool, ResetTool, SaveTool
from bokeh.models.widgets import Div, DataTable, TableColumn, Select, CheckboxGroup, DateRangeSlider
from bokeh.layouts import layout
from bokeh.plotting import figure
from datetime import datetime, date
from math import radians
from pytz import timezone
from bokeh.layouts import row, column, widgetbox
from initialize_data import *

div_style = """
    <link rel="stylesheet" type="text/css" href="//fonts.googleapis.com/css?family=Open+Sans" />
    <style>
        .sans-font {
            font-family: "Open Sans";
        }
    </style>
"""

####################################
## Helper Functions
####################################
def get_github_file(m):
    fname = "data/output/github_" + m.lower() + ".csv"
    data = pd.read_csv(fname)
    # # filter to protocol
    #data = data[data.protocol.isin(p)]
    colors = protocols[['protocol','color']]
    data = data.merge(colors,how='inner',on='protocol')

    if m == 'Commits':
        data = data[['protocol','week_date','total','color']]
    if m == 'Stars':
        data = data[['protocol','starred_at','count','color']]

    data.columns = ['protocol','date','count','color']

    return data

# List of protocols
protocols_list = list(protocols['protocol'])

#dictionary to store time series lines
keys = ["l" + str(i) for i in range(0,len(protocols_list))]

#create figures
def build_figure(figname):
    f=figure(x_axis_type='datetime',plot_width=800, plot_height=500, 
        background_fill_color = "grey", background_fill_alpha = .15, 
        title = figname, name = figname, 
        tools=['box_zoom','wheel_zoom','pan','reset','save'], active_scroll='wheel_zoom', active_drag='pan', toolbar_location=None)
    f.title.text_font = "verdana"
    f.xaxis.axis_label = "Date"
    f.yaxis.axis_label = "Count"
    f.xaxis.major_label_orientation=radians(90)
    f.min_border_right = 90
    f.min_border_bottom = 0
    return f

#add all time series lines
def build_line(fig,source_data,n):
    #select subset of source (workaround to get Hover to work)
    name = protocols_list[n]
    d = pd.DataFrame(source_data)
    d = d[d.protocol==name]

    if d.shape[0] > 1:

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
        val = fig.line('date', 'count', source=source_sub, line_color=source_sub.data['color'].iloc[0], legend=name, line_width=2, line_alpha=0.7)

        #set Hover
        fig.add_tools(HoverTool(renderers=[val], tooltips=[('Name', name),('Date', '@date_formatted'),('Count', '@count')]))

        #format legend
        fig.legend.spacing = 1
        fig.legend.label_text_font_size = '8pt'
        fig.legend.padding = 1
        fig.legend.background_fill_color = "grey"
        fig.legend.background_fill_alpha = 0.022
        
    else:
        val = None

    return val

####################################
## GitHub
####################################
# Data
commits = get_github_file('Commits')
stars = get_github_file('Stars')

# import PreText data (static table)
github_data_total = pd.read_csv("data/output/github_data_total.csv")
github_data_total = github_data_total.fillna("") 

#create ColumnDataSources
#source = ColumnDataSource(data=dict(protocol=[], date=[], count=[], color=[]))
gsource_stats = ColumnDataSource(data=dict())
gsource_stats.data = gsource_stats.from_df(github_data_total)

f_commits = build_figure("Commits")
f_stars = build_figure("Stars")

lines_dict_commits = dict.fromkeys(keys)
lines_dict_stars = dict.fromkeys(keys)

#set up widgets
gsection_title = Div(text=div_style + '<div class="sans-font">' + '<h2>GitHub Activity</h2></div>')
columns = [
        TableColumn(field="protocol", title="Protocol"),
        TableColumn(field="total_commits_past_year", title="Total Commits"),
        TableColumn(field="total_forks_count", title="Total Forks"),
        TableColumn(field="total_stars_count", title="Total Stars"),
        TableColumn(field="created_at", title="Created On")
    ]
gstats = DataTable(source=gsource_stats, columns=columns, fit_columns=True, row_headers=False, width=480, height=685)
gcomments = Div(text=div_style + '''<div class="sans-font" style="width:750px;text-align: center;">''' 
    + "<font size='1'>Commits are only available at a weekly basis for the last 12 months, hence why the data starts end of January 2017</font></div>")

#controls
gprotocolSelect = CheckboxGroup(labels=protocols_list, active=[0,1,2], width=100)
gmetric = Select(value='Commits', options=['Commits', 'Stars'])

####################################
## StackOverflow
####################################
ssection_title = Div(text=div_style + '<div class="sans-font">' + '<h2>StackOverflow Questions</h2></div>')

####################################
## Reddit, Twitter, Search
####################################
sosection_title = Div(text=div_style + '<div class="sans-font">' + '<h2>Social Media and Search Activity</h2></div>')

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

def line_update():
    i = 0
    #get the select values
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

# Update checkbox controls
check_controls = [gprotocolSelect]
for control in check_controls:
    gprotocolSelect.on_change('active', lambda attr, old, new: line_update())

# Callback which either adds or removes a plot depending on what metric is selected
def selectCallback():
    # Either add or remove the second graph
    if  gmetric.value=='Stars':
        add_lines('Stars')
        glayout.children[1].children[0].children[1].children[1] = row(f_stars,name='stars')
        line_update()

    if gmetric.value=='Commits':
        add_lines('Commits')
        glayout.children[1].children[0].children[1].children[1] = row(f_commits,name='commits')
        line_update()

# Update select controls
select_controls = [gmetric]
for control in select_controls:
    control.on_change('value', lambda attr, old, new: selectCallback())

####################################
## Layouts, Initialization
####################################
#GitHub
glinesSelect = row(gprotocolSelect)
gfig = row(f_commits,name='commits')
gfig_final = column(gmetric,gfig,gcomments)
gmain_col = row(glinesSelect,gfig_final)
gmain_elements = row(gmain_col, gstats)
glayout = column(gsection_title, gmain_elements, sizing_mode='scale_width')
#StackOverflow
slayout = column(ssection_title, sizing_mode='scale_width')
#Social/Search
solayout = column(sosection_title, sizing_mode='scale_width')
# initialize
add_lines('Commits')
line_update()

curdoc().add_root(glayout)
curdoc().add_root(slayout)
curdoc().add_root(solayout)
