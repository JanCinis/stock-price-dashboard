import keys
import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from alpha_vantage.timeseries import TimeSeries
# ----------------------------------------------

# API settings and df creation
ts = TimeSeries(keys.key, output_format='pandas') # 'pandas' or 'json' or 'csv'
ttm_data, ttm_meta_data = ts.get_intraday(symbol='AAPL',interval='1min', outputsize='compact')
df = ttm_data.iloc[:50].copy()
df=df.transpose()
df.rename(index={"1. open":"open", "2. high":"high", "3. low":"low",
                 "4. close":"close","5. volume":"volume"},inplace=True)
df=df.reset_index().rename(columns={'index': 'indicator'})
df = pd.melt(df,id_vars=['indicator'],var_name='date',value_name='rate')
df = df[df['indicator']!='volume']
dff = df[df.indicator.isin(['high'])]

#d_columns = [{'name': x, 'id': x} for x in dff]
d_columns=[
            #{'name': 'Indicator', 'id': 'indicator'},
            {'name': 'Date', 'id': 'date'},
            {'name': 'Rate', 'id': 'rate'}
          ]

d_table = dash_table.DataTable(id='df_data_table',
            columns=d_columns,
            data=dff.to_dict('records'),
            cell_selectable=False,
            sort_action='native',
            column_selectable='single',
            page_size=10,
            style_data={
            'width': '150px', 'minWidth': '150px', 'maxWidth': '150px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',}
            )

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], # make it responsive for mobile layouts 
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )
# Declare server for Heroku deployment. Needed for Procfile.
server = app.server

# layout for graph
app.layout = dbc.Container([
    # dbc.Row([html.Div([html.A('Back to portfolio', href='https://jancinis.github.io/')],
    #                  style={'text-align':'center', 'display':'inline-block', 'width':'85%'})]),
    dbc.Row([
        dbc.Col([
            dbc.Card( # 5 rows required - logo, title, graph, buy/sell "buttons", descripiton
                [
                    dbc.CardImg( # logo
                        src="/assets/aapl.jpg",
                        top=True,
                        style={"width": "6rem"},
                        className="ml-3"
                    ),

                    dbc.CardBody([ # 2 columns desciption + trend value
                        dbc.Row([ 
                            dbc.Col([
                                html.P("CHANGE (1D)", className="ml-3") # period
                            ],width={'size':5, 'offset':1}),

                            dbc.Col([
                                dcc.Graph(id='indicator-graph', figure={},
                                          config={'displayModeBar':False})
                            ],width={'size':3, 'offset':2})
                        ]),

                        dbc.Row([ # daily line graph
                            dbc.Col([
                                dcc.Graph(id='daily-line', figure={},
                                          config={'displayModeBar':False})
                            ], width=12)
                        ]),

                        dbc.Row([ # 2 rows for "buttons"
                            dbc.Col([
                                dbc.Button("SELL"),
                            ], width=4),

                            dbc.Col([
                                dbc.Button("BUY")
                            ], width=4)
                        ], justify="between"), # create space between buttons

                        dbc.Row([ # 2 rows for "button" values
                            dbc.Col([
                                dbc.Label(id='low-price', children=dff.iloc[-1, 2]-1),
                            ], width=4, style={"padding-top": "15px"}),
                            #className="p-1"),
                            dbc.Col([
                                dbc.Label(id='high-price', children=dff.iloc[-1, 2]),
                            ], width=4, style={"padding-top": "15px"}),
                        ], justify="between"),
                        
                        dbc.Row([ # 1 rows for data table
                            dbc.Col([
                                html.Div(children=[dcc.Markdown('Stock Price History'), 
                                                   d_table
                                                   ],
                                         #style={'width':'850px', 'height':'750px'}
                                        )], 
                                    style={'text-align':'center', 'display':'inline-block', 'width':'100%'}
                                    )
                        ], justify="between"),
                    ]),
                ],
                style={"width": "24rem"},
                className="mt-3" # 3 units of space in the top margin
            )
        ], width=6) # 6 columns dashboard width
    ], justify='center'),

    dcc.Interval(id='update', n_intervals=0, interval=1000*20) # update the app every 20 sec (max 5 timer per 60 sec = min 12)
])

