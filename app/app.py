from flask import Flask, flash, redirect, render_template, request, url_for, session
import mysql.connector
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets


app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="0079306",
        database="supermarketApp"
    )




@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password', '')

        try:
            db = get_connection()
            cursor = db.cursor(dictionary=True)

            cursor.execute("SELECT * FROM customer WHERE email = %s;", (email,))
            user = cursor.fetchone()

            if user:
                db_password = user["password"]
                if check_password_hash(db_password, password):
                    session['user_email'] = user['email']
                    session['user_name'] = user['fname']
                    flash('Login successful')
                    return redirect(url_for('home'))
                else:
                    flash('Incorrect password.')
            else:
                flash('No account found with that email.')

        except Exception as e:
            flash('Something went wrong. Try again.')

        finally:
            cursor.close()
            db.close()

    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    db = get_connection()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        fname = request.form['firstName']
        lname = request.form['lastName']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        registration_date = datetime.today().date()
        loyalty_score = 0  # Default value

        
        # Check if email already exists
        cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already registered')
            return redirect(url_for('register'))

        # Insert new customer
        cursor.execute("""
            INSERT INTO customer (fname, lname, email, phone, password, registration_date, loyalty_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (fname, lname, email, phone, hashed_password, registration_date, loyalty_score))
        db.commit()

        # Start session
        session['user_email'] = email
        session['user_name'] = fname

        flash('Registration successful! You are now logged in.')
        return redirect(url_for('home'))
    cursor.close()
    db.close()
    return render_template('register.html')
@app.route('/addProduct', methods =['POST', 'GET'] )
def addProduct():
    db = get_connection()
    cursor = db.cursor(dictionary=True)
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        stock = request.form.get("stock")
        category = request.form.get("category")
        image_file = request.files.get("image")
        image_data = image_file.read() if image_file else None
        cursor.execute("INSERT INTO product (name, price, stock, category_id,image) VALUES (%s, %s, %s, %s, %s);", (name, price, stock, category, image_data))
        db.commit()
    cursor.close()
    db.close()
    return render_template("addProduct.html")

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))
    
if __name__ == '__main__':
    app.run(debug=True)

        