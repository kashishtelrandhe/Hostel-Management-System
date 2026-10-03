
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'hostel.db')

app = Flask(__name__)
app.secret_key = 'change_this_secret_for_production'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    if not os.path.exists(DB_PATH):
        db = sqlite3.connect(DB_PATH)
        c = db.cursor()
        c.executescript('''
        CREATE TABLE admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_no TEXT UNIQUE NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 1,
            occupied INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            room_id INTEGER,
            join_date TEXT,
            status TEXT DEFAULT 'active',
            FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE SET NULL
        );
        ''')
        # default admin (password: admin123)
        from werkzeug.security import generate_password_hash
        pw = generate_password_hash('admin123')
        c.execute('INSERT INTO admin (username, password) VALUES (?,?)', ('admin', pw))
        # seed rooms
        rooms = [('A-101',2,0),('A-102',2,0),('B-201',3,0),('B-202',1,0)]
        for r in rooms:
            c.execute('INSERT INTO rooms (room_no, capacity, occupied) VALUES (?,?,?)', r)
        db.commit()
        db.close()


@app.before_request
def before_request():
    # Initialize DB only once (safe check)
    if not hasattr(app, 'db_initialized'):
        init_db()
        app.db_initialized = True

# ----- Auth helpers -----
def is_logged_in():
    return session.get('admin_id') is not None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated

# ----- Routes -----
@app.route('/')
def home():
    return redirect(url_for('students'))

@app.route('/login', methods=['GET','POST'])
def login():
    if is_logged_in():
        return redirect(url_for('students'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        db = get_db()
        cur = db.execute('SELECT * FROM admin WHERE username = ?', (username,))
        admin = cur.fetchone()
        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']
            session['admin_user'] = admin['username']
            flash('Logged in successfully.', 'success')
            nxt = request.args.get('next') or url_for('students')
            return redirect(nxt)
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

# ----- Students CRUD -----
@app.route('/students')
@login_required
def students():
    db = get_db()
    cur = db.execute('''
        SELECT s.*, r.room_no FROM students s
        LEFT JOIN rooms r ON s.room_id = r.id
        ORDER BY s.id DESC
    ''')
    rows = cur.fetchall()
    return render_template('students/list.html', students=rows)

@app.route('/students/add', methods=['GET','POST'])
@login_required
def add_student():
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip()
        phone = request.form.get('phone','').strip()
        room_id = request.form.get('room_id') or None
        jd = date.today().isoformat()
        db.execute('INSERT INTO students (name,email,phone,room_id,join_date) VALUES (?,?,?,?,?)', (name,email,phone, room_id, jd))
        if room_id:
            db.execute('UPDATE rooms SET occupied = occupied + 1 WHERE id = ?', (room_id,))
        db.commit()
        flash('Student added.', 'success')
        return redirect(url_for('students'))
    rooms = db.execute('SELECT * FROM rooms').fetchall()
    return render_template('students/add.html', rooms=rooms)

@app.route('/students/edit/<int:sid>', methods=['GET','POST'])
@login_required
def edit_student(sid):
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE id = ?', (sid,)).fetchone()
    if not student:
        flash('Student not found.', 'warning')
        return redirect(url_for('students'))
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip()
        phone = request.form.get('phone','').strip()
        new_room = request.form.get('room_id') or None
        old_room = student['room_id']
        db.execute('UPDATE students SET name=?,email=?,phone=?,room_id=? WHERE id=?', (name,email,phone,new_room,sid))
        # adjust room occupancy
        if old_room != new_room:
            if old_room:
                db.execute('UPDATE rooms SET occupied = occupied - 1 WHERE id = ?', (old_room,))
            if new_room:
                db.execute('UPDATE rooms SET occupied = occupied + 1 WHERE id = ?', (new_room,))
        db.commit()
        flash('Student updated.', 'success')
        return redirect(url_for('students'))
    rooms = db.execute('SELECT * FROM rooms').fetchall()
    return render_template('students/edit.html', student=student, rooms=rooms)

@app.route('/students/delete/<int:sid>', methods=['POST'])
@login_required
def delete_student(sid):
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE id = ?', (sid,)).fetchone()
    if student:
        if student['room_id']:
            db.execute('UPDATE rooms SET occupied = occupied - 1 WHERE id = ?', (student['room_id'],))
        db.execute('DELETE FROM students WHERE id = ?', (sid,))
        db.commit()
        flash('Student deleted.', 'info')
    return redirect(url_for('students'))

# ----- Rooms -----
@app.route('/rooms')
@login_required
def rooms():
    db = get_db()
    rows = db.execute('SELECT * FROM rooms ORDER BY room_no').fetchall()
    return render_template('rooms/list.html', rooms=rows)

@app.route('/rooms/add', methods=['GET','POST'])
@login_required
def add_room():
    db = get_db()
    if request.method == 'POST':
        room_no = request.form.get('room_no','').strip()
        capacity = int(request.form.get('capacity') or 1)
        db.execute('INSERT INTO rooms (room_no, capacity, occupied) VALUES (?,?,0)', (room_no, capacity))
        db.commit()
        flash('Room added.', 'success')
        return redirect(url_for('rooms'))
    return render_template('rooms/add.html')

@app.route('/rooms/vacate/<int:rid>', methods=['POST'])
@login_required
def vacate_room(rid):
    db = get_db()
    # set students in this room to NULL and update occupied to 0
    db.execute('UPDATE students SET room_id = NULL, status = "vacated" WHERE room_id = ?', (rid,))
    db.execute('UPDATE rooms SET occupied = 0 WHERE id = ?', (rid,))
    db.commit()
    flash('Room vacated and students marked vacated.', 'info')
    return redirect(url_for('rooms'))

if __name__ == '__main__':
    app.run(debug=True)
