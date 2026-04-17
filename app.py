import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, timedelta

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Sowing and Watering", layout="wide")

# ---------- STYLING ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #f6f2e9 0%, #e9dfcf 100%);
    color: #2f2a24;
}

.stApp::before {
    content: "“I have planted, Apollos watered; but God gave the increase.”";
    position: fixed;
    top: 94%;
    left: 50%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(-12deg);
    font-size: 64px;
    color: rgba(0, 0, 0, 0.05);
    text-align: center;
    width: 90%;
    z-index: 0;
    pointer-events: none;
    font-family: Georgia, serif;
}

.block-container {
    position: relative;
    z-index: 1;
    padding-top: 2rem;
    max-width: 1180px;
}

/* Header */
h1, h2, h3 {
    font-family: Georgia, serif;
    color: #3e3428;
}

.hero-box {
    background: rgba(255,255,255,0.68);
    border-radius: 18px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(120, 100, 80, 0.15);
    box-shadow: 0 4px 20px rgba(60,40,20,0.06);
}

/* Inputs */
.stTextInput input,
.stDateInput input,
.stNumberInput input {
    background-color: #fcfaf6 !important;
    border: 1px solid #cdbfae !important;
    border-radius: 10px !important;
    color: rgb(30, 30, 30) !important;
    font-weight: 600 !important;
}

input[type="text"],
input[type="number"],
input[type="date"] {
    color: rgb(30, 30, 30) !important;
    -webkit-text-fill-color: rgb(30, 30, 30) !important;
}

.stTextInput input:focus,
.stDateInput input:focus,
.stNumberInput input:focus {
    border: 1px solid #7f8c6b !important;
    box-shadow: 0 0 0 2px rgba(127, 140, 107, 0.2) !important;
    color: rgb(30, 30, 30) !important;
}

[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] label,
label {
    color: rgb(30, 30, 30) !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
}

input::placeholder {
    color: rgb(120, 110, 95) !important;
    opacity: 1 !important;
}

/* Buttons */
.stButton button {
    background-color: #7f8c6b;
    color: white;
    border-radius: 10px;
    font-weight: 600;
    border: none;
}

.stButton button:hover {
    background-color: #6e7b5c;
    color: white;
}

/* Metrics */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.60);
    padding: 12px;
    border-radius: 12px;
}

