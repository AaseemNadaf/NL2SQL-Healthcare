HEALTHCARE_SCHEMA = """
DATABASE: mediquery_db (MySQL 8.0)

TABLE: patients
  patient_id      INT           PRIMARY KEY AUTO_INCREMENT
  first_name      VARCHAR(50)   NOT NULL
  last_name       VARCHAR(50)   NOT NULL
  date_of_birth   DATE          NOT NULL
  gender          ENUM          ('Male','Female','Other')
  blood_type      VARCHAR(5)
  phone           VARCHAR(15)
  email           VARCHAR(100)
  address         TEXT
  city            VARCHAR(50)
  state           VARCHAR(50)
  created_at      TIMESTAMP

TABLE: doctors
  doctor_id       INT           PRIMARY KEY AUTO_INCREMENT
  first_name      VARCHAR(50)   NOT NULL
  last_name       VARCHAR(50)   NOT NULL
  specialization  VARCHAR(100)  NOT NULL
  license_number  VARCHAR(50)   UNIQUE
  phone           VARCHAR(15)
  email           VARCHAR(100)
  years_experience INT
  created_at      TIMESTAMP

TABLE: departments
  department_id   INT           PRIMARY KEY AUTO_INCREMENT
  name            VARCHAR(100)  NOT NULL
  head_doctor_id  INT           FK → doctors(doctor_id)
  floor_number    INT
  phone           VARCHAR(15)

TABLE: appointments
  appointment_id  INT           PRIMARY KEY AUTO_INCREMENT
  patient_id      INT           FK → patients(patient_id)
  doctor_id       INT           FK → doctors(doctor_id)
  appointment_date DATETIME     NOT NULL
  reason          TEXT
  status          ENUM          ('Scheduled','Completed','Cancelled','No-Show')
  notes           TEXT
  created_at      TIMESTAMP

TABLE: medical_records
  record_id       INT           PRIMARY KEY AUTO_INCREMENT
  patient_id      INT           FK → patients(patient_id)
  doctor_id       INT           FK → doctors(doctor_id)
  visit_date      DATE          NOT NULL
  diagnosis       TEXT          NOT NULL
  treatment       TEXT
  prescription    TEXT
  follow_up_date  DATE
  created_at      TIMESTAMP

TABLE: medications
  medication_id   INT           PRIMARY KEY AUTO_INCREMENT
  name            VARCHAR(100)  NOT NULL
  generic_name    VARCHAR(100)
  category        VARCHAR(100)
  manufacturer    VARCHAR(100)
  unit_price      DECIMAL(10,2)
  stock_quantity  INT

TABLE: prescriptions
  prescription_id INT           PRIMARY KEY AUTO_INCREMENT
  record_id       INT           FK → medical_records(record_id)
  medication_id   INT           FK → medications(medication_id)
  dosage          VARCHAR(100)
  frequency       VARCHAR(100)
  duration_days   INT
  instructions    TEXT

TABLE: billing
  bill_id         INT           PRIMARY KEY AUTO_INCREMENT
  patient_id      INT           FK → patients(patient_id)
  appointment_id  INT           FK → appointments(appointment_id)
  total_amount    DECIMAL(10,2) NOT NULL
  paid_amount     DECIMAL(10,2)
  payment_status  ENUM          ('Pending','Partial','Paid','Overdue')
  payment_date    DATE
  insurance_claim BOOLEAN
  created_at      TIMESTAMP

TABLE: lab_tests
  test_id         INT           PRIMARY KEY AUTO_INCREMENT
  patient_id      INT           FK → patients(patient_id)
  doctor_id       INT           FK → doctors(doctor_id)
  test_name       VARCHAR(100)  NOT NULL
  test_date       DATE          NOT NULL
  result          TEXT
  normal_range    VARCHAR(100)
  status          ENUM          ('Ordered','In Progress','Completed')

RELATIONSHIPS:
  patients      → appointments    (one-to-many  via patient_id)
  patients      → medical_records (one-to-many  via patient_id)
  patients      → billing         (one-to-many  via patient_id)
  patients      → lab_tests       (one-to-many  via patient_id)
  doctors       → appointments    (one-to-many  via doctor_id)
  doctors       → medical_records (one-to-many  via doctor_id)
  doctors       → lab_tests       (one-to-many  via doctor_id)
  doctors       → departments     (one-to-one   via head_doctor_id)
  appointments  → billing         (one-to-one   via appointment_id)
  medical_records → prescriptions (one-to-many  via record_id)
  medications   → prescriptions   (one-to-many  via medication_id)

NOTES FOR QUERY GENERATION:
  - Always use table aliases for clarity (e.g. p for patients, d for doctors)
  - Always use mediquery_db as the database context
  - Patient full name = CONCAT(first_name, ' ', last_name)
  - Doctor full name  = CONCAT(first_name, ' ', last_name)
  - Age calculation   = TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE())
  - Prefer LIMIT 100 on open-ended SELECT queries to avoid large result sets
  - Never generate DROP, DELETE, TRUNCATE, or ALTER statements
  - For partial name matches use LIKE '%value%'
"""

TABLE_COLUMNS = {
    "patients": [
        "patient_id", "first_name", "last_name", "date_of_birth",
        "gender", "blood_type", "phone", "email", "address", "city", "state", "created_at"
    ],
    "doctors": [
        "doctor_id", "first_name", "last_name", "specialization",
        "license_number", "phone", "email", "years_experience", "created_at"
    ],
    "departments": [
        "department_id", "name", "head_doctor_id", "floor_number", "phone"
    ],
    "appointments": [
        "appointment_id", "patient_id", "doctor_id", "appointment_date",
        "reason", "status", "notes", "created_at"
    ],
    "medical_records": [
        "record_id", "patient_id", "doctor_id", "visit_date",
        "diagnosis", "treatment", "prescription", "follow_up_date", "created_at"
    ],
    "medications": [
        "medication_id", "name", "generic_name", "category",
        "manufacturer", "unit_price", "stock_quantity"
    ],
    "prescriptions": [
        "prescription_id", "record_id", "medication_id",
        "dosage", "frequency", "duration_days", "instructions"
    ],
    "billing": [
        "bill_id", "patient_id", "appointment_id", "total_amount",
        "paid_amount", "payment_status", "payment_date", "insurance_claim", "created_at"
    ],
    "lab_tests": [
        "test_id", "patient_id", "doctor_id", "test_name",
        "test_date", "result", "normal_range", "status"
    ],
}

SAMPLE_PROMPTS = [
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
]