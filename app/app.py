from flask import Flask, request
import mysql.connector

app = Flask(__name__)

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="yourusername",
        password="yourpassword",
        database="yourdatabase"
    )

# Added db connection and cursor to connect the code to the db
db_connection = get_connection()
db_cursor = db_connection.cursor(buffered=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Add function to get email and password from the user

        
        