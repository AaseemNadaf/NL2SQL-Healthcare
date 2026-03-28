-- ============================================================
--  MediQuery AI  –  Sample Healthcare Database
--  MySQL 8.0+
--  Run: mysql -u root -p < setup_db.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS mediquery_db;
USE mediquery_db;

-- ─────────────────────────────────────────────
--  1. PATIENTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    patient_id      INT AUTO_INCREMENT PRIMARY KEY,
    first_name      VARCHAR(50)  NOT NULL,
    last_name       VARCHAR(50)  NOT NULL,
    date_of_birth   DATE         NOT NULL,
    gender          ENUM('Male','Female','Other') NOT NULL,
    blood_type      VARCHAR(5),
    phone           VARCHAR(15),
    email           VARCHAR(100),
    address         TEXT,
    city            VARCHAR(50),
    state           VARCHAR(50),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
--  2. DOCTORS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id       INT AUTO_INCREMENT PRIMARY KEY,
    first_name      VARCHAR(50)  NOT NULL,
    last_name       VARCHAR(50)  NOT NULL,
    specialization  VARCHAR(100) NOT NULL,
    license_number  VARCHAR(50)  UNIQUE NOT NULL,
    phone           VARCHAR(15),
    email           VARCHAR(100),
    years_experience INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
--  3. DEPARTMENTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    department_id   INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    head_doctor_id  INT,
    floor_number    INT,
    phone           VARCHAR(15),
    FOREIGN KEY (head_doctor_id) REFERENCES doctors(doctor_id)
);

-- ─────────────────────────────────────────────
--  4. APPOINTMENTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id  INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT NOT NULL,
    doctor_id       INT NOT NULL,
    appointment_date DATETIME NOT NULL,
    reason          TEXT,
    status          ENUM('Scheduled','Completed','Cancelled','No-Show') DEFAULT 'Scheduled',
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)  REFERENCES doctors(doctor_id)
);

-- ─────────────────────────────────────────────
--  5. MEDICAL RECORDS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS medical_records (
    record_id       INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT NOT NULL,
    doctor_id       INT NOT NULL,
    visit_date      DATE NOT NULL,
    diagnosis       TEXT NOT NULL,
    treatment       TEXT,
    prescription    TEXT,
    follow_up_date  DATE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)  REFERENCES doctors(doctor_id)
);

-- ─────────────────────────────────────────────
--  6. MEDICATIONS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS medications (
    medication_id   INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    generic_name    VARCHAR(100),
    category        VARCHAR(100),
    manufacturer    VARCHAR(100),
    unit_price      DECIMAL(10,2),
    stock_quantity  INT DEFAULT 0
);

-- ─────────────────────────────────────────────
--  7. PRESCRIPTIONS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    record_id       INT NOT NULL,
    medication_id   INT NOT NULL,
    dosage          VARCHAR(100),
    frequency       VARCHAR(100),
    duration_days   INT,
    instructions    TEXT,
    FOREIGN KEY (record_id)     REFERENCES medical_records(record_id),
    FOREIGN KEY (medication_id) REFERENCES medications(medication_id)
);

-- ─────────────────────────────────────────────
--  8. BILLING
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS billing (
    bill_id         INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT NOT NULL,
    appointment_id  INT,
    total_amount    DECIMAL(10,2) NOT NULL,
    paid_amount     DECIMAL(10,2) DEFAULT 0.00,
    payment_status  ENUM('Pending','Partial','Paid','Overdue') DEFAULT 'Pending',
    payment_date    DATE,
    insurance_claim BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id)    REFERENCES patients(patient_id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
);

-- ─────────────────────────────────────────────
--  9. LAB TESTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lab_tests (
    test_id         INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT NOT NULL,
    doctor_id       INT NOT NULL,
    test_name       VARCHAR(100) NOT NULL,
    test_date       DATE NOT NULL,
    result          TEXT,
    normal_range    VARCHAR(100),
    status          ENUM('Ordered','In Progress','Completed') DEFAULT 'Ordered',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)  REFERENCES doctors(doctor_id)
);

-- ============================================================
--  SAMPLE DATA
-- ============================================================

