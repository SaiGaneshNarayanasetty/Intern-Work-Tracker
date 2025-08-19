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

# --- VIBRANT COLOR SCHEME: inject custom CSS ---
st.markdown("""
    <style>
        .stApp {
            background-color: #f3f2fc;
        }
        h1, h2, h3 {
            color: #2E2B5F;
        }
        .stButton > button {
            background-color: #FF5733;
            color: white;
            border-radius: 8px;
            border: none;
            transition: box-shadow 0.2s;
            font-weight: bold;
        }
        .stButton > button:hover {
            background-color: #2574A9;
            box-shadow: 0 2px 8px #febc8e;
        }
        .stTextInput > div > input,
        .stTextArea textarea,
        .stSelectbox > div > div > div {
            background-color: #f5e6fa !important;
            border-color: #FF5733 !important;
        }
        .stDownloadButton > button {
            background: #26c281 !important;
            color: #fff !important;
        }
        .stMetric {
            background: #fff6e6 !important;
        }
        /* Highlight selected calendar cell */
        .selected-date {
            background-color: #FFDAB9 !important;
            color: #FF5733 !important;
            border-radius: 50% !important;
            box-shadow: 0 0 0 2px #FF5733 !important;
            font-weight: bold !important;
        }
    </style>
""", unsafe_allow_html=True)


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

    # --------- CALENDAR UI WITH SELECTED-DATE HIGHLIGHT ---------
    with left_col:
        st.markdown("### Calendar")

        cal_controls = st.columns([1, 1, 2])

        if cal_controls[0].button("Previous"):
            y, m = st.session_state.view_year, st.session_state.view_month
            if m == 1:
                st.session_state.view_year = y - 1
                st.session_state.view_month = 12
            else:
                st.session_state.view_month = m - 1

        if cal_controls[1].button("Next"):
            y, m = st.session_state.view_year, st.session_state.view_month
            if m == 12:
                st.session_state.view_year = y + 1
                st.session_state.view_month = 1
            else:
                st.session_state.view_month = m + 1
        
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
        for week in month_cal:
            cols = st.columns(7)
            for i, daynum in enumerate(week):
                if daynum == 0:
                    cols[i].markdown(" ")
                    continue
                cell_date = date(st.session_state.view_year, st.session_state.view_month, daynum)
                badge = ""
                if fmt_date(cell_date) in counts_by_date:
                    badge = f" ({counts_by_date[fmt_date(cell_date)]})"
                is_selected = (cell_date == st.session_state.selected_date)
                button_label = f"{daynum}{badge}"
                button_key = f"calbtn_{cell_date}"
                button_kwargs = {'key':button_key,'use_container_width':True}
                if is_selected:
                    # Highlight the selected date using custom HTML styling
                    cols[i].markdown(
                        f"<div class='selected-date' style='display:inline-block;width:40px;height:40px;line-height:40px;text-align:center;font-size:17px;'>{button_label}</div>",
                        unsafe_allow_html=True,
                    )
                    if cols[i].button("", key=f"sel{button_key}", use_container_width=True):
                        st.session_state.selected_date = cell_date
                else:
                    # Normal button for non-selected dates
                    if cols[i].button(button_label, **button_kwargs):
                        st.session_state.selected_date = cell_date

    # --------- RIGHT-COLUMN: FILTERS, RESULTS, STATS ----------
    with right_col:
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
            df_filtered = df_filtered[
                (df_filtered["date"] >= pd.to_datetime(scope_obj.start_date)) &
                (df_filtered["date"] <= pd.to_datetime(scope_obj.end_date))
            ]
            if query.strip():
                q = query.strip().lower()
                df_filtered = df_filtered[df_filtered["intern_name"].str.lower().str.contains(q, na=False)]
            df_filtered = df_filtered.sort_values(by=["date", "created_at"], ascending=[False, False])
            return df_filtered

        filtered = apply_filters(df, search_query, scope)

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

    # --------- CENTERED "ADD / EDIT UPDATE" FORM SECTION ----------
    st.markdown("### Add / Edit update")

    # Center the form using columns
    center_col = st.columns([1, 2, 1])[1]  # Centered 2/4 width

    # Initialize session state for form fields
    for key in ["intern_name", "role_input", "update_text", "tags", "updated_by", "form_submitted"]:
        if key not in st.session_state:
            st.session_state[key] = "" if key != "form_submitted" else False

    with center_col:
        with st.form("add_update_form"):
            col1, col2 = st.columns([2, 1])
            unique_names = sorted(df["intern_name"].dropna().unique().tolist()) if not df.empty else []
            intern_name = col1.selectbox("Intern name", options=[""] + unique_names, index=0)
            if intern_name == "":
                intern_name = col1.text_input("New intern name", value=st.session_state["intern_name"])
            role_input = col2.text_input("Role / Team (optional)", value=st.session_state["role_input"])
            date_input = st.date_input("Date of update", value=st.session_state.selected_date)
            update_text = st.text_area("Update text (what did you do today?)", height=120, value=st.session_state["update_text"])
            tags = st.text_input("Tags (comma-separated, optional)", value=st.session_state["tags"])
            updated_by = st.text_input("Updated by (your name)", value=st.session_state["updated_by"])
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

if __name__ == "__main__":
    main()
