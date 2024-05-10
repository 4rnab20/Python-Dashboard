import pandas as pd
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
import json
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px


st.set_page_config(
    page_title="US Sales Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")
data = pd.read_csv("sales_data.csv")
city_data = pd.read_csv("uscities.csv")
city_data = city_data.rename(columns={'city': 'City', 'state_name': 'State'})
data = pd.merge(data, city_data[["City", "State", "lat", "lng"]], on=['City', 'State'], how='left')

data['Sales'] = pd.to_numeric(data['Sales'])
data['Ship Date'] = pd.to_datetime(data['Ship Date'], format="%d/%m/%Y").dt.year
total_sales_by_state = data.groupby('State')['Sales'].sum().reset_index()
        
with st.sidebar:
    st.title('Select Parameters')
    
    year_list = list(data['Ship Date'].unique())[::-1]
    
    selected_year = st.selectbox('Select a year', year_list, index=len(year_list)-1)
    df_selected_year = data[data['Ship Date'] == selected_year]
    df_selected_year_sorted = df_selected_year.sort_values(by="Sales", ascending=False)
    df_selected_total = df_selected_year.groupby('State')['Sales'].sum().reset_index()

    map_theme_list = ['carto-darkmatter', 'carto-positron', 'open-street-map']
    selected_map_theme = st.selectbox('Select a map theme', map_theme_list)

def make_choropleth(input_df, total_df, input_id, input_column, map_theme):

    with open('us-states.json', 'r') as f:
        states = json.load(f)

    fig = px.choropleth_mapbox(
        total_df,
        geojson=states,
        locations=input_id,
        color_continuous_scale="Ice",    
        color= input_column,
        mapbox_style=map_theme,  
        zoom=3,  # Set the initial zoom level,
        center = {"lat": 38, "lon": -96},
        opacity = 0.8,
        featureidkey="properties.name",
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),  # Adjust the left, right, top, and bottom margins
        legend=dict(
            title = "Ship Mode",
            y=0.99,
            x=0.01,
            bgcolor="rgba(0,0,0,0.5)",
            font=dict(color="white")
        )
    )
    scatter_fig = px.scatter_mapbox(
        input_df,
        lat="lat",
        lon="lng",
        color="Ship Mode",  # Example column for color differentiation
        hover_name= "Product Name",
        zoom=1,
        center={"lat": 39, "lon": -96},
        opacity=0.3,    
    )

    for trace in scatter_fig.data:
        fig.add_trace(trace)

    # Show the combined figure
    return fig

def calculate_sales_difference(input_df, input_year):
  selected_year_data = input_df[input_df['Ship Date'] == input_year].groupby('State')['Sales'].sum().reset_index()
  previous_year_data = input_df[input_df['Ship Date'] == input_year - 1].groupby('State')['Sales'].sum().reset_index()
  selected_year_data['sales_difference'] = selected_year_data.Sales.sub(previous_year_data.Sales, fill_value=0)
  return pd.concat([selected_year_data.State, selected_year_data.Sales, selected_year_data.sales_difference], axis=1).sort_values(by="sales_difference", ascending=False)

def format_number(num):
    if abs(num) > 1000000:
        if not abs(num) % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'
    return f'{num // 1000} K'

st.header('US Sales Dashboard', divider = 'blue')
with st.expander('About', expanded=True):
    st.write('''
        - Data: [Kaggle](<https://www.kaggle.com/datasets/sulaimanahmed/sales-dataset-of-usa-updated>).
        - :orange[**Sales Gains/Losses**]: Shows the fluctuation in sales over consecutive years to identify gains or losses in revenue trends.
        - :red[**Total Sales by State with Order Locations**]: Visualizes total sales by state with order locations represented by cities.
        ''')

col2 = st.columns((15, 5), gap='medium')
with col2[0]:
    st.markdown('#### Total Sales by State with Order Locations')
    choropleth = make_choropleth(df_selected_year, df_selected_total, 'State', 'Sales', selected_map_theme)
    st.plotly_chart(choropleth, use_container_width=True)

with col2[1]:
    st.markdown('#### Top States')
    st.dataframe(df_selected_total.sort_values(by="Sales", ascending=False),
    column_order=("State", "Sales"),
    width=800, 
    height= 450, 
    hide_index=True,
    column_config={
    "State": st.column_config.TextColumn(
        "State",
    ),
    "Sales": st.column_config.ProgressColumn(
        "Sales",
        format="%i",
        min_value=0,
        max_value=max(df_selected_total.Sales),
        )}
    )

col = st.columns([2, 1, 4], gap='medium')

with col[0]:
    st.markdown('#### Sales by Category')
    fig = px.sunburst(df_selected_year, path=['Category', 'Sub-Category'], values='Sales')
    st.plotly_chart(fig, use_container_width=True)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

with col[1]:

    st.markdown('#### Gains/Losses')
    df_sales_difference_sorted = calculate_sales_difference(data, selected_year)
    st.markdown('###### max gain/loss:')
    if selected_year > 2015:
        first_state_name = df_sales_difference_sorted.State.iloc[0]
        first_state_sales = format_number(df_sales_difference_sorted.Sales.iloc[0])
        first_state_delta = format_number(df_sales_difference_sorted.sales_difference.iloc[0])
    else:
        first_state_name = '-'
        first_state_sales = '-'
        first_state_delta = ''
    st.metric(label=first_state_name, value=first_state_sales, delta=first_state_delta)
    
    st.markdown('##### min gain/loss:')
    if selected_year > 2015:
        last_state_name = df_sales_difference_sorted.State.iloc[-1]
        first_state_sales = format_number(df_sales_difference_sorted.Sales.iloc[-1])   
        last_state_delta = format_number(df_sales_difference_sorted.sales_difference.iloc[-1])   
    else:
        last_state_name = '-'
        first_state_sales = '-'
        last_state_delta = ''
    st.metric(label=last_state_name, value=first_state_sales, delta=last_state_delta)

with col[2]:
    st.markdown('#### Total Sales Heatmap by Year and State')

    new_df = data.groupby(["State","Ship Date"])["Sales"].sum().reset_index()
    new_df  = new_df.pivot(index='Ship Date', columns='State')['Sales'].fillna(0)
    fig = px.imshow(new_df, x=new_df.columns, y=new_df.index, color_continuous_scale = "IceFire"
)
    fig.update_layout(
        xaxis=dict(title="State"),
        yaxis=dict(title="Ship Date"),
        coloraxis_colorbar=dict(title="Sales"),
        margin=dict(l=10, r=10, t=10, b=10),  # Adjust the left, right, top, and bottom margins
    )
    st.plotly_chart(fig, use_container_width=True)
