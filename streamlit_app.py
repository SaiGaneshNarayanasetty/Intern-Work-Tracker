from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import streamlit as st

from utils import (
    append_update_to_sheet,
    df_from_sheet,
    load_service_account_credentials,
    parse_sheet_dataframe,
)

st.set_page_config(
    page_title="Intern Work Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_TITLE = "Intern Work Tracker"

# Extensive UI Redesign using custom CSS
st.markdown(
    """
<style>
/* Font import */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    color: #333333; /* Darker grey for overall text for better readability */
}

/* Background Gradient for the main app */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #e0f7fa, #ede7f6); /* Pastel blue to light lavender */
    position: relative;
    /* Removed overflow: hidden; to allow scrolling */
}

/* Optional: Subtle radial gradient for depth */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 80% 20%, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 50%);
    pointer-events: none;
}

/* Sidebar background */
[data-testid="stSidebar"] {
    background-color: rgba(255, 255, 255, 0.85); /* Semi-transparent white */
    border-right: 1px solid rgba(0,0,0,0.05);
}

/* Reduce sidebar width */
[data-testid="stSidebar"] > div:first-child {
    max-width: 250px; /* Slightly wider sidebar */
    min-width: 180px;
    width: 220px;
}

/* Card-style containers for sections */
.stContainer, .stForm, [data-testid="stVerticalBlock"] > div:has(h3) {
    background-color: rgba(255, 255, 255, 0.95); /* Nearly white, slightly transparent */
    border-radius: 16px; /* More rounded corners */
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08); /* Soft shadow */
    padding: 30px; /* Increased padding for spaciousness */
    margin-bottom: 25px; /* Spacing between cards */
    transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
}

.stContainer:hover, .stForm:hover, [data-testid="stVerticalBlock"] > div:has(h3):hover {
    transform: translateY(-5px); /* Slight lift on hover */
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

/* Center and widen the form (already done, just ensuring styles apply) */
.stForm {
    width: 100%;
    max-width: 850px; /* Max width for forms */
    margin: 30px auto; /* Center alignment with top/bottom margin */
    padding: 35px; /* More padding */
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    color: #06B6D4; /* Primary accent color for headings */
    font-weight: 600; /* Semi-bold for headings */
    margin-bottom: 15px;
}
h1 { font-size: 2.8em; margin-bottom: 30px;}
h3 { font-size: 1.6em; margin-bottom: 20px;}
h4 { font-size: 1.3em; margin-bottom: 15px;}

/* Buttons - Gradient and hover effects */
div.stButton > button {
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.3s ease-in-out;
    border: none;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

div.stButton > button:first-child:not([kind="primary"]):not([kind="secondary"]) {
    background-image: linear-gradient(45deg, #00BFA6, #06B6D4); /* Teal to Cyan */
    color: white;
}

div.stButton > button:first-child:not([kind="primary"]):not([kind="secondary"]):hover {
    background-image: linear-gradient(45deg, #06B6D4, #00BFA6);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15), 0 0 15px rgba(6, 182, 212, 0.6); /* Glow effect */
}

/* Primary buttons (used for selected date and submit) */
.stButton button[kind="primary"] {
    background-image: linear-gradient(45deg, #007BFF, #6A5ACD) !important; /* Blue to Slate Blue */
    color: white !important;
    font-weight: bold;
    border: none;
    transition: all 0.3s ease-in-out;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.stButton button[kind="primary"]:hover {
    background-image: linear-gradient(45deg, #6A5ACD, #007BFF) !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15), 0 0 15px rgba(0, 123, 255, 0.6); /* Glow effect */
}

/* Secondary buttons (calendar days) */
.stButton button[kind="secondary"] {
    background-color: #F0F2F6; /* Light gray */
    color: #333333;
    border: 1px solid #D1D9E6;
}

.stButton button[kind="secondary"]:hover {
    background-color: #E0E2E6;
    border-color: #C1C9D6;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}

/* Input fields - soft border, inner shadow, focus glow */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stDateInput > div > div > input,
.stSelectbox > div > div > div > input {
    border: 1px solid #D1D9E6;
    border-radius: 8px;
    padding: 10px 15px;
    box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.05); /* Inner shadow */
    transition: all 0.2s ease-in-out;
    background-color: #FFFFFF;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stDateInput > div > div > input:focus,
.stSelectbox > div > div > div > input:focus {
    border-color: #8B5CF6; /* Purple accent on focus */
    box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.08), 0 0 0 3px rgba(139, 92, 246, 0.2); /* Focus glow */
    outline: none;
}

/* Calendar Day Buttons (specifically for the day numbers) */
[data-testid^="stColumn"] > div > .stButton > button {
    width: 100%; /* Make buttons fill the column */
    height: 45px; /* Fixed height for consistent look */
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 25px; /* Pill shape for dates */
    font-size: 1.1em;
    font-weight: 500;
}

/* Selected date glowing pulse animation */
.stButton button[kind="primary"] {
    animation: pulse 1.5s infinite alternate;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.7); }
    100% { box-shadow: 0 0 0 10px rgba(0, 123, 255, 0); }
}

/* Expanders (for results) fade-in */
[data-testid="stExpander"] {
    opacity: 0;
    animation: fadeIn 0.5s forwards;
    animation-delay: 0.2s; /* Delay for a smoother reveal */
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Adjust markdown elements within expanders for better spacing */
.stExpander div[data-testid="stMarkdownContainer"] {
    padding-top: 5px;
    padding-bottom: 5px;
}

/* Metrics styling */
[data-testid="stMetric"] > div {
    background-color: rgba(255, 255, 255, 0.95);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    transition: transform 0.3s ease;
}
[data-testid="stMetric"] > div:hover {
    transform: translateY(-3px);
}
[data-testid="stMetricValue"] {
    color: #8B5CF6; /* Accent color for metric values */
    font-size: 2em;
    font-weight: 700;
}
[data-testid="stMetricLabel"] {
    color: #555555;
    font-weight: 500;
}

</style>
""",
    unsafe_allow_html=True,
)


@dataclass
class FilterScope:
    kind: str
    start_date: date
    end_date: date


def week_range_for(d: date) -> Tuple[date, date]:
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end


def month_range_for(year: int, month: int) -> Tuple[date, date]:
    first = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = date(year, month, last_day)
    return first, last


def fmt_date(d: date) -> str:
    return d.isoformat()


@st.cache_data(ttl=10)
def load_sheet_dataframe(sheet_id: str, creds: Dict[str, Any]) -> pd.DataFrame:
    raw = df_from_sheet(sheet_id=sheet_id, credentials=creds)
    return parse_sheet_dataframe(raw)


def main() -> None:
    st.title(APP_TITLE)

    sheet_id = st.secrets.get("SHEET_ID") if "SHEET_ID" in st.secrets else None

    creds = None
    try:
        creds = load_service_account_credentials()
    except Exception as exc:
        st.error("Credentials problem: " + str(exc))

    left_col, right_col = st.columns([1.3, 2])

    df: Optional[pd.DataFrame]
    if sheet_id and creds:
        try:
            df = load_sheet_dataframe(sheet_id=sheet_id, creds=creds)
        except Exception as exc:
            st.exception(exc)
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(
            columns=[
                "date",
                "intern_name",
                "role",
                "update_text",
                "tags",
                "created_at",
                "created_by",
            ]
        )

    today = date.today()
    if "view_year" not in st.session_state:
        st.session_state.view_year = today.year
    if "view_month" not in st.session_state:
        st.session_state.view_month = today.month
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = today

    with left_col:
        # Calendar Section
        st.markdown("### Calendar")
        cal_controls = st.columns([1, 1, 2])
        if cal_controls[0].button("Previous"):
            y, m = st.session_state.view_year, st.session_state.view_month
            if m == 1:
                st.session_state.view_year = y - 1
                st.session_state.view_month = 12
            else:
                st.session_state.view_month = m - 1
            st.rerun()
        if cal_controls[1].button("Next"):
            y, m = st.session_state.view_year, st.session_state.view_month
            if m == 12:
                st.session_state.view_year = y + 1
                st.session_state.view_month = 1
            else:
                st.session_state.view_month = m + 1
            st.rerun()
        cal_controls[2].button("Today", key="cal_today_button", on_click=lambda: _set_to_today())

        st.markdown(f"#### {calendar.month_name[st.session_state.view_month]} {st.session_state.view_year}")

        counts_by_date: Dict[str, int] = {}
        try:
            if not df.empty:
                counts = df.groupby("date").size()
                counts_by_date = counts.to_dict()
        except Exception:
            counts_by_date = {}

        month_cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)

        # Days of the week header
        week_day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        week_cols = st.columns(7)
        for i, day_name in enumerate(week_day_names):
            week_cols[i].markdown(f"<p style='text-align: center; font-weight: 600; color: #555;'>{day_name}</p>", unsafe_allow_html=True)


        for week in month_cal:
            cols = st.columns(7)
            for i, daynum in enumerate(week):
                if daynum == 0:
                    cols[i].markdown("&nbsp;")
                    continue
                cell_date = date(st.session_state.view_year, st.session_state.view_month, daynum)
                badge = ""
                if fmt_date(cell_date) in counts_by_date:
                    badge = f" ({counts_by_date[fmt_date(cell_date)]})"
                
                button_type = "primary" if cell_date == st.session_state.selected_date else "secondary"
                
                if cols[i].button(f"{daynum}{badge}", key=f"cal_day_{cell_date.isoformat()}", type=button_type):
                    st.session_state.selected_date = cell_date
                    st.rerun()

    with right_col:
        # Controls Section
        st.markdown("### Controls")

        search_col1, search_col2, search_col3 = st.columns([2, 1, 1])
        search_query = search_col1.text_input("Search intern name (partial)", value="")
        scope_kind = search_col2.selectbox("Scope", options=["Month", "Week", "Day"], index=0)
        scope_date = search_col3.date_input("Reference date", value=st.session_state.selected_date)

        if scope_kind.lower() == "day":
            scope = FilterScope("day", scope_date, scope_date)
        elif scope_kind.lower() == "week":
            start, end = week_range_for(scope_date)
            scope = FilterScope("week", start, end)
        else:
            start, end = month_range_for(scope_date.year, scope_date.month)
            scope = FilterScope("month", start, end)

        if st.button("Refresh data"):
            st.cache_data.clear()
            df = load_sheet_dataframe(sheet_id=sheet_id, creds=creds) if sheet_id and creds else pd.DataFrame()
            st.success("Data refreshed")

        def apply_filters(dataframe: pd.DataFrame, query: str, scope_obj: FilterScope) -> pd.DataFrame:
            if dataframe.empty:
                return dataframe
            df_filtered = dataframe.copy()
            df_filtered["date"] = pd.to_datetime(df_filtered["date"]) # Ensure 'date' is datetime
            df_filtered = df_filtered[(df_filtered["date"] >= pd.to_datetime(scope_obj.start_date)) & (df_filtered["date"] <= pd.to_datetime(scope_obj.end_date))]
            if query.strip():
                q = query.strip().lower()
                df_filtered = df_filtered[df_filtered["intern_name"].str.lower().str.contains(q, na=False)]
            df_filtered = df_filtered.sort_values(by=["date", "created_at"], ascending=[False, False])
            return df_filtered

        filtered = apply_filters(df, search_query, scope)

        # Results Section
        st.markdown("### Results")
        stat_col1, stat_col2, stat_col3 = st.columns([1, 1, 2])
        stat_col1.metric("Updates in view", len(filtered))
        stat_col2.metric("Unique interns", filtered["intern_name"].nunique() if not filtered.empty else 0)

        if not filtered.empty:
            csv_bytes = filtered.to_csv(index=False).encode("utf-8")
            stat_col3.download_button("Download CSV", data=csv_bytes, file_name="filtered_updates.csv", mime="text/csv")

        if filtered.empty:
            st.info("No updates for the selected filters. Add the first update below.")
        else:
            for d, group in filtered.groupby(filtered["date"].dt.date):
                with st.expander(f"{d} — {len(group)} update(s)"):
                    for _, row in group.iterrows():
                        st.markdown(f"**{row['intern_name']}** — _{row.get('role', '')}_")
                        st.write(row["update_text"])
                        if row.get("tags") and pd.notna(row.get("tags")):
                            st.caption(f"Tags: {row['tags']}")
                        if row.get("created_by") and pd.notna(row.get("created_by")):
                            st.caption(f"Updated by: {row['created_by']}")
                        st.markdown("---")

    # Add / Edit update section (full-width and centered)
    st.markdown("### Add / Edit update")

    # Initialize session state for form fields
    for key in ["intern_name", "role_input", "update_text", "tags", "updated_by", "form_submitted"]:
        if key not in st.session_state:
            st.session_state[key] = "" if key != "form_submitted" else False

    with st.form("add_update_form"):
        col1, col2 = st.columns([2, 1])
        unique_names = sorted(df["intern_name"].dropna().unique().tolist()) if not df.empty else []
        intern_name = col1.selectbox("Intern name", options=["<new>"] + unique_names, index=0)
        if intern_name == "<new>":
            intern_name = col1.text_input("New intern name", value=st.session_state["intern_name"])
        role_input = col2.text_input("Role / Team (optional)", value=st.session_state["role_input"])
        date_input = st.date_input("Date of update", value=st.session_state.selected_date)
        update_text = st.text_area("Update text (what did you do today?)", height=120, value=st.session_state["update_text"])
        tags = st.text_input("Tags (comma-separated, optional)", value=st.session_state["tags"])
        updated_by = st.text_input("Updated by (your name)", value=st.session_state["updated_by"])

        submitted = st.form_submit_button("Submit update", type="primary")

        if submitted:
            if not intern_name.strip():
                st.error("Intern name is required")
            elif not update_text.strip():
                st.error("Update text is required")
            else:
                new_row = {
                    "date": fmt_date(date_input),
                    "intern_name": intern_name.strip(),
                    "role": role_input.strip(),
                    "update_text": update_text.strip(),
                    "tags": tags.strip(),
                    "created_at": datetime.now().astimezone().isoformat(),
                    "created_by": updated_by.strip() if updated_by.strip() else st.session_state.get("user", "unknown"),
                }
                try:
                    append_update_to_sheet(sheet_id=sheet_id, credentials=creds, row=new_row)
                    st.cache_data.clear()
                    st.session_state["form_submitted"] = True
                    st.success("Update added successfully")
                    st.rerun() # Rerun to clear form and refresh data
                except Exception as exc:
                    st.exception(exc)

    # Clear form values after successful submission
    if st.session_state.get("form_submitted"):
        st.session_state["intern_name"] = ""
        st.session_state["role_input"] = ""
        st.session_state["update_text"] = ""
        st.session_state["tags"] = ""
        st.session_state["updated_by"] = ""
        st.session_state["form_submitted"] = False


def _set_to_today() -> None:
    today = date.today()
    st.session_state.view_year = today.year
    st.session_state.view_month = today.month
    st.session_state.selected_date = today
    st.rerun()


if __name__ == "__main__":
    main()
