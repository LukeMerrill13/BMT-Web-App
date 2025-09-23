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

df = df.replace({"Samaritans of Blackburn with Darwen, Hyndburn and Ribble Valley": "Samaritans"})


years = list(range(int(df['Award Year'].min()), int(df['End Year'].max())+1))


def AnnualSpending(threesixty_data):
    data = pd.DataFrame()
    for index, row in threesixty_data.iterrows():
        vals = []
        award = pd.to_datetime(row['Award Date'])
        end   = pd.to_datetime(row['End Date']) - pd.DateOffset(years=1)
        for year in years:
            # UK tax year boundaries: [6 Apr <year>, 6 Apr <year+1>)
            tax_start = pd.Timestamp(year=year, month=4, day=5) 
            tax_end   = pd.Timestamp(year=year+1, month=4, day=6)

            # overlap test: grant active at any point in this tax year?
            if (end <= tax_start) or (award >= tax_end):
                vals.append(0)
            else:
                vals.append(row['Grant'])
        data[index] = vals
    return data

Annual_Spending = AnnualSpending(df).transpose().join(df['Programme']).groupby(['Programme']).sum()
Annual_Spending = Annual_Spending.set_axis(years, axis='columns').reset_index()

data = df[['Organisation', 'Programme', 'Grant', 'Award Date', 'Duration (years)','End Date']]
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
    
    st.subheader("Portfolio Allocation")
    col1, col2, col3 = st.columns(3)

    with col1:
        def PortfolioAllocation(selected_date):
            pa = data.copy()
            pa['Active'] = (pa['Award Date'] <= selected_date) & (selected_date <= pa['End Date'])
            return pa.groupby(['Programme'], as_index=False)['Active'].sum()
        
        today = datetime.date.today()
        selected_date = pd.Timestamp(st.date_input('', min_value=today, value=today))
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
        
        
        figp.update_traces(textinfo='none', hoverlabel=dict(font_size=20))
        st.plotly_chart(figp, use_container_width=False)

    with col2:
        today_year = datetime.date.today().year
        valid_years = [y for y in years if y >= today_year]
        default_index = 0
        selected_year = st.selectbox('', (valid_years), index=default_index, key = "first box")

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
        figx.update_layout(title_text="Investments", title_x=0.4, showlegend=False, hoverlabel=dict(font_size=20))
        st.plotly_chart(figx, use_container_width=False)

    with col3:
        default_index = 0
        selectedYear = st.selectbox('', (valid_years), index=default_index, key = "second box")
        Funds = ['Used', 'Available']
        Value = [sum(Annual_Spending[selectedYear]), 1200000 - sum(Annual_Spending[selectedYear])]
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
            annotations=[dict(text="£" + str(round(1200000 - sum(Annual_Spending[selectedYear]), 2)), x=0.5, y=0.5, font_size=40, showarrow=False)],
        )
        figb.update_traces(hoverinfo='label+percent', marker=dict(line=dict(color='#565656', width=2)))
        figb.update_layout(showlegend=False, hoverlabel=dict(font_size=20))
        figb.update_traces(textinfo='none')
        st.plotly_chart(figb, use_container_width=False)

    st.subheader("Grant Timeline")
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
                ),
        hoverlabel=dict(font_size=20)
        )

    fig.update_layout(legend_title_text="Programme", legend=dict(font=dict(size=16), title_font=dict(size=18)))
   
    fig.update_layout(
        xaxis_title_font=dict(size=18),  
        yaxis_title_font=dict(size=18),
        xaxis=dict(tickfont=dict(size=14)),  
        yaxis=dict(tickfont=dict(size=14))
    )
    
    st.plotly_chart(fig, use_container_width=False)

    st.subheader("Existing Grants")
    st.dataframe(data.iloc[:,:-1], use_container_width = True, hide_index = True)

