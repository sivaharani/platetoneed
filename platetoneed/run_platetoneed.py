from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'key123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///donations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "hotel" or "helper"


class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    pickup_time = db.Column(db.String(50), nullable=False)
    donor_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Available')
    hotel_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    # Always show home (with Login / Sign Up buttons)
    return render_template('home.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered, please login.')
            return redirect(url_for('login'))

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        flash('Signup successful. Please login.')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Wrong email or password')
            return render_template('login.html')

        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_role'] = user.role
        flash('Logged in successfully.')
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('home'))


@app.route('/donations')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    donations = Donation.query.filter_by(status='Available').all()
    return render_template('index.html', donations=donations,
                           user_name=session.get('user_name'))


@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'hotel':
        flash('Only hotel providers can add donations.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_donation = Donation(
            food_type=request.form['food_type'],
            quantity=request.form['quantity'],
            location=request.form['location'],
            pickup_time=request.form['pickup_time'],
            donor_name=request.form['donor_name'],
            hotel_id=session['user_id']
        )
        db.session.add(new_donation)
        db.session.commit()
        flash('✅ Donation added!')
        return redirect(url_for('index'))

    return render_template('donate.html')


@app.route('/claim/<int:id>')
def claim(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'helper':
        flash('Only social helpers can claim food.')
        return redirect(url_for('index'))

    donation = Donation.query.get_or_404(id)
    if donation.status == 'Available':
        donation.status = 'Claimed'
        db.session.commit()
        flash('✅ Claimed!')

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