-- Doctors
INSERT INTO doctors (first_name, last_name, specialization, license_number, phone, email, years_experience) VALUES
('Priya',    'Sharma',    'Cardiology',        'MH-CARD-1021', '9876543210', 'priya.sharma@mediquery.in',    14),
('Rohan',    'Mehta',     'Neurology',         'MH-NEUR-2045', '9876543211', 'rohan.mehta@mediquery.in',     9),
('Ananya',   'Iyer',      'Pediatrics',        'MH-PEDI-3067', '9876543212', 'ananya.iyer@mediquery.in',     11),
('Vikram',   'Desai',     'Orthopedics',       'MH-ORTH-4089', '9876543213', 'vikram.desai@mediquery.in',    17),
('Kavitha',  'Nair',      'General Medicine',  'MH-GENM-5012', '9876543214', 'kavitha.nair@mediquery.in',    6),
('Arjun',    'Patel',     'Oncology',          'MH-ONCO-6034', '9876543215', 'arjun.patel@mediquery.in',     20),
('Sneha',    'Kulkarni',  'Dermatology',       'MH-DERM-7056', '9876543216', 'sneha.kulkarni@mediquery.in',  8),
('Deepak',   'Rao',       'Psychiatry',        'MH-PSYC-8078', '9876543217', 'deepak.rao@mediquery.in',      12);

-- Departments
INSERT INTO departments (name, head_doctor_id, floor_number, phone) VALUES
('Cardiology',       1, 3, '020-27001001'),
('Neurology',        2, 4, '020-27001002'),
('Pediatrics',       3, 2, '020-27001003'),
('Orthopedics',      4, 5, '020-27001004'),
('General Medicine', 5, 1, '020-27001005'),
('Oncology',         6, 6, '020-27001006'),
('Dermatology',      7, 2, '020-27001007'),
('Psychiatry',       8, 7, '020-27001008');

-- Patients
INSERT INTO patients (first_name, last_name, date_of_birth, gender, blood_type, phone, email, city, state) VALUES
('Aarav',    'Shah',       '1985-03-12', 'Male',   'O+',  '9800001001', 'aarav.shah@gmail.com',       'Pune',      'Maharashtra'),
('Meera',    'Joshi',      '1992-07-25', 'Female', 'A+',  '9800001002', 'meera.joshi@gmail.com',      'Pune',      'Maharashtra'),
('Suresh',   'Kumar',      '1978-11-03', 'Male',   'B+',  '9800001003', 'suresh.kumar@gmail.com',     'Mumbai',    'Maharashtra'),
('Lakshmi',  'Reddy',      '2001-05-18', 'Female', 'AB-', '9800001004', 'lakshmi.reddy@gmail.com',    'Pune',      'Maharashtra'),
('Rahul',    'Gupta',      '1965-09-30', 'Male',   'A-',  '9800001005', 'rahul.gupta@gmail.com',      'Nashik',    'Maharashtra'),
('Divya',    'Singh',      '1999-01-14', 'Female', 'O-',  '9800001006', 'divya.singh@gmail.com',      'Pune',      'Maharashtra'),
('Kiran',    'Patil',      '1956-06-22', 'Male',   'B-',  '9800001007', 'kiran.patil@gmail.com',      'Solapur',   'Maharashtra'),
('Anita',    'Verma',      '1988-12-09', 'Female', 'AB+', '9800001008', 'anita.verma@gmail.com',      'Pune',      'Maharashtra'),
('Nikhil',   'Bose',       '2010-04-05', 'Male',   'O+',  '9800001009', 'nikhil.bose@gmail.com',      'Kolkata',   'West Bengal'),
('Preethi',  'Nambiar',    '1973-08-17', 'Female', 'A+',  '9800001010', 'preethi.nambiar@gmail.com',  'Pune',      'Maharashtra'),
('Aryan',    'Kapoor',     '1995-02-28', 'Male',   'B+',  '9800001011', 'aryan.kapoor@gmail.com',     'Delhi',     'Delhi'),
('Sunita',   'Mishra',     '1980-10-11', 'Female', 'O+',  '9800001012', 'sunita.mishra@gmail.com',    'Pune',      'Maharashtra');