/* Tables */
[data-testid="stDataFrame"] {
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ---------- SUPABASE ----------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "daily_metrics"

TEAM = [
    "Alston","Bishop","Blake","Chandler","Chris",
    "Dekota","Eric","Gage","Jack","Jaron",
    "Kobie","Levi","Madeline","Maryia","Matthew",
    "Nathan","Patten","Ryan","Scott","Shaun",
    "Ty","W. Joel"
]

# ---------- HELPERS ----------
def safe_int(value):
    if value is None:
        return 0
    return int(value)

def safe_float(value):
    if value is None:
        return 0.0
    return float(value)

def fmt_aum(n):
    n = safe_float(n)
    if n == 0:
        return "$0"
    if n >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"${n/1_000:.0f}K"
    return f"${n:,.0f}"

def seed_status(n):
    n = safe_int(n)
    if n >= 17:
        return "WIN"
    if n >= 10:
        return "WARNING"
    if n > 0:
        return "BELOW STANDARD"
    return "NO POST"

def period_start(period):
    today = date.today()
    if period == "today":
        return today
    if period == "week":
        return today - timedelta(days=today.weekday())
    return None  # alltime

def fetch_entries():
    result = (
        supabase.table(TABLE_NAME)
        .select("*")
        .order("entry_date", desc=True)
        .limit(5000)
        .execute()
    )
    data = result.data if result.data else []
    df = pd.DataFrame(data)

    if df.empty:
        return df

    if "entry_date" in df.columns:
        df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date

    # Ensure expected columns exist
    expected_defaults = {
        "user_name": "",
        "seeds_sown": 0,
        "convos": 0,
        "meetings_set": 0,
        "meetings_ran": 0,
        "net_new_aum": 0.0,
        "Time_In_Word_Minutes": 0
    }

    for col, default in expected_defaults.items():
        if col not in df.columns:
            df[col] = default

    return df

def filter_by_period(df, period):
    if df.empty:
        return df
    start = period_start(period)
    if start is None:
        return df.copy()
    return df[df["entry_date"] >= start].copy()

def latest_per_person(df):
    if df.empty:
        return df
    temp = df.sort_values(["entry_date"], ascending=[False]).copy()
    latest = temp.groupby("user_name", as_index=False).first()
    return latest

def build_scoreboard_df(df):
    if df.empty:
        return pd.DataFrame(columns=[
            "Rank", "Name", "Seeds", "Status", "Convos",
            "Meetings Set", "Meetings Ran", "AUM", "Word Minutes"
        ])

    board = latest_per_person(df).copy()
    board["Seeds"] = board["seeds_sown"].fillna(0).astype(int)
    board["Convos"] = board["convos"].fillna(0).astype(int)
    board["Meetings Set"] = board["meetings_set"].fillna(0).astype(int)
    board["Meetings Ran"] = board["meetings_ran"].fillna(0).astype(int)
    board["AUM Raw"] = board["net_new_aum"].fillna(0.0).astype(float)
    board["Word Minutes"] = board["Time_In_Word_Minutes"].fillna(0).astype(int)
    board["Status"] = board["Seeds"].apply(seed_status)

    board = board.sort_values(["Seeds", "Meetings Set", "AUM Raw"], ascending=[False, False, False]).reset_index(drop=True)

    ranks = []
    for i in range(len(board)):
        if i == 0:
            ranks.append("🥇")
        elif i == 1:
            ranks.append("🥈")
        elif i == 2:
            ranks.append("🥉")
        else:
            ranks.append(f"{i+1}")
    board["Rank"] = ranks

    board["AUM"] = board["AUM Raw"].apply(fmt_aum)
    board["Name"] = board["user_name"]

    return board[[
        "Rank", "Name", "Seeds", "Status", "Convos",
        "Meetings Set", "Meetings Ran", "AUM", "Word Minutes"
    ]]

# ---------- HEADER ----------
st.markdown("""
<div class="hero-box">
    <h1 style="margin-bottom:0.3rem;">Sowing and Watering</h1>
    <p style="margin-top:0; color:#6b5c4d;">
        Daily faithfulness. Daily discipline. Daily stewardship.
    </p>
</div>
""", unsafe_allow_html=True)

# ---------- LOAD DATA ----------
df_all = fetch_entries()

# ---------- TABS ----------
tab1, tab2, tab3, tab4 = st.tabs(["Daily Entry", "Scoreboard", "Leader View", "Reports"])

# ---------- TAB 1: DAILY ENTRY ----------
with tab1:
    st.markdown("### Post Today’s Activity")

    user_name = st.text_input("Your name")
    entry_date = st.date_input("Date", value=date.today())

    c1, c2, c3 = st.columns(3)

    with c1:
        seeds_sown = st.number_input("Seeds Sown (out of 17)", min_value=0, max_value=17, step=1)
        convos = st.number_input("Conversations", min_value=0, step=1)
        meetings_set = st.number_input("Meetings Set", min_value=0, step=1)

    with c2:
        meetings_ran = st.number_input("Meetings Ran", min_value=0, step=1)
        net_new_aum = st.number_input("Net New AUM ($)", min_value=0.0, step=1000.0)
        Time_In_Word_Minutes = st.number_input("Time in the Word (minutes)", min_value=0, step=1)

    with c3:
        st.metric("Daily Seed Goal", f"{safe_int(seeds_sown)}/17")
        st.progress(min(safe_int(seeds_sown) / 17, 1.0))
        st.metric("Status", seed_status(seeds_sown))

    if st.button("Save Daily Entry"):
        if not user_name.strip():
            st.error("Please enter your name.")
        else:
            payload = {
                "user_name": user_name.strip(),
                "entry_date": str(entry_date),
                "seeds_sown": int(seeds_sown),
                "convos": int(convos),
                "meetings_set": int(meetings_set),
                "meetings_ran": int(meetings_ran),
                "net_new_aum": float(net_new_aum),
                "Time_In_Word_Minutes": int(Time_In_Word_Minutes),
            }

            supabase.table(TABLE_NAME).upsert(payload).execute()
            st.success("Entry saved. Refreshing...")
            st.rerun()

    st.divider()

    if user_name and not df_all.empty:
        user_df = df_all[df_all["user_name"] == user_name].copy()
        if not user_df.empty:
            st.markdown("### Your Recent Entries")
            display_cols = [
                "entry_date", "seeds_sown", "convos", "meetings_set",
                "meetings_ran", "net_new_aum", "Time_In_Word_Minutes"
            ]
            st.dataframe(
                user_df.sort_values("entry_date", ascending=False)[display_cols],
                use_container_width=True
            )
        else:
            st.info("No entries yet for this user.")

# ---------- TAB 2: SCOREBOARD ----------
with tab2:
    st.markdown("### Scoreboard")

    period = st.radio(
        "Period",
        options=["today", "week", "alltime"],
        horizontal=True,
        key="scoreboard_period"
    )

    period_df = filter_by_period(df_all, period)
    board_df = build_scoreboard_df(period_df)

    total_seeds = safe_int(period_df["seeds_sown"].sum()) if not period_df.empty else 0
    total_mset = safe_int(period_df["meetings_set"].sum()) if not period_df.empty else 0
    total_aum = safe_float(period_df["net_new_aum"].sum()) if not period_df.empty else 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("Seeds", total_seeds)
    m2.metric("Meetings Set", total_mset)
    m3.metric("AUM", fmt_aum(total_aum))

    if board_df.empty:
        st.info("No scores posted for this period.")
    else:
        st.dataframe(board_df, use_container_width=True)

# ---------- TAB 3: LEADER VIEW ----------
with tab3:
    st.markdown("### Leader View")

    leader_period = st.radio(
        "Period",
        options=["today", "week", "alltime"],
        horizontal=True,
        key="leader_period"
    )

    leader_df = filter_by_period(df_all, leader_period)
    latest_df = latest_per_person(leader_df)

    if latest_df.empty:
        st.info("No data for this period.")
    else:
        latest_df["Seeds"] = latest_df["seeds_sown"].fillna(0).astype(int)
        latest_df["Convos"] = latest_df["convos"].fillna(0).astype(int)
        latest_df["Meetings Set"] = latest_df["meetings_set"].fillna(0).astype(int)
        latest_df["Meetings Ran"] = latest_df["meetings_ran"].fillna(0).astype(int)
        latest_df["Word Minutes"] = latest_df["Time_In_Word_Minutes"].fillna(0).astype(int)
        latest_df["AUM"] = latest_df["net_new_aum"].fillna(0.0).apply(fmt_aum)
        latest_df["Status"] = latest_df["Seeds"].apply(seed_status)
        latest_df["Name"] = latest_df["user_name"]

        display = latest_df[[
            "Name", "Seeds", "Convos", "Meetings Set",
            "Meetings Ran", "AUM", "Word Minutes", "Status"
        ]].sort_values(["Seeds", "Meetings Set"], ascending=[False, False])

        posted_names = set(display["Name"].tolist())
        not_posted = [n for n in TEAM if n not in posted_names]

        st.dataframe(display, use_container_width=True)

        st.markdown(f"**Posted:** {len(posted_names)}/{len(TEAM)}")

        if not_posted:
            st.markdown("**No Post:** " + ", ".join(not_posted))

# ---------- TAB 4: REPORTS ----------
with tab4:
    st.markdown("### Reports")

    if df_all.empty:
        st.info("No data available yet.")
    else:
        users = sorted([u for u in df_all["user_name"].dropna().unique().tolist() if u])
        selected_user = st.selectbox("User", options=users)

        user_df = df_all[df_all["user_name"] == selected_user].copy()

        if user_df.empty:
            st.info("No data for that user.")
        else:
            r1, r2 = st.columns(2)

            with r1:
                report_start = st.date_input(
                    "Start Date",
                    value=min(user_df["entry_date"]),
                    key="report_start"
                )
            with r2:
                report_end = st.date_input(
                    "End Date",
                    value=max(user_df["entry_date"]),
                    key="report_end"
                )

            filtered = user_df[
                (user_df["entry_date"] >= report_start) &
                (user_df["entry_date"] <= report_end)
            ].copy()

            if filtered.empty:
                st.info("No data in selected range.")
            else:
                days = filtered["entry_date"].nunique()
                seeds = safe_int(filtered["seeds_sown"].sum())
                convos_total = safe_int(filtered["convos"].sum())
                set_meetings = safe_int(filtered["meetings_set"].sum())
                ran_meetings = safe_int(filtered["meetings_ran"].sum())
                aum = safe_float(filtered["net_new_aum"].sum())
                word = safe_int(filtered["Time_In_Word_Minutes"].sum())

                close_rate = (ran_meetings / set_meetings * 100) if set_meetings > 0 else 0
                avg_seeds = (seeds / days) if days > 0 else 0

                x1, x2, x3, x4 = st.columns(4)
                x1.metric("Days", days)
                x2.metric("Seeds", seeds)
                x3.metric("Avg Seeds/Day", f"{avg_seeds:.2f}")
                x4.metric("Close Rate", f"{close_rate:.1f}%")

                summary_df = pd.DataFrame([{
                    "User": selected_user,
                    "Start Date": report_start,
                    "End Date": report_end,
                    "Days": days,
                    "Seeds": seeds,
                    "Conversations": convos_total,
                    "Meetings Set": set_meetings,
                    "Meetings Ran": ran_meetings,
                    "Close Rate %": round(close_rate, 1),
                    "Net New AUM": round(aum, 2),
                    "Time_In_Word_Minutes": word
                }])

                st.dataframe(summary_df, use_container_width=True)

                detail_cols = [
                    "entry_date", "seeds_sown", "convos", "meetings_set",
                    "meetings_ran", "net_new_aum", "Time_In_Word_Minutes"
                ]
                st.dataframe(
                    filtered.sort_values("entry_date", ascending=False)[detail_cols],
                    use_container_width=True
                )

                csv = filtered.sort_values("entry_date").to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Detailed CSV",
                    csv,
                    f"{selected_user}_report.csv",
                    "text/csv"
                )
