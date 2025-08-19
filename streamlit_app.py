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

# --- Custom CSS for Modern UI Theme ---
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

:root {
    --primary-color: #3B82F6; /* Vibrant Blue */
    --secondary-color: #8B5CF6; /* Purple/Violet */
    --accent-color: #F59E0B; /* Orange */
    --neutral-bg-light: #F9FAFB;
    --card-bg: rgba(255, 255, 255, 0.9); /* White with subtle transparency */
    --text-color: #333333;
    --heading-color: #222222;
    --border-radius-lg: 12px;
    --border-radius-md: 8px;
    --shadow-light: rgba(0, 0, 0, 0.08) 0px 4px 12px;
    --shadow-hover: rgba(0, 0, 0, 0.15) 0px 8px 24px;
}

body {
    font-family: 'Poppins', sans-serif;
    color: var(--text-color);
}

/* Gradient Background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #E0F7FA, #E8EAF6); /* Light Teal to Lavender */
    background-size: cover;
    background-attachment: fixed;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: var(--card-bg); /* Use card background for sidebar */
    padding-top: 20px;
    box-shadow: var(--shadow-light);
    border-radius: var(--border-radius-lg);
    margin: 10px; /* Add some margin for the card effect */
    transition: all 0.3s ease-in-out;
}
[data-testid="stSidebar"] > div:first-child {
    max-width: 220px;
    min-width: 160px;
    width: 180px;
}

/* Main Content Area Padding */
.main .block-container {
    padding-top: 3rem;
    padding-right: 3rem;
    padding-left: 3rem;
    padding-bottom: 3rem;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-weight: 600; /* Semi-bold */
    color: var(--heading-color);
}
h1 { font-size: 2.5rem; color: var(--primary-color); }
h3 { font-size: 1.5rem; color: var(--heading-color); }

/* Card Containers for Sections */
.stCard {
    background-color: var(--card-bg);
    border-radius: var(--border-radius-lg);
    padding: 25px;
    margin-bottom: 25px;
    box-shadow: var(--shadow-light);
    transition: all 0.3s ease-in-out;
    border: 1px solid rgba(0, 0, 0, 0.05); /* Subtle border */
}
.stCard:hover {
    box-shadow: var(--shadow-hover);
    transform: translateY(-2px);
}

/* Buttons */
div.stButton > button:first-child {
    background: linear-gradient(90deg, var(--primary-color), #6D5FFD); /* Gradient for buttons */
    color: white;
    border: none;
    border-radius: var(--border-radius-md);
    padding: 10px 20px;
    font-weight: 500;
    transition: all 0.3s ease-in-out;
    box-shadow: rgba(0, 0, 0, 0.1) 0px 4px 6px;
}
div.stButton > button:first-child:hover {
    transform: translateY(-1px) scale(1.02);
    box-shadow: rgba(0, 0, 0, 0.2) 0px 6px 10px;
    filter: brightness(1.1);
}

/* Primary Button (for selected date) */
.stButton button[kind="primary"] {
    background: linear-gradient(90deg, var(--secondary-color), #A779FC) !important; /* Purple gradient for selected date */
    box-shadow: rgba(0, 0, 0, 0.2) 0px 4px 12px, var(--secondary-color) 0px 0px 15px 2px !important; /* Glow effect */
    border: none !important;
}
.stButton button[kind="primary"]:hover {
    box-shadow: rgba(0, 0, 0, 0.3) 0px 6px 16px, var(--secondary-color) 0px 0px 20px 4px !important;
    transform: translateY(-2px) scale(1.03);
}

/* Input Fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stDateInput > div > div > input,
.stSelectbox > div > div > div > input {
    background-color: var(--neutral-bg-light);
    border: 1px solid #D1D5DB;
    border-radius: var(--border-radius-md);
    padding: 10px 15px;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
    transition: all 0.2s ease-in-out;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stDateInput > div > div > input:focus,
.stSelectbox > div > div > div > input:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25); /* Focus glow */
    outline: none;
}

/* Calendar Specific Styling */
.calendar-day-button {
    width: 45px; /* Fixed size for rounded square */
    height: 45px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--border-radius-md); /* Rounded square */
    font-weight: 500;
    margin: 3px; /* Space between days */
    transition: all 0.2s ease-in-out;
    background-color: var(--neutral-bg-light);
    border: 1px solid rgba(0, 0, 0, 0.05);
}
.calendar-day-button:hover {
    box-shadow: var(--shadow-light);
    transform: translateY(-1px) scale(1.05);
    background-color: rgba(var(--primary-color), 0.1); /* Light tint on hover */
}
/* Ensure Streamlit buttons within calendar columns take up full space and look like our custom buttons */
.st-emotion-cache-1j0zdrh button { /* Targeting the actual button inside the column */
    width: 100%;
    height: 100%;
    border-radius: var(--border-radius-md);
    padding: 0; /* Remove default button padding */
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1; /* Adjust line height for better centering */
}
/* Adjust individual date button styling to inherit from calendar-day-button */
.st-emotion-cache-1j0zdrh button[data-testid^="stButton"] {
    background-color: var(--neutral-bg-light);
    color: var(--text-color);
    font-weight: 500;
    transition: all 0.2s ease-in-out;
    box-shadow: none;
}
.st-emotion-cache-1j0zdrh button[data-testid^="stButton"]:hover {
    background-color: rgba(var(--primary-color), 0.1);
    box-shadow: var(--shadow-light);
    transform: translateY(-1px) scale(1.05);
}


