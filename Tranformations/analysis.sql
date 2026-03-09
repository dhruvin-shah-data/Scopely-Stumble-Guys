-- ── 1. DAU / MAU / STICKINESS ───────────────────────────────────
-- Daily Active Users
SELECT
    session_date,
    COUNT(DISTINCT player_id) AS dau
FROM sessions
GROUP BY session_date
ORDER BY session_date;

-- Monthly Active Users + Stickiness
WITH daily AS (
    SELECT
        DATE_TRUNC('month', session_date) AS month,
        session_date,
        COUNT(DISTINCT player_id) AS dau
    FROM sessions
    GROUP BY 1, 2
),
monthly AS (
    SELECT
        DATE_TRUNC('month', session_date) AS month,
        COUNT(DISTINCT player_id) AS mau
    FROM sessions
    GROUP BY 1
)
SELECT
    m.month,
    m.mau,
    ROUND(AVG(d.dau), 0)                          AS avg_dau,
    ROUND(AVG(d.dau) / m.mau * 100, 1)           AS stickiness_pct
FROM monthly m
JOIN daily d ON d.month = m.month
GROUP BY m.month, m.mau
ORDER BY m.month;

-- ── 2. COHORT RETENTION ─────────────────────────────────────────
WITH cohorts AS (
    SELECT
        player_id,
        DATE_TRUNC('week', install_date) AS cohort_week
    FROM players
),
activity AS (
    SELECT
        s.player_id,
        c.cohort_week,
        DATEDIFF('day', c.cohort_week, s.session_date) AS days_since_install
    FROM sessions s
    JOIN cohorts c ON s.player_id = c.player_id
)
SELECT
    cohort_week,
    COUNT(DISTINCT player_id)                                               AS cohort_size,
    ROUND(COUNT(DISTINCT CASE WHEN days_since_install = 1  THEN player_id END)
          / COUNT(DISTINCT player_id) * 100, 1)                            AS d1_retention,
    ROUND(COUNT(DISTINCT CASE WHEN days_since_install = 7  THEN player_id END)
          / COUNT(DISTINCT player_id) * 100, 1)                            AS d7_retention,
    ROUND(COUNT(DISTINCT CASE WHEN days_since_install = 14 THEN player_id END)
          / COUNT(DISTINCT player_id) * 100, 1)                            AS d14_retention,
    ROUND(COUNT(DISTINCT CASE WHEN days_since_install = 30 THEN player_id END)
          / COUNT(DISTINCT player_id) * 100, 1)                            AS d30_retention
FROM activity
GROUP BY cohort_week
ORDER BY cohort_week;

-- ── 3. CHURN BY ACQUISITION SOURCE ──────────────────────────────
WITH last_seen AS (
    SELECT player_id, MAX(session_date) AS last_session
    FROM sessions
    GROUP BY player_id
),
player_status AS (
    SELECT
        p.player_id,
        p.acq_source,
        l.last_session,
        CASE WHEN l.last_session < CURRENT_DATE - INTERVAL '7 days'
             THEN 1 ELSE 0 END AS is_churned
    FROM players p
    LEFT JOIN last_seen l ON p.player_id = l.player_id
)
SELECT
    acq_source,
    COUNT(*)                             AS total_players,
    SUM(is_churned)                      AS churned,
    ROUND(AVG(is_churned) * 100, 1)     AS churn_rate_pct
FROM player_status
GROUP BY acq_source
ORDER BY churn_rate_pct ASC;

-- ── 4. REVENUE METRICS ───────────────────────────────────────────
-- ARPU / ARPPU / Conversion
SELECT
    COUNT(DISTINCT p.player_id)                                 AS total_players,
    COUNT(DISTINCT pu.player_id)                                AS paying_players,
    ROUND(COUNT(DISTINCT pu.player_id)::FLOAT
          / COUNT(DISTINCT p.player_id) * 100, 1)              AS conversion_rate_pct,
    ROUND(SUM(pu.price_usd), 2)                                AS total_revenue,
    ROUND(SUM(pu.price_usd) / COUNT(DISTINCT p.player_id), 2) AS arpu,
    ROUND(SUM(pu.price_usd) / COUNT(DISTINCT pu.player_id), 2)AS arppu
FROM players p
LEFT JOIN purchases pu ON p.player_id = pu.player_id;

-- Revenue by item, sorted
SELECT
    item_name,
    item_category,
    COUNT(*)                    AS transactions,
    ROUND(SUM(price_usd), 2)   AS total_revenue,
    ROUND(AVG(price_usd), 2)   AS avg_price
FROM purchases
GROUP BY item_name, item_category
ORDER BY total_revenue DESC;

-- Revenue by country
SELECT
    country,
    COUNT(DISTINCT player_id)   AS paying_players,
    COUNT(*)                    AS transactions,
    ROUND(SUM(price_usd), 2)   AS revenue
FROM purchases
GROUP BY country
ORDER BY revenue DESC
LIMIT 10;

-- Monthly revenue trend
SELECT
    DATE_TRUNC('month', purchase_date) AS month,
    ROUND(SUM(price_usd), 2)           AS revenue,
    COUNT(DISTINCT player_id)          AS unique_payers,
    COUNT(*)                           AS transactions
FROM purchases
GROUP BY 1
ORDER BY 1;

-- ── 5. BATTLE PASS ANALYSIS ──────────────────────────────────────
SELECT
    season,
    COUNT(*)                                AS pass_holders,
    ROUND(AVG(tier_reached), 1)            AS avg_tier_reached,
    ROUND(AVG(tier_reached::FLOAT
          / max_tier * 100), 1)            AS avg_completion_pct,
    ROUND(AVG(missions_completed), 1)      AS avg_missions_done,
    ROUND(SUM(gems_spent), 2)              AS total_revenue
FROM battle_pass
GROUP BY season
ORDER BY season;

-- ── 6. MAP PERFORMANCE ───────────────────────────────────────────
SELECT
    map_name,
    COUNT(*)                               AS total_plays,
    ROUND(AVG(CASE WHEN completed THEN 1.0 ELSE 0 END) * 100, 1) AS completion_rate_pct,
    ROUND(AVG(placement), 1)              AS avg_placement,
    ROUND(AVG(duration_sec), 0)           AS avg_duration_sec,
    ROUND(AVG(coins_earned), 0)           AS avg_coins_earned
FROM matches
GROUP BY map_name
ORDER BY total_plays DESC;

-- ── 7. PLATFORM COMPARISON ───────────────────────────────────────
SELECT
    s.platform,
    COUNT(DISTINCT s.player_id)            AS unique_players,
    COUNT(s.session_id)                    AS total_sessions,
    ROUND(AVG(s.duration_sec) / 60, 1)   AS avg_session_min,
    ROUND(SUM(pu.price_usd), 2)           AS total_revenue,
    ROUND(SUM(pu.price_usd)
          / COUNT(DISTINCT s.player_id), 2) AS arpu
FROM sessions s
LEFT JOIN purchases pu ON s.player_id = pu.player_id
GROUP BY s.platform;
