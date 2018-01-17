from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter
from bokeh.models.widgets import Div, DataTable, TableColumn, Select, MultiSelect
from bokeh.layouts import layout
from bokeh.plotting import figure
from datetime import datetime
from math import radians
from pytz import timezone
from bokeh.layouts import row, column, widgetbox

from initialize_data import *
from access_tokens import *

div_style = """
    <link rel="stylesheet" type="text/css" href="//fonts.googleapis.com/css?family=Open+Sans" />
    <style>
        .sans-font {
            font-family: "Open Sans";
        }
    </style>
"""

def get_github_file(protocols, metric):
    fname = "data/output/github_" + metric.lower() + ".csv"
    data = pd.read_csv(fname)
    # filter to protocol
    data = data[data.protocol.isin(protocols)]

    if metric == 'Commits':
        data = data[['week_date','total']]
    if metric == 'Stars':
        data = data[['starred_at','count']]

    data.columns = ['date','count']
    print(data)
    return data

# import PreText data (static table)
github_data_total = pd.read_csv("data/output/github_data_total.csv")

#create ColumnDataSources
source = ColumnDataSource(data=dict(date=[], count=[]))
source_static = ColumnDataSource(data=dict(date=[], count=[]))
source_stats = ColumnDataSource(data=dict())
source_stats.data = source_stats.from_df(github_data_total)

#create figure
f_github=figure(x_axis_type='datetime')
f_github.title.text_font = "verdana"
f_github.xaxis.axis_label = "Date"
f_github.yaxis.axis_label = "Count"
#create glyphs
f_github.line('date','count',source=source_static)

f_github.xaxis.formatter=DatetimeTickFormatter(formats=dict(
seconds=["%Y-%m-%d"],
minsec=["%Y-%m-%d"],
minutes=["%Y-%m-%d"],
hourmin=["%Y-%m-%d"],
hours=["%Y-%m-%d"],
days=["%Y-%m-%d"],
months=["%Y-%m-%d"],
years=["%Y-%m-%d"],
))

f_github.xaxis.major_label_orientation=radians(90)


# set up widgets
section_title = Div(text=div_style + '<div class="sans-font">' + '<h2>GitHub Activity</h2></div>')
columns = [
        TableColumn(field="protocol", title="Protocol"),
        TableColumn(field="total_commits_past_year", title="Total Commits (past year)"),
        TableColumn(field="total_forks_count", title="Total Forks"),
        TableColumn(field="total_stars_count", title="Total Stars"),
        TableColumn(field="created_at", title="Created On")
    ]
stats = DataTable(source=source_stats, columns=columns, width=700, height=700)
protocols = MultiSelect(value=['Ethereum'], options=list(protocols['protocol']))
metric = Select(value='Commits', options=['Commits', 'Stars'])


# updates
def metric_change(attrname, old, new):
    update()

def protocol_change(attrname, old, new):
    update()

def update(selected=None):
    p, m = protocols.value, metric.value

    data = get_github_file(p, m)
    source.data = source.from_df(data)
    source_static.data = source.data

    f_github.title.text = m

protocols.on_change('value', protocol_change)
metric.on_change('value', metric_change)

def selection_change(attrname, old, new):
    p, m = protocols.value, metric.value
    data = get_data(p, m)
    selected = source.selected
    print(selected)

source.on_change('selected', selection_change)

# set up layout
widgets = row(protocols, metric)
main_col = column(widgets,f_github)
main_elements = row(main_col, stats)
layout = column(section_title, main_elements)

# initialize
update()

curdoc().add_root(layout)
