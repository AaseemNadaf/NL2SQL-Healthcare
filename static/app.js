const FLASK_URL = 'http://localhost:5000';

const SCHEMA_COLS = {
  patients:        ["patient_id","first_name","last_name","date_of_birth","gender","blood_type","phone","email","address","city","state","created_at"],
  doctors:         ["doctor_id","first_name","last_name","specialization","license_number","phone","email","years_experience","created_at"],
  departments:     ["department_id","name","head_doctor_id","floor_number","phone"],
  appointments:    ["appointment_id","patient_id","doctor_id","appointment_date","reason","status","notes","created_at"],
  medical_records: ["record_id","patient_id","doctor_id","visit_date","diagnosis","treatment","prescription","follow_up_date","created_at"],
  medications:     ["medication_id","name","generic_name","category","manufacturer","unit_price","stock_quantity"],
  prescriptions:   ["prescription_id","record_id","medication_id","dosage","frequency","duration_days","instructions"],
  billing:         ["bill_id","patient_id","appointment_id","total_amount","paid_amount","payment_status","payment_date","insurance_claim","created_at"],
  lab_tests:       ["test_id","patient_id","doctor_id","test_name","test_date","result","normal_range","status"],
};

const SAMPLE_PROMPTS = [
  "Show all patients from Pune with their age",
  "List all appointments scheduled for December 2024",
  "Which doctor has the most completed appointments?",
  "Show all pending bills with patient names and amounts",
  "List all prescriptions for diabetes-related medications",
  "Find patients who have lab tests still in progress",
  "Show total revenue collected per month",
  "Which patients have a follow-up appointment due this month?",
  "List all doctors in the Cardiology department",
  "Show medications that are running low (stock under 300)",
];

const SYSTEM_PROMPT = `You are a MySQL query generator for a healthcare database.

DATABASE: mediquery_db (MySQL 8.0)

TABLE: patients — patient_id, first_name, last_name, date_of_birth, gender, blood_type, phone, email, address, city, state, created_at
TABLE: doctors — doctor_id, first_name, last_name, specialization, license_number, phone, email, years_experience, created_at
TABLE: departments — department_id, name, head_doctor_id (FK doctors), floor_number, phone
TABLE: appointments — appointment_id, patient_id (FK patients), doctor_id (FK doctors), appointment_date, reason, status (Scheduled/Completed/Cancelled/No-Show), notes, created_at
TABLE: medical_records — record_id, patient_id, doctor_id, visit_date, diagnosis, treatment, prescription, follow_up_date, created_at
TABLE: medications — medication_id, name, generic_name, category, manufacturer, unit_price, stock_quantity
TABLE: prescriptions — prescription_id, record_id (FK medical_records), medication_id (FK medications), dosage, frequency, duration_days, instructions
TABLE: billing — bill_id, patient_id, appointment_id, total_amount, paid_amount, payment_status (Pending/Partial/Paid/Overdue), payment_date, insurance_claim, created_at
TABLE: lab_tests — test_id, patient_id, doctor_id, test_name, test_date, result, normal_range, status (Ordered/In Progress/Completed)

Return only the SQL query. No explanation. No markdown. No code fences.

Rules:
- SELECT queries only
- Use CONCAT(first_name,' ',last_name) AS name — no 'name' or 'patient_name' column exists
- Use TIMESTAMPDIFF(YEAR,date_of_birth,CURDATE()) AS age — no 'age' column exists
- Use aliases: p=patients, d=doctors, a=appointments, b=billing, m=medications, r=medical_records, pr=prescriptions, l=lab_tests
- LIMIT 100 on all non-aggregate queries

Input: Show all patients from Pune with their age
Output: SELECT p.patient_id, CONCAT(p.first_name,' ',p.last_name) AS name, TIMESTAMPDIFF(YEAR,p.date_of_birth,CURDATE()) AS age, p.city FROM patients p WHERE p.city='Pune' LIMIT 100;

Input: How many appointments were completed?
Output: SELECT COUNT(*) AS total_completed FROM appointments WHERE status='Completed';`;

const state = {
  currentSQL  : null,
  currentPrompt: '',
  history     : [],
  lastResults : null,
};

function $(id) { return document.getElementById(id); }
function show(id) { $(id).classList.remove('hidden'); }
function hide(id) { $(id).classList.add('hidden'); }

function cleanSQL(raw) {
  let s = raw.replace(/```sql/gi, '').replace(/```/g, '').trim();
  const idx = s.toUpperCase().indexOf('SELECT');
  if (idx === -1) return s.trim();
  s = s.substring(idx);
  const semi = s.lastIndexOf(';');
  if (semi !== -1) s = s.substring(0, semi + 1);
  return s.replace(/\s+/g, ' ').trim();
}

