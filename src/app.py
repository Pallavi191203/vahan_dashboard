# src/app.py
"""
Run: streamlit run src/app.py
Simple investor-friendly dashboard with filters and KPIs.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

DATA_PATH = Path('data/processed_vahan.csv')

st.set_page_config(page_title='Vahan Investor Dashboard', layout='wide')
st.title('Vahan — Vehicle Registrations (Investor View)')

if not DATA_PATH.exists():
    st.error('Processed data not found. Run: python src/process_data.py')
    st.stop()


df = pd.read_csv(DATA_PATH, parse_dates=['month'])
df['month'] = pd.to_datetime(df['month'])

# Sidebar filters
st.sidebar.header('Filters')
min_date = df['month'].min().date()
max_date = df['month'].max().date()
start_date, end_date = st.sidebar.date_input('Date range', [min_date, max_date])
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

vehicle_types = df['vehicle_type'].unique().tolist()
selected_types = st.sidebar.multiselect('Vehicle Type', vehicle_types, default=vehicle_types)

manufacturers = df['manufacturer'].unique().tolist()
selected_mans = st.sidebar.multiselect('Manufacturer (top shown)', manufacturers, default=manufacturers[:10])

mask = (
    (df['month'] >= start_date) &
    (df['month'] <= end_date) &
    (df['vehicle_type'].isin(selected_types)) &
    (df['manufacturer'].isin(selected_mans))
)
filtered = df[mask]
import io
import streamlit as st

st.sidebar.subheader("Download Data")
buffer = io.BytesIO()
filtered.to_csv(buffer, index=False)
st.sidebar.download_button(
    label="Download CSV",
    data=buffer.getvalue(),
    file_name="filtered_vahan_data.csv",
    mime="text/csv"
)


st.subheader('High-level KPIs')
if filtered.empty:
    st.info('No data for current selection.')
else:
    latest_month = filtered['month'].max()
    kpi_df = filtered[filtered['month'] == latest_month].groupby('vehicle_type', as_index=False)['registrations'].sum()
    kpi_df_prev12 = filtered[filtered['month'] == (latest_month - pd.DateOffset(months=12))].groupby('vehicle_type', as_index=False)['registrations'].sum()
    kpi = pd.merge(kpi_df, kpi_df_prev12, on='vehicle_type', how='left', suffixes=('','_prev12'))
    kpi['yoy_pct'] = (kpi['registrations'] - kpi['registrations_prev12']) / kpi['registrations_prev12'] * 100

    cols = st.columns(min(len(kpi), 4))
    for idx, row in kpi.iterrows():
        col = cols[idx % len(cols)]
        col.metric(label=row['vehicle_type'], value=f"{int(row['registrations']):,}",
                   delta=(f"{row['yoy_pct']:.2f}% YoY" if pd.notna(row['yoy_pct']) else 'N/A'))

    st.subheader('Registrations over time')
    ts = filtered.groupby(['month', 'vehicle_type'], as_index=False)['registrations'].sum()
    fig = px.line(ts, x='month', y='registrations', color='vehicle_type', markers=True,
                  title='Registrations over time by vehicle type')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('Manufacturer performance (latest month)')
    man_perf = filtered.groupby(['manufacturer', 'month'], as_index=False)['registrations'].sum()
    latest = man_perf[man_perf['month'] == latest_month].sort_values('registrations', ascending=False)
    st.dataframe(latest.reset_index(drop=True))

    if 'yoy_pct' in df.columns and 'qoq_pct' in df.columns:
        st.subheader('Sample YoY & QoQ values')
        st.dataframe(filtered[['month','vehicle_type','manufacturer','registrations','yoy_pct','qoq_pct']].tail(30))

st.markdown('-')