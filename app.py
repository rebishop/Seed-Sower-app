
import streamlit as st
import pandas as pd
from supabase import create_client

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Sowing and Watering", layout="wide")

# ---------- STYLING ----------
st.markdown("""
<style>

/* App background */
.stApp {
    background: linear-gradient(180deg, #f6f2e9 0%, #e9dfcf 100%);
    color: #2f2a24;
}

/* Faded Bible verse background */
.stApp::before {
    content: "“I have planted, Apollos watered; but God gave the increase.”";
    position: fixed;
    top: 85%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(-8deg);
    font-size: 35px;
    color: rgba(255, 255, 255);
    text-align: center;
    width: 90%;
    z-index: 0;
    pointer-events: none;
    font-family: 'Great Vibes', cursive;
}

/* Keep content above background */
.block-container {
    position: relative;
    z-index: 1;
    padding-top: 2rem;
    max-width: 1100px;
}

/* Headers */
h1, h2, h3 {
    font-family: Georgia, serif;
    color: #3e3428;
}

/* Hero box */
.hero-box {
    background: rgba(255,255,255,0.65);
    border-radius: 18px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(120, 100, 80, 0.15);
    box-shadow: 0 4px 20px rgba(60,40,20,0.06);
}

/* INPUT BOXES */
.stTextInput input,
.stDateInput input,
.stNumberInput input {
    background-color: #fcfaf6 !important;
    border: 1px solid #cdbfae !important;
    border-radius: 10px !important;
    color: rgb(30, 30, 30) !important;
    font-weight: 600 !important;
}

/* Extra fallback for number/date/text values */
input[type="text"],
input[type="number"],
input[type="date"] {
    color: rgb(30, 30, 30) !important;
    -webkit-text-fill-color: rgb(30, 30, 30) !important;
}

/* Focus styling */
.stTextInput input:focus,
.stDateInput input:focus,
.stNumberInput input:focus {
    border: 1px solid #7f8c6b !important;
    box-shadow: 0 0 0 2px rgba(127, 140, 107, 0.2) !important;
    color: rgb(30, 30, 30) !important;
}

/* LABELS */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] label,
label {
    color: rgb(30, 30, 30) !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
}

/* Placeholder text */
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
    min-height: 48px;
}

.stButton button:hover {
    background-color: #6e7b5c;
    color: white;
}

/* Tables */
[data-testid="stDataFrame"] {
    border-radius: 12px;
}

/* Metrics */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.6);
    padding: 10px;
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

# ---------- SUPABASE ----------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- TEAM ----------
TEAM = [
    "Alston", "Bishop", "Blake", "Chandler", "Chris",
    "Dekota", "Eric", "Gage", "Jack", "Jaron",
    "Kobie", "Levi", "Madeline", "Maryia", "Matthew",
    "Nathan", "Patten", "Ryan", "Scott", "Shaun",
    "Ty", "W. Joel"
]

if "selected_user" not in st.session_state:
    st.session_state.selected_user = ""

# ---------- HEADER ----------
st.markdown("""
<div class="hero-box">
    <h1 style="margin-bottom:0.3rem; font-family: 'Great Vibes', cursive;">
        Sowing and Watering
    </h1>

    <p style="margin-top:0; color:#6b5c4d;">
        Daily Faithfulness. Daily Discipline. Daily Stewardship.
    </p>
</div>
""", unsafe_allow_html=True)

# ---------- INPUT SECTION ----------
st.markdown("### Daily Entry")
st.markdown("#### Select Your Name")

grid_cols = st.columns(4)

for i, name in enumerate(TEAM):
    with grid_cols[i % 4]:
        is_selected = st.session_state.selected_user == name
        button_label = f"✓ {name}" if is_selected else name
        if st.button(button_label, key=f"user_{name}", use_container_width=True):
            st.session_state.selected_user = name

user_name = st.session_state.selected_user

if user_name:
    st.success(f"Selected: {user_name}")
else:
    st.info("Please select your name.")

entry_date = st.date_input("Date")

col1, col2, col3 = st.columns(3)

with col1:
    seeds_sown = st.number_input("Seeds Sown (out of 17)", min_value=0, max_value=17, step=1)
    meetings_set = st.number_input("Meetings Set", min_value=0, step=1)

with col2:
    meetings_ran = st.number_input("Meetings Ran", min_value=0, step=1)
    net_new_aum = st.number_input("Net New AUM ($)", min_value=0.0, step=1000.0)

with col3:
    Time_In_Word_Minutes = st.number_input("Time In The Word (minutes)", min_value=0, step=1)

# ---------- SAVE ----------
if st.button("Save Daily Entry"):
    if not user_name:
        st.error("Please select your name before saving.")
    else:
        payload = {
            "user_name": user_name,
            "entry_date": str(entry_date),
            "seeds_sown": int(seeds_sown),
            "meetings_set": int(meetings_set),
            "meetings_ran": int(meetings_ran),
            "net_new_aum": float(net_new_aum),
            "Time_In_Word_Minutes": int(Time_In_Word_Minutes),
        }

        supabase.table("daily_metrics").upsert(payload).execute()
        st.success("Entry saved.")

st.divider()

# ---------- DATA DISPLAY ----------
if user_name:
    result = (
        supabase.table("daily_metrics")
        .select("*")
        .eq("user_name", user_name)
        .order("entry_date", desc=True)
        .limit(1000)
        .execute()
    )

    data = result.data if result.data else []

    if data:
        df = pd.DataFrame(data)
        df["entry_date"] = pd.to_datetime(df["entry_date"])

        st.markdown("### Recent Entries")
        st.dataframe(df.sort_values("entry_date", ascending=False), use_container_width=True)

        total_seeds = int(df["seeds_sown"].sum())
        total_set = int(df["meetings_set"].sum())
        total_ran = int(df["meetings_ran"].sum())
        total_aum = float(df["net_new_aum"].sum())
        total_word = int(df["Time_In_Word_Minutes"].sum()) if "Time_In_Word_Minutes" in df.columns else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Seeds", total_seeds)
        c2.metric("Meetings Set", total_set)
        c3.metric("Meetings Ran", total_ran)
        c4.metric("Net New AUM", f"${total_aum:,.0f}")
        c5.metric("Word Minutes", total_word)

        st.divider()

        # ---------- REPORTS ----------
        st.markdown("### Reports")

        r1, r2 = st.columns(2)

        with r1:
            report_start = st.date_input(
                "Start Date",
                value=df["entry_date"].min().date(),
                key="report_start"
            )
        with r2:
            report_end = st.date_input(
                "End Date",
                value=df["entry_date"].max().date(),
                key="report_end"
            )

        filtered = df[
            (df["entry_date"].dt.date >= report_start) &
            (df["entry_date"].dt.date <= report_end)
        ].copy()

        if not filtered.empty:
            days = filtered["entry_date"].nunique()
            seeds = int(filtered["seeds_sown"].sum())
            set_meetings = int(filtered["meetings_set"].sum())
            ran_meetings = int(filtered["meetings_ran"].sum())
            aum = float(filtered["net_new_aum"].sum())
            word = int(filtered["Time_In_Word_Minutes"].sum()) if "Time_In_Word_Minutes" in filtered.columns else 0

            close_rate = (ran_meetings / set_meetings * 100) if set_meetings > 0 else 0
            avg_seeds = seeds / days if days > 0 else 0

            s1, s2, s3 = st.columns(3)
            s1.metric("Days", days)
            s2.metric("Avg Seeds/Day", f"{avg_seeds:.2f}")
            s3.metric("Close Rate", f"{close_rate:.1f}%")

            summary_df = pd.DataFrame([{
                "User": user_name,
                "Days": days,
                "Seeds": seeds,
                "Meetings Set": set_meetings,
                "Meetings Ran": ran_meetings,
                "Close Rate %": round(close_rate, 1),
                "Net New AUM": round(aum, 2),
                "Time_In_Word_Minutes": word
            }])

            st.dataframe(summary_df, use_container_width=True)

            csv = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Detailed CSV",
                csv,
                "report.csv",
                "text/csv"
            )
        else:
            st.info("No data in selected range.")
    else:
        st.info("No entries yet.")
