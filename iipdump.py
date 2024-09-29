import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.io as pio
import io
from plotly.subplots import make_subplots
import dash_core_components as dcc
import dash_html_components as html
from dotenv import load_dotenv 
import os


        
# Load environment variables from .env file
load_dotenv()

# Construct database URL from environment variables
#db_url = f"{os.getenv("ENGINE")}://{os.getenv('DTABASE_USER')}:{os.getenv('PASSWORD')}@{os.getenv('HOST')}:{os.getenv('PORT')}/{os.getenv('IIP_DATABASE')}"
db_url =  create_engine(f'{os.getenv("ENGINE")}://{os.getenv("DTABASE_USER")}:{os.getenv("PASSWORD")}@{os.getenv("HOST")}/{os.getenv("IIP_DATABASE")}')

# # Database URL
# db_url = 'postgresql://read_user:read_user@10.24.89.9:5432/iip_db'

# Read data from the database
post_state = pd.read_sql_query('select * from iip_fact', db_url)
post_data = pd.DataFrame(post_state)

post_data = pd.read_sql_query('SELECT category_code,subcategory_code, frequency_code, type, financialyear, month_code, year, index, growth_rate, base_year from public.iip_fact where subcategory_code is Null', db_url)
#post_data["subcategory_code"].fillna('NA',inplace=True)
#post_data=post_data[post_data["subcategory_code"]=='NA']
post_data1 = pd.read_sql_query('select frequency_code , description from frequency', db_url)
post_data2 = pd.read_sql_query('select category_code, description from category', db_url)
post_data3 = pd.read_sql_query('select month_code, description from month', db_url)
df = post_data[["category_code",    "frequency_code",   "type", "financialyear",   "month_code","year", "index", "growth_rate","base_year"]]

# Dictionary mapping column names to their respective DataFrames and keys
mappings = {
    'category_code': (post_data2, 'category_code'),
    'frequency_code': (post_data1, 'frequency_code'),
    'month_code': (post_data3, 'month_code'),
}

# Perform the mapping for each column
for col, (df_mapping, key) in mappings.items():
    mapping_dict = df_mapping.set_index(key)['description'].to_dict()
    print(f"Mapping for {col}: {mapping_dict}")  # Debugging statement
    df.loc[:, col] = df[col].map(mapping_dict)


# Mapping month names to zero-padded numeric values
month_to_numeric = {
    'January': '01', 'February': '02', 'March': '03', 'April': '04',
    'May': '05', 'June': '06', 'July': '07', 'August': '08',
    'September': '09', 'October': '10', 'November': '11', 'December': '12'
}

# Convert month names to zero-padded numeric values
df['month_numeric'] = df['month_code'].map(month_to_numeric)

# Convert NaN values in 'month' column to NA
df['month_code'] = df['month_code'].replace(np.nan, 'NA')

df['year'] = df['year'].astype('Int64')   # Use 'Int64' to preserve NaN values

# Convert NaN to 'NA'
df = df.astype(str).replace('nan', 'NA')

df = df.astype(str).replace('<NA>', 'NA')

df["Month_year"]=df["year"]+df["month_numeric"]
df_monthly=df[df["frequency_code"]=="Monthly"]
df_annually=df[df["frequency_code"]=="Annually"]

df_monthly["Month_year1"]=df_monthly["month_code"].astype(str)+' '+df_monthly["year"].astype(str)
df_monthly.sort_values(by="Month_year",ascending=True,inplace=True)
df_annually.sort_values(by="financialyear",ascending=True,inplace=True)


# Create a Dash application
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
    {
        "href": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css",
        "rel": "stylesheet",
    },
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
# app = dash.Dash(__name__, external_stylesheets=external_stylesheets, routes_pathname_prefix = '/viz/iip/', requests_pathname_prefix = '/viz/iip/')
app.title = "Index Of Industrial Production"

# Default figure for initial graph display
default_fig = go.Figure()

