# Trip Management System 🧳

A **Flask + MySQL** based web application designed for managing trips, bookings, and payments.  
This project was developed as part of the Micro Project as academic requirement.

---

## 🚀 Features
- 🔐 **User Authentication** – Registration, login, and secure session handling  
- 🏝️ **Trip & Destination Management** – Add, view, and explore trips  
- 📅 **Booking System** – Reserve trips with real-time calculation of total cost  
- 💳 **Payment Integration** – Dummy payment workflow  
- 📝 **Feedback Module** – Users can submit reviews and feedback  
- 📊 **Admin Panel** – Manage users, bookings, and trips  

---

## 🛠️ Tech Stack
- **Backend**: Flask (Python)  
- **Frontend**: HTML, CSS, Bootstrap, Jinja2 Templates  
- **Database**: MySQL  
- **Version Control**: Git & GitHub  

---

## 📂 Project Structure

trip-management-system/
│── app.py # Main Flask application
│── templates/ # HTML templates (Jinja2)
│── static/ # CSS, JS, Images
│── model.py # Database helper file (if used)
│── requirements.txt # Python dependencies
│── trip.sql # Database schema and seed data

## ⚙️ Installation & Setup

Follow these steps to set up and run the Trip Management System on your local machine:

### 1️⃣ Clone the Repository

git clone https://github.com/<your-username>/trip-management-system.git
cd trip-management-system

2️⃣ Create & Activate Virtual Environment (Recommended)

### Create virtual environment
python -m venv venv

### Activate it
venv\Scripts\activate      # For Windows
source venv/bin/activate   # For Mac/Linux

3️⃣ Install Project Dependencies

pip install -r requirements.txt

4️⃣ Configure the Database

Ensure MySQL server is running.

Create a new database:
CREATE DATABASE trip;
Import schema:
mysql -u root -p trip < trip.sql
Update your database credentials in app.py if necessary.

5️⃣ Run the Application

python app.py,
The application will start on 👉 http://127.0.0.1:5000

License

This project is for educational purposes only.
