import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

np.random.seed(42)
random.seed(42)

START = datetime(2024, 1, 1)
END   = datetime(2024, 3, 31)
DAYS  = (END - START).days + 1
N_PLAYERS = 2000

# ── 1. players.csv ─────────────────────────────────────────────────
countries  = ['US','BR','ID','IN','DE','GB','MX','PH','TR','FR']
cw         = [0.22,0.15,0.12,0.10,0.07,0.07,0.06,0.06,0.08,0.07]
platforms  = ['android','ios']
pw         = [0.78, 0.22]
age_groups = ['13-17','18-24','25-34','35-44','45+']
aw         = [0.18,0.35,0.27,0.13,0.07]
acq        = ['organic','paid_social','influencer','cross_promo','app_store_search']
acqw       = [0.30,0.28,0.18,0.14,0.10]

install_dates = [START + timedelta(days=random.randint(0, DAYS-1)) for _ in range(N_PLAYERS)]

players = pd.DataFrame({
    'player_id':    [f'P{str(i).zfill(5)}' for i in range(N_PLAYERS)],
    'install_date': install_dates,
    'country':      np.random.choice(countries, N_PLAYERS, p=cw),
    'platform':     np.random.choice(platforms, N_PLAYERS, p=pw),
    'age_group':    np.random.choice(age_groups, N_PLAYERS, p=aw),
    'acq_source':   np.random.choice(acq, N_PLAYERS, p=acqw),
    'is_payer':     np.random.choice([True,False], N_PLAYERS, p=[0.08,0.92]),
    'stumble_pass': np.random.choice([True,False], N_PLAYERS, p=[0.12,0.88]),
    'lifetime_gems': np.random.randint(0, 50000, N_PLAYERS),
})
players['install_date'] = pd.to_datetime(players['install_date'])

# ── 2. sessions.csv ────────────────────────────────────────────────
session_rows = []
for _, p in players.iterrows():
    install = p['install_date']
    days_active = random.randint(1, DAYS - (install - START).days)
    # retention curve: high early, drops fast
    for d in range(days_active):
        # probability of playing on day d
        prob = max(0.05, 0.95 * np.exp(-d * 0.05))
        if random.random() < prob:
            n_sessions = random.choices([1,2,3,4,5],[0.4,0.3,0.15,0.1,0.05])[0]
            for _ in range(n_sessions):
                sess_date = install + timedelta(days=d)
                if sess_date > END: break
                duration = int(np.random.lognormal(7.5, 0.6))  # seconds
                duration = min(max(duration, 120), 5400)
                rounds_played = random.randint(1, 8)
                session_rows.append({
                    'session_id':    f'S{len(session_rows):07d}',
                    'player_id':     p['player_id'],
                    'session_date':  sess_date.date(),
                    'platform':      p['platform'],
                    'country':       p['country'],
                    'duration_sec':  duration,
                    'rounds_played': rounds_played,
                    'rounds_won':    random.randint(0, min(rounds_played,3)),
                })

sessions = pd.DataFrame(session_rows)
print(f"Sessions: {len(sessions)}")

# ── 3. matches.csv ─────────────────────────────────────────────────
maps = ['Honey Drop','Lava Rush','Block Dash','Stumble Soccer','Rocket Mayhem',
        'Hex-a-Gone','Rainbow Road','Freezy Peak','Jungle Roll','Cannon Climb']
match_rows = []
for _, s in sessions.iterrows():
    for r in range(s['rounds_played']):
        match_rows.append({
            'match_id':       f'M{len(match_rows):08d}',
            'session_id':     s['session_id'],
            'player_id':      s['player_id'],
            'match_date':     s['session_date'],
            'map_name':       random.choice(maps),
            'players_in_match': random.randint(20, 32),
            'placement':      random.randint(1, 32),
            'completed':      random.random() > 0.08,
            'duration_sec':   random.randint(90, 240),
            'coins_earned':   random.randint(10, 200),
            'xp_earned':      random.randint(50, 500),
        })