function updateStats() {
  $('stat-total').textContent    = state.history.length;
  $('stat-approved').textContent = state.history.filter(h => h.status === 'Approved').length;
  $('stat-denied').textContent   = state.history.filter(h => h.status === 'Denied').length;
}

function renderTable(columns, rows, containerId, tbodyId, theadId) {
  $(theadId).innerHTML = '<tr>' + columns.map(c => `<th>${c}</th>`).join('') + '</tr>';
  $(tbodyId).innerHTML = rows.map(row =>
    '<tr>' + row.map(cell => `<td>${cell === null ? '<span style="color:var(--text-3)">null</span>' : cell}</td>`).join('') + '</tr>'
  ).join('');
}

function renderHistory() {
  const list = $('history-list');
  if (state.history.length === 0) {
    list.innerHTML = '<div class="empty-state">No queries run yet. Go to the Query tab to get started.</div>';
    return;
  }
  list.innerHTML = [...state.history].reverse().map(h => {
    const badgeClass = h.status === 'Approved' ? 'badge-approved' : h.status === 'Denied' ? 'badge-denied' : 'badge-error';
    return `
      <div class="history-item">
        <div class="history-item-top">
          <span class="history-prompt">${h.prompt}</span>
          <span class="badge ${badgeClass}">${h.status}</span>
        </div>
        <div class="history-sql">${h.sql}</div>
        <div class="history-footer">
          <span>${h.time}</span>
          <span>${h.rows} row(s)</span>
        </div>
      </div>`;
  }).join('');
}

async function checkDB() {
  const el = $('db-status');
  try {
    const res  = await fetch(`${FLASK_URL}/api/health`);
    const data = await res.json();
    if (data.status === 'ok') {
      el.className   = 'nav-status ok';
      el.innerHTML   = '<span class="dot"></span>mediquery_db';
    } else {
      el.className   = 'nav-status error';
      el.innerHTML   = '<span class="dot"></span>DB Error';
    }
  } catch {
    el.className = 'nav-status error';
    el.innerHTML = '<span class="dot"></span>Backend offline';
  }
}

async function loadSchemaSummary() {
  try {
    const res  = await fetch(`${FLASK_URL}/api/tables`);
    const data = await res.json();
    $('summary-grid').innerHTML = data.map(r => `
      <div class="summary-card">
        <div class="summary-card-name">${r.Table}</div>
        <div class="summary-card-count">${r['Row Count']}</div>
        <div class="summary-card-label">rows</div>
      </div>`).join('');
  } catch {
    $('summary-grid').innerHTML = '<div class="alert alert-error">Could not load table stats.</div>';
  }
}

function buildSchemaCards() {
  $('table-cards').innerHTML = Object.entries(SCHEMA_COLS).map(([table, cols]) => `
    <div class="table-card">
      <div class="table-card-header" onclick="toggleTableCard(this, '${table}')">
        <span class="table-card-name">${table}</span>
        <span class="table-card-meta">
          <span>${cols.length} columns</span>
          <span class="chevron">&#9660;</span>
        </span>
      </div>
      <div class="table-card-body" id="card-body-${table}">
        <div class="col-pills">${cols.map(c => `<span class="col-pill">${c}</span>`).join('')}</div>
        <div class="preview-wrap">
          <div class="preview-loading" id="preview-${table}">Click to load sample rows...</div>
        </div>
      </div>
    </div>`).join('');
}

function toggleTableCard(header, table) {
  const body = $(`card-body-${table}`);
  const isOpen = body.classList.toggle('open');
  header.classList.toggle('open', isOpen);
  if (isOpen) loadPreview(table);
}

async function loadPreview(table) {
  const container = $(`preview-${table}`);
  container.innerHTML = '<div class="preview-loading">Loading...</div>';
  try {
    const res  = await fetch(`${FLASK_URL}/api/preview/${table}`);
    const data = await res.json();
    if (data.error || data.rows.length === 0) {
      container.innerHTML = '<div class="preview-loading">No data available.</div>';
      return;
    }
    container.innerHTML = `
      <div class="table-wrap">
        <table>
          <thead><tr>${data.columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>
          <tbody>${data.rows.map(row =>
            '<tr>' + row.map(cell => `<td>${cell === null ? '' : cell}</td>`).join('') + '</tr>'
          ).join('')}</tbody>
        </table>
      </div>`;
  } catch {
    container.innerHTML = '<div class="preview-loading">Could not load preview.</div>';
  }
}

