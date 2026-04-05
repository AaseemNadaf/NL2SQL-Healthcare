import time
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

from schema import TABLE_COLUMNS, SAMPLE_PROMPTS
from db_connector import run_query, get_table_preview, get_table_row_counts, test_connection
from llm_client import get_puter_component_html

st.set_page_config(
    page_title="MediQuery AI",
    page_icon="",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"]  { font-family: 'IBM Plex Sans', sans-serif; }
h1, h2, h3                  { font-family: 'IBM Plex Mono', monospace !important; }
.stApp                      { background-color: #0d1117; color: #e6edf3; }

.header-bar {
    background: linear-gradient(135deg, #1a2a3a 0%, #0d2137 100%);
    border: 1px solid #21c55d33;
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 28px;
}
.header-bar h1 { color: #21c55d; margin: 0; font-size: 2rem; }
.header-bar p  { color: #8b949e; margin: 6px 0 0; font-size: 0.95rem; }

.sql-box {
    background: #161b22;
    border: 1px solid #21c55d55;
    border-left: 4px solid #21c55d;
    border-radius: 8px;
    padding: 20px 24px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.88rem;
    color: #79c0ff;
    white-space: pre-wrap;
    line-height: 1.7;
    margin: 12px 0;
}

.status-success { background:#1a3a2a; border:1px solid #21c55d66;
                  color:#21c55d; border-radius:8px; padding:12px 18px; margin:8px 0; }
.status-error   { background:#3a1a1a; border:1px solid #f8514966;
                  color:#f85149; border-radius:8px; padding:12px 18px; margin:8px 0; }
.status-info    { background:#1a2a3a; border:1px solid #388bfd66;
                  color:#79c0ff;  border-radius:8px; padding:12px 18px; margin:8px 0; }
.status-warn    { background:#2a2a1a; border:1px solid #e3b34166;
                  color:#e3b341;  border-radius:8px; padding:12px 18px; margin:8px 0; }

.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600; border-radius: 8px;
    padding: 10px 28px; transition: all .2s;
}
.approve-btn > button {
    background: #21c55d !important; color: #0d1117 !important;
    border: none !important;
}
.approve-btn > button:hover { background: #16a349 !important; transform: translateY(-1px); }
.deny-btn > button {
    background: transparent !important; color: #f85149 !important;
    border: 1px solid #f8514966 !important;
}
.deny-btn > button:hover { background: #3a1a1a !important; transform: translateY(-1px); }

.section-label {
    color: #8b949e; font-size: 0.78rem;
    text-transform: uppercase; letter-spacing: .08em;
    margin: 18px 0 8px;
}
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

defaults = {
    "pending_sql"    : None,
    "query_result"   : None,
    "query_error"    : None,
    "query_history"  : [],
    "generating"     : False,
    "current_prompt" : "",
    "show_puter"     : False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def add_to_history(prompt, sql, status, rows=0):
    st.session_state.query_history.append({
        "time"  : datetime.now().strftime("%H:%M:%S"),
        "prompt": prompt,
        "sql"   : sql,
        "status": status,
        "rows"  : rows,
    })


st.markdown("""
<div class="header-bar">
  <h1>MediQuery AI</h1>
  <p>Natural Language to SQL for Healthcare | Powered by Claude via Puter.js</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Settings")

    ok, msg = test_connection()
    if ok:
        st.markdown('<div class="status-success">Database connected</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-error">DB Error: {msg}</div>',
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p class="section-label">Sample Prompts</p>', unsafe_allow_html=True)
    st.caption("Click any prompt to load it")

    for prompt in SAMPLE_PROMPTS:
        if st.button(prompt, key=f"sp_{prompt[:30]}", use_container_width=True):
            st.session_state.current_prompt = prompt

    st.markdown("---")
    st.markdown("**Session Stats**")
    total    = len(st.session_state.query_history)
    approved = sum(1 for h in st.session_state.query_history if h["status"] == "Approved")
    denied   = sum(1 for h in st.session_state.query_history if h["status"] == "Denied")
    st.metric("Total Queries", total)
    col1, col2 = st.columns(2)
    col1.metric("Approved", approved)
    col2.metric("Denied",   denied)


tab_query, tab_schema, tab_history = st.tabs(["Query", "Schema Viewer", "History"])


with tab_query:

    st.markdown("### Ask a question about your healthcare data")

    user_prompt = st.text_area(
        "Your question",
        value=st.session_state.current_prompt,
        placeholder="e.g. Show all patients from Pune with their age",
        height=90,
        label_visibility="collapsed",
    )

    generate_clicked = st.button("Generate SQL", type="primary")

    if generate_clicked:
        if not user_prompt.strip():
            st.markdown('<div class="status-warn">Please enter a question first.</div>',
                        unsafe_allow_html=True)
        else:
            st.query_params.clear()
            st.session_state.pending_sql    = None
            st.session_state.query_result   = None
            st.session_state.query_error    = None
            st.session_state.current_prompt = user_prompt
            st.session_state.show_puter     = True
            st.session_state.generating     = True

    if st.session_state.show_puter and st.session_state.generating:

        puter_html = get_puter_component_html(st.session_state.current_prompt)
        components.html(puter_html, height=60)

        status_box = st.empty()
        status_box.markdown('<div class="status-info">Claude is generating your SQL query...</div>',
                            unsafe_allow_html=True)

        sql_from_params = st.query_params.get("puter_sql", "")
        if sql_from_params:
            st.session_state.pending_sql = sql_from_params
            st.session_state.generating  = False
            st.session_state.show_puter  = False
            st.query_params.clear()
            st.rerun()
        else:
            time.sleep(1)
            st.rerun()

    if st.session_state.pending_sql and not st.session_state.generating:

        st.markdown("### Review Generated SQL")
        st.caption("Verify the query before it runs on your database.")

        st.markdown(
            f'<div class="sql-box">{st.session_state.pending_sql}</div>',
            unsafe_allow_html=True,
        )

        with st.expander("Edit SQL before approving"):
            edited_sql = st.text_area(
                "Edit SQL",
                value=st.session_state.pending_sql,
                height=120,
                label_visibility="collapsed",
                key="edited_sql",
            )
            if st.button("Save Edits"):
                st.session_state.pending_sql = edited_sql
                st.rerun()

        st.markdown("#### What would you like to do?")
        col_approve, col_deny, col_spacer = st.columns([1, 1, 4])

        with col_approve:
            st.markdown('<div class="approve-btn">', unsafe_allow_html=True)
            approve = st.button("Approve and Run", key="approve_btn")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_deny:
            st.markdown('<div class="deny-btn">', unsafe_allow_html=True)
            deny = st.button("Deny", key="deny_btn")
            st.markdown('</div>', unsafe_allow_html=True)

        if approve:
            with st.spinner("Running query on database..."):
                df, err = run_query(st.session_state.pending_sql)

            if err:
                st.session_state.query_error  = err
                st.session_state.query_result = None
                add_to_history(st.session_state.current_prompt,
                               st.session_state.pending_sql, "Error")
            else:
                st.session_state.query_result = df
                st.session_state.query_error  = None
                add_to_history(st.session_state.current_prompt,
                               st.session_state.pending_sql, "Approved", len(df))

            st.session_state.pending_sql = None
            st.rerun()

        if deny:
            add_to_history(st.session_state.current_prompt,
                           st.session_state.pending_sql, "Denied")
            st.session_state.pending_sql  = None
            st.session_state.query_result = None
            st.session_state.query_error  = None
            st.rerun()

    if st.session_state.query_error:
        st.markdown(
            f'<div class="status-error">{st.session_state.query_error}</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.query_result is not None:
        df = st.session_state.query_result
        if df.empty:
            st.markdown(
                '<div class="status-warn">Query ran successfully but returned no rows.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="status-success">{len(df)} row(s) returned.</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Export as CSV",
                data=csv,
                file_name=f"mediquery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )


with tab_schema:

    st.markdown("### Database Schema — mediquery_db")

    with st.spinner("Loading table stats..."):
        counts_df = get_table_row_counts()

    st.markdown("#### Table Summary")
    st.dataframe(counts_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### Table Details and Preview")

    for table, columns in TABLE_COLUMNS.items():
        with st.expander(f"{table}  ({len(columns)} columns)"):
            st.markdown("**Columns:**")
            cols_display = "  |  ".join(columns)
            st.markdown(
                f'<div class="status-info" style="font-family:monospace;font-size:0.82rem;">'
                f'{cols_display}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("**Sample rows (top 5):**")
            df_prev, err = get_table_preview(table, limit=5)
            if err:
                st.error(err)
            elif df_prev is not None and not df_prev.empty:
                st.dataframe(df_prev, use_container_width=True)
            else:
                st.info("No data found in this table.")


with tab_history:

    st.markdown("### Query History (this session)")

    if not st.session_state.query_history:
        st.markdown(
            '<div class="status-info">No queries run yet. Go to the Query tab to get started.</div>',
            unsafe_allow_html=True,
        )
    else:
        history_df = pd.DataFrame(st.session_state.query_history)
        history_df.index = history_df.index + 1

        st.dataframe(
            history_df[["time", "prompt", "status", "rows"]].rename(columns={
                "time"  : "Time",
                "prompt": "Prompt",
                "status": "Status",
                "rows"  : "Rows",
            }),
            use_container_width=True,
        )

        st.markdown("#### SQL Details")
        for i, row in enumerate(reversed(st.session_state.query_history), 1):
            label = f"[{row['time']}] {row['prompt'][:60]}{'...' if len(row['prompt'])>60 else ''}"
            with st.expander(label):
                st.markdown(
                    f'<div class="sql-box">{row["sql"]}</div>',
                    unsafe_allow_html=True,
                )
                badge_class = {
                    "Approved": "status-success",
                    "Denied"  : "status-error",
                    "Error"   : "status-warn",
                }.get(row["status"], "status-info")
                st.markdown(
                    f'<div class="{badge_class}">Status: {row["status"]} — {row["rows"]} row(s)</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        csv_hist = history_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Export History as CSV",
            data=csv_hist,
            file_name=f"mediquery_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

        if st.button("Clear History"):
            st.session_state.query_history = []
            st.rerun()