
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rental_phase2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    transmission = db.Column(db.String(50), nullable=False)
    price_per_day = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255), nullable=False)
    available = db.Column(db.Boolean, default=True)
    bookings = db.relationship('Booking', backref='car', lazy=True, cascade='all, delete-orphan')

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    pickup_location = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='confirmed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def seed_admin():
    if not User.query.filter_by(email='admin@rentalx.com').first():
        admin = User(
            name='Admin User',
            email='admin@rentalx.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

def seed_cars():
    if Car.query.count() == 0:
        cars = [

            # ✅ SUV (matches white SUV)
            Car(
                name='Luxury SUV',
                category='SUV',
                seats=7,
                transmission='Automatic',
                price_per_day=5000,
                image='https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=1200&q=80'
            ),

            # ✅ Hatchback
            Car(
                name='Compact Hatchback',
                category='Hatchback',
                seats=5,
                transmission='Manual',
                price_per_day=2000,
                image='https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?q=80&w=1200&auto=format&fit=crop'
            ),

            # ✅ Electric sedan (matches red car)
            Car(
                name='Electric City Car',
                category='Electric',
                seats=5,
                transmission='Automatic',
                price_per_day=3500,
                image='https://images.unsplash.com/photo-1552519507-da3b142c6e3d?q=80&w=1200&auto=format&fit=crop'
            ),

            # ✅ Off-road SUV
            Car(
                name='Off-road SUV',
                category='SUV',
                seats=4,
                transmission='Manual',
                price_per_day=4500,
                image='https://images.unsplash.com/photo-1549399542-7e3f8b79c341?q=80&w=1200&auto=format&fit=crop'
            ),

            # ✅ Sedan (proper match)
            Car(
                name='Premium Sedan',
                category='Sedan',
                seats=5,
                transmission='Automatic',
                price_per_day=3000,
                image='https://images.unsplash.com/photo-1553440569-bcc63803a83d?q=80&w=1200&auto=format&fit=crop'
            ),

            # ✅ Van (use van-like image)
            Car(
                name='Family Van',
                category='Van',
                seats=7,
                transmission='Automatic',
                price_per_day=5500,
                image='https://images.unsplash.com/photo-1583267746897-2cf415887172?auto=format&fit=crop&w=1200&q=80'
            ),
        ]

        db.session.add_all(cars)
        db.session.commit()

@app.before_request
def setup_db():
    db.create_all()
    seed_cars()
    seed_admin()


def current_user():
    user_id = session.get('user_id')
    return User.query.get(user_id) if user_id else None


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_user():
    return {'current_user': current_user()}


def parse_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').date()


def has_conflict(car_id, start_date, end_date, exclude_booking_id=None):
    proposed_start = parse_date(start_date)
    proposed_end = parse_date(end_date)
    bookings = Booking.query.filter_by(car_id=car_id, status='confirmed').all()
    for booking in bookings:
        if exclude_booking_id and booking.id == exclude_booking_id:
            continue
        existing_start = parse_date(booking.start_date)
        existing_end = parse_date(booking.end_date)
        if proposed_start <= existing_end and proposed_end >= existing_start:
            return True
    return False

@app.route('/')
def home():
    featured_cars = Car.query.limit(3).all()
    return render_template('home.html', featured_cars=featured_cars)

@app.route('/cars')
def cars():
    category = request.args.get('category', '').strip()
    query = Car.query.filter_by(available=True)
    if category:
        query = query.filter(Car.category.ilike(category))
    cars = query.order_by(Car.id.desc()).all()
    return render_template('cars.html', cars=cars, selected_category=category)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already exists. Use a different email.', 'error')
            return redirect(url_for('register'))
        user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/book/<int:car_id>', methods=['GET', 'POST'])
def book(car_id):
    user = current_user()
    if not user:
        flash('Please log in to book a car.', 'error')
        return redirect(url_for('login'))
    car = Car.query.get_or_404(car_id)
    if not car.available:
        flash('This car is currently unavailable.', 'error')
        return redirect(url_for('cars'))

    if request.method == 'POST':
        pickup_location = request.form['pickup_location'].strip()
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        try:
            start = parse_date(start_date)
            end = parse_date(end_date)
            days = (end - start).days + 1
            if days <= 0:
                raise ValueError
        except Exception:
            flash('Please enter valid dates.', 'error')
            return redirect(url_for('book', car_id=car.id))

        if has_conflict(car.id, start_date, end_date):
            flash('Selected dates conflict with an existing booking for this car.', 'error')
            return redirect(url_for('book', car_id=car.id))

        total_price = days * car.price_per_day
        booking = Booking(
            user_id=user.id,
            car_id=car.id,
            pickup_location=pickup_location,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price
        )
        db.session.add(booking)
        db.session.commit()
        flash('Booking created successfully.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('book.html', car=car)

@app.route('/dashboard')
def dashboard():
    user = current_user()
    if not user:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
    return render_template('dashboard.html', bookings=bookings)

@app.route('/booking/cancel/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    user = current_user()
    if not user:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != user.id and user.role != 'admin':
        flash('Unauthorized action.', 'error')
        return redirect(url_for('dashboard'))
    booking.status = 'cancelled'
    db.session.commit()
    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('dashboard'))

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    cars = Car.query.order_by(Car.id.desc()).all()
    bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    return render_template('admin_dashboard.html', cars=cars, bookings=bookings)

@app.route('/admin/cars/new', methods=['GET', 'POST'])
@admin_required
def admin_add_car():
    if request.method == 'POST':
        car = Car(
            name=request.form['name'].strip(),
            category=request.form['category'].strip(),
            seats=int(request.form['seats']),
            transmission=request.form['transmission'].strip(),
            price_per_day=int(request.form['price_per_day']),
            image=request.form['image'].strip(),
            available=True if request.form.get('available') == 'on' else False,
        )
        db.session.add(car)
        db.session.commit()
        flash('Car added successfully.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_car_form.html', car=None)

@app.route('/admin/cars/edit/<int:car_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_car(car_id):
    car = Car.query.get_or_404(car_id)
    if request.method == 'POST':
        car.name = request.form['name'].strip()
        car.category = request.form['category'].strip()
        car.seats = int(request.form['seats'])
        car.transmission = request.form['transmission'].strip()
        car.price_per_day = int(request.form['price_per_day'])
        car.image = request.form['image'].strip()
        car.available = True if request.form.get('available') == 'on' else False
        db.session.commit()
        flash('Car updated successfully.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_car_form.html', car=car)

@app.route('/admin/cars/delete/<int:car_id>', methods=['POST'])
@admin_required
def admin_delete_car(car_id):
    car = Car.query.get_or_404(car_id)
    db.session.delete(car)
    db.session.commit()
    flash('Car deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
