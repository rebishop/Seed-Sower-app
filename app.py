import os
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
from supabase import Client, create_client

st.set_page_config(page_title="Seed Sower Tracker", page_icon="🌱", layout="wide")

SEEDS_PER_DAY = 17


def get_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
    if not url or not key:
        st.error(
            "Missing Supabase credentials. Add SUPABASE_URL and SUPABASE_KEY to Streamlit secrets."
        )
        st.stop()
    return create_client(url, key)


@st.cache_resource
def init_client() -> Client:
    return get_supabase()


sb = init_client()


# --- Helpers ---
def fetch_entries(user_name: str, start_date: date | None = None, end_date: date | None = None) -> pd.DataFrame:
    query = sb.table("daily_metrics").select("*").eq("user_name", user_name).order("entry_date")
    if start_date:
        query = query.gte("entry_date", start_date.isoformat())
    if end_date:
        query = query.lte("entry_date", end_date.isoformat())
    response = query.execute()
    rows = response.data or []
    if not rows:
        return pd.DataFrame(
            columns=[
                "entry_date",
                "seeds_sown",
                "meetings_set",
                "meetings_ran",
                "net_new_aum",
                "time_in_word_minutes",
                "notes",
            ]
        )
    df = pd.DataFrame(rows)
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    for col in ["seeds_sown", "meetings_set", "meetings_ran", "net_new_aum", "time_in_word_minutes"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def fetch_single_entry(user_name: str, selected_date: date):
    response = (
        sb.table("daily_metrics")
        .select("*")
        .eq("user_name", user_name)
        .eq("entry_date", selected_date.isoformat())
        .limit(1)
        .execute()
    )
    return (response.data or [None])[0]



def save_entry(payload: dict):
    sb.table("daily_metrics").upsert(payload, on_conflict="user_name,entry_date").execute()



def format_currency(value: float) -> str:
    return f"${value:,.0f}"


# --- Header ---
st.title("🌱 Seed Sower Tracker")
st.caption("Track daily seeds sown out of 17, meetings, net new AUM, and time in the Word.")

with st.sidebar:
    st.header("Profile")
    user_name = st.text_input("User name", value="Eric")
    selected_date = st.date_input("Entry date", value=date.today())
    st.divider()
    st.markdown("**Goal**")
    st.write(f"{SEEDS_PER_DAY} seeds per day")

existing = fetch_single_entry(user_name, selected_date)

# --- Input form ---
with st.form("daily_entry"):
    st.subheader("Daily Entry")

    c1, c2, c3 = st.columns(3)
    with c1:
        seeds_sown = st.number_input(
            "Seeds sown",
            min_value=0,
            max_value=SEEDS_PER_DAY,
            value=int(existing["seeds_sown"]) if existing else 0,
            step=1,
            help="Main daily score out of 17.",
        )
    with c2:
        meetings_set = st.number_input(
            "Meetings set",
            min_value=0,
            value=int(existing["meetings_set"]) if existing else 0,
            step=1,
        )
    with c3:
        meetings_ran = st.number_input(
            "Meetings ran",
            min_value=0,
            value=int(existing["meetings_ran"]) if existing else 0,
            step=1,
        )

    c4, c5 = st.columns(2)
    with c4:
        net_new_aum = st.number_input(
            "Net new AUM ($)",
            min_value=0.0,
            value=float(existing["net_new_aum"]) if existing else 0.0,
            step=1000.0,
            format="%.2f",
        )
    with c5:
        time_in_word_minutes = st.number_input(
            "Time in the Word (minutes)",
            min_value=0,
            value=int(existing["time_in_word_minutes"]) if existing else 0,
            step=5,
        )

    notes = st.text_area("Notes", value=existing["notes"] if existing and existing.get("notes") else "")

    submitted = st.form_submit_button("Save entry", use_container_width=True)

if submitted:
    save_entry(
        {
            "user_name": user_name,
            "entry_date": selected_date.isoformat(),
            "seeds_sown": int(seeds_sown),
            "meetings_set": int(meetings_set),
            "meetings_ran": int(meetings_ran),
            "net_new_aum": float(net_new_aum),
            "time_in_word_minutes": int(time_in_word_minutes),
            "notes": notes,
            "updated_at": datetime.utcnow().isoformat(),
        }
    )
    st.success("Entry saved.")
    st.rerun()

# --- Today section ---
progress = seeds_sown / SEEDS_PER_DAY if SEEDS_PER_DAY else 0
st.subheader("Today")
st.progress(progress, text=f"{seeds_sown} / {SEEDS_PER_DAY} seeds sown")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Seeds", f"{seeds_sown}/{SEEDS_PER_DAY}")
m2.metric("Meetings Set", meetings_set)
m3.metric("Meetings Ran", meetings_ran)
m4.metric("Net New AUM", format_currency(net_new_aum))
m5.metric("Word Time", f"{time_in_word_minutes} min")

# --- Analytics ---
start_30 = date.today() - timedelta(days=29)
df = fetch_entries(user_name, start_30, date.today())

st.subheader("Last 30 Days")
if df.empty:
    st.info("No data yet. Save your first entry to populate the dashboard.")
else:
    df = df.sort_values("entry_date")
    df["seed_goal_pct"] = (df["seeds_sown"] / SEEDS_PER_DAY) * 100

    last_7 = df[df["entry_date"].dt.date >= date.today() - timedelta(days=6)]
    month_to_date = df[df["entry_date"].dt.month == date.today().month]

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("7-Day Seeds", int(last_7["seeds_sown"].sum()))
    k2.metric("7-Day Meetings Set", int(last_7["meetings_set"].sum()))
    k3.metric("7-Day Meetings Ran", int(last_7["meetings_ran"].sum()))
    k4.metric("MTD Net New AUM", format_currency(month_to_date["net_new_aum"].sum()))
    k5.metric("MTD Word Time", f"{int(month_to_date['time_in_word_minutes'].sum())} min")

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.markdown("**Seeds Sown**")
        seeds_chart = df.set_index("entry_date")[["seeds_sown"]]
        st.line_chart(seeds_chart)

    with chart_cols[1]:
        st.markdown("**Meetings & Word Time**")
        mix_chart = df.set_index("entry_date")[["meetings_set", "meetings_ran", "time_in_word_minutes"]]
        st.line_chart(mix_chart)

    st.markdown("**Daily Log**")
    display_df = df[[
        "entry_date",
        "seeds_sown",
        "meetings_set",
        "meetings_ran",
        "net_new_aum",
        "time_in_word_minutes",
        "notes",
    ]].copy()
    display_df["entry_date"] = display_df["entry_date"].dt.strftime("%Y-%m-%d")
    display_df = display_df.rename(
        columns={
            "entry_date": "Date",
            "seeds_sown": "Seeds",
            "meetings_set": "Meetings Set",
            "meetings_ran": "Meetings Ran",
            "net_new_aum": "Net New AUM",
            "time_in_word_minutes": "Word Time (min)",
            "notes": "Notes",
        }
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()
st.caption("Built with Streamlit + Supabase")
