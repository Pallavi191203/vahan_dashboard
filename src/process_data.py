# src/process_data.py
"""
Cleans raw_vahan.csv and produces data/processed_vahan.csv with monthly aggregates
and YoY & QoQ percentage changes per (vehicle_type, manufacturer).
"""

import pandas as pd
from pathlib import Path

INPUT = Path(__file__).resolve().parents[1] / 'data' / 'raw_vahan.csv'
OUT = Path(__file__).resolve().parents[1] / 'data' / 'processed_vahan.csv'


def load_and_clean(path=INPUT):
    df = pd.read_csv(path)
    # normalize column names
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    # find date/period column
    date_cols = [c for c in df.columns if 'date' in c or 'period' in c]
    if not date_cols:
        raise ValueError("No date/period column found. Inspect the CSV columns: %s" % list(df.columns))
    df['date'] = pd.to_datetime(df[date_cols[0]], errors='coerce')

    # find registrations column
    reg_cols = [c for c in df.columns if 'registration' in c or 'registrations' in c or 'count' in c]
    if reg_cols:
        df['registrations'] = pd.to_numeric(df[reg_cols[0]].astype(str).str.replace(',', ''), errors='coerce')
    else:
        df['registrations'] = pd.to_numeric(df.iloc[:, -1].astype(str).str.replace(',', ''), errors='coerce')

    # ensure manufacturer and vehicle_type
    if 'manufacturer' not in df.columns:
        poss = [c for c in df.columns if 'manufact' in c]
        df['manufacturer'] = df[poss[0]] if poss else 'UNKNOWN'
    if 'vehicle_type' not in df.columns:
        poss = [c for c in df.columns if 'vehicle' in c and 'type' in c]
        df['vehicle_type'] = df[poss[0]] if poss else 'ALL'

    df = df[['date', 'vehicle_type', 'manufacturer', 'registrations']].dropna(subset=['date', 'registrations'])
    return df
def aggregate_monthly(df):
    # group by month
    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
    agg = df.groupby(['month', 'vehicle_type', 'manufacturer'], as_index=False)['registrations'].sum()
    agg = agg.sort_values(['vehicle_type', 'manufacturer', 'month'])
    return agg

def compute_changes(agg):
    agg = agg.copy()

    # YoY % change
    agg['yoy_pct'] = (
        agg.groupby(['vehicle_type', 'manufacturer'])['registrations']
        .apply(lambda s: s.pct_change(periods=12) * 100)
        .reset_index(level=[0, 1], drop=True)
    )

    # QoQ % change
    agg['qoq_pct'] = (
        agg.groupby(['vehicle_type', 'manufacturer'])['registrations']
        .apply(lambda s: s.pct_change(periods=3) * 100)
        .reset_index(level=[0, 1], drop=True)
    )

    return agg


def main():
    df = load_and_clean()
    agg = aggregate_monthly(df)
    final = compute_changes(agg)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(OUT, index=False)
    print('Wrote processed data to', OUT)


if __name__ == '__main__':
    main()