/* Expander styling (for results) */
.streamlit-expanderHeader {
    background-color: var(--neutral-bg-light);
    border-radius: var(--border-radius-md);
    padding: 15px;
    margin-bottom: 10px;
    box-shadow: rgba(0, 0, 0, 0.05) 0px 2px 4px;
    transition: all 0.2s ease-in-out;
    font-weight: 600;
}
.streamlit-expanderHeader:hover {
    background-color: #E6E8EB;
    box-shadow: rgba(0, 0, 0, 0.1) 0px 4px 8px;
}
.streamlit-expanderContent {
    background-color: var(--neutral-bg-light);
    border-radius: var(--border-radius-md);
    padding: 15px;
    margin-top: -5px; /* Adjust to sit right below header */
    box-shadow: rgba(0, 0, 0, 0.05) 0px 2px 4px;
    border-top-left-radius: 0;
    border-top-right-radius: 0;
    animation: fadeIn 0.3s ease-out; /* Fade-in effect */
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Metric styling */
[data-testid="stMetric"] {
    background-color: var(--card-bg);
    border-radius: var(--border-radius-md);
    padding: 15px;
    box-shadow: var(--shadow-light);
    text-align: center;
    margin-top: 10px;
    margin-bottom: 10px;
}
[data-testid="stMetric"] > div > div:first-child {
    color: var(--primary-color);
    font-size: 1.8rem;
    font-weight: 700;
}
[data-testid="stMetric"] > div > div:last-child {
    color: var(--text-color);
    font-size: 0.9rem;
    font-weight: 500;
}

/* General component spacing */
div[data-testid="stVerticalBlock"] > div:not(:last-child) {
    padding-bottom: 1rem;
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

    # Using st.container for card-like sections
    sidebar_container = st.sidebar.container()
    main_cols = st.columns([1.3, 2]) # Adjusted ratio for content areas
    
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

    with sidebar_container:
        st.markdown("<div class='stCard'>", unsafe_allow_html=True) # Start Calendar Card
        st.markdown("<h3>Calendar</h3>", unsafe_allow_html=True)
        cal_controls = st.columns([1, 1, 2])
        if cal_controls[0].button("Previous"):
            y, m = st.session_state.view_year, st.session_state.view_month
            if m == 1:
                st.session_state.view_year = y - 1
                st.session_state.view_month = 12
            else:
                st.session_state.view_month = m - 1
            st.rerun() # Rerun to update calendar view
        if cal_controls[1].button("Next"):
            y, m = st.session_state.view_year, st.session_state.view_month
            if m == 12:
                st.session_state.view_year = y + 1
                st.session_state.view_month = 1
            else:
                st.session_state.view_month = m + 1
            st.rerun() # Rerun to update calendar view
        cal_controls[2].button("Today", key="cal_today_button", on_click=lambda: _set_to_today())

        st.markdown(f"<h4>{calendar.month_name[st.session_state.view_month]} {st.session_state.view_year}</h4>", unsafe_allow_html=True)

        counts_by_date: Dict[str, int] = {}
        try:
            if not df.empty:
                # Ensure 'date' column is datetime objects for correct comparison
                df['date'] = pd.to_datetime(df['date']).dt.date
                counts = df.groupby("date").size()
                counts_by_date = {str(k): v for k, v in counts.to_dict().items()}
        except Exception:
            counts_by_date = {}

        month_cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)

        for week in month_cal:
            cols = st.columns(7)
            for i, daynum in enumerate(week):
                if daynum == 0:
                    cols[i].markdown("<div class='calendar-day-button'>&nbsp;</div>", unsafe_allow_html=True)
                    continue
                
                cell_date = date(st.session_state.view_year, st.session_state.view_month, daynum)
                badge = ""
                # Format the date string for lookup
                if fmt_date(cell_date) in counts_by_date:
                    badge = f" ({counts_by_date[fmt_date(cell_date)]})"
                
                button_type = "primary" if cell_date == st.session_state.selected_date else "secondary"
                
                # Apply custom class for base styling, then Streamlit's type for accent
                if cols[i].button(f"{daynum}{badge}", key=f"cal_day_{cell_date.isoformat()}", type=button_type):
                    st.session_state.selected_date = cell_date
                    st.rerun() # Rerun to update the selected date highlight

        st.markdown("</div>", unsafe_allow_html=True) # End Calendar Card

    with main_cols[0]: # Left column for Controls and Results
        st.markdown("<div class='stCard'>", unsafe_allow_html=True) # Start Controls Card
        st.markdown("<h3>Controls</h3>", unsafe_allow_html=True)

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
        st.markdown("</div>", unsafe_allow_html=True) # End Controls Card


        st.markdown("<div class='stCard'>", unsafe_allow_html=True) # Start Results Card
        st.markdown("<h3>Results</h3>", unsafe_allow_html=True)
        stat_col1, stat_col2, stat_col3 = st.columns([1, 1, 2])
        
        # Ensure 'date' column is of datetime.date type for filtering
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        def apply_filters(dataframe: pd.DataFrame, query: str, scope_obj: FilterScope) -> pd.DataFrame:
            if dataframe.empty:
                return dataframe
            df_filtered = dataframe.copy()
            df_filtered = df_filtered[(df_filtered["date"] >= scope_obj.start_date) & (df_filtered["date"] <= scope_obj.end_date)]
            if query.strip():
                q = query.strip().lower()
                df_filtered = df_filtered[df_filtered["intern_name"].str.lower().str.contains(q, na=False)]
            df_filtered = df_filtered.sort_values(by=["date", "created_at"], ascending=[False, False])
            return df_filtered

        filtered = apply_filters(df, search_query, scope)

        stat_col1.metric("Updates in view", len(filtered))
        stat_col2.metric("Unique interns", filtered["intern_name"].nunique() if not filtered.empty else 0)

        if not filtered.empty:
            csv_bytes = filtered.to_csv(index=False).encode("utf-8")
            stat_col3.download_button("Download CSV", data=csv_bytes, file_name="filtered_updates.csv", mime="text/csv")

        if filtered.empty:
            st.info("No updates for the selected filters. Add the first update below.")
        else:
            for d, group in filtered.groupby(filtered["date"].dt.date):
                # Using a unique key for each expander based on date to prevent issues
                with st.expander(f"{d.strftime('%b %d, %Y')} — {len(group)} update(s)", expanded=False):
                    for _, row in group.iterrows():
                        st.markdown(f"**{row['intern_name']}** — _{row.get('role', 'N/A')}_")
                        st.write(row["update_text"])
                        if row.get("tags") and pd.notna(row.get("tags")):
                            st.caption(f"Tags: {row['tags']}")
                        if row.get("created_by") and pd.notna(row.get("created_by")):
                            st.caption(f"Updated by: {row['created_by']}")
                        st.markdown("---")
        st.markdown("</div>", unsafe_allow_html=True) # End Results Card


    with main_cols[1]: # Right column for Add/Edit Update
        st.markdown("<div class='stCard'>", unsafe_allow_html=True) # Start Add/Edit Update Card
        st.markdown("<h3>Add / Edit Update</h3>", unsafe_allow_html=True)

        # Initialize session state for form fields
        for key in ["intern_name_form", "role_input", "update_text", "tags", "updated_by", "form_submitted"]:
            if key not in st.session_state:
                st.session_state[key] = "" if key != "form_submitted" else False

        with st.form("add_update_form"):
            col1, col2 = st.columns([2, 1])
            unique_names = sorted(df["intern_name"].dropna().unique().tolist()) if not df.empty else []
            intern_name_selection = col1.selectbox("Intern name", options=["<new>"] + unique_names, index=0, key="intern_name_select")
            if intern_name_selection == "<new>":
                intern_name = col1.text_input("New intern name", value=st.session_state["intern_name_form"], key="new_intern_name_input")
            else:
                intern_name = intern_name_selection
            
            role_input = col2.text_input("Role / Team (optional)", value=st.session_state["role_input"], key="role_input")
            date_input = st.date_input("Date of update", value=st.session_state.selected_date, key="date_input")
            update_text = st.text_area("Update text (what did you do today?)", height=120, value=st.session_state["update_text"], key="update_text_area")
            tags = st.text_input("Tags (comma-separated, optional)", value=st.session_state["tags"], key="tags_input")
            updated_by = st.text_input("Updated by (your name)", value=st.session_state["updated_by"], key="updated_by_input")

            submitted = st.form_submit_button("Submit update")

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
                        # Clear form values in session state
                        st.session_state["intern_name_form"] = ""
                        st.session_state["role_input"] = ""
                        st.session_state["update_text"] = ""
                        st.session_state["tags"] = ""
                        st.session_state["updated_by"] = ""
                        st.session_state.selected_date = date.today() # Reset selected date
                        st.rerun() # Rerun to clear form and update data
                    except Exception as exc:
                        st.exception(exc)

        st.markdown("</div>", unsafe_allow_html=True) # End Add/Edit Update Card


def _set_to_today() -> None:
    today = date.today()
    st.session_state.view_year = today.year
    st.session_state.view_month = today.month
    st.session_state.selected_date = today
    st.rerun()


if __name__ == "__main__":
    main()