def grant_calculator ():
    import streamlit as st    
    
   
    # Page heading 
    st.markdown("Calculate and forecast changes to the trust's portfolio by adding and renewing grants:")

    
    # Current grants
    st.subheader("Current Grants")
    pa = data.copy()
    # OR, if you really only want pure dates (dtype = object of type date):
    pa["Award Date"] = pd.to_datetime(pa["Award Date"]).dt.date
    pa["End Date"]   = pd.to_datetime(pa["End Date"]).dt.date
    pa["Renew"] = 0
    pa["Renew"] = pa["Renew"].astype(bool)
    
    # Keep an editable copy in session state
    if "pa_edit" not in st.session_state:
        st.session_state.pa_edit = pa.copy()
    if "renew_backup" not in st.session_state:
        # keep original per-row values so you can revert when unticking
        st.session_state.renew_backup = st.session_state.pa_edit["Renew"].copy()
    
    # ⬇️ Checkbox to (temporarily) set all to True
    renew_all = st.checkbox("Renew all existing grants")
    
    if renew_all:
        st.session_state.pa_edit["Renew"] = True
    else:
        # revert to whatever the rows had before the 'renew all' was ticked
        st.session_state.pa_edit["Renew"] = st.session_state.renew_backup

    
    edited = st.data_editor(
        st.session_state.pa_edit,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",  
        column_config={
            "Renew": st.column_config.CheckboxColumn("Renew?", help="Tick to mark this grant for renewal", default=False)
        },
        disabled=[c for c in st.session_state.pa_edit.columns if c != "Renew"],
        key="pa_editor",
    )
    
    # save back (convert to 0/1 if you want a binary int column downstream)
    st.session_state.pa_edit = edited.copy()
    st.session_state.pa_edit["Renew"] = st.session_state.pa_edit["Renew"].astype(int)
    
    # if you also want 'pa' updated in-place for later code:
    pa = st.session_state.pa_edit.copy()    

    
    
    # New Grants
    st.subheader("New Grants")
    
    
    with st.form("manual_add_new_grants"):
        col1, col2, col3, col4, col5 = st.columns(5)
    
        # Programme options come from pa
        programme_options = sorted([p for p in pa['Programme'].dropna().unique().tolist()])
        organisation = col1.text_input("Organisation", key="org_input")
    
        programmes = col2.selectbox(
            "Programme",
            options=programme_options,
            help="Select the relevant programme",
            key="prog_multiselect",
        )
    
        grant = col3.number_input(
            "Grant",
            min_value=0.0,
            step=1000.0,
            format="%.2f",
            help="Enter the value of the grant per annum",
            key="grant_input",
        )
    
        duration_years = col4.number_input(
            "Duration (years)",
            min_value=0.0,
            step=0.5,
            format="%.2f",
            help="Enter the number of years the grant will run for",
            key="duration_input",
        )
    
        today = datetime.date.today()
        award_date = col5.date_input(
            "Award Date",
            value=today,
            key="award_date_input",
        )
    
        submitted = st.form_submit_button("Add grant", use_container_width=True)
    
    
    if submitted:
        # --- Validation ---
        errors = []
        if not organisation.strip():
            errors.append("Organisation is required.")
        if not programmes:
            errors.append("Select at least one Programme.")
        if float(duration_years) <= 0:
            errors.append("Duration (years) must be greater than 0.")
    
        if errors:
            for e in errors:
                st.error(e)
        else:
            # Use provided duration; compute End Date = Award Date + Duration (years)
            duration_years_calc = float(duration_years)
    
            # Compute end date (approximate: 365.25-day years to handle leap years on average)
            award_ts = pd.to_datetime(award_date)
            end_date = award_ts + pd.to_timedelta(duration_years_calc * 365.25, unit="D")
    
            # Build a single new row; Programme stores the list from multiselect
            new_rows_df = pd.DataFrame([{
                "Organisation": organisation.strip(),
                "Programme": programmes,                      # list in a single cell
                "Grant": float(grant),
                "Duration (years)": duration_years_calc,
                "Award Date": award_ts,
                "End Date": end_date,
            }])
    
            # Append to the separate dataset
            st.session_state.new_grants = pd.concat(
                [st.session_state.new_grants, new_rows_df],
                ignore_index=True
            )
    
            st.success("New grant created")

    
    if "new_grants" not in st.session_state:
        st.session_state.new_grants = pd.DataFrame({
            c: pd.Series(dtype=pa[c].dtype) for c in pa.columns
        })
    
    cols6 = ["Organisation", "Programme", "Grant", "Duration (years)", "Award Date", "Renew"]
    
    # only add Renew once (don't reset every rerun)
    if "Renew" not in st.session_state.new_grants.columns:
        st.session_state.new_grants["Renew"] = False
    st.session_state.new_grants["Renew"] = st.session_state.new_grants["Renew"].astype(bool)
    
    programme_options = sorted([p for p in pa['Programme'].dropna().unique().tolist()])
    
    edited = st.data_editor(
        st.session_state.new_grants.reindex(columns=cols6).reset_index(drop=True),
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "Organisation": st.column_config.TextColumn("Organisation"),
            "Programme": st.column_config.SelectboxColumn("Programme", options=programme_options),
            "Grant": st.column_config.NumberColumn("Grant (£)", min_value=0.0, step=500.0, format="%.2f"),
            "Duration (years)": st.column_config.NumberColumn("Duration (years)", min_value=0.0, step=1.0, format="%.2f"),
            "Award Date": st.column_config.DateColumn("Award Date"),
            "Renew": st.column_config.CheckboxColumn("Renew?", help="Tick to mark this grant for renewal", default=False)
        },
        key="new_grants_editor",
    )
    
    # --- minimal fix: match row index to the edited grid BEFORE assigning columns
    st.session_state.new_grants = st.session_state.new_grants.reindex(index=edited.index).copy()
    st.session_state.new_grants = st.session_state.new_grants.reindex(columns=pa.columns)  # keep pa's columns
    
    for c in cols6:
        st.session_state.new_grants[c] = edited[c]
    
    st.session_state.new_grants["Award Date"] = pd.to_datetime(
        st.session_state.new_grants["Award Date"], errors="coerce"
    ).dt.normalize()
    st.session_state.new_grants["Duration (years)"] = pd.to_numeric(
        st.session_state.new_grants["Duration (years)"], errors="coerce"
    )
    st.session_state.new_grants["End Date"] = st.session_state.new_grants["Award Date"] + pd.to_timedelta(
        st.session_state.new_grants["Duration (years)"] * 365.25, unit="D"
    )
        

    st.subheader("Grant Portfolio")
    
    new_portfolio = pd.concat(
        [pa, st.session_state.new_grants.reindex(columns=pa.columns)],
        ignore_index=True
    )
    
    new_portfolio['Award Date'] = pd.to_datetime(new_portfolio['Award Date'])
    new_portfolio['End Date'] = pd.to_datetime(new_portfolio['End Date'])   
    today = datetime.date.today()
    new_end = pd.to_datetime(today) + pd.DateOffset(years=10)
    new_portfolio["End Date"] = pd.to_datetime(new_portfolio["End Date"], errors="coerce")
    new_portfolio.loc[new_portfolio["Renew"] == 1, "End Date"] = new_end
    
    years = list(range(int(pd.to_datetime(new_portfolio['Award Date']).dt.year.min()), int(pd.to_datetime(new_portfolio['End Date']).dt.year.max()+1)))

        
    col1, col2, col3 = st.columns(3)

    with col1:
        def PortfolioAllocation(selected_date):
            new_portfolio['Active'] = (new_portfolio['Award Date'] <= selected_date) & (selected_date <= new_portfolio['End Date'])
            return new_portfolio.groupby(['Programme'], as_index=False)['Active'].sum()
        
        today = datetime.date.today()
        selected_date = pd.Timestamp(st.date_input('', min_value=today, value=today))
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
            title_x=0.375,
            annotations=[dict(text=str(int(Portfolio_Allocation["Active"].sum())), x=0.5, y=0.5, font_size=80, showarrow=False)],
            showlegend=False,
            hoverlabel=dict(font_size=20)
        )
        
        figp.update_traces(textinfo='none')
        st.plotly_chart(figp, use_container_width=False)
        

        
        

    with col2:
        
        def AnnualSpending(threesixty_data):
            data = pd.DataFrame()
            for index, row in threesixty_data.iterrows():
                vals = []
                award = pd.to_datetime(row['Award Date'])
                end   = pd.to_datetime(row['End Date']) - pd.DateOffset(years=1)
                for year in years:
                    # UK tax year boundaries: [6 Apr <year>, 6 Apr <year+1>)
                    tax_start = pd.Timestamp(year=year, month=4, day=5) 
                    tax_end   = pd.Timestamp(year=year+1, month=4, day=6)
    
                    # overlap test: grant active at any point in this tax year?
                    if (end <= tax_start) or (award >= tax_end):
                        vals.append(0)
                    else:
                        vals.append(row['Grant'])
                data[index] = vals
            return data
            
        NP = AnnualSpending(new_portfolio).transpose().join(new_portfolio['Programme']).groupby(['Programme']).sum()
        NP = NP.set_axis(years, axis='columns').reset_index()
    
        
        today_year = datetime.date.today().year
        valid_years = [y for y in years if y >= today_year]
        default_index = 0
        selected_year = st.selectbox('', (valid_years), index=default_index, key = "first box")

        figx = px.pie(
            NP,
            values=selected_year,
            names="Programme",
            color="Programme",
            color_discrete_map={
                "Prevention and Relief of Human Suffering": "#FF9900",
                "Causes Local to Blackburn, Lancashire": "#565656",
                "Art in the North West of England": "#E2E2E2",
            },
        )
        figx.update_layout(title_text="Investments", title_x=0.41, showlegend=False, hoverlabel=dict(font_size=20))
        st.plotly_chart(figx, use_container_width=False)
        
        
        

    with col3:
        default_index = 0
        selectedYear = st.selectbox('', (valid_years), index=default_index, key = "second box")
        Funds = ['Used', 'Available']
        Value = [sum(NP[selectedYear]), 1200000 - sum(NP[selectedYear])]
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
            title_x=0.375,
            annotations=[dict(text="£" + str(round(1200000 - sum(NP[selectedYear]), 2)), x=0.5, y=0.5, font_size=40, showarrow=False)],
        )
        figb.update_traces(hoverinfo='label+percent', marker=dict(line=dict(color='#565656', width=2)))
        figb.update_layout(showlegend=False, hoverlabel=dict(font_size=20))
        figb.update_traces(textinfo='none')
        st.plotly_chart(figb, use_container_width=False)    



    
    # Spendig Trajectory
    st.subheader("Spending Forecast")
    

    def AnnualSpending(threesixty_data):
        data = pd.DataFrame()
        for index, row in threesixty_data.iterrows():
            vals = []
            award = pd.to_datetime(row['Award Date'])
            end   = pd.to_datetime(row['End Date']) - pd.DateOffset(years=1)
            for year in years:
                # UK tax year boundaries: [6 Apr <year>, 6 Apr <year+1>)
                tax_start = pd.Timestamp(year=year, month=4, day=5) 
                tax_end   = pd.Timestamp(year=year+1, month=4, day=6)

                # overlap test: grant active at any point in this tax year?
                if (end <= tax_start) or (award >= tax_end):
                    vals.append(0)
                else:
                    vals.append(row['Grant'])
            data[index] = vals
        return data
        
    NP = AnnualSpending(new_portfolio).transpose().join(new_portfolio['Programme']).groupby(['Programme']).sum()
    NP = NP.set_axis(years, axis='columns').reset_index()
    

    NP = NP.set_index('Programme').transpose().reset_index().rename(columns={'index': 'Year'})
    NP = NP[NP['Year'].astype(int) >= (datetime.date.today().year)]
    
    
    fig1 = px.bar(
        NP,
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
    fig1.update_layout(yaxis_title="Value (£)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=0.75), height = 600, hoverlabel=dict(font_size=20))
    fig1.add_shape(type="line", x0=datetime.date.today().year - 0.5, x1=NP['Year'].min()+5.5, y0=1200000, y1=1200000, line=dict(color='red', width=2, dash="dash"))
    fig1.update_yaxes(range=[0, 1500000])
    fig1.update_xaxes(range=[datetime.date.today().year - 0.5 ,NP['Year'].min()+5.5])
    
    fig1.update_layout(legend_title_text="Programme", legend=dict(font=dict(size=16), title_font=dict(size=18)))
   
    fig1.update_layout(
        xaxis_title="Year",
        yaxis_title="Value (£)",
        xaxis_title_font=dict(size=18),  # axis title font
        yaxis_title_font=dict(size=18),
        xaxis=dict(tickfont=dict(size=14)),  # tick labels
        yaxis=dict(tickfont=dict(size=14))
    )

        
    st.plotly_chart(fig1, use_container_width=False)    

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
    st.dataframe(df, use_container_width=True, hide_index=True)
    

page_names_to_funcs = {
    "Home": home,
    "Current Portfolio": current_grants,
    "Grant Calculator": grant_calculator
}

demo_name = st.sidebar.selectbox("Select page", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()













