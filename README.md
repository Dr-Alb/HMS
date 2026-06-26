# Kenyatta National Hospital - Management System Prototype (KNH-HMS)

A responsive, multi-role hospital management web application developed as an academic project for the Business Information Technology curriculum. This platform models realistic hospital workflows, transitioning a patient from self-registration to administrative scheduling, clinical documentation, safe prescription fulfillment, and financial clearance.

The core distinguishing feature of this system is the **SipoiEngine Gateway**, an embedded Clinical Decision Support System (CDSS) layer designed to catch and intercept hazardous drug-to-drug interactions and critical patient allergies before records are committed to the database.

---

## 🚀 System Architecture & Workflows

The application coordinates data and operations across five distinct user roles, ensuring secure segregation of duties:

1. **Patients:** Register for accounts, update medical backgrounds, request outpatient clinic slots, and view live status tracking of their booking lifecycle.
2. **Receptionists / Nurses:** Monitor incoming patient registration lines, manage resource availability, and formally confirm `Pending Approval` bookings into active `Scheduled` slots.
3. **Medical Officers (Doctors):** Review historical patient trends, document symptoms, input diagnoses, and issue prescriptions via a dedicated consultation interface.
4. **Pharmacists:** Process pending medical orders, manage live pharmaceutical stock levels, and securely execute inventory deductions.
5. **Accountants / Admin:** Access a comprehensive telemetry panel to monitor live system logs, track billing transactions, and review intercepted medical alert data.

---

## 🛠️ Tech Stack & Dependencies

* **Backend Framework:** Python 3.x / Flask
* **Database Layer:** SQLAlchemy ORM with an atomic SQLite instance
* **Session Management:** Flask-Login (Secure role-based access control tokens)
* **Security & Hashing:** Flask-Bcrypt (Blowfish password-hashing algorithm)
* **Frontend Interface:** HTML5, CSS3 (Custom Glassmorphism styling), Bootstrap 5 Grid System

---

## 🛡️ Key Feature Spotlight: The SipoiEngine Safety Gateway

To prevent administrative blindspots and medical errors, the system features an interception gateway in the backend prescription route:
* **Allergy Intercept:** If a doctor types a medication that matches an allergy keyword flagged in the patient's medical file (e.g., *Penicillin*), the backend freezes the execution context.
* **Drug Interaction Guard:** The engine evaluates current orders against the patient's active prescription history (e.g., blocking an *Aspirin* order if the patient is currently taking *Warfarin* due to high hemorrhage risks).
* **Telemetry Broadcast:** Blocked prescription errors don't just fail silently; they generate an instant alert log pushed directly to the Admin and Pharmacist tracking dashboards.

---

## 📁 Repository Structure

text
├── app.py                  # Main Flask application, routes, and database models
├── seed.py                 # Database seeding script for default roles and inventory
├── requirements.txt        # Python package dependencies for cloud deployment
├── static/                 # CSS stylesheets, assets, and custom design layouts
└── templates/              # Jinja2 HTML layout components
    ├── base.html           # Core application wrapper and navbar structures
    ├── login.html          # Custom frosted-glass access portal
    ├── appointments.html   # Receptionist booking management log
    ├── prescribe.html      # Doctor's clinical workspace
    └── dashboard.html      # Role-specific telemetry and summary data grids


## ⚙️ Local Installation & Setup
Follow these steps to run the environment locally on your development machine:
 1. **Clone the repository:**
   bash
   git clone [https://github.com/Dr-Alb/HMS.git](https://github.com/Dr-Alb/HMS.git)
   cd knh-hms-prototype
   
   
 2. **Establish a virtual environment:**
   bash
   python -m venv venv
   # On Windows activation:
   venv\Scripts\activate
   # On macOS/Linux activation:
   source venv/bin/activate
   
   
 3. **Install required application packages:**
   bash
   pip install -r requirements.txt
   
   
 4. **Initialize and Seed the Database:**
   Run the seeding script to compile your local database file and create default administrative, clinical, and stock variables:
   bash
   python seed.py
   
   
 5. **Execute the local development server:**
   bash
   python app.py
   
   
   Open your browser and navigate to http://127.0.0.1:5000/
## 📱 Responsiveness Optimization
The user interface utilizes a **Mobile-First Responsive Grid Paradigm**. Recognizing that medical personnel interact with systems using tablet computers during ward rounds while administrative staff use large desktop terminals, all core data logs feature managed horizontal overflow swipe states (table-responsive) and dynamic breakpoints (col-12 col-lg-*). This preserves readable text ratios and form alignment from 360px up to full desktop displays.
## 📝 Academic Disclaimer
This system was built exclusively as a functional software prototype for academic evaluation, research, and presentation purposes.