# App layout
app.layout = html.Div(
    className="content-wrapper",
    children=[
        html.Div(
            style={'flex': '0 1 320px', 'padding': '10px', 'boxSizing': 'border-box'},
            children=[
               html.H1("Select Parameters to Get Chart", className="parameter-data",style={'fontSize': '15px', 'fontWeight': 'normal','marginBottom': '0px', 'marginTop': '20px'}),
                html.Div(
                    children=[
                        html.Div(children="Base Year", className="menu-title"),
                        dcc.Dropdown(
                            id="base-year-dropdown",
                            options=[{'label': i, 'value': i} for i in df['base_year'].unique()],
                            multi=False,
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                            placeholder="Base_year",
                            value="2012",  # Default value
                        ),
                    ],
                    style={'marginBottom': '0px'}
                ),
                html.Div(
                    children=[
                        html.Div(children="Frequency", className="menu-title"),
                        dcc.Dropdown(
                            id="frequency-dropdown",
                            options=[{'label': 'Annually', 'value': 'Annually'}, {'label': 'Monthly', 'value': 'Monthly'}],
                            multi=False,
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                            placeholder="Select Frequency",
                            value="Annually",  # Default value
                        ),
                    ],
                    style={'marginBottom': '0px'}
                ),
                html.Div(
                    children=[
                        html.Div(children="Type", className="menu-title"),
                        dcc.Dropdown(
                            id="type-dropdown",
                            options=[{'label': i, 'value': i} for i in df['type'].unique()],
                            clearable=False,
                            placeholder="Type",
                            searchable=False,
                            className="dropdown",
                            value="General",  # Default value
                        ),
                    ],
                    style={'marginBottom': '0px'}
                ),
                html.Div(
                    children=[
                        html.Div(children="Category", className="menu-title"),
                        dcc.Dropdown(
                            id="category-dropdown",
                            options=[{'label': i, 'value': i} for i in df['category_code'].unique()],
                            clearable=False,
                            placeholder="Category",
                            searchable=False,
                            className="dropdown",
                            value="General",  # Default value
                        ),
                    ],
                    style={'marginBottom': '0px'}
                ),
                html.Div(
                    children=[
                        html.Div(children="Indicator", className="menu-title"),
                        dcc.Dropdown(
                            id="price-type-dropdown",
                            options=[
                                {'label': 'Index', 'value': 'index'},
                                {'label': 'Growth Rate (%)', 'value': 'growth_rate'},
                            ],
                            value='growth_rate',
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                            placeholder="Select Price Type"
                        ),
                    ],
                    style={'marginBottom': '0px'}
                ),
                html.Div(
                    id="financial-year-container",
                    children=[
                        html.Div(children="Financial Year", className="menu-title"),
                        dcc.Dropdown(
                            id="financial-year-dropdown",
                            options=[{'label': 'Select All', 'value': 'Select All'}] + [{'label': str(year), 'value': year} for year in df_annually['financialyear'].unique()],
                            multi=True,

                            className="dropdown",
                            placeholder="Select Financial Year",
                            value="Select All"  # Default value
                        ),
                    ],
                    style={'marginBottom': '0px'}
                ),
                html.Div(
                    id="year-container",
                    style={'display': 'none','marginBottom': '0px'},  # Initially hide the Year dropdown container
                    children=[
                        html.Div(children="Year", className="menu-title"),
                        dcc.Dropdown(
                            id="year-dropdown",
                            options=[{'label': 'Select All', 'value': 'Select All'}]+[{'label': str(year), 'value': year} for year in df_monthly['year'].unique()],
                            multi=True,
                            className="dropdown",
                            placeholder="Select Year",
                            value='Select All'  # Default value
                        ),
                    ],
                ),
                html.Button(
                    'Apply', id='apply-button', n_clicks=0, className='mr-1',
                    style={
                        'width': '100%',
                        'background': 'radial-gradient(circle, #0a266c 0, #085858 3%, #0a266c 94%)',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'text-align': 'center',
                        'text-decoration': 'none',
                        'display': 'inline-block',
                        'font-size': '16px',
                        'margin': '15px 0',
                        'cursor': 'pointer',
                        'border-radius': '8px',
                        'marginTop': '30px',
                        'marginBottom': '0px'
                    }
                ),
                html.Button(
                    'Download', id='download-svg-button', n_clicks=0, className='mr-1',
                    style={
                        'width': '100%',
                        'background': 'radial-gradient(circle, #0a266c 0, #085858 3%, #0a266c 94%)',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'text-align': 'center',
                        'text-decoration': 'none',
                        'display': 'inline-block',
                        'font-size': '16px',
                        'margin': '20px 0',
                        'cursor': 'pointer',
                        'border-radius': '8px',
                        'marginBottom': '0px'
                    }
                ),
                html.Div(
                    id='error-message',
                    style={'color': 'red', 'textAlign': 'center', 'marginTop': '20px'}
                ),
            ]
        ),
        dcc.Download(id="download-svg"),
        html.Div(
            style={'flex': '1', 'padding': '20px', 'position': 'relative', 'text-align': 'center',
                   'height': 'calc(100% - 50px)'},
            children=[
                dcc.Loading(
                    id="loading-graph",
                    type="circle", color='#83b944',  # or "default"
                    children=[
                        html.Div(
                            id='graph-container',
                            style={'position': 'relative'},
                            children=[
                                html.Div(
                                    className="loader",
                                    id="loading-circle",
                                    style={"position": "absolute", "top": "50%", "left": "50%",
                                           "transform": "translate(-50%, -50%)"}
                                ),
                                dcc.Graph(
                                    id="time-series-plot",
                                    config={"displayModeBar": False},
                                    # style={'width': '100%', 'height': '100%'}
                                ),
                            ]
                        ),
                    ]
                ),
            ],
        ),
    ]
)
# Callback to update financial year and year dropdown visibility based on frequency
@app.callback(
    [Output("financial-year-container", "style"),
     Output("year-container", "style")],
    Input("frequency-dropdown", "value")
)
def update_dropdown_visibility(frequency):
    if frequency == "Annually":
        return {'display': 'block'}, {'display': 'none'}
    elif frequency == "Monthly":
        return {'display': 'none'}, {'display': 'block'}
    else:
        return {'display': 'none'}, {'display': 'none'}