-- Appointments
INSERT INTO appointments (patient_id, doctor_id, appointment_date, reason, status, notes) VALUES
(1,  1, '2024-11-05 09:00:00', 'Chest pain and shortness of breath',   'Completed', 'ECG ordered'),
(2,  5, '2024-11-06 10:30:00', 'Fever and cough for 3 days',           'Completed', 'Prescribed antibiotics'),
(3,  2, '2024-11-07 11:00:00', 'Recurring headaches',                  'Completed', 'MRI recommended'),
(4,  3, '2024-11-08 09:30:00', 'Annual pediatric checkup',             'Completed', 'Vaccinations updated'),
(5,  1, '2024-11-10 14:00:00', 'Follow-up for hypertension',           'Completed', 'Medication adjusted'),
(6,  7, '2024-11-12 11:30:00', 'Skin rash on arms',                    'Completed', 'Allergic reaction suspected'),
(7,  4, '2024-11-13 08:00:00', 'Knee pain after fall',                 'Completed', 'X-Ray taken'),
(8,  5, '2024-11-14 15:00:00', 'Diabetes management review',           'Completed', 'HbA1c test ordered'),
(9,  3, '2024-11-15 10:00:00', 'Cold and sore throat',                 'Completed', 'Rest and fluids advised'),
(10, 6, '2024-11-18 13:00:00', 'Breast lump evaluation',               'Completed', 'Biopsy scheduled'),
(11, 8, '2024-11-19 16:00:00', 'Anxiety and sleep disorders',          'Completed', 'CBT sessions recommended'),
(12, 1, '2024-12-01 09:00:00', 'Palpitations',                        'Scheduled', NULL),
(1,  1, '2024-12-10 09:00:00', 'Cardiac follow-up',                   'Scheduled', NULL),
(3,  2, '2024-12-11 11:00:00', 'MRI results review',                  'Scheduled', NULL),
(5,  1, '2024-11-20 14:00:00', 'BP check',                            'No-Show',   NULL);

-- Medical Records
INSERT INTO medical_records (patient_id, doctor_id, visit_date, diagnosis, treatment, prescription, follow_up_date) VALUES
(1,  1, '2024-11-05', 'Hypertensive heart disease',           'Lifestyle changes, medication',    'Amlodipine 5mg',          '2024-12-10'),
(2,  5, '2024-11-06', 'Acute upper respiratory tract infection', 'Rest, hydration, antibiotics', 'Amoxicillin 500mg',       '2024-11-20'),
(3,  2, '2024-11-07', 'Migraine without aura',                'Pain management, triggers diary', 'Sumatriptan 50mg',        '2024-12-11'),
(4,  3, '2024-11-08', 'Healthy child, routine checkup',       'Vaccination administered',         'Vitamin D drops',         NULL),
(5,  1, '2024-11-10', 'Essential hypertension',               'Medication review',                'Losartan 50mg',           '2024-12-01'),
(6,  7, '2024-11-12', 'Contact dermatitis',                   'Topical corticosteroid cream',     'Hydrocortisone 1% cream', '2024-11-26'),
(7,  4, '2024-11-13', 'Knee contusion with minor ligament strain', 'RICE protocol, physiotherapy', 'Ibuprofen 400mg',        '2024-11-27'),
(8,  5, '2024-11-14', 'Type 2 diabetes mellitus',             'Diet control, exercise',           'Metformin 500mg',         '2024-12-14'),
(10, 6, '2024-11-18', 'Breast lump – pending biopsy',         'Biopsy ordered',                   NULL,                      '2024-12-02'),
(11, 8, '2024-11-19', 'Generalised anxiety disorder',         'CBT, relaxation techniques',       'Sertraline 50mg',         '2024-12-03');

-- Medications
INSERT INTO medications (name, generic_name, category, manufacturer, unit_price, stock_quantity) VALUES
('Amlodipine 5mg',         'Amlodipine',    'Calcium Channel Blocker', 'Sun Pharma',     8.50,   500),
('Amoxicillin 500mg',      'Amoxicillin',   'Antibiotic',              'Cipla',          12.00,  800),
('Sumatriptan 50mg',       'Sumatriptan',   'Triptan/Antimigraine',    'GSK',            45.00,  200),
('Losartan 50mg',          'Losartan',      'ARB Antihypertensive',    'Lupin',          15.00,  600),
('Hydrocortisone 1% cream','Hydrocortisone','Topical Corticosteroid',  'Glaxo',          22.00,  300),
('Ibuprofen 400mg',        'Ibuprofen',     'NSAID',                   'Abbott',         6.00,   1000),
('Metformin 500mg',        'Metformin',     'Biguanide Antidiabetic',  'USV',            5.00,   900),
('Sertraline 50mg',        'Sertraline',    'SSRI Antidepressant',     'Pfizer',         30.00,  250),
('Vitamin D 1000IU',       'Cholecalciferol','Vitamin Supplement',     'Mankind Pharma', 4.50,   700),
('Paracetamol 500mg',      'Paracetamol',   'Analgesic/Antipyretic',   'Cipla',          3.00,   1500);

-- Prescriptions
INSERT INTO prescriptions (record_id, medication_id, dosage, frequency, duration_days, instructions) VALUES
(1,  1, '5mg',  'Once daily',   30, 'Take in the morning with water'),
(2,  2, '500mg','Three times daily', 7, 'Complete full course'),
(3,  3, '50mg', 'As needed',    10, 'Take at onset of migraine'),
(4,  9, '1000IU','Once daily',  90, 'Take with food'),
(5,  4, '50mg', 'Once daily',   30, 'Monitor BP weekly'),
(6,  5, 'Apply thin layer','Twice daily', 14, 'Avoid eyes and mucous membranes'),
(7,  6, '400mg','Three times daily', 5, 'Take after food'),
(8,  7, '500mg','Twice daily',  90, 'Take with meals'),
(10, 8, '50mg', 'Once daily',   30, 'Take at bedtime');

-- Billing
INSERT INTO billing (patient_id, appointment_id, total_amount, paid_amount, payment_status, payment_date, insurance_claim) VALUES
(1,  1,  1500.00, 1500.00, 'Paid',    '2024-11-05', TRUE),
(2,  2,   800.00,  800.00, 'Paid',    '2024-11-06', FALSE),
(3,  3,  2000.00, 2000.00, 'Paid',    '2024-11-07', TRUE),
(4,  4,  1200.00, 1200.00, 'Paid',    '2024-11-08', FALSE),
(5,  5,  1000.00,  500.00, 'Partial', NULL,          TRUE),
(6,  6,   900.00,  900.00, 'Paid',    '2024-11-12', FALSE),
(7,  7,  3500.00, 3500.00, 'Paid',    '2024-11-13', TRUE),
(8,  8,  1100.00,    0.00, 'Pending', NULL,          FALSE),
(10, 10, 5000.00, 2500.00, 'Partial', NULL,          TRUE),
(11, 11, 1800.00, 1800.00, 'Paid',    '2024-11-19', FALSE);

-- Lab Tests
INSERT INTO lab_tests (patient_id, doctor_id, test_name, test_date, result, normal_range, status) VALUES
(1,  1, 'ECG',                    '2024-11-05', 'Mild LVH pattern',          'Normal sinus rhythm',   'Completed'),
(3,  2, 'MRI Brain',              '2024-11-10', 'No structural abnormality', 'Normal',                'Completed'),
(5,  1, 'Blood Pressure Monitor', '2024-11-10', '148/92 mmHg',               '< 120/80 mmHg',         'Completed'),
(8,  5, 'HbA1c',                  '2024-11-14', '7.8%',                      '< 5.7% (normal)',       'Completed'),
(8,  5, 'Fasting Blood Glucose',  '2024-11-14', '142 mg/dL',                 '70-100 mg/dL',          'Completed'),
(10, 6, 'Biopsy – Breast Tissue', '2024-11-25', NULL,                         NULL,                   'In Progress'),
(1,  1, 'Lipid Profile',          '2024-11-05', 'LDL: 145 mg/dL',           'LDL < 100 mg/dL',       'Completed'),
(2,  5, 'CBC',                    '2024-11-06', 'WBC 11.2 x10^3/uL',        '4.5–11.0 x10^3/uL',    'Completed');