function buildPromptChips() {
  $('prompt-chips').innerHTML = SAMPLE_PROMPTS.map(p =>
    `<button class="chip" onclick="loadPrompt(this)">${p}</button>`
  ).join('');
}

function loadPrompt(btn) {
  $('nl-input').value = btn.textContent;
  $('nl-input').focus();
}

$('generate-btn').addEventListener('click', async () => {
  const prompt = $('nl-input').value.trim();
  if (!prompt) return;

  state.currentPrompt = prompt;
  hide('review-section');
  hide('results-section');
  hide('error-alert');
  hide('success-alert');
  show('generating-alert');
  $('generate-btn').disabled = true;
  $('sql-output').innerHTML  = '<span class="sql-placeholder">Generating...</span>';

  try {
    const fullPrompt = `${SYSTEM_PROMPT}\n\nInput: ${prompt}\nOutput:`;
    const response   = await puter.ai.chat(fullPrompt, { model: 'claude-sonnet-4-5' });

    let raw = '';
    if (typeof response === 'string') {
      raw = response;
    } else if (response?.message?.content) {
      const c = response.message.content;
      raw = Array.isArray(c) ? c.map(x => x.text || '').join('') : String(c);
    } else if (response?.text) {
      raw = response.text;
    }

    const sql      = cleanSQL(raw);
    state.currentSQL = sql;

    hide('generating-alert');
    $('sql-output').textContent = sql;
    show('review-section');

  } catch (err) {
    hide('generating-alert');
    $('error-alert').textContent = 'Error generating SQL: ' + err.message;
    show('error-alert');
    $('sql-output').innerHTML = '<span class="sql-placeholder">Generation failed.</span>';
  }

  $('generate-btn').disabled = false;
});

$('approve-btn').addEventListener('click', async () => {
  if (!state.currentSQL) return;

  $('approve-btn').disabled  = true;
  $('deny-btn').disabled     = true;
  $('approve-btn').textContent = 'Running...';

  try {
    const res  = await fetch(`${FLASK_URL}/api/execute`, {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ sql: state.currentSQL }),
    });
    const data = await res.json();

    if (data.error) {
      $('error-alert').textContent = data.error;
      show('error-alert');
      state.history.push({ prompt: state.currentPrompt, sql: state.currentSQL, status: 'Error', rows: 0, time: new Date().toLocaleTimeString() });
    } else {
      state.lastResults = data;
      $('success-alert').textContent = `${data.count} row(s) returned.`;
      show('success-alert');

      if (data.count > 0) {
        renderTable(data.columns, data.rows, 'results-section', 'results-tbody', 'results-thead');
        show('results-section');
      }
      state.history.push({ prompt: state.currentPrompt, sql: state.currentSQL, status: 'Approved', rows: data.count, time: new Date().toLocaleTimeString() });
    }
  } catch (err) {
    $('error-alert').textContent = 'Could not reach backend: ' + err.message;
    show('error-alert');
  }

  hide('review-section');
  $('approve-btn').disabled    = false;
  $('deny-btn').disabled       = false;
  $('approve-btn').textContent = 'Approve and Run';
  updateStats();
  renderHistory();
});

$('deny-btn').addEventListener('click', () => {
  state.history.push({ prompt: state.currentPrompt, sql: state.currentSQL, status: 'Denied', rows: 0, time: new Date().toLocaleTimeString() });
  hide('review-section');
  updateStats();
  renderHistory();
});

$('export-btn').addEventListener('click', () => {
  if (!state.lastResults) return;
  const { columns, rows } = state.lastResults;
  const csv = [columns.join(','), ...rows.map(r => r.map(c => `"${c ?? ''}"`).join(','))].join('\n');
  const a   = Object.assign(document.createElement('a'), {
    href    : 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv),
    download: `mediquery_${Date.now()}.csv`,
  });
  a.click();
});

$('export-history-btn').addEventListener('click', () => {
  if (!state.history.length) return;
  const cols = ['time','prompt','sql','status','rows'];
  const csv  = [cols.join(','), ...state.history.map(h =>
    cols.map(c => `"${(h[c] ?? '').toString().replace(/"/g, '""')}"`).join(',')
  )].join('\n');
  const a = Object.assign(document.createElement('a'), {
    href    : 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv),
    download: `mediquery_history_${Date.now()}.csv`,
  });
  a.click();
});

$('clear-history-btn').addEventListener('click', () => {
  state.history = [];
  updateStats();
  renderHistory();
});

document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    $('page-' + tab.dataset.tab).classList.add('active');
    if (tab.dataset.tab === 'schema') {
      loadSchemaSummary();
      buildSchemaCards();
    }
  });
});

checkDB();
buildPromptChips();
renderHistory();