# Callback to update financial year dropdown options based on frequency and base year selection
@app.callback(
    Output("financial-year-dropdown", "options"),
    [Input("frequency-dropdown", "value"),
     Input("base-year-dropdown", "value")]
)
def update_financial_year_options(frequency, base_year):
    if frequency == "Annually":
        fin_years = df_annually[df_annually["base_year"] == base_year]
        fin_year = fin_years["financialyear"].unique()
        return [{'label': 'Select All', 'value': 'Select All'}] + [{"label": str(year), "value": year} for year in fin_year]
    else:
        return [{'label': 'Select All', 'value': 'Select All'}]

# Callback to update year dropdown options based on frequency and base year selection
@app.callback(
    Output("year-dropdown", "options"),
    [Input("frequency-dropdown", "value"),
     Input("base-year-dropdown", "value")]
)
def update_year_options(frequency, base_year):
    if frequency == "Monthly":
        years = df_monthly[df_monthly["base_year"] == base_year]
        year = years['year'].unique()
        return [{'label': 'Select All', 'value': 'Select All'}] + [{"label": str(year), "value": year} for year in year]
    else:
        return []

# Callback to update type dropdown options based on frequency
@app.callback(
    Output("type-dropdown", "options"),
    Input("frequency-dropdown", "value")
)
def update_type_options(frequency):
    filtered_data = df[df['frequency_code'] == frequency]
    return [{'label': i, 'value': i} for i in filtered_data['type'].unique()]

# Callback to update category dropdown options based on type selection
@app.callback(
    Output("category-dropdown", "options"),
    Input("type-dropdown", "value")
)
def update_category_options(selected_type):
    filtered_data = df[df['type'] == selected_type]
    return [{'label': i, 'value': i} for i in filtered_data['category_code'].unique()]

