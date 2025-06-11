import decimal
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for, session, Response
import mysql.connector
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import imghdr


app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="0079306",
        database="supermarketApp"
    )
    
def loginDialog():
    if 'user_email' not in session:
        flash("Please log in first.")
        return redirect(url_for('login'))
    
# To serve the image
@app.route('/product_image/<int:product_id>')
def product_image(product_id):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT image FROM product WHERE product_id = %s", (product_id,))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result and result[0]:
        image_data = result[0]
        image_type = imghdr.what(None, image_data) or 'jpeg'  # fallback to jpeg
        return Response(image_data, mimetype=f'image/{image_type}')
    else:
        return '', 404

################################################### route codes #######################################################

########################################### Login , register, logout ##################################################
# Home
@app.route('/')
def home():
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM product;")
    products = cursor.fetchall()
    return render_template('index.html', products = products)

# Login
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

# Register
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

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))
############################################################################################################

############################################# Adding Product ###############################################
# Add Product to db
@app.route('/addProduct', methods =['POST', 'GET'] )
def addProduct():
    loginDialog()
    db = get_connection()
    cursor = db.cursor()
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        stock = request.form.get("stock")
        category = request.form.get("category")
        image_file = request.files.get("image")
        image_data = image_file.read() if image_file else None
        print("Image file:", image_file)
        print("Image data size:", len(image_data) if image_data else "No image")
        cursor.execute("INSERT INTO product (name, price, stock, category_id,image) VALUES (%s, %s, %s, %s, %s);", (name, price, stock, category, image_data))
        db.commit()
    cursor.execute("SELECT * FROM category;")
    categories = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("addProduct.html", categories=categories)
############################################################################################################

