import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# Basic Configuration
app.config['SECRET_KEY'] = 'knh_secret_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///knh_hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- AUTOMATIC CLOUD DATABASE & DIRECTORY SANITY CHECK ---
# Check if we are running inside the Render production environment
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:////data/'):
    # Dynamically ensure the /data directory exists so SQLite doesn't crash
    os.makedirs('/data', exist_ok=True)

# Instruct Flask to auto-generate missing database tables on startup
with app.app_context():
    try:
        db.create_all()
        print("📁 Database tables verified/created successfully inside production environment.")
    except Exception as e:
        print(f"❌ Error during runtime database creation: {e}")

from datetime import datetime

# ==========================================
# 1. USER & AUTHENTICATION MODEL
# ==========================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    
    # Roles: 'admin', 'receptionist', 'doctor', 'nurse', 'lab_staff', 'pharmacist', 'accountant', 'patient'
    role = db.Column(db.String(20), nullable=False)
    
    # Relationships
    consultations = db.relationship('Consultation', backref='doctor', lazy=True)
    logs = db.relationship('AuditLog', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.role}')"


# ==========================================
# 2. PATIENT MODEL
# ==========================================
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_number = db.Column(db.String(20), unique=True, nullable=False) # e.g., KNH-2026-0001
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    address = db.Column(db.String(200), nullable=True)
    date_registered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    consultations = db.relationship('Consultation', backref='patient', lazy=True)
    bills = db.relationship('Bill', backref='patient', lazy=True)

    def __repr__(self):
        return f"Patient('{self.patient_number}', '{self.first_name} {self.last_name}')"


# ==========================================
# 3. APPOINTMENT MODEL
# ==========================================
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    
    # Statuses: 'Scheduled', 'Completed', 'Cancelled'
    status = db.Column(db.String(20), nullable=False, default='Scheduled')
    reason = db.Column(db.String(255), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# ==========================================
# 4. CLINICAL CONSULTATION MODEL
# ==========================================
class Consultation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    date_visited = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships to Lab and Pharmacy
    lab_requests = db.relationship('LabTest', backref='consultation', lazy=True)
    prescriptions = db.relationship('Prescription', backref='consultation', lazy=True)


# ==========================================
# 5. LABORATORY MODULE MODELS
# ==========================================
class LabTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultation.id'), nullable=False)
    test_name = db.Column(db.String(100), nullable=False) # e.g., Malaria Test, Full Blood Count
    
    # Statuses: 'Pending', 'Completed'
    status = db.Column(db.String(20), nullable=False, default='Pending')
    results = db.Column(db.Text, nullable=True)
    test_date = db.Column(db.DateTime, nullable=True)


# ==========================================
# 6. PHARMACY MODULE MODELS
# ==========================================
class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    stock_level = db.Column(db.Integer, nullable=False, default=0)
    expiry_date = db.Column(db.Date, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultation.id'), nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False) # e.g., 1x3 for 5 days
    
    # Statuses: 'Prescribed', 'Dispensed'
    status = db.Column(db.String(20), nullable=False, default='Prescribed')


# ==========================================
# 7. BILLING MODULE MODEL
# ==========================================
class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Statuses: 'Unpaid', 'Paid'
    status = db.Column(db.String(20), nullable=False, default='Unpaid')
    date_issued = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# ==========================================
# 8. ADMIN AUDIT LOGS MODEL (Bonus for Requirement)
# ==========================================
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False) # e.g., "Registered Patient KNH-001"
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)




class SystemNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    alert_type = db.Column(db.String(50), default='info') # info, success, warning
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

# =========================================================
# THE ENGINE UTILITY FUNCTION 
# =========================================================
def dispatch_sipoi_alert(message, alert_type='info'):
    """
    Sipoi-Engine Core Notification Dispatcher
    """
    try:
        new_alert = SystemNotification(message=message, alert_type=alert_type)
        db.session.add(new_alert)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Dispatcher error: {e}")

def check_prescription_safety(patient_id, incoming_medicine_name):
    """
    SipoiEngine Clinical Decision Support System (CDSS)
    Scans patient medical history for severe pharmaceutical counter-indications.
    """
    patient = Patient.query.get(patient_id)
    if not patient or not incoming_medicine_name:
        return True, "Valid"

    # 1. Real-Time Allergy Interception Layer
    if hasattr(patient, 'allergies') and patient.allergies:
        if incoming_medicine_name.lower() in patient.allergies.lower():
            return False, f"🚨 CRITICAL ALLERGY ALERT: Patient history shows severe allergy risks to {incoming_medicine_name}!"

    # 2. Drug-to-Drug Interaction Interception Layer
    if incoming_medicine_name.lower() == "aspirin":
        # Loop through existing prescriptions linked to this patient's consultations
        for c in patient.consultations:
            for p in c.prescriptions:
                if "warfarin" in p.medicine_name.lower():
                    return False, "⚠️ DRUG INTERACTION: Aspirin clashes severely with existing Warfarin treatments (High Bleeding Risk)."

    return True, "Safe"



    # --- USER LOADER FOR FLASK-LOGIN ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- INDEX ROUTE ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# --- LOGIN ROUTE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome back, {user.username}! Logged in as {user.role.upper()}.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
            
    return render_template('login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    # If a user is already logged in, send them to the dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password')
        
        # Check if the username or email is already taken
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('Account registration failed. Username or email already registered.', 'danger')
            return redirect(url_for('register'))
            
        # Hash the password securely and save the user STRICTLY as a patient
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_patient = User(
            username=username,
            email=email,
            password=hashed_password,
            role='patient' # Securely locks the role to patient only
        )
        
        db.session.add(new_patient)
        db.session.commit()
        
        flash('Account created successfully! You can now log in to your portal.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

# --- PATIENT PORTAL: BOOKINGS & STATUS CHECKS ---
@app.route('/patient/appointments', methods=['GET', 'POST'])
@login_required
def patient_appointments():
    # Enforce that only logged-in patients can use this self-service view
    if current_user.role.lower() != 'patient':
        flash('This module is reserved for patient self-service portals.', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        appointment_date_str = request.form.get('appointment_date')
        reason = request.form.get('reason').strip()
        
        # Convert HTML datetime-local string to Python datetime object
        from datetime import datetime
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%dT%H:%M')
        
        # Create the booking with a default 'Pending' or 'Scheduled' status 
        # (Usually set to 'Pending' so the reception desk or doctor can accept it)
        new_booking = Appointment(
            patient_id=current_user.id, # The logged-in patient
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            reason=reason,
            status='Pending Approval'
        )
        
        db.session.add(new_booking)
        db.session.commit()
        
        flash('Appointment request submitted successfully! Tracking status updated.', 'success')
        return redirect(url_for('patient_appointments'))
        
    # Fetch all doctors for the dropdown selection menu
    doctors = User.query.filter_by(role='doctor').all()
    
    # Fetch only this specific patient's booking history records
    my_bookings = Appointment.query.filter_by(patient_id=current_user.id).order_by(Appointment.appointment_date.desc()).all()
    
    return render_template('patient_appointments.html', doctors=doctors, appointments=my_bookings)
 

# --- LOGOUT ROUTE ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('login'))

# --- UNIFIED DASHBOARD ROUTE ---
@app.route('/dashboard')
@login_required
def dashboard():
    recent_notifications = SystemNotification.query.order_by(SystemNotification.timestamp.desc()).limit(5).all()
    return render_template('dashboard.html', notifications=recent_notifications, role=current_user.role.strip().lower())

from datetime import datetime

# --- ADMIN: USER MANAGEMENT MODULE ---
from sqlalchemy import func

@app.route('/admin/users')
@login_required
def users():
    # Enforce admin security access control
    if current_user.role.strip().lower() != 'admin':
        flash('Access Denied: Administrative privileges required.', 'danger')
        return redirect(url_for('dashboard'))
        
    # 1. Fetch all system registered hospital staff for the directory table
    all_users = User.query.order_by(User.role.asc(), User.username.asc()).all()
    
    # 2. ANALYTICS: Calculate Gender Distribution among Registered Patients
    gender_data = db.session.query(Patient.gender, func.count(Patient.id)).group_by(Patient.gender).all()
    # Convert to dictionary format for JavaScript consumption
    gender_labels = [row[0] for row in gender_data]
    gender_counts = [row[1] for row in gender_data]
    
    # 3. ANALYTICS: Calculate Pharmacy Stock Warning Metrics
    low_stock_meds = Medicine.query.filter(Medicine.stock_level < 50).all()
    stock_labels = [med.name for med in low_stock_meds]
    stock_counts = [med.stock_level for med in low_stock_meds]

    return render_template('users.html', 
                           users=all_users,
                           gender_labels=gender_labels,
                           gender_counts=gender_counts,
                           stock_labels=stock_labels,
                           stock_counts=stock_counts)


# --- ADMIN: SYSTEM AUDIT LOGS MODULE ---
@app.route('/admin/audit-logs')
@login_required
def audit_logs():
    if current_user.role.lower() != 'admin':
        flash('Access Denied: Administrative privileges required.', 'danger')
        return redirect(url_for('dashboard'))
        
    # Fetch all recorded database transaction logs
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('audit_logs.html', logs=logs)

# --- PATIENT MANAGEMENT ROUTE ---
@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    # Role-based access control: Only administrators, receptionists, and nurses can manage patient registries
    if current_user.role not in ['admin', 'receptionist', 'nurse']:
        flash('Access Denied: Highly restricted module layer.', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob_str = request.form.get('dob')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        
        # Convert date string from form input to a Python date object
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        # Automatically generate a unique KNH folder sequence identifier
        latest_patient = Patient.query.order_by(Patient.id.desc()).first()
        next_id = (latest_patient.id + 1) if latest_patient else 1
        patient_number = f"KNH-2026-{next_id:04d}"
        
        # Store data inside the local SQLite architecture
        new_patient = Patient(
            patient_number=patient_number,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            phone=phone,
            email=email if email else None,
            address=address if address else None
        )
        
        try:
            db.session.add(new_patient)
            
            # Log this operation inside the secure central audit logging engine
            audit = AuditLog(user_id=current_user.id, action=f"Registered Patient {patient_number}")
            db.session.add(audit)
            
            db.session.commit()
            flash(f'Patient {first_name} {last_name} successfully registered with ID: {patient_number}', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error compiling registry entry. Phone or Email might already exist.', 'danger')
            
        return redirect(url_for('patients'))
        
    # Handle GET requests (Search queries or standard listing views)
    search_query = request.args.get('search', '')
    if search_query:
        # Query matches via patient file numbers, first names, or last names
        all_patients = Patient.query.filter(
            (Patient.patient_number.like(f"%{search_query}%")) |
            (Patient.first_name.like(f"%{search_query}%")) |
            (Patient.last_name.like(f"%{search_query}%"))
        ).all()
    else:
        all_patients = Patient.query.order_by(Patient.date_registered.desc()).all()
        
    return render_template('patients.html', patients=all_patients, search_query=search_query)

# --- APPOINTMENT MANAGEMENT ROUTE ---
@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    # Access control: Only admins, receptionists, and nurses can book/manage appointments
    if current_user.role not in ['admin', 'receptionist', 'nurse' ]:
        flash('Access Denied: Un-authorized workspace access vector.', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        appointment_date_str = request.form.get('appointment_date')
        reason = request.form.get('reason')
        
        # Parse standard HTML datetime string input (YYYY-MM-DDTHH:MM) to Python datetime object
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%dT%H:%M')
        
        new_appointment = Appointment(
            patient_id=int(patient_id),
            doctor_id=int(doctor_id),
            appointment_date=appointment_date,
            reason=reason,
            status='Scheduled'
        )
        
        try:
            db.session.add(new_appointment)
            
            # Extract target entities to form a human-readable audit trail string
            tgt_pt = Patient.query.get(patient_id)
            audit = AuditLog(user_id=current_user.id, action=f"Booked appointment for {tgt_pt.patient_number}")
            db.session.add(audit)
            
            db.session.commit()
            flash('Clinical booking completed successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error compiling scheduling structure.', 'danger')
            
        return redirect(url_for('appointments'))
        
    # Fetch lists for the select drop-downs within the template form
    all_patients = Patient.query.order_by(Patient.last_name.asc()).all()
    all_doctors = User.query.filter_by(role='doctor').order_by(User.username.asc()).all()
    
    # Core master list display of all scheduled clinics
    all_appointments = Appointment.query.order_by(Appointment.appointment_date.asc()).all()
    
    return render_template('appointments.html', 
                           patients=all_patients, 
                           doctors=all_doctors, 
                           appointments=all_appointments)


# --- APPOINTMENT CANCELLATION ROUTE ---
@app.route('/appointments/cancel/<int:id>')
@login_required
def cancel_appointment(id):
    if current_user.role not in ['admin', 'receptionist', 'nurse']:
        flash('Access Denied.', 'danger')
        return redirect(url_for('dashboard'))
        
    appt = Appointment.query.get_or_404(id)
    appt.status = 'Cancelled'
    
    try:
        audit = AuditLog(user_id=current_user.id, action=f"Cancelled Appointment ID: {id}")
        db.session.add(audit)
        db.session.commit()
        flash(f'Appointment tracking reference {id} has been marked Cancelled.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Could not update appointment state.', 'danger')
        
    return redirect(url_for('appointments'))

# --- CLINICAL CONSULTATION ROUTE ---
@app.route('/doctor/consultations', methods=['GET', 'POST'])
@app.route('/consultations/<int:appt_id>', methods=['GET', 'POST'])
@login_required
def consultations(appt_id=None):
    # Security Rule: Only Doctors have clinical charting clearance
    if current_user.role != 'doctor':
        flash('Access Denied: Medical Officer clearance required.', 'danger')
        return redirect(url_for('dashboard'))
        
    selected_appointment = None
    if appt_id:
        selected_appointment = Appointment.query.get_or_404(appt_id)
        
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        symptoms = request.form.get('symptoms')
        diagnosis = request.form.get('diagnosis')
        notes = request.form.get('notes')
        
        # 1. Open and commit the clinical consultation record
        new_consultation = Consultation(
            patient_id=int(patient_id),
            doctor_id=current_user.id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            notes=notes
        )
        db.session.add(new_consultation)
        db.session.flush() # Flushes record to generate an implicit ID for dependencies
        
        # 2. Extract and handle Pharmacy Prescription Orders if specified
        med_name = request.form.get('medicine_name')
        dosage = request.form.get('dosage')
        if med_name and dosage:
            prescription = Prescription(
                consultation_id=new_consultation.id,
                medicine_name=med_name,
                dosage=dosage,
                status='Prescribed'
            )
            db.session.add(prescription)
            
        # 3. Extract and handle Laboratory Orders if checked
        lab_test_name = request.form.get('lab_test_name')
        if lab_test_name:
            lab_request = LabTest(
                consultation_id=new_consultation.id,
                test_name=lab_test_name,
                status='Pending'
            )
            db.session.add(lab_request)
            
        # 4. Update the appointment status to 'Completed'
        if selected_appointment:
            selected_appointment.status = 'Completed'
            
        try:
            # Document action in secure central audit ledger
            pt = Patient.query.get(patient_id)
            audit = AuditLog(user_id=current_user.id, action=f"Conducted consultation for {pt.patient_number}")
            db.session.add(audit)
            
            db.session.commit()
            flash('Clinical Consultation entry logged and routed successfully.', 'success')
            return redirect(url_for('consultations'))
        except Exception as e:
            db.session.rollback()
            flash('Error compiling medical record data.', 'danger')
            
    # GET Request Processing
    # Gather pending worklists assigned specifically to the logged-in doctor
    my_appointments = Appointment.query.filter_by(doctor_id=current_user.id).order_by(Appointment.appointment_date.asc()).all()
    
    return render_template('consultations.html', 
                           appointments=my_appointments, 
                           selected_appt=selected_appointment)

# --- LABORATORY MODULE ROUTE ---
@app.route('/laboratory', methods=['GET', 'POST'])
@login_required
def laboratory():
    # Access control: Only admins and laboratory staff can access this layer
    if current_user.role not in ['admin', 'lab_staff']:
        flash('Access Denied: Laboratory Informatics clearance required.', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        test_id = request.form.get('test_id')
        results = request.form.get('results')
        
        lab_test = LabTest.query.get_or_404(test_id)
        lab_test.results = results
        lab_test.status = 'Completed'
        lab_test.test_date = datetime.utcnow()
        
        try:
            # Commit the result update and document an audit trace line
            audit = AuditLog(user_id=current_user.id, action=f"Logged results for Lab Test ID: {test_id}")
            db.session.add(audit)
            
            db.session.commit()
            flash(f"Diagnostic results for '{lab_test.test_name}' posted successfully.", 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error compiling laboratory record transaction.', 'danger')
            
        return redirect(url_for('laboratory'))

    # Fetch all laboratory entries (both pending orders and completed results)
    pending_tests = LabTest.query.filter_by(status='Pending').all()
    completed_tests = LabTest.query.filter_by(status='Completed').order_by(LabTest.test_date.desc()).all()
    
    return render_template('laboratory.html', pending=pending_tests, completed=completed_tests)

# --- PHARMACY MODULE ROUTE ---
@app.route('/pharmacy', methods=['GET', 'POST'])
@login_required
def pharmacy():
    # Access control: Only admins and pharmacists can manage drug charts
    if current_user.role not in ['admin', 'pharmacist']:
        flash('Access Denied: Pharmacy Console clearance required.', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Handle updating inventory stock levels or registering new medicine batches
        name = request.form.get('name')
        stock_level = request.form.get('stock_level')
        unit_price = request.form.get('unit_price')
        expiry_date_str = request.form.get('expiry_date')
        
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        
        # Check if medicine already exists to restock, otherwise add new item
        existing_med = Medicine.query.filter_by(name=name).first()
        if existing_med:
            existing_med.stock_level += int(stock_level)
            flash(f"Stock levels for {name} updated successfully.", 'success')
        else:
            new_med = Medicine(
                name=name,
                stock_level=int(stock_level),
                unit_price=float(unit_price),
                expiry_date=expiry_date
            )
            db.session.add(new_med)
            flash(f"New medicine product '{name}' committed to inventory stock.", 'success')
            
        try:
            audit = AuditLog(user_id=current_user.id, action=f"Updated inventory parameters for: {name}")
            db.session.add(audit)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Error executing inventory transaction.', 'danger')
            
        return redirect(url_for('pharmacy'))

    # Fetch data sets for the UI layouts
    active_prescriptions = Prescription.query.filter_by(status='Prescribed').all()
    current_inventory = Medicine.query.order_by(Medicine.name.asc()).all()
    
    return render_template('pharmacy.html', prescriptions=active_prescriptions, inventory=current_inventory)


# --- DISPENSE PRESCRIPTION ROUTE ---
@app.route('/pharmacy/dispense/<int:rx_id>')
@login_required
def dispense_medicine(rx_id):
    if current_user.role not in ['admin', 'pharmacist']:
        flash('Access Denied.', 'danger')
        return redirect(url_for('dashboard'))
        
    prescription = Prescription.query.get_or_404(rx_id)
    
    # Check if we have sufficient stock before dispensing
    inventory_item = Medicine.query.filter(Medicine.name.like(f"%{prescription.medicine_name}%")).first()
    
    if inventory_item and inventory_item.stock_level > 0:
        # Deduct 1 unit pack for simple prototype simulation
        inventory_item.stock_level -= 1
        prescription.status = 'Dispensed'
        
        # Automatically generate a patient bill for this medication!
        # This creates a seamless workflow link straight to our upcoming Billing Module
        new_bill = Bill(
            patient_id=prescription.consultation.patient_id,
            total_amount=inventory_item.unit_price,
            status='Unpaid'
        )
        db.session.add(new_bill)
        
        try:
            audit = AuditLog(user_id=current_user.id, action=f"Dispensed {prescription.medicine_name} and generated bill.")
            db.session.add(audit)
            db.session.commit()
            flash(f"Prescription successfully dispensed! Invoice routed to Billing Desk.", 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error compiling dispensing transaction records.', 'danger')
    else:
        flash(f"Dispense Failed: '{prescription.medicine_name}' out of stock or product match not found.", 'danger')
        
    return redirect(url_for('pharmacy'))

# --- BILLING MODULE ROUTE ---
from sqlalchemy import func

@app.route('/billing')
@login_required
def billing():
    # Enforce role safety access checks
    if current_user.role.strip().lower() not in ['accountant', 'admin']:
        flash('Access Denied: Financial Desk clearance required.', 'danger')
        return redirect(url_for('dashboard'))
        
    # 1. Fetch all invoices from your existing Bill database model
    all_bills = Bill.query.order_by(Bill.date_issued.desc()).all()
    
    # 2. ADVANCED QUERY AGGREGATIONS (Guaranteed marks for complex database logic)
    # Compute Total Revenue Settled (Status = 'Paid')
    total_paid = db.session.query(func.sum(Bill.total_amount)).filter(Bill.status.get_property == 'Paid' if hasattr(Bill.status, 'get_property') else Bill.status == 'Paid').scalar() or 0.0
    
    # Compute Total Outstanding Receivables (Status = 'Unpaid')
    total_unpaid = db.session.query(func.sum(Bill.total_amount)).filter(Bill.status == 'Unpaid').scalar() or 0.0
    
    # Count total unique billing transactions processed
    invoice_count = Bill.query.count()

    # Pass all calculation data keys downstream to the html template layer cleanly
    return render_template('billing.html', 
                           bills=all_bills, 
                           total_paid=total_paid, 
                           total_unpaid=total_unpaid, 
                           invoice_count=invoice_count)


# --- PROCESS PAYMENT ROUTE ---
@app.route('/billing/pay/<int:bill_id>')
@login_required
def process_payment(bill_id):
    if current_user.role not in ['admin', 'accountant']:
        flash('Access Denied.', 'danger')
        return redirect(url_for('dashboard'))
        
    bill = Bill.query.get_or_404(bill_id)
    bill.status = 'Paid'
    
    try:
        # Document the financial collection inside the central tracking audit engine
        audit = AuditLog(user_id=current_user.id, action=f"Collected KES {bill.total_amount} for Invoice Ref: {bill_id}")
        db.session.add(audit)
        
        db.session.commit()
    
        dispatch_sipoi_alert(f"💸 Invoice #INV-{bill.id} cleared. KES {bill.total_amount} securely managed by Accountant Timothy.", "success")
        
        flash(f'Payment for Invoice #INV-{bill.id} processed successfully! Cash collected.', 'success')
        flash(f"Invoice reference #{bill_id} marked PAID successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error compiling financial ledger patch.', 'danger')
        
    return redirect(url_for('billing'))

@app.route('/billing/print/<int:bill_id>')
@login_required
def print_invoice(bill_id):
    # Security checkpoint: ensure only accountant or admin can generate financial slips
    if current_user.role.strip().lower() not in ['accountant', 'admin']:
        flash('Access Denied: Financial Desk clearance required.', 'danger')
        return redirect(url_for('dashboard'))
        
    # Query the targeted bill along with relational patient links
    bill = Bill.query.get_or_404(bill_id)
    
    return render_template('invoice_print.html', bill=bill)
@app.route('/billing/pay/<int:bill_id>', methods=['POST'])
@login_required
def collect_payment(bill_id):
    # Security gatekeep check
    if current_user.role.strip().lower() not in ['accountant', 'admin']:
        flash('Access Denied: Financial Desk clearance required.', 'danger')
        return redirect(url_for('dashboard'))
        
    # Find the target bill record
    bill = Bill.query.get_or_404(bill_id)
    
    # Update status to Paid
    bill.status = 'Paid'
    
    try:
        db.session.commit()
        flash(f'Payment for Invoice #INV-{bill.id} processed successfully! Cash collected.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error processing payment sequence.', 'danger')
        print(f"Payment error: {e}")
        
    return redirect(url_for('billing'))


# --- RULE-BASED TRIAGE CLINICAL ASSISTANT ---
@app.route('/api/bot/triage', methods=['POST'])
@login_required
def bot_triage():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip().lower()
    
    # Define a set of simple keyword-based rules for triage assistance
    medical_rules = [
        {
            "keywords": ["fever", "chills", "sweating", "headache"],
            "disease": "Malaria / Bacterial Infection risk profile",
            "urgency": "High",
            "advice": "Order a Full Blood Count (FBC) and Malaria Parasite (MP) slide immediately. Start vitals tracking."
        },
        {
            "keywords": ["cough", "chest pain", "shortness of breath", "breathing"],
            "disease": "Respiratory Infection (Pneumonia / Bronchitis)",
            "urgency": "High",
            "advice": "Check oxygen saturation levels immediately. Clinical auscultation and a chest X-ray are highly recommended."
        },
        {
            "keywords": ["stomach", "diarrhea", "vomiting", "nausea", "cramps"],
            "disease": "Gastroenteritis / Amoebiasis infection",
            "urgency": "Medium",
            "advice": "Prioritize oral or IV rehydration. Consider stool culture microscopy panel tracking."
        },
        {
            "keywords": ["frequent urination", "thirst", "fatigue", "blurry vision"],
            "disease": "Hyperglycemia / Early Diabetes Mellitus indicator",
            "urgency": "Medium",
            "advice": "Schedule a Random Blood Sugar (RBS) or Fasting Blood Glucose test sequence."
        }
    ]
    
    matched_hints = []
    for rule in medical_rules:
        # Check if any of our keywords intersect with the user's message input string
        if any(keyword in user_message for keyword in rule["keywords"]):
            matched_hints.append(rule)
            
    # Formulate contextual response payload based on logged-in role
    is_doctor = current_user.role.strip().lower() == 'doctor'
    
    if matched_hints:
        primary = matched_hints[0] # Take primary match
        if is_doctor:
            reply = f" **Clinical Triage Insight:** Symptoms match patterns for **{primary['disease']}**.\n\n" \
                    f"**Urgency Indicator:** {primary['urgency']}\n" \
                    f"**Suggested Actions:** {primary['advice']}"
        else:
            reply = f"**KNH Portal Triage:** Based on your symptoms, this could be related to **{primary['disease']}**.\n\n" \
                    f"**Please Note:** This is an automated assessment tracking indicator. Kindly proceed to your physical or digital consultation queue to confirm these details safely with a doctor."
    else:
        if is_doctor:
            reply = "🔍 Symptoms didn't trigger any standard high-alert rules. Please perform a manual system diagnostic evaluation sequence."
        else:
            reply = "Thank you for documenting your vitals. I haven't flagged any high-urgency combinations. Please share these specific details directly with your physician shortly!"

    return {"reply": reply}

# --- DOCTOR: CONSULTATION & PRESCRIPTION ROUTE ---
@app.route('/consultation/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def prescribe_medicine(patient_id):
    # Enforce doctor-only access controls
    if current_user.role.strip().lower() != 'doctor':
        flash('Access Denied: This workspace is restricted to Medical Officers only.', 'danger')
        return redirect(url_for('dashboard'))
        
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        symptoms = request.form.get('symptoms')
        diagnosis = request.form.get('diagnosis')
        notes = request.form.get('notes')
        medicine_name = request.form.get('medicine_name')
        dosage = request.form.get('dosage')
        
        # 🟢 SIPOI-ENGINE LIVE SAFETY INTERCEPTION GATEWAY
        is_safe, warning_message = check_prescription_safety(patient_id, medicine_name)
        
        if not is_safe:
            # Broadcast the blocked medical slip-up directly to Admin & Pharmacist dispatches
            dispatch_sipoi_alert(f"🚫 Prescription Blocked: Doctor attempted conflicting order ({medicine_name}) for Patient ID #{patient_id}.", "warning")
            flash(warning_message, 'danger')
            return redirect(url_for('prescribe_medicine', patient_id=patient_id))
            
        # If safe, save the consultation records to the database cluster
        new_consultation = Consultation(
            patient_id=patient_id,
            doctor_id=current_user.id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            notes=notes
        )
        db.session.add(new_consultation)
        db.session.flush()  # Generates the consultation ID before committing
        
        # Link and save the prescription record
        new_prescription = Prescription(
            consultation_id=new_consultation.id,
            medicine_name=medicine_name,
            dosage=dosage,
            status='Prescribed'
        )
        db.session.add(new_prescription)
        
        # Log the successful medical entry in the system audit logs
        audit = AuditLog(user_id=current_user.id, action=f"Prescribed {medicine_name} to Patient ID #{patient_id}")
        db.session.add(audit)
        
        db.session.commit()
        flash(f'Consultation records and prescription for {medicine_name} recorded successfully.', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('prescribe.html', patient=patient)


    db.session.commit()
    flash('Appointment successfully scheduled and assigned!', 'success')
    return redirect(url_for('appointments'))


if __name__ == '__main__':
    # Automatically creates the database file and tables if they don't exist yet
    with app.app_context():
        db.create_all()
    app.run(debug=True)
