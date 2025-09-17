#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 10:54:25 2024

@author: luke
"""

# Importing packages
import pandas as pd
import datetime
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
import plotly.express as px

# Maniulating the data
df = pd.read_excel('/Users/luke/Documents/Python/BMT/BMT_360_Giving_Data.xlsx')
df = df[['Amount Awarded','Award Date','Planned Dates:Duration (months)','Recipient Org:Name', 'Grant Programme:Title']]
df['End Date'] = df['Award Date'] + df['Planned Dates:Duration (months)'].astype('timedelta64[M]')
df['Grant PA'] = df['Amount Awarded']/(df['Planned Dates:Duration (months)']/12)
df = df.sort_values('End Date', ascending=True)
df['Award Year'] = df['Award Date'].dt.strftime("%Y")
df['End Year'] = df['End Date'].dt.strftime("%Y")
df = df.rename(columns={'Planned Dates:Duration (months)': 'Duration (months)',
                        'Recipient Org:Name': 'Organisation',
                        'Grant Programme:Title': 'Programme',
                        'Amount Awarded': 'Grant Value'
                        })

years = list(range(int(df['Award Year'].min()), int(df['End Year'].max())+1))
def AnnualSpending(threesixty_data):
    data = pd.DataFrame()
    for index,row in threesixty_data.iterrows():
        list = []
        for year in years:
            if year < int(row['Award Year']) or year >= int(row['End Year']):
                list.append(0)
            else:
                list.append(row['Grant PA'])
        data[index] = list 
    return(data)

Annual_Spending = AnnualSpending(df).transpose().join(df[['Organisation','Programme']]).groupby(['Programme']).sum()
Annual_Spending = Annual_Spending.set_axis(years, axis='columns').reset_index()

DATA = df[['Organisation', 'Programme', 'Grant Value', 'Award Date', 'Duration (months)']]


# Streamlit Web App
import streamlit as st


# Title
st.markdown("<h1 style='text-align: center; color: black;'>The Brian Mercer Trust</h1>", unsafe_allow_html=True)

# Homepage
def home():
    import streamlit as st
    
    st.write( """Next trustee meeting: Wednesday 5th September, 2024""")
    st.write(""" ###  News and Updates from our Charities""")
    st.write(""" ###  New Applications""")
    st.write(""" ###  Expiring Grants""")
   

# Data
def data():
    import streamlit as st    
    
    st.write(""" ### Portfolio Allocation""")
    
    col1, col2, col3 = st.columns(3)
    

# Portfoio Allocation Pie Chart   
    with col1:
        
        Portfolio_Allocation = df
        active = []
        def PortfolioAllocation(date):
            for index, row in df.iterrows():
                if date >= row['Award Date'] and date <= row['End Date']:
                    active.append(True)
                else:
                    active.append(False)
            Portfolio_Allocation['Active'] = active
            return Portfolio_Allocation.groupby(['Programme']).sum().reset_index() 
        
        selected_date = st.date_input('') 
        Portfolio_Allocation = PortfolioAllocation(selected_date)
    
        figp = px.pie(Portfolio_Allocation,
                      values = "Active", names = "Programme", color = "Programme", hole = .7, color_discrete_map={
                          "Prevention and Relief of Human Suffering": "FF9900",
                          "Causes Local to Blackburn, Lancashire": "#565656",
                          "Art in the North West of England": "#E2E2E2"
                          })
        figp.update_layout(title_text="No. Organisations", title_x=0.5, title_y=0.95, title_xanchor="center", title_yanchor="top",
                           annotations=[dict(text=str(Portfolio_Allocation["Active"].sum()),
                                                      x=0.5, y=0.5, font_size=80, showarrow=False)])
        figp.update_layout(showlegend=False)
        figp.update_traces(textinfo='none')

        st.plotly_chart(figp, use_container_width=False)
        
    
# Budget Allocation Pie Chart
    with col2:
        
        default_index = date.today().year - 2020
        selected_year = st.selectbox('', (years[0:-1]), index = default_index)
        
        figx = px.pie(Annual_Spending, values = selected_year , names = "Programme", color = "Programme", color_discrete_map={
            "Prevention and Relief of Human Suffering": "FF9900",
            "Causes Local to Blackburn, Lancashire": "#565656",
            "Art in the North West of England": "#E2E2E2"
            })
        figx.update_layout(title_text="Investments", title_x=0.5, title_y=0.95, title_xanchor="center", title_yanchor="top")
        figx.update_layout(showlegend=False)
        st.plotly_chart(figx, use_container_width=False)
        
        
