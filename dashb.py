import pandas as pd
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
import json
from urllib.request import urlopen
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from datetime import datetime

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
    st.title('US Sales Dashboard')
    
    year_list = list(data['Ship Date'].unique())[::-1]
    
    selected_year = st.selectbox('Select a year', year_list, index=len(year_list)-1)
    df_selected_year = data[data['Ship Date'] == selected_year]
    df_selected_year_sorted = df_selected_year.sort_values(by="Sales", ascending=False)
    df_selected_total = df_selected_year.groupby('State')['Sales'].sum().reset_index()

    map_theme_list = ['open-street-map', 'carto-positron', 'carto-darkmatter']
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
        paper_bgcolor='black',  # Set the overall background color to black
        font=dict(color='white'),  # Set font color to white
        margin=dict(l=10, r=10, t=10, b=10),  # Adjust the left, right, top, and bottom margins
        legend=dict(
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
  selected_year_data = input_df[input_df['Ship Date'] == input_year].reset_index()
  previous_year_data = input_df[input_df['Ship Date'] == input_year - 1].reset_index()
  selected_year_data['sales_difference'] = selected_year_data.Sales.sub(previous_year_data.Sales, fill_value=0)
  return pd.concat([selected_year_data.State, selected_year_data.Sales, selected_year_data.sales_difference], axis=1).sort_values(by="sales_difference", ascending=False)

def make_donut(input_response, input_text, input_color):
  if input_color == 'blue':
      chart_color = ['#29b5e8', '#155F7A']
  if input_color == 'green':
      chart_color = ['#27AE60', '#12783D']
  if input_color == 'orange':
      chart_color = ['#F39C12', '#875A12']
  if input_color == 'red':
      chart_color = ['#E74C3C', '#781F16']
    
  source = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100-input_response, input_response]
  })
  source_bg = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100, 0]
  })
    
  plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          #domain=['A', 'B'],
                          domain=[input_text, ''],
                          # range=['#29b5e8', '#155F7A']),  # 31333F
                          range=chart_color),
                      legend=None),
  ).properties(width=130, height=130)
    
  text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
  plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          # domain=['A', 'B'],
                          domain=[input_text, ''],
                          range=chart_color),  # 31333F
                      legend=None),
  ).properties(width=130, height=130)
  return plot_bg + plot + text

col = st.columns((1.5, 10, 4), gap='small')

with col[1]:
    st.markdown('#### Total Sales by State with Order Locations')
    
    choropleth = make_choropleth(df_selected_year, df_selected_total, 'State', 'Sales', selected_map_theme)
    st.plotly_chart(choropleth, use_container_width=True)

with col[2]:
    st.markdown('#### Top States')

    st.dataframe(df_selected_total.sort_values(by="Sales", ascending=False),
                 column_order=("State", "Sales"),
                 width=800,  
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
    
    with st.expander('About', expanded=True):
        st.write('''
            - Data: [Kaggle](<https://www.kaggle.com/datasets/sulaimanahmed/sales-dataset-of-usa-updated>).
            ''')