# Callback to update graph based on user input
@app.callback(
    [Output("time-series-plot", "figure"),
     Output("error-message", "children"),
     Output('graph-container', 'style')],
    Input('apply-button', 'n_clicks'),
    [State("frequency-dropdown", "value"),
     State("type-dropdown", "value"),
     State("category-dropdown", "value"),
     State("price-type-dropdown", "value"),
     State("financial-year-dropdown", "value"),
     State("year-dropdown", "value"),  
     State("base-year-dropdown", "value")]
)
def update_graph(n_clicks, frequency, selected_type, selected_category, price_type, selected_financial_years, selected_year, base_year):
    try:
        # Ensure selected_financial_years or selected_year is a list
        if frequency == "Annually":
            if not selected_financial_years or 'Select All' in selected_financial_years:
                selected_financial_years = df_annually['financialyear'].unique().tolist()
            elif not isinstance(selected_financial_years, list):
                selected_financial_years = [selected_financial_years]
        elif frequency == "Monthly":
            if not selected_year or 'Select All' in selected_year:
                selected_year = df_monthly['year'].unique().tolist()
            elif not isinstance(selected_year, list):
                selected_year = [selected_year]

        # Filter data based on selected parameters
        if frequency == "Annually":
            filtered_data = df_annually[
                (df_annually['frequency_code'] == frequency) &
                (df_annually['type'] == selected_type) &
                (df_annually['category_code'] == selected_category) &
                (df_annually["financialyear"].isin(selected_financial_years)) &
                (df_annually['base_year'] == base_year)
            ]
            x_axis = 'financialyear'
        elif frequency == "Monthly":
            filtered_data = df_monthly[
                (df_monthly['frequency_code'] == frequency) &
                (df_monthly['type'] == selected_type) &
                (df_monthly['category_code'] == selected_category) &
                (df_monthly["year"].isin(selected_year)) &
                (df_monthly['base_year'] == base_year)
            ]
            x_axis = 'Month_year1'

        # Convert index and growth_rate columns to float if necessary
        filtered_data['index'] = filtered_data['index'].astype(float)
        filtered_data['growth_rate'] = filtered_data['growth_rate'].replace('NA', np.nan).astype(float)

        # Create figure
        fig = make_subplots(specs=[[{"secondary_y": True}]])

         # Add bar chart for Index
        if price_type in ['index']:
            fig.add_trace(go.Scatter(x=filtered_data[x_axis], y=filtered_data['index'], name='Index',mode='lines+markers', marker_color='#0F4366', hovertemplate='Index: %{y:.1f}<extra></extra>'), secondary_y=False)

        # Add line chart for Growth Rate
        if price_type in ['growth_rate']:
            fig.add_trace(go.Scatter(x=filtered_data[x_axis], y=filtered_data['growth_rate'], mode='lines+markers', name='Growth Rate', marker_color='#EF553B', hovertemplate='Growth Rate: %{y:.1f}%<extra></extra>'),secondary_y=False)

        #title_text = 'Index Of Industrial Production'
        # Update layout
        fig.update_layout(
            #title={'text': f'<span style="text-decoration: underline;">{title_text}</span>', 'x': 0.5, 'xanchor': 'center'},
            xaxis_title='Financial Year' if frequency == 'Annually' else 'Month-Year',
            yaxis_title='Index',
            yaxis2_title='Growth Rate (%)',
            title_font=dict(size=20, family='Arial, sans-serif', color='black', weight='bold'),
            xaxis_title_font=dict(size=17, family='Arial, sans-serif', color='black', weight='bold'),
            yaxis_title_font=dict(size=17, family='Arial, sans-serif', color='black', weight='bold'),
            yaxis2_title_font=dict(size=17, family='Arial, sans-serif', color='black', weight='bold'),
            xaxis=dict(
            tickangle=270 # Set the tickangle based on selected_frequency
        ),
            font_color='black',
            # title_x=0.5,
            margin=dict(t=0),
            # width=1520,
            # height=770,
            template='plotly_white',
            legend=dict(
                yanchor="top",
                y=1.2,
                xanchor="right"
            ),
            hovermode='x'
        )

        fig.update_xaxes(title_text='Financial Year' if frequency == 'Annually' else 'Month-Year', color='black', title_font=dict(size=18, family='Arial, sans-serif', color='black', weight='bold'))
        if price_type=="index":
            fig.update_yaxes(title_text='Index', color='black', title_font=dict(size=18, family='Arial, sans-serif', color='black', weight='bold'), secondary_y=False)
        if price_type=="growth_rate":
            fig.update_yaxes(title_text='Growth Rate (%)', title_font=dict(size=18, family='Arial, sans-serif', color='black', weight='bold'), secondary_y=False)
        return fig, "", {'position': 'relative'}

    except Exception as e:
        error_message = f"Error updating graph: {str(e)}"
        return default_fig, error_message, {'display': 'none'}  # Hide graph container on error


# Callback to download SVG
@app.callback(
    Output("download-svg", "data"),
    Input("download-svg-button", "n_clicks"),
    State("time-series-plot", "figure"),
    prevent_initial_call=True
)
def download_svg(n_clicks, figure):
    try:
        if n_clicks > 0:
            fig = go.Figure(figure)
            svg_str = pio.to_image(fig, format="svg")

            buffer = io.BytesIO()
            buffer.write(svg_str)
            buffer.seek(0)

            return dcc.send_bytes(buffer.getvalue(), "plot.svg")
    except Exception as e:
        print(f"Error downloading SVG: {str(e)}")
    return None

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_ui=False, dev_tools_props_check=False, port=4574, host="localhost")