# Annual Budget Pie Chart 
    with col3:
        
        selectedYear = st.selectbox('', (years), index = default_index)
        Funds = ['Used', 'Available']
        Value = [sum(Annual_Spending[selectedYear]), 1000000 - sum(Annual_Spending[selectedYear])]
        Budget = pd.DataFrame([Funds, Value]).transpose()
        Budget = Budget.rename(columns={0: "Funds", 1: "Value"})

        figb = px.pie(Budget, values = 'Value', names = 'Funds', color = 'Funds', hole = .7, color_discrete_map={
         'Used':"#565656", 
         'Available': 'white'
         })
        
        figb.update_layout(title_text="Remaining Budget", title_x=0.5, title_y=0.95, title_xanchor="center", title_yanchor="top", 
                           annotations=[dict(text = "£" + str(round(1000000 - sum(Annual_Spending[selectedYear]),2)), x=0.5, y=0.5, font_size=40, showarrow=False)])
        figb.update_traces(hoverinfo='label+percent', marker=dict(line=dict(color='#565656', width=2)))
        figb.update_layout(showlegend=False)
        figb.update_traces(textinfo='none')
        st.plotly_chart(figb, use_container_width=False)
        
        
# Gantt Chart       
    st.write(" ### Active Grants Timeline")
    
    fig = px.timeline(df.drop(df[df['End Date']<= datetime.datetime.now()].index), x_start="Award Date", x_end="End Date", y="Organisation", color="Programme", color_discrete_map={
        "Prevention and Relief of Human Suffering": "#FF9900",
        "Causes Local to Blackburn, Lancashire": "#565656",
        "Art in the North West of England": "#E2E2E2"
        })
    fig.update_layout(yaxis=dict(autorange='reversed'))
    fig.update_layout(yaxis={'categoryorder':'array', 'categoryarray':["Art in the North West of England", "Causes Local to Blackburn, Lancashire", "Prevention and Relief of Human Suffering"]})
    fig.update_layout(width=1800)
    fig.update_layout(height=800)
    fig.update_layout(
        xaxis=dict(range=[datetime.datetime.now(), '2028-01-07']))
    fig.update_layout(
        xaxis=dict(tickfont=dict(size=12)),
        yaxis=dict(tickfont=dict(size=7)))
    fig.update_layout(
        legend=dict(orientation="h",yanchor="bottom", y=1.02, xanchor="center", x=0.4))
    
    st.plotly_chart(fig, use_container_width=False)
    
    
    
# Annual Spending Chart 
    st.write(" ### Annual Spending")
    
    AS = Annual_Spending.set_index('Programme').transpose().reset_index().rename(columns={'index': 'Year'})
    
    fig1 = px.bar(AS, x='Year', y=["Causes Local to Blackburn, Lancashire", "Art in the North West of England", "Prevention and Relief of Human Suffering"], color_discrete_map={
        "Prevention and Relief of Human Suffering": "#FF9900",
        "Causes Local to Blackburn, Lancashire": "#565656",
        "Art in the North West of England": "#E2E2E2"
        })
    fig1.update_layout(yaxis_title="Value (£)",
        legend=dict(orientation="h",yanchor="bottom", y=1.02, xanchor="right", x=0.75))
    fig1.add_shape(type="line",
                  x0=2019.5, x1=2027.5, y0=1000000, y1=1000000,  
                  line=dict(color="#000000", width=2, dash="dash")) 
    fig1.update_yaxes(range=[0, 1250000]) 
    fig1.update_layout(legend_title_text="Programme")
    
    st.plotly_chart(fig1, use_container_width=False)
    
    
# Dataframe
    st.write(" ### Grant Database (2020-2024)")
    st.dataframe(DATA)

    
# Sidebar 
page_names_to_funcs = {
    "Home": home,
    "Data": data,
}


demo_name = st.sidebar.selectbox("Select page", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()