################################################ Cart ######################################################
# Cart
@app.route('/cart')
def cart():
    loginDialog()
    db = get_connection()
    cursor = db.cursor(dictionary=True)
    email = session['user_email']

    try:
        # Get customer_id
        cursor.execute("SELECT customer_id FROM customer WHERE email = %s", (email,))
        customer = cursor.fetchone()
        if not customer:
            flash("Customer not found.")
            return redirect(url_for('home'))

        customer_id = customer['customer_id']

        # Get open cart
        cursor.execute("""
            SELECT cart_id FROM cart 
            WHERE customer_id = %s AND status = 'open'
        """, (customer_id,))
        cart = cursor.fetchone()
        if not cart:
            return render_template("cart.html", items=[], total=0)

        cart_id = cart['cart_id']

        # Get items in cart
        cursor.execute("""
            SELECT ci.cart_item_id, ci.quantity, p.name, p.price, (p.price * ci.quantity) AS total_price, p.product_id
            FROM cartitem ci
            JOIN product p ON ci.product_id = p.product_id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        items = cursor.fetchall()

        subtotal = sum(item['total_price'] for item in items)
        subtotal = decimal.Decimal(subtotal)  # ensure it's Decimal

        # Conditional delivery fee logic
        delivery_fee = decimal.Decimal("0.00") if subtotal >= decimal.Decimal("500.00") else decimal.Decimal("39.90")
        total = subtotal + delivery_fee

        return render_template("cart.html", items=items, total=total, delivery_fee=delivery_fee, subtotal=subtotal)

    finally:
        cursor.close()
        db.close()

# Add product to cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    loginDialog()
    product_id = request.form.get('product_id')
    email = session['user_email']

    db = get_connection()
    cursor = db.cursor()

    try:
        # Get customer_id
        cursor.execute("SELECT customer_id FROM customer WHERE email = %s", (email,))
        customer = cursor.fetchone()
        if not customer:
            flash("Customer not found.")
            return redirect(url_for('home'))

        customer_id = customer[0]

        # Check if an open cart exists
        cursor.execute("""
            SELECT cart_id FROM cart 
            WHERE customer_id = %s AND status = 'open'
        """, (customer_id,))
        cart = cursor.fetchone()

        if cart:
            cart_id = cart[0]
        else:
            # Create a new cart
            cursor.execute("""
                INSERT INTO cart (created_date, status, customer_id)
                VALUES (%s, 'open', %s)
            """, (datetime.today().date(), customer_id))
            db.commit()
            cart_id = cursor.lastrowid

        # Check if product already in cart
        cursor.execute("""
            SELECT cart_item_id, quantity FROM cartitem 
            WHERE cart_id = %s AND product_id = %s
        """, (cart_id, product_id))
        item = cursor.fetchone()

        if item:
            # If exists, increase quantity
            cursor.execute("""
                UPDATE cartitem SET quantity = quantity + 1 
                WHERE cart_item_id = %s
            """, (item[0],))
        else:
            # Add new item
            cursor.execute("""
                INSERT INTO cartitem (quantity, cart_id, product_id)
                VALUES (1, %s, %s)
            """, (cart_id, product_id))
        
        db.commit()
        flash("Item added to cart!")
    except Exception as e:
        print(e)
        flash("An error occurred while adding to cart.")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('home'))

# Update the Cart
@app.route('/update_cart', methods=['POST'])
def update_cart():
    loginDialog()
    quantities = request.form.getlist('quantities')
    cart_item_ids = request.form.getlist('quantities')

    # Alternatively, if you use a dict-like name: quantities[cart_item_id]
    # then use request.form.to_dict(flat=False)['quantities']
    quantities_dict = request.form.to_dict(flat=False).get('quantities', {})

    db = get_connection()
    cursor = db.cursor()

    try:
        for cart_item_id, quantity in quantities_dict.items():
            cart_item_id = int(cart_item_id)
            quantity = int(quantity[0])
            if quantity < 1:
                cursor.execute("DELETE FROM cartitem WHERE cart_item_id = %s", (cart_item_id,))
            else:
                cursor.execute("UPDATE cartitem SET quantity = %s WHERE cart_item_id = %s", (quantity, cart_item_id))
        db.commit()
        flash("Cart updated successfully.")
    except Exception as e:
        print(e)
        flash("Error updating cart.")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('cart'))

# remove item
@app.route('/remove_item', methods=['POST'])
def remove_item():
    loginDialog()

    cart_item_id = request.form.get('cart_item_id')

    db = get_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM cartitem WHERE cart_item_id = %s", (cart_item_id,))
        db.commit()
        flash("Item removed.")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('cart'))

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    if 'user_email' not in session:
        flash("You must be logged in to clear your cart.")
        return redirect(url_for('login'))

    db = get_connection()
    cursor = db.cursor()
    email = session['user_email']

    try:
        # Get customer_id
        cursor.execute("SELECT customer_id FROM customer WHERE email = %s", (email,))
        customer = cursor.fetchone()
        if not customer:
            flash("Customer not found.")
            return redirect(url_for('home'))

        customer_id = customer[0]

        # Get open cart
        cursor.execute("""
            SELECT cart_id FROM cart 
            WHERE customer_id = %s AND status = 'open'
        """, (customer_id,))
        cart = cursor.fetchone()
        if not cart:
            flash("No active cart to clear.")
            return redirect(url_for('cart'))

        cart_id = cart[0]

        # First, delete items from cartitem
        cursor.execute("DELETE FROM cartitem WHERE cart_id = %s", (cart_id,))

        # Then, delete the cart itself
        cursor.execute("DELETE FROM cart WHERE cart_id = %s", (cart_id,))

        db.commit()
        flash("Cart cleared successfully.")

    except Exception as e:
        print(e)
        flash("An error occurred while clearing the cart.")

    finally:
        cursor.close()
        db.close()

    return redirect(url_for('cart'))


@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    if 'user_email' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    cart_item_id = data.get('cart_item_id')
    new_quantity = data.get('quantity')

    db = get_connection()
    cursor = db.cursor()

    try:
        if new_quantity <= 0:
            cursor.execute("DELETE FROM cartitem WHERE cart_item_id = %s", (cart_item_id,))
        else:
            cursor.execute("UPDATE cartitem SET quantity = %s WHERE cart_item_id = %s", (new_quantity, cart_item_id))
        db.commit()

        # Recalculate total
        cursor.execute("""
            SELECT SUM(p.price * ci.quantity)
            FROM cartitem ci
            JOIN cart c ON ci.cart_id = c.cart_id
            JOIN product p ON ci.product_id = p.product_id
            WHERE c.customer_id = (
                SELECT customer_id FROM customer WHERE email = %s
            ) AND c.status = 'open'
        """, (session['user_email'],))
        total = cursor.fetchone()[0] or 0

        return jsonify({'success': True, 'cart_total': total})

    finally:
        cursor.close()
        db.close()
        
@app.route('/adjust_quantity', methods=['POST'])
def adjust_quantity():
    if 'user_email' not in session:
        flash("Please log in first.")
        return redirect(url_for('login'))

    cart_item_id = request.form.get('cart_item_id')
    action = request.form.get('action')

    if not cart_item_id or action not in ('increase', 'decrease'):
        flash("Invalid request.")
        return redirect(url_for('cart'))

    db = get_connection()
    cursor = db.cursor()

    try:
        # Get current quantity
        cursor.execute("SELECT quantity FROM cartitem WHERE cart_item_id = %s", (cart_item_id,))
        row = cursor.fetchone()
        if not row:
            flash("Item not found.")
            return redirect(url_for('cart'))

        current_qty = row[0]
        if action == 'increase' and current_qty < 10:
            new_qty = current_qty + 1
        elif action == 'decrease' and current_qty > 1:
            new_qty = current_qty - 1
        else:
            new_qty = current_qty  # no change

        cursor.execute("UPDATE cartitem SET quantity = %s WHERE cart_item_id = %s", (new_qty, cart_item_id))
        db.commit()
        flash("Quantity updated.")

    except Exception as e:
        print(e)
        flash("Failed to update quantity.")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('cart'))

############################################################################################################

############################################ Checkout ######################################################
@app.route('/checkout')
def checkout():
    loginDialog()
    email = session['user_email']

    db = get_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Get customer_id
        cursor.execute("SELECT customer_id FROM customer WHERE email = %s", (email,))
        customer = cursor.fetchone()
        if not customer:
            flash("Customer not found.")
            return redirect(url_for('home'))

        customer_id = customer['customer_id']

        # Get open cart
        cursor.execute("""
            SELECT cart_id FROM cart
            WHERE customer_id = %s AND status = 'open'
        """, (customer_id,))
        cart = cursor.fetchone()

        if not cart:
            flash("Your cart is empty.")
            return render_template("checkout.html", items=[], subtotal=0, delivery_fee=0, total=0)

        cart_id = cart['cart_id']

        # Get cart items
        cursor.execute("""
            SELECT ci.quantity, p.name, p.price, (ci.quantity * p.price) AS total_price,
                   p.product_id
            FROM cartitem ci
            JOIN product p ON ci.product_id = p.product_id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        items = cursor.fetchall()

        # Calculate subtotal
        subtotal = sum(item['total_price'] for item in items)
        subtotal = decimal.Decimal(subtotal)

        # Calculate delivery fee
        delivery_fee = decimal.Decimal("0.00") if subtotal >= decimal.Decimal("500.00") else decimal.Decimal("39.90")
        total = subtotal + delivery_fee

        return render_template("checkout.html", items=items, subtotal=subtotal, delivery_fee=delivery_fee, total=total)

    finally:
        cursor.close()
        db.close()
from werkzeug.security import generate_password_hash

@app.route('/place_order', methods=['POST'])
def place_order():
    loginDialog()
    db = get_connection()
    cursor = db.cursor()

    try:
        email = session['user_email']

        # Get customer_id
        cursor.execute("SELECT customer_id FROM customer WHERE email = %s", (email,))
        customer = cursor.fetchone()
        if not customer:
            flash("Customer not found.")
            return redirect(url_for('checkout'))

        customer_id = customer[0]

        # Get active cart
        cursor.execute("SELECT cart_id FROM cart WHERE customer_id = %s AND status = 'open'", (customer_id,))
        cart = cursor.fetchone()
        if not cart:
            flash("No items in cart.")
            return redirect(url_for('checkout'))

        cart_id = cart[0]

        # Get cart items
        cursor.execute("""
            SELECT ci.product_id, ci.quantity, p.name, p.price
            FROM cartitem ci
            JOIN product p ON ci.product_id = p.product_id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        cart_items = cursor.fetchall()

        # Collect form data
        fname = request.form.get('first-name')
        lname = request.form.get('last-name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        apartment = request.form.get('apartment')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip')
        country = request.form.get('country')
        save_address = request.form.get('save-address') == 'on'

        card_number = request.form.get('card-number')
        exp_date = request.form.get('expiry')  # format MM/YY
        card_name = request.form.get('card-name')

        # Handle delivery fee
        subtotal = sum(decimal.Decimal(qty) * decimal.Decimal(price) for (_, qty, _, price) in cart_items)
        delivery_fee = decimal.Decimal("0.00") if subtotal >= decimal.Decimal("500.00") else decimal.Decimal("39.90")
        total = subtotal + delivery_fee

        # Insert into order_table
        cursor.execute("""
            INSERT INTO order_table (date, total_amount, delivery_id, status_id, customer_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (datetime.today().date(), total, 1, 1, customer_id))
        db.commit()
        order_id = cursor.lastrowid

        # Save address
        if save_address:
            cursor.execute("""
                INSERT INTO address (customer_id, zip_code, city, country, street, apt_no)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (customer_id, zip_code, city, country, address, apartment))

        # Save credit card if info was filled (basic presence check)
        if card_number and exp_date and card_name:
            hashed_card = generate_password_hash(card_number)
            cursor.execute("""
                INSERT INTO credit_card (customer_id, card_number, exp_date, owner_name)
                VALUES (%s, %s, STR_TO_DATE(%s, '%%m/%%y'), %s)
            """, (customer_id, hashed_card, exp_date, card_name))

        # Insert into order_detail
        for (product_id, quantity, product_name, unit_price) in cart_items:
            cursor.execute("""
                INSERT INTO order_detail (
                    order_id, product_id, fname, lname, email, pnum,
                    quantity, unit_price
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (order_id, product_id, fname, lname, email, phone, quantity, unit_price))

            # Log in `buys` table
            cursor.execute("INSERT IGNORE INTO buys (customer_id, product_id) VALUES (%s, %s)",
                           (customer_id, product_id))

        # Mark cart as completed
        cursor.execute("DELETE FROM cart WHERE cart_id = %s", (cart_id,))
        db.commit()

        flash("Order placed successfully.")
        return redirect(url_for('home'))

    except Exception as e:
        db.rollback()
        print("Order error:", e)
        flash("An error occurred while placing the order.")
        return redirect(url_for('checkout'))

    finally:
        cursor.close()
        db.close()


if __name__ == '__main__':
    app.run(debug=True)
    

############################################################################################################       