import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import requests
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objs as go

# to be moved into a config file
user_id = '9452074C-9BA9-4108-B38D-55B924516C1C'

# Define function to fetch data based on selected date
def fetch_data(user_id, table_name):
    parameters = {
        "UserID": user_id,
        "Method": "GetData",
        "Datasetname": "NIPA",
        "TableName": table_name,
        "Frequency": "Q",
        "Year": "ALL",
        "ResultFormat": "JSON"
    }
    response = requests.get('https://apps.bea.gov/api/data/', params=parameters)
    data = response.json()["BEAAPI"]["Results"]["Data"]
    df = pd.DataFrame(data)
    df["DataValue"] = pd.to_numeric(df["DataValue"])
    df = df.pivot_table(index="TimePeriod", columns="LineDescription", values="DataValue")
    return df

# Fetch initial data to set min/max dates for the date picker
df_quantity = fetch_data(user_id, 'T20303')
df_price = fetch_data(user_id, 'T20304')

# Create a df for quantity and prices of goods and services
df_pq = df_quantity[['Goods', 'Services']]
df_pq = df_pq.rename(columns = {'Goods': 'Quantity (goods)', 'Services': 'Quantity (services)'})
df_pq['Price (goods)'] = df_price['Goods']
df_pq['Price (services)'] = df_price['Services']
df_pq.index = pd.PeriodIndex(df_pq.index, freq='Q').to_timestamp()

# Define app layout
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("BEA: price and quantities of goods and services"),
    html.Div([
        html.Label("Start Date:"),
        dcc.DatePickerSingle(
            id="start-date-picker",
            min_date_allowed=df_pq.index.min().strftime('%Y-%m-%d'),
            max_date_allowed=df_pq.index.max().strftime('%Y-%m-%d'),
            initial_visible_month=df_pq.index[-20].strftime('%Y-%m-%d'),
            date='2010-01-01'  # Set default start date

        ),
        html.Label("End Date:"),
        dcc.DatePickerSingle(
            id="end-date-picker",
            min_date_allowed=df_pq.index.min().strftime('%Y-%m-%d'),
            max_date_allowed=df_pq.index.max().strftime('%Y-%m-%d'),
            initial_visible_month=df_pq.index[-1].strftime('%Y-%m-%d'),
            date=df_pq.index.max().strftime('%Y-%m-%d')  # Set default start date

        )
    ]),
    dcc.Graph(id="price-quantity-graph")
])

# Define callback to update graph based on selected dates
@app.callback(
    Output("price-quantity-graph", "figure"),
    [Input("start-date-picker", "date"), Input("end-date-picker", "date")]
)
def update_graph(start_date, end_date):
    df_quantity = fetch_data(user_id, 'T20303')
    df_price = fetch_data(user_id, 'T20304')

    # Create a df for quantity and prices of goods and services
    df_pq = df_quantity[['Goods', 'Services']]
    df_pq = df_pq.rename(columns = {'Goods': 'Quantity (goods)', 'Services': 'Quantity (services)'})
    df_pq['Price (goods)'] = df_price['Goods']
    df_pq['Price (services)'] = df_price['Services']
    df_pq.index = pd.PeriodIndex(df_pq.index, freq='Q').to_timestamp()


    # Filter data based on selected dates
    if start_date is not None and end_date is not None:
        df_pq_latest = df_pq.loc[start_date:end_date]
    else:
        df_pq_latest = df_pq  # Keep all data if no dates selected
    
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("Goods", "Services"),
                        column_widths=[0.5, 0.5],
                        horizontal_spacing=0.1,
                        specs=[[{"type": "scatter"}, {"type": "scatter"}]],
                        )
    
    fig.add_trace(
        go.Scatter(x=df_pq_latest['Quantity (goods)'],
                   y=df_pq_latest['Price (goods)'],
                   mode='lines+markers+text',
                   name='goods',
                   # text=df_pq_latest.index,
                   text=[index.date() if i%4==0 else '' for i, index in enumerate(df_pq_latest.index)],
                   textposition="top center",
                   textfont=dict(size=10),
                   marker=dict(size=8, line=dict(width=1, color="black")),
                   showlegend=False),
        row=1, col=1
        )
  
    fig.update_xaxes(title_text="Quantity",
                   showgrid=True, gridcolor='lightgray', zeroline=False,
                   row=1, col=1)
    
    fig.update_yaxes(title_text="Price (2012=100)",
                   showgrid=True, gridcolor='lightgray', zeroline=False,
                   row=1, col=1)

    fig.add_trace(
        go.Scatter(x=df_pq_latest['Quantity (services)'],
                   y=df_pq_latest['Price (services)'],
                   mode='lines+markers+text',
                   name='services',
                   # text=df_pq_latest.index,
                   text=[index.date() if i%4==0 else '' for i, index in enumerate(df_pq_latest.index)],
                   textposition="top left",
                   textfont=dict(size=10),
                   marker=dict(size=8, line=dict(width=1, color="black")),
                   showlegend=False),
        row=1, col=2
        )

    fig.update_xaxes(title_text="Quantity",
                   showgrid=True, gridcolor='lightgray', zeroline=False,
                   row=1, col=2)
    fig.update_yaxes(title_text="Price",
                    showgrid=True, gridcolor='lightgray', zeroline=False,
                    row=1, col=2)

    fig.update_layout(height=800, width=1600,
                    title_x=0.5, title_y=0.97,
                    margin=dict(l=50, r=50, t=50, b=50),
                    title_text="NIPA TABLES T20303-T20304",
                    font=dict(family="Arial", size=12, color="black"),
                    plot_bgcolor='white',
                    )
    
    return fig

update_graph('2010Q1', '2023Q1')

if __name__ == '__main__':
    app.run_server(debug=True)
