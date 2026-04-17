import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

st.set_page_config(page_title="Seed Sower Tracker", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Seed Sower Tracker")

user_name = st.text_input("Your name")
entry_date = st.date_input("Date")

st.subheader("Daily Inputs")

col1, col2, col3 = st.columns(3)

with col1:
    seeds_sown = st.number_input("Seeds Sown", min_value=0, max_value=17, step=1)
    meetings_set = st.number_input("Meetings Set", min_value=0, step=1)

with col2:
    meetings_ran = st.number_input("Meetings Ran", min_value=0, step=1)
    net_new_aum = st.number_input("Net New AUM ($)", min_value=0.0, step=1000.0)

with col3:
    time_in_word_minutes = st.number_input("Time in the Word (minutes)", min_value=0, step=1)

if st.button("Save Daily Entry"):
    payload = {
        "user_name": user_name,
        "entry_date": str(entry_date),
        "seeds_sown": int(seeds_sown),
        "meetings_set": int(meetings_set),
        "meetings_ran": int(meetings_ran),
        "net_new_aum": float(net_new_aum),
        "time_in_word_minutes": int(time_in_word_minutes),
    }

    supabase.table("daily_metrics").upsert(payload).execute()
    st.success("Entry saved.")

st.divider()

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

        st.subheader("Recent Entries")
        st.dataframe(
            df.sort_values("entry_date", ascending=False),
            use_container_width=True
        )

        total_seeds = int(df["seeds_sown"].sum())
        total_set = int(df["meetings_set"].sum())
        total_ran = int(df["meetings_ran"].sum())
        total_aum = float(df["net_new_aum"].sum())
        total_word = int(df["time_in_word_minutes"].sum())

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Seeds", total_seeds)
        c2.metric("Meetings Set", total_set)
        c3.metric("Meetings Ran", total_ran)
        c4.metric("Net New AUM", f"${total_aum:,.0f}")
        c5.metric("Time_In_Word_Minutes", total_word)

        st.divider()
        st.subheader("Reports")

        r1, r2 = st.columns(2)
        with r1:
            report_start = st.date_input("Report Start Date", value=df["entry_date"].min().date(), key="report_start")
        with r2:
            report_end = st.date_input("Report End Date", value=df["entry_date"].max().date(), key="report_end")

        filtered = df[
            (df["entry_date"].dt.date >= report_start) &
            (df["entry_date"].dt.date <= report_end)
        ].copy()

        if not filtered.empty:
            num_days = filtered["entry_date"].nunique()
            total_seeds = int(filtered["seeds_sown"].sum())
            total_set = int(filtered["meetings_set"].sum())
            total_ran = int(filtered["meetings_ran"].sum())
            total_aum = float(filtered["net_new_aum"].sum())
            total_word = int(filtered["time_in_word_minutes"].sum())

            close_rate = (total_ran / total_set * 100) if total_set > 0 else 0
            avg_seeds_per_day = total_seeds / num_days if num_days > 0 else 0

            s1, s2, s3 = st.columns(3)
            s1.metric("Days Reported", num_days)
            s2.metric("Avg Seeds / Day", f"{avg_seeds_per_day:.2f}")
            s3.metric("Meeting Run Rate", f"{close_rate:.1f}%")

            summary_df = pd.DataFrame([{
                "User": user_name,
                "Start Date": report_start,
                "End Date": report_end,
                "Days Reported": num_days,
                "Seeds Sown": total_seeds,
                "Meetings Set": total_set,
                "Meetings Ran": total_ran,
                "Meeting Run Rate %": round(close_rate, 1),
                "Net New AUM": round(total_aum, 2),
                "Time_In_Word_Minutes": total_word
            }])

            st.subheader("Report Summary")
            st.dataframe(summary_df, use_container_width=True)

            csv = filtered.sort_values("entry_date").to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Detailed Report CSV",
                data=csv,
                file_name=f"{user_name}_report_{report_start}_to_{report_end}.csv",
                mime="text/csv"
            )

            summary_csv = summary_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Summary CSV",
                data=summary_csv,
                file_name=f"{user_name}_summary_{report_start}_to_{report_end}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data in that date range.")
    else:
        st.info("No entries yet for this user.")