matches = pd.DataFrame(match_rows)
print(f"Matches: {len(matches)}")

# ── 4. purchases.csv ───────────────────────────────────────────────
items = [
    ('Stumble Pass Monthly','season_pass',4.99),
    ('Gem Pack S','gems',0.99),
    ('Gem Pack M','gems',4.99),
    ('Gem Pack L','gems',9.99),
    ('Gem Pack XL','gems',19.99),
    ('Starter Bundle','bundle',2.99),
    ('VIP Bundle','bundle',14.99),
    ('Legend Skin','cosmetic',7.99),
    ('Rare Skin','cosmetic',3.99),
    ('Emote Pack','cosmetic',1.99),
]
payers = players[players['is_payer']]
purchase_rows = []
for _, p in payers.iterrows():
    n_purchases = random.randint(1, 15)
    for _ in range(n_purchases):
        item = random.choice(items)
        pdate = p['install_date'] + timedelta(days=random.randint(0, DAYS-1))
        if pdate > END: pdate = END
        purchase_rows.append({
            'purchase_id':   f'T{len(purchase_rows):07d}',
            'player_id':     p['player_id'],
            'purchase_date': pdate.date(),
            'item_name':     item[0],
            'item_category': item[1],
            'price_usd':     item[2],
            'platform':      p['platform'],
            'country':       p['country'],
        })

purchases = pd.DataFrame(purchase_rows)
print(f"Purchases: {len(purchases)}")

# ── 5. battle_pass.csv ─────────────────────────────────────────────
pass_holders = players[players['stumble_pass']]
bp_rows = []
for _, p in pass_holders.iterrows():
    season = random.choice(['S12','S13','S14'])
    bp_rows.append({
        'player_id':        p['player_id'],
        'season':           season,
        'purchase_date':    (p['install_date'] + timedelta(days=random.randint(0,14))).date(),
        'tier_reached':     random.randint(1, 50),
        'max_tier':         50,
        'missions_completed': random.randint(5, 30),
        'gems_spent':       4.99,
        'platform':         p['platform'],
        'country':          p['country'],
    })

battle_pass = pd.DataFrame(bp_rows)
print(f"Battle Pass: {len(battle_pass)}")

# ── 6. retention.csv (pre-computed cohort table) ────────────────────
cohort_rows = []
for week_offset in range(12):
    cohort_start = START + timedelta(weeks=week_offset)
    cohort_end   = cohort_start + timedelta(days=6)
    cohort_players = players[
        (players['install_date'] >= cohort_start) & 
        (players['install_date'] <= cohort_end)
    ]
    n = len(cohort_players)
    if n < 5: continue
    # realistic retention decay
    d1  = round(random.uniform(0.38, 0.48), 3)
    d7  = round(random.uniform(0.14, 0.22), 3)
    d14 = round(random.uniform(0.09, 0.14), 3)
    d30 = round(random.uniform(0.05, 0.09), 3)
    cohort_rows.append({
        'cohort_week':    cohort_start.strftime('%Y-%m-%d'),
        'cohort_size':    n,
        'd1_retention':   d1,
        'd7_retention':   d7,
        'd14_retention':  d14,
        'd30_retention':  d30,
        'avg_sessions_d7': round(random.uniform(2.5, 5.5), 1),
    })

retention = pd.DataFrame(cohort_rows)

# ── SAVE ───────────────────────────────────────────────────────────
out = '/home/claude/stumble/data'
os.makedirs(out, exist_ok=True)
players.to_csv(f'{out}/players.csv', index=False)
sessions.to_csv(f'{out}/sessions.csv', index=False)
matches.to_csv(f'{out}/matches.csv', index=False)
purchases.to_csv(f'{out}/purchases.csv', index=False)
battle_pass.to_csv(f'{out}/battle_pass.csv', index=False)
retention.to_csv(f'{out}/retention.csv', index=False)
print("All CSVs saved!")
