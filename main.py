from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter
from bokeh.models.tools import HoverTool, UndoTool, ResetTool, SaveTool
from bokeh.models.widgets import Div, DataTable, TableColumn, Select, CheckboxGroup, DateRangeSlider
from bokeh.layouts import layout
from bokeh.plotting import figure
from bokeh.palettes import Spectral11
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

# Data
commits = get_github_file('Commits')
stars = get_github_file('Stars')

# import PreText data (static table)
github_data_total = pd.read_csv("data/output/github_data_total.csv")
github_data_total = github_data_total.fillna("") 

#create ColumnDataSources
source = ColumnDataSource(data=dict(protocol=[], date=[], count=[], color=[]))
source_stats = ColumnDataSource(data=dict())
source_stats.data = source_stats.from_df(github_data_total)

#create figures
def build_figure(figname)
    f=figure(x_axis_type='datetime',plot_width=860, plot_height=560, title = figname, name = figname)
    f.title.text_font = "verdana"
    f.xaxis.axis_label = "Date"
    f.yaxis.axis_label = "Count"
    f.xaxis.major_label_orientation=radians(90)
    return f

f_commits = build_figure("Commits")
f_stars = build_figure("Stars")

line_props = dict(line_width=2, line_alpha = 0.8)

#dictionary to store time series lines
keys = ["l" + str(i) for i in range(0,len(protocols_list))]
lines_dict_commits = dict.fromkeys(keys)
lines_dict_stars = dict.fromkeys(keys)

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

        val = fig.line('date', 'count', source=source_sub, line_color=source_sub.data['color'].iloc[0], legend=name, **line_props)

        #set Hover
        fig.add_tools(HoverTool(renderers=[val], tooltips=[('Name:', name),('Date:', '@date_formatted'),('Count:', '@y{int}')]))
        
    else:
        val = None

    return val

i = 0
for l in lines_dict_commits:
    lines_dict_commits[l] = build_line(f_commits,commits,i)
    lines_dict_stars[l] = build_line(f_stars,stars,i)
    i+=1

#set up widgets
section_title = Div(text=div_style + '<div class="sans-font">' + '<h2>GitHub Activity</h2></div>')
columns = [
        TableColumn(field="protocol", title="Protocol"),
        TableColumn(field="total_commits_past_year", title="Total Commits (past year)"),
        TableColumn(field="total_forks_count", title="Total Forks"),
        TableColumn(field="total_stars_count", title="Total Stars"),
        TableColumn(field="created_at", title="Created On")
    ]
stats = DataTable(source=source_stats, columns=columns, fit_columns=True, row_headers=False, width=550, height=700)

#controls
protocolSelect = CheckboxGroup(labels=protocols_list, active=[1], width=100)

def line_update():
    for i in range(0,len(lines_dict_commits)):
        l1 = lines_dict_commits[i]
        l2= lines_dict_stars[i]
        if l1 != None:
            l1.visible = i in protocolSelect.active
        if l2 != None:
            l2.visible = i in protocolSelect.active

protocolSelect.on_change('active', lambda attr, old, new: line_update())

# set up layout
widgets = row(protocolSelect)
main_col = column(widgets,f_commits)
main_elements = row(main_col, stats)
layout = column(section_title, main_elements, sizing_mode='scale_width')

# initialize
line_update()

curdoc().add_root(layout)

##########################
# metric = Select(value='Commits', options=['Commits', 'Stars'])
# date_slider = DateRangeSlider(title="Date Range: ", start=date(2010, 12, 19), end=date.today(), value=(date(2017, 4, 1), date.today()), step=1)

#updates
# def select_data():
#     m = metric.value
#     p = protocols_list[protocolSelect.active]
#     data = get_github_file(m)
#     data.date = pd.to_datetime(data.date)
#     selected = data[(data.protocol.isin(p)) &
#                 (data.date >= date_slider.value[0]) &
#                 (data.date <= date_slider.value[1])]
#     print(selected)
#     return selected

# def update():
#     df = select_data()
#     f_github.title.text = metric.value
#     source.data = dict(
#         protocol=df['protocol'],
#         date=df['date'],
#         count=df['count'],
#         color=df['color']
#     )

    #update plot
    # for name in protocols_list[protocolSelect.active]:
    #     #manipulate source
        # d = pd.DataFrame(source.data)
        # d = d[d.protocol==name]
        # d['date'] = pd.to_datetime(d['date'])
        # f_github.line(d['date'], d['count'], line_color=d['color'].iloc[0], line_width=2,  line_alpha = 0.8, legend=name)
    # f_github.legend.location = "top_left"
    # f_github.legend.click_policy="hide"


# controls = [metric, date_slider]
# for control in controls:
#     control.on_change('value', lambda attr, old, new: update())


# def selection_change(attrname, old, new):
#     p, m = protocolSelect.value, metric.value
#     data = get_github_file(p,m)
#     selected = source.selected['1d']['indices']
#     if selected:
#         data = data.iloc[selected, :]

# source.on_change('selected', selection_change)
