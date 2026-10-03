
# Hostel Management System (Flask) - Simple CRUD

This is a simple Hostel Management System built with **Flask** and **SQLite**.
Beautiful UI uses **Bootstrap 5** and a small custom CSS file.

## Features
- Admin login (default user: `admin`, password: `admin123`)
- Student CRUD (Create / Read / Update / Delete)
- Room management (list rooms, allocate/vacate)
- SQLite database (file created automatically)
- Single-file Flask app for simplicity + templates + static assets

## How to run (macOS)
1. Make sure Python 3.8+ is installed.
2. Open Terminal in the extracted project folder.
3. (Recommended) Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the app:
   ```bash
   python app.py
   ```
6. Open http://127.0.0.1:5000 in your browser.

The first time the app runs it will create `hostel.db` with a default admin:
- username: `admin`
- password: `admin123`

## Notes
- This project is intentionally simple for learning and quick deployment.
- For production, use proper user management, password policies, and a production WSGI server.