# Indicator Graph
@app.callback(
    Output('indicator-graph', 'figure'), # changes indicator-graph
    Input('update', 'n_intervals') # take intervals from dcc.Interval every X seconds
)
def update_graph(timer):
    dff_rv = dff.iloc[::-1] # reverse order - start with the earliest time
    day_start = dff_rv[dff_rv['date'] == dff_rv['date'].min()]['rate'].values[0] # min date value
    day_end = dff_rv[dff_rv['date'] == dff_rv['date'].max()]['rate'].values[0] # max date value

    fig = go.Figure(go.Indicator(
        mode="delta", # also possible "number+delta" to have the value as well
        value=day_end,
        delta={'reference': day_start, 'relative': True, 'valueformat':'.2%'})) # difference - percentage, 2 decimals points
    fig.update_traces(delta_font={'size':12}) # font update to fit the screen
    fig.update_layout(height=30, width=70) # the size

    # colors to display regarding positive or negative delta value
    if day_end >= day_start:
        fig.update_traces(delta_increasing_color='green')
    elif day_end < day_start:
        fig.update_traces(delta_decreasing_color='red')

    return fig

# Line Graph---------------------------------------------------------------
@app.callback(
    Output('daily-line', 'figure'), # update figure
    Input('update', 'n_intervals') # take intervals from dcc.Interval every X seconds
)
def update_graph(timer):
    dff_rv = dff.iloc[::-1] # from the beginning of the day to the end
    fig = px.line(dff_rv, x='date', y='rate',
                   range_y=[dff_rv['rate'].min(), dff_rv['rate'].max() + 0.1], # minimize indents, +0.1 just to add a little space
                   height=120).update_layout(margin=dict(t=0, r=0, l=0, b=20), # how many px. in margin for each side
                                             paper_bgcolor='rgba(0,0,0,0)',
                                             plot_bgcolor='rgba(0,0,0,0)', # background color
                                             yaxis=dict(
                                             title=None,
                                             showgrid=False,
                                             showticklabels=False
                                             ),
                                             xaxis=dict(
                                             title=None,
                                             showgrid=False, # hide grid lines
                                             showticklabels=False
                                             ))

    # take values for the day
    day_start = dff_rv[dff_rv['date'] == dff_rv['date'].min()]['rate'].values[0]
    day_end = dff_rv[dff_rv['date'] == dff_rv['date'].max()]['rate'].values[0]

    # compare values in order to determine graph's color
    if day_end >= day_start:
        return fig.update_traces(fill='tozeroy',line={'color':'green'}) # fill for trace scatter color
    elif day_end < day_start:
        return fig.update_traces(fill='tozeroy',
                             line={'color': 'red'})

# Below the value buttons--------------------------------------------------------
@app.callback(
    Output('high-price', 'children'),
    Output('high-price', 'className'),
    Input('update', 'n_intervals') # take intervals from dcc.Interval every X seconds
)
def update_graph(timer): # fot every update takes the last 2 rows from df
    key = 'WLVKCGWW5FUHRT62' # Your API Key
    ts = TimeSeries(key, output_format='pandas') # 'pandas' or 'json' or 'csv'
    ttm_data, ttm_meta_data = ts.get_intraday(symbol='AAPL',interval='1min', outputsize='compact')
    df = ttm_data.iloc[:50].copy()
    df=df.transpose()
    df.rename(index={"1. open":"open", "2. high":"high", "3. low":"low",
                    "4. close":"close","5. volume":"volume"},inplace=True)
    df=df.reset_index().rename(columns={'index': 'indicator'})
    df = pd.melt(df,id_vars=['indicator'],var_name='date',value_name='rate')
    df = df[df['indicator']!='volume']

    #df = df[df.indicator.isin(['high'])]
    df['date'] = pd.to_datetime(df['date'])
    two_recent_times = df['date'].nlargest(2) # 2 largest dates from recent times
    df = df[df['date'].isin(two_recent_times.values)]
    recent_high = df['rate'].iloc[0]
    older_high = df['rate'].iloc[1]
    print(recent_high, older_high)

    # color buy value conditions - bootstrap class names from https://hackerthemes.com/bootstrap-cheatsheet/
    if recent_high > older_high:
        return recent_high, "bg-success text-white border border-primary border-top-0"
    elif recent_high == older_high:
        return recent_high, "bg-white border border-primary border-top-0"
    elif recent_high < older_high:
        return recent_high, "bg-danger text-white border border-primary border-top-0"

if __name__=='__main__':
    app.run_server(debug=True, port=8050)