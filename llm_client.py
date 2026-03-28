"""
llm_client.py
-------------
LLM client using Puter.js (free, no API key needed).
Puter.js runs Claude in the browser via JavaScript.

Architecture:
  Streamlit renders an HTML component with Puter.js
  -> Puter.js calls Claude for free
  -> Returns SQL back to Streamlit via postMessage / session state
"""

import streamlit.components.v1 as components
from schema import HEALTHCARE_SCHEMA


# ── System prompt ─────────────────────────────────────────────────────────────
def build_system_prompt() -> str:
    return f"""You are an expert MySQL query generator for a healthcare database.

Your job is to convert natural language questions into valid, safe MySQL SELECT queries.

{HEALTHCARE_SCHEMA}

STRICT RULES you must always follow:
1. Output ONLY the raw SQL query — no explanation, no markdown, no code fences.
2. Always generate SELECT queries only. Never use DROP, DELETE, UPDATE, INSERT, ALTER.
3. Use table aliases (p = patients, d = doctors, a = appointments, etc.)
4. Use CONCAT(first_name, ' ', last_name) for full names.
5. Use TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) to calculate age.
6. Add LIMIT 100 to any query that could return many rows.
7. If the question cannot be answered from this schema, output exactly:
   CANNOT_GENERATE: <reason>"""


# ── Puter.js HTML component ───────────────────────────────────────────────────
def get_puter_component_html(user_prompt: str) -> str:
    """
    Returns an HTML page that:
      1. Loads Puter.js from CDN
      2. Calls Claude (free) with the prompt + schema system prompt
      3. Posts the SQL result back to the parent Streamlit window
    app.py renders this with st.components.v1.html()
    """
    system_prompt = build_system_prompt()

    # Escape for JS template literals
    def js_escape(s: str) -> str:
        return (s.replace("\\", "\\\\")
                 .replace("`", "\\`")
                 .replace("${", "\\${"))

    safe_system = js_escape(system_prompt)
    safe_user   = js_escape(user_prompt)

    return f"""
<!DOCTYPE html>
<html>
<head>
  <script src="https://js.puter.com/v2/"></script>
  <style>
    body {{ margin: 0; padding: 10px; font-family: monospace; font-size: 13px;
           background: transparent; color: #8b949e; }}
  </style>
</head>
<body>
  <div id="status">⏳ Calling Claude via Puter.js (free)...</div>

  <script>
    (async () => {{
      const statusEl = document.getElementById('status');

      try {{
        const response = await puter.ai.chat(
          `{safe_user}`,
          {{
            model : 'claude-sonnet-4-5',
            system: `{safe_system}`
          }}
        );

        // ── Normalise the response across Puter.js return shapes ──
        let sql = '';
        if (typeof response === 'string') {{
          sql = response;
        }} else if (response?.message?.content) {{
          const c = response.message.content;
          sql = Array.isArray(c) ? c.map(x => x.text || '').join('') : String(c);
        }} else if (response?.text) {{
          sql = response.text;
        }}

        // Strip accidental markdown fences
        sql = sql.replace(/^```(sql)?\\s*/i, '').replace(/\\s*```$/, '').trim();

        statusEl.innerHTML = '✅ SQL ready!';
        statusEl.style.color = '#21c55d';

        // ── Send result to parent Streamlit window ──
        window.parent.postMessage({{
          type : 'puter_sql_result',
          sql  : sql,
          error: null
        }}, '*');

      }} catch (err) {{
        statusEl.innerHTML = '❌ Puter error: ' + err.message;
        statusEl.style.color = '#f85149';

        window.parent.postMessage({{
          type : 'puter_sql_result',
          sql  : null,
          error: err.message
        }}, '*');
      }}
    }})();
  </script>
</body>
</html>
"""


# ── JS listener injected once into the Streamlit page ────────────────────────
PUTER_LISTENER_HTML = """
<script>
if (!window._puterListenerAttached) {
  window._puterListenerAttached = true;
  window.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'puter_sql_result') {
      // Write into a hidden textarea Streamlit can observe via query params trick
      const sql   = event.data.sql   || '';
      const error = event.data.error || '';
      sessionStorage.setItem('puter_sql',   sql);
      sessionStorage.setItem('puter_error', error);

      // Dispatch a custom DOM event that our polling script picks up
      window.dispatchEvent(new CustomEvent('puterDone', { detail: { sql, error } }));
    }
  });
}
</script>
"""