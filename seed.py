from app import app, db, User, Medicine
from flask_bcrypt import Bcrypt
from datetime import date, datetime, timedelta

bcrypt = Bcrypt()

def seed_database():
    with app.app_context():
        # Clear existing data to avoid duplicates if rerun
        db.drop_all()
        db.create_all()
        
        print("Creating default system users for KNH...")
        
        # 1. Create Sample Users with Roles
        users = [
            User(username="Albert", email="albert@gmail.com", role="admin",
                 password=bcrypt.generate_password_hash("Albert@123").decode('utf-8')),
                 
            User(username="Minoo", email="minoo@gmail.com", role="receptionist",
                 password=bcrypt.generate_password_hash("Minoo@123").decode('utf-8')),
                 
            User(username="Dr Alb", email="dr.alb@knh.or.ke", role="doctor",
                 password=bcrypt.generate_password_hash("Dralb@123").decode('utf-8')),

            User(username="Nderu", email="nderu@gmail.com", role="doctor",
                 password=bcrypt.generate_password_hash("Nderu@123").decode('utf-8')),
                 
            User(username="nurse_Anne", email="nurse.anne@gmail.com", role="nurse",
                 password=bcrypt.generate_password_hash("Anne@123").decode('utf-8')),
                 
            User(username="Oscar", email="oscar@gmail.com", role="lab_staff",
                 password=bcrypt.generate_password_hash("Oscar@123").decode('utf-8')),
                 
            User(username="pharmacist_Fiona", email="fiona@gmail.com", role="pharmacist",
                 password=bcrypt.generate_password_hash("Fiona@123").decode('utf-8')),
                 
            User(username="accountant_Timothy", email="timothy@gmail.com", role="accountant",
                 password=bcrypt.generate_password_hash("Timothy@123").decode('utf-8'))
        ]
        
        db.session.add_all(users)
        
        print("Populating initial pharmacy inventory...")
        
        # 2. Pre-populate some medicine stock
        medicines = [
            Medicine(name="Paracetamol 500mg", stock_level=1200, unit_price=5.00, 
                     expiry_date=date(2027, 12, 31)),
            Medicine(name="Amoxicillin 500mg", stock_level=450, unit_price=15.50, 
                     expiry_date=date(2027, 6, 30)),
            Medicine(name="Cetirizine 10mg", stock_level=600, unit_price=8.00, 
                     expiry_date=date(2028, 1, 15)),
            Medicine(name="Metformin 500mg", stock_level=300, unit_price=12.00, 
                     expiry_date=date(2026, 11, 20))
        ]
        
        db.session.add_all(medicines)
        
        # Commit to save changes to knh_hospital.db
        db.session.commit()
        print("Database initialized and populated successfully!")

if __name__ == '__main__':
    seed_database()