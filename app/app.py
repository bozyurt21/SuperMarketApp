from flask import Flask, flash, redirect, render_template, request, url_for
import mysql.connector

app = Flask(__name__)


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="0079306",
        #database="yourdatabase"
    )

# Added db connection and cursor to connect the code to the db
db_connection = get_connection()
db_cursor = db_connection.cursor(buffered=True)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')  # Use .get() to avoid KeyError
        password = request.form.get('password')
        
        # Example logic
        if email == 'admin@example.com' and password == 'secret':
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
            return render_template('login.html')

    return render_template('login.html')  # for GET request

@app.route('/register', methods=['POST', 'GET'])
def register():
    return render_template('register.html') 
    
if __name__ == '__main__':
    app.run(debug=True)

        
        