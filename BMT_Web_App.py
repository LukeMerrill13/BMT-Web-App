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

# Manipulating the data
df = pd.read_excel('/Users/luke/Documents/Python/BMT/BMT_360_Giving_Data.xlsx')
df = df[['Amount Awarded','Award Date','Planned Dates:Duration (months)','Recipient Org:Name', 'Grant Programme:Title']]
df = df.fillna(0)
df['End Date'] = df['Award Date'] + df['Planned Dates:Duration (months)'].astype('timedelta64[M]')
df['Planned Dates:Duration (months)'] = df['Planned Dates:Duration (months)']/12
df['Amount Awarded'] = df['Amount Awarded']/(df['Planned Dates:Duration (months)'])
df = df.sort_values('End Date', ascending=True)
df['Award Year'] = df['Award Date'].dt.strftime("%Y")
df['End Year'] = df['End Date'].dt.strftime("%Y")
df = df.rename(columns={'Planned Dates:Duration (months)': 'Duration (years)',
                        'Recipient Org:Name': 'Organisation',
                        'Grant Programme:Title': 'Programme',
                        'Amount Awarded': 'Grant'
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
                list.append(row['Grant'])
        data[index] = list 
    return(data)

Annual_Spending = AnnualSpending(df).transpose().join(df['Programme']).groupby(['Programme']).sum()
Annual_Spending = Annual_Spending.set_axis(years, axis='columns').reset_index()

data = df[['Organisation', 'Programme', 'Grant', 'Duration (years)', 'Award Date', 'End Date']]
data = data[data["End Date"] > pd.Timestamp.now()].sort_values(by=["Programme", "End Date"], ascending=[False, False])


# Streamlit Web App
import streamlit as st

st.markdown("<h1 style='text-align: center; color: white;'>The Brian Mercer Trust</h1>", unsafe_allow_html=True)

def home():
    import streamlit as st
    st.write("Next trustee meeting: Wednesday 5th September, 2024")
    st.write(" ###  News and Updates from our Charities")
    st.write(" ###  New Applications")
    st.write(" ###  Expiring Grants")

def current_grants():
    import streamlit as st    

    st.write(" ### Current Portfolio Allocation")
    col1, col2, col3 = st.columns(3)

    with col1:
        def PortfolioAllocation(selected_date):
            pa = data.copy()
            pa['Active'] = (pa['Award Date'] <= selected_date) & (selected_date <= pa['End Date'])
            return pa.groupby(['Programme'], as_index=False)['Active'].sum()

        selected_date = pd.Timestamp(st.date_input(''))
        Portfolio_Allocation = PortfolioAllocation(selected_date)

        figp = px.pie(
            Portfolio_Allocation,
            values="Active",
            names="Programme",
            color="Programme",
            hole=.7,
            color_discrete_map={
                "Prevention and Relief of Human Suffering": "#FF9900",
                "Causes Local to Blackburn, Lancashire": "#565656",
                "Art in the North West of England": "#E2E2E2",
            },
        )

        figp.update_layout(
            title_text="No. Organisations",
            title_x=0.35,
            annotations=[dict(text=str(int(Portfolio_Allocation["Active"].sum())), x=0.5, y=0.5, font_size=80, showarrow=False)],
            showlegend=False,
        )
        
        
        figp.update_traces(textinfo='none')
        st.plotly_chart(figp, use_container_width=False)

    with col2:
        default_index = date.today().year - 2020
        selected_year = st.selectbox('', (years[0:-1]), index=default_index)

        figx = px.pie(
            Annual_Spending,
            values=selected_year,
            names="Programme",
            color="Programme",
            color_discrete_map={
                "Prevention and Relief of Human Suffering": "#FF9900",
                "Causes Local to Blackburn, Lancashire": "#565656",
                "Art in the North West of England": "#E2E2E2",
            },
        )
        figx.update_layout(title_text="Investments", title_x=0.4, showlegend=False)
        st.plotly_chart(figx, use_container_width=False)

    with col3:
        default_index = date.today().year - 2020
        selectedYear = st.selectbox('', (years), index=default_index)
        Funds = ['Used', 'Available']
        Value = [sum(Annual_Spending[selectedYear]), 1000000 - sum(Annual_Spending[selectedYear])]
        Budget = pd.DataFrame([Funds, Value]).transpose()
        Budget = Budget.rename(columns={0: "Funds", 1: "Value"})

        figb = px.pie(
            Budget,
            values='Value',
            names='Funds',
            color='Funds',
            hole=.7,
            color_discrete_map={'Used': "#565656", 'Available': 'white'},
        )
        figb.update_layout(
            title_text="Remaining Budget",
            title_x=0.35,
            annotations=[dict(text="£" + str(round(1000000 - sum(Annual_Spending[selectedYear]), 2)), x=0.5, y=0.5, font_size=40, showarrow=False)],
        )
        figb.update_traces(hoverinfo='label+percent', marker=dict(line=dict(color='#565656', width=2)))
        figb.update_layout(showlegend=False)
        figb.update_traces(textinfo='none')
        st.plotly_chart(figb, use_container_width=False)

    st.write(" ### Grant Timeline")
    gantt_df = df[df["End Date"] > pd.Timestamp.now()].sort_values(
        by=["Programme", "End Date"], ascending=[False, False]
        )

    
    fig = px.timeline(
        gantt_df,
        x_start="Award Date",
        x_end="End Date",
        y="Organisation",
        color="Programme",
        color_discrete_map={
            "Prevention and Relief of Human Suffering": "#FF9900",
            "Causes Local to Blackburn, Lancashire": "#565656",
            "Art in the North West of England": "#E2E2E2",
            },
        )
    ordered_orgs = gantt_df["Organisation"].drop_duplicates().tolist()
    #fig.update_yaxes(autorange="reversed")
    x_start = pd.Timestamp.now()
    x_end = pd.to_datetime(gantt_df["End Date"]).max()
    fig.update_xaxes(range=[x_start, x_end], tickfont=dict(size=12))

    fig.update_layout(
        width=1800,
        height=800,
        yaxis=dict(tickfont=dict(size=7)),
        legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.4
                )
        )

    st.plotly_chart(fig, use_container_width=False)

    
def historic_grants ():
    import streamlit as st    
    
    
    st.write(" ### Annual Spending Hitsory")
    AS = Annual_Spending.set_index('Programme').transpose().reset_index().rename(columns={'index': 'Year'})
    fig1 = px.bar(
        AS,
        x='Year',
        y=[
            "Causes Local to Blackburn, Lancashire",
            "Art in the North West of England",
            "Prevention and Relief of Human Suffering",
        ],
        color_discrete_map={
            "Prevention and Relief of Human Suffering": "#FF9900",
            "Causes Local to Blackburn, Lancashire": "#565656",
            "Art in the North West of England": "#E2E2E2",
        },
    )
    fig1.update_layout(yaxis_title="Value (£)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=0.75))
    fig1.add_shape(type="line", x0=2019.5, x1=2027.5, y0=1000000, y1=1000000, line=dict(color="#000000", width=2, dash="dash"))
    fig1.update_yaxes(range=[0, 1250000])
    fig1.update_layout(legend_title_text="Programme")
    st.plotly_chart(fig1, use_container_width=False)

    st.write(" ### Historic Grants")
    st.dataframe(df)

def grant_calculator ():
    import streamlit as st    

    st.write(" ### Grant Calculator")

    st.write(" #### Discontinued Grants")
    st.write(" #### Current Grants")
    st.write(" #### New Grants")
    st.write(" #### Discontinued Grants")
    
    
    
    
    
page_names_to_funcs = {
    "Home": home,
    "Current Grants": current_grants,
    "Historic Grants": historic_grants,
    "Grant Calculator": grant_calculator
}

demo_name = st.sidebar.selectbox("Select page", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()













