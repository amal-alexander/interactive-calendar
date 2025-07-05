import streamlit as st
from datetime import date, timedelta
from tinydb import TinyDB, Query
import hashlib
import os
import pandas as pd
from streamlit_calendar import calendar

# ---------------------------
# Streamlit page setup
# ---------------------------
st.set_page_config(page_title="📅 Interactive Content Calendar", layout="centered")

# ---------------------------
# Database setup
# ---------------------------
if not os.path.exists("db"):
    os.mkdir("db")
db = TinyDB("db/calendar_db.json")

# ---------------------------
# User identification
# ---------------------------
def get_user_id():
    ip = st.session_state.get("ip", "127.0.0.1")
    ua = st.session_state.get("ua", "streamlit")
    return hashlib.sha256(f"{ip}_{ua}".encode()).hexdigest()

if "ip" not in st.session_state:
    st.session_state["ip"] = "127.0.0.1"
if "ua" not in st.session_state:
    st.session_state["ua"] = "streamlit"

user_id = get_user_id()

st.title("📅 Interactive Content Calendar")

# ---------------------------
# Example ideas
# ---------------------------
with st.expander("💡 Sample Content Ideas"):
    st.markdown("""
    - Blog Post  
    - YouTube Video  
    - Email Newsletter  
    - LinkedIn Post  
    - Instagram Story  
    """)

# ---------------------------
# Session state for edit mode
# ---------------------------
if "edit_mode" not in st.session_state:
    st.session_state["edit_mode"] = False
if "edit_id" not in st.session_state:
    st.session_state["edit_id"] = None

# ---------------------------
# Add / Edit Form
# ---------------------------
with st.form("content_form"):
    if st.session_state["edit_mode"]:
        st.subheader("✏️ Edit Content")
        title = st.text_input("Title", value=st.session_state["edit_title"])
        content_type = st.text_input("Content Type", value=st.session_state["edit_type"])
        scheduled_date = st.date_input("Start Date", value=st.session_state["edit_start"])
        num_days = st.number_input("Number of Days", min_value=1, max_value=30, value=st.session_state["edit_days"])
    else:
        st.subheader("➕ Add New Content")
        title = st.text_input("Title")
        content_type = st.text_input("Content Type")
        scheduled_date = st.date_input("Start Date", value=date.today())
        num_days = st.number_input("Number of Days", min_value=1, max_value=30, value=1)

    submitted = st.form_submit_button("Save")

# ---------------------------
# Save / Update Logic
# ---------------------------
if submitted and title and content_type:
    end_date = scheduled_date + timedelta(days=num_days - 1)
    if st.session_state["edit_mode"]:
        db.update(
            {
                "title": title,
                "type": content_type,
                "start_date": scheduled_date.isoformat(),
                "end_date": end_date.isoformat(),
                "num_days": num_days
            },
            doc_ids=[st.session_state["edit_id"]]
        )
        st.success("✅ Updated successfully!")
        st.session_state["edit_mode"] = False
        st.session_state["edit_id"] = None
    else:
        db.insert({
            "user_id": user_id,
            "title": title,
            "type": content_type,
            "start_date": scheduled_date.isoformat(),
            "end_date": end_date.isoformat(),
            "num_days": num_days
        })
        st.success("✅ Added to your calendar!")

    st.rerun()

# ---------------------------
# Load Data
# ---------------------------
User = Query()
entries = db.search(User.user_id == user_id)

if entries:
    st.subheader("📆 Your Content Cards")

    df = pd.DataFrame(entries)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    df = df.sort_values("start_date")

    for row in df.itertuples():
        st.markdown(f"""
        <div style='
            background:#f0f4f8;
            padding:10px;
            border-left:6px solid #4f8bf9;
            margin:10px 0;
            border-radius:5px;
            word-wrap: break-word;
            overflow-wrap: break-word;
            white-space: pre-wrap;
            max-width: 600px;
        '>
        <strong>{row.type}:</strong> {row.title}<br>
        📅 {row.start_date.strftime("%A, %B %d, %Y")} to {row.end_date.strftime("%A, %B %d, %Y")} ({row.num_days} days)
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(2)
        with cols[0]:
            if st.button(f"✏️ Edit", key=f"edit_{row.Index}"):
                st.session_state["edit_mode"] = True
                st.session_state["edit_id"] = entries[row.Index].doc_id
                st.session_state["edit_title"] = row.title
                st.session_state["edit_type"] = row.type
                st.session_state["edit_start"] = row.start_date.date()
                st.session_state["edit_days"] = row.num_days
                st.rerun()
        with cols[1]:
            if st.button(f"🗑️ Delete", key=f"delete_{row.Index}"):
                db.remove(doc_ids=[entries[row.Index].doc_id])
                st.success(f"✅ Deleted: {row.title}")
                st.rerun()

    # ---------------------------
    # Inject CSS for event bubbles to wrap long titles
    # ---------------------------
    st.markdown("""
        <style>
        .fc-event-title {
            white-space: normal !important;
        }
        .fc-daygrid-event {
            height: auto !important;
        }
        .fc-event {
            white-space: normal !important;
            overflow: visible !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # ---------------------------
    # Calendar Grid View
    # ---------------------------
    st.subheader("📅 Monthly Calendar View")

    events = [
        {
            "title": f"{row['type']}: {row['title']}",
            "start": row['start_date'].strftime("%Y-%m-%d"),
            "end": (row['end_date'] + timedelta(days=1)).strftime("%Y-%m-%d")  # end is exclusive
        }
        for _, row in df.iterrows()
    ]

    calendar(
        events,
        options={
            "initialView": "dayGridMonth",
            "editable": False,
            "eventDisplay": "block"
        }
    )

    # ---------------------------
    # CSV Download
    # ---------------------------
    st.download_button("⬇️ Download CSV", df.to_csv(index=False), "calendar.csv", "text/csv")

else:
    st.info("No content yet. Use the form above to get started!")
