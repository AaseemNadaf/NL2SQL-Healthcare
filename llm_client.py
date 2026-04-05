from schema import HEALTHCARE_SCHEMA


def build_system_prompt() -> str:
    return f"""You are a MySQL query generator for a healthcare database. You have the full schema below.

{HEALTHCARE_SCHEMA}

Return only the SQL query. No explanation. No markdown. No code fences.

Rules:
- SELECT queries only
- Use CONCAT(first_name,' ',last_name) AS name (no 'name' or 'patient_name' column exists)
- Use TIMESTAMPDIFF(YEAR,date_of_birth,CURDATE()) AS age (no 'age' column exists)
- Use aliases: p=patients, d=doctors, a=appointments, b=billing, m=medications, r=medical_records, pr=prescriptions, l=lab_tests
- LIMIT 100 on all non-aggregate queries

Input: Show all patients from Pune with their age
Output: SELECT p.patient_id, CONCAT(p.first_name,' ',p.last_name) AS name, TIMESTAMPDIFF(YEAR,p.date_of_birth,CURDATE()) AS age, p.city FROM patients p WHERE p.city='Pune' LIMIT 100;

Input: How many appointments were completed?
Output: SELECT COUNT(*) AS total_completed FROM appointments WHERE status='Completed';"""


def get_puter_component_html(user_prompt: str) -> str:
    system_prompt = build_system_prompt()

    def js_escape(s: str) -> str:
        return (s.replace("\\", "\\\\")
                 .replace("`", "\\`")
                 .replace("${", "\\${"))

    safe_system = js_escape(system_prompt)
    safe_user   = js_escape(user_prompt)

    return f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://js.puter.com/v2/"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Courier New', monospace;
      background: #0d1117;
      color: #e6edf3;
      padding: 12px;
    }}
    #status {{
      font-size: 13px;
      color: #8b949e;
      margin-bottom: 10px;
    }}
    #error-box {{
      display: none;
      color: #f85149;
      background: #3a1a1a;
      border: 1px solid #f8514966;
      border-radius: 6px;
      padding: 10px;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <div id="status">Generating SQL...</div>
  <div id="error-box"></div>

  <script>
    function cleanSQL(raw) {{
      let s = raw.replace(/```sql/gi, '').replace(/```/g, '').trim();
      const selectIdx = s.toUpperCase().indexOf('SELECT');
      if (selectIdx === -1) return s.trim();
      s = s.substring(selectIdx);
      const semiIdx = s.lastIndexOf(';');
      if (semiIdx !== -1) s = s.substring(0, semiIdx + 1);
      s = s.replace(/\\s+/g, ' ').trim();
      return s;
    }}

    (async () => {{
      const statusEl = document.getElementById('status');
      const sqlArea  = document.getElementById('sql-area');
      const copyBtn  = document.getElementById('copy-btn');
      const errorBox = document.getElementById('error-box');

      try {{
        const fullPrompt = `{safe_system}

User question: {safe_user}

SQL query:`;

        const response = await puter.ai.chat(
          fullPrompt,
          {{ model: 'claude-sonnet-4-5' }}
        );

        let raw = '';
        if (typeof response === 'string') {{
          raw = response;
        }} else if (response?.message?.content) {{
          const c = response.message.content;
          raw = Array.isArray(c) ? c.map(x => x.text || '').join('') : String(c);
        }} else if (response?.text) {{
          raw = response.text;
        }}

        const sql = cleanSQL(raw);

        statusEl.innerHTML   = 'SQL generated successfully.';
        statusEl.style.color = '#21c55d';

        const encoded = encodeURIComponent(sql);
        const newUrl = window.parent.location.href.split('?')[0] + '?puter_sql=' + encoded;
        window.parent.history.replaceState(null, '', newUrl);

      }} catch (err) {{
        statusEl.innerHTML     = 'Error generating SQL';
        statusEl.style.color   = '#f85149';
        errorBox.style.display = 'block';
        errorBox.innerText     = err.message;
      }}
    }})();
  </script>
</body>
</html>"""