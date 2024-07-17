import streamlit as st
import pandas as pd
from datetime import datetime

# Load the Actual and Budget data from the provided CSV files
actual_data = pd.read_csv("./Actual.csv")
budget_data = pd.read_csv("./Budget.csv")

# Convert date columns to datetime
actual_data['Last Discharge Port Depart'] = pd.to_datetime(actual_data['Last Discharge Port Depart'])
actual_data['Discharge Port Depart'] = pd.to_datetime(actual_data['Discharge Port Depart'])
budget_data['Last Discharge Port Depart'] = pd.to_datetime(budget_data['Last Discharge Port Depart'])
budget_data['Discharge Port Depart'] = pd.to_datetime(budget_data['Discharge Port Depart'])

# Streamlit app
st.title('Actual vs Budget Data Analysis')

# Date selectors
start_date = st.date_input('Start Date', value=datetime(2024, 1, 1))
end_date = st.date_input('End Date', value=datetime(2024, 12, 31))

# Convert Streamlit date inputs to datetime
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)


# Define the filtering and computation logic
def filter_and_compute_time(data):
    conditions = [
        ((start_date < data['Last Discharge Port Depart']) &
         (data['Last Discharge Port Depart'] < data['Discharge Port Depart']) &
         (data['Discharge Port Depart'] < end_date)),
        ((start_date < data['Last Discharge Port Depart']) &
         (data['Last Discharge Port Depart'] < end_date) &
         (end_date < data['Discharge Port Depart'])),
        ((data['Last Discharge Port Depart'] < start_date) &
         (start_date < data['Discharge Port Depart']) &
         (data['Discharge Port Depart'] < end_date)),
        ((data['Last Discharge Port Depart'] < start_date) &
         (start_date < end_date) &
         (end_date < data['Discharge Port Depart']))
    ]

    choices = [
        (data['Discharge Port Depart'] - data['Last Discharge Port Depart']),
        (end_date - data['Last Discharge Port Depart']),
        (data['Discharge Port Depart'] - start_date),
        (end_date - start_date)
    ]

    data['Recognized Time'] = pd.to_timedelta(0)  # Initialize the Time column
    for condition, choice in zip(conditions, choices):
        data.loc[condition, 'Recognized Time'] = choice

    # Convert Time to days with 2 decimal precision
    data['Recognized Time'] = data['Recognized Time'].dt.total_seconds() / (24 * 3600)

    # Calculate Actual Revenue
    data['Total Time'] = data['Total Time'].astype(float)
    data['Total Revenue'] = data['Total Revenue'].astype(float)
    data['Recognized Revenue'] = data.apply(
        lambda row: row['Total Revenue'] * (row['Recognized Time'] / row['Total Time']) if row['Total Time'] != 0 else 0, axis=1)
    data['Recognized Revenue'] = data['Recognized Revenue'].round(2)
    data['Recognized Time'] = data['Recognized Time'].round(2)
    data['Total Revenue'] = data['Total Revenue'].round(2)
    return data[
        conditions[0] | conditions[1] | conditions[2] | conditions[3]
        ]


# Filter and compute time and actual revenue for Actual and Budget data
filtered_actual_data = filter_and_compute_time(actual_data)
filtered_actual_data = filtered_actual_data.rename(columns={'Discharge Port Depart': 'End Date', 'Last Discharge Port Depart': 'Start Date', 'Total Time': 'Total Trip Time'})
filtered_budget_data = filter_and_compute_time(budget_data)
filtered_budget_data = filtered_budget_data.rename(columns={'Discharge Port Depart': 'End Date', 'Last Discharge Port Depart': 'Start Date', 'Total Time': 'Total Trip Time'})

# Group by Vessel and calculate the total actual and budget revenue
summary_actual = filtered_actual_data.groupby('Vessel').agg({'Recognized Revenue': 'sum'}).reset_index()
summary_budget = filtered_budget_data.groupby('Vessel').agg({'Recognized Revenue': 'sum'}).reset_index()

# Merge the actual and budget summaries
summary = pd.merge(summary_actual, summary_budget, on='Vessel', how='outer', suffixes=(' (Actual)', ' (Budget)'))
summary['Variance'] = summary['Recognized Revenue (Actual)'] - summary['Recognized Revenue (Budget)']

# Display the summarized results
st.subheader('Summarized Results by Vessel')
st.write(summary)

# Display the filtered and computed data
st.subheader('Filtered and Computed Actual Data')
st.write(filtered_actual_data[
             ['Vessel', 'Trip No', 'Start Date', 'End Date', 'Recognized Time', 'Trip Details', 'Total Load Quantity', 'Total Trip Time', 'Recognized Revenue', 'Total Revenue']])

st.subheader('Filtered and Computed Budget Data')
st.write(filtered_budget_data[
             ['Vessel', 'Trip No', 'Start Date', 'End Date', 'Recognized Time', 'Trip Details', 'Total Load Quantity', 'Total Trip Time', 'Recognized Revenue', 'Total Revenue']])

# Add any additional analysis or visualizations here
