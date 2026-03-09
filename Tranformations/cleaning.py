import pandas as pd
import numpy as np

# ── LOAD ──────────────────────────────────────────────────────────
players   = pd.read_csv('data/players.csv')
sessions  = pd.read_csv('data/sessions.csv')
matches   = pd.read_csv('data/matches.csv')
purchases = pd.read_csv('data/purchases.csv')
bp        = pd.read_csv('data/battle_pass.csv')
retention = pd.read_csv('data/retention.csv')

print("=== RAW DATA SHAPES ===")
for name, df in [('players',players),('sessions',sessions),('matches',matches),
                 ('purchases',purchases),('battle_pass',bp),('retention',retention)]:
    print(f"{name:15s}: {df.shape[0]:>6,} rows × {df.shape[1]} cols")

# ── PLAYERS CLEANING ──────────────────────────────────────────────
print("\n=== PLAYERS ===")
players['install_date'] = pd.to_datetime(players['install_date'])
print(f"Duplicates: {players.duplicated('player_id').sum()}")
print(f"Null install_date: {players['install_date'].isna().sum()}")
print(f"Platforms: {players['platform'].value_counts().to_dict()}")
print(f"VIP payers: {players['is_payer'].sum()} ({players['is_payer'].mean()*100:.1f}%)")
print(f"Pass holders: {players['stumble_pass'].sum()} ({players['stumble_pass'].mean()*100:.1f}%)")

# Flag invalid gem values
players['gems_valid'] = players['lifetime_gems'] >= 0
print(f"Invalid gem values: {(~players['gems_valid']).sum()}")

# ── SESSIONS CLEANING ─────────────────────────────────────────────
print("\n=== SESSIONS ===")
sessions['session_date'] = pd.to_datetime(sessions['session_date'])
print(f"Duplicates: {sessions.duplicated('session_id').sum()}")
print(f"Null durations: {sessions['duration_sec'].isna().sum()}")

# Flag outlier sessions (< 60s or > 7200s)
sessions['duration_outlier'] = (sessions['duration_sec'] < 60) | (sessions['duration_sec'] > 7200)
print(f"Duration outliers: {sessions['duration_outlier'].sum()} ({sessions['duration_outlier'].mean()*100:.1f}%)")
print(f"Avg session: {sessions['duration_sec'].mean()/60:.1f} min")
print(f"Median session: {sessions['duration_sec'].median()/60:.1f} min")

# ── MATCHES CLEANING ──────────────────────────────────────────────
print("\n=== MATCHES ===")
matches['match_date'] = pd.to_datetime(matches['match_date'])
print(f"Completion rate: {matches['completed'].mean()*100:.1f}%")
print(f"Avg placement: {matches['placement'].mean():.1f} / 32")
print(f"Maps distribution:\n{matches['map_name'].value_counts().to_string()}")

# Flag impossible placements
matches['placement_valid'] = matches['placement'].between(1, matches['players_in_match'])
print(f"Invalid placements: {(~matches['placement_valid']).sum()}")

# ── PURCHASES CLEANING ────────────────────────────────────────────
print("\n=== PURCHASES ===")
purchases['purchase_date'] = pd.to_datetime(purchases['purchase_date'])
print(f"Duplicates: {purchases.duplicated('purchase_id').sum()}")
print(f"Null price: {purchases['price_usd'].isna().sum()}")
print(f"Negative prices: {(purchases['price_usd'] < 0).sum()}")
print(f"Total revenue: ${purchases['price_usd'].sum():,.2f}")
print(f"Categories:\n{purchases.groupby('item_category')['price_usd'].sum().sort_values(ascending=False).to_string()}")

# ── COMPUTED METRICS ──────────────────────────────────────────────
print("\n=== COMPUTED METRICS ===")
# DAU per day
dau = sessions.groupby('session_date')['player_id'].nunique()
print(f"Avg DAU: {dau.mean():.0f} | Peak DAU: {dau.max()} on {dau.idxmax().date()}")

# MAU per month
sessions['month'] = sessions['session_date'].dt.to_period('M')
mau = sessions.groupby('month')['player_id'].nunique()
print(f"MAU: {mau.to_dict()}")

# ARPU / ARPPU
n_players = len(players)
n_payers  = players['is_payer'].sum()
total_rev = purchases['price_usd'].sum()
print(f"ARPU:  ${total_rev/n_players:.2f}")
print(f"ARPPU: ${total_rev/n_payers:.2f}")
print(f"Conversion: {n_payers/n_players*100:.1f}%")

# Stickiness
for m, mau_val in mau.items():
    month_str = str(m)
    avg_dau = dau[dau.index.to_period('M') == m].mean()
    print(f"  Stickiness {month_str}: {avg_dau/mau_val*100:.1f}%")

print("\n=== CLEANING COMPLETE ===")
