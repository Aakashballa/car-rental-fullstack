
# 🚗 Full-Stack Car Rental System — Phase 2

Phase 2 adds a lightweight **admin panel**, **car management (add/edit/delete)**, **booking conflict detection**, and **booking cancellation**.

## New in Phase 2
- Admin dashboard
- Add, edit, and delete cars
- Toggle car availability
- Booking conflict check to prevent date overlap for the same car
- Booking cancellation support
- Seeded admin account for testing

## Admin Login
- **Email:** `admin@rentalx.com`
- **Password:** `admin123`

## Core Features
- User registration and login
- Browse available cars
- Filter cars by category
- Book a car with pickup location and rental dates
- Conflict detection for overlapping bookings
- Dashboard to view and cancel user bookings
- Admin dashboard to manage inventory

## Run Locally
```bash
git clone <your-repo-url>
cd car-rental-fullstack-phase2
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000)
