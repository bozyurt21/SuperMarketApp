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
# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

def loginDialog():
    if 'user_email' not in session:
        flash("Please log in first.")
        return redirect(url_for('login'))
# Home
@app.route('/')
def home():
    db = get_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM product;")
    products = cursor.fetchall()
    
    ###################################################### Advance Queries ######################################################
    ### Most Sold Products Per Category
    # Get Most Sold Products Per Category
    cursor.execute("""
        SELECT 
            p.category_id,
            c.name AS category_name,
            p.product_id,
            p.name AS product_name,
            p.price AS price,
            p.stock AS stock,
            SUM(od.quantity) AS total_sold
        FROM product p
        JOIN order_detail od ON p.product_id = od.product_id
        JOIN category c ON p.category_id = c.category_id
        GROUP BY p.category_id, p.product_id
        HAVING total_sold = (
            SELECT MAX(inner_total) FROM (
                SELECT SUM(od2.quantity) AS inner_total
                FROM product p2
                JOIN order_detail od2 ON p2.product_id = od2.product_id
                WHERE p2.category_id = p.category_id
                GROUP BY p2.product_id
            ) AS inner_query
        )
        ORDER BY category_name;
    """)
    most_sold_per_category = cursor.fetchall()
    
    
    # Get Most Popular Categories
    cursor.execute("""
        SELECT 
            cat.category_id,
            cat.name AS category_name,
            SUM(od.quantity) AS total_items_sold
        FROM category cat
        JOIN product p ON cat.category_id = p.category_id
        JOIN order_detail od ON p.product_id = od.product_id
        GROUP BY cat.category_id
        ORDER BY total_items_sold DESC
        LIMIT 1;
    """)
    popular_category = cursor.fetchall()
    
    # Get Frequently Bought Together Pairs
    cursor.execute("""
        SELECT 
    p1.product_id AS product1_id,
    p1.name AS product1_name,
    p1.price AS product1_price,
    p1.stock AS product1_stock,
    p2.product_id AS product2_id,
    p2.name AS product2_name,
    p2.price AS product2_price,
    p2.stock AS product2_stock,
    COUNT(*) AS times_bought_together
FROM order_detail od1
JOIN order_detail od2 
    ON od1.order_id = od2.order_id 
    AND od1.product_id < od2.product_id
JOIN product p1 ON od1.product_id = p1.product_id
JOIN product p2 ON od2.product_id = p2.product_id
GROUP BY p1.product_id, p2.product_id
ORDER BY times_bought_together DESC
LIMIT 10;
    """)
    bought_together = cursor.fetchall()
    
    # Personalized Recommendations (if logged in)
    user_recommendations = []
    if 'user_email' in session:
        cursor.execute("SELECT customer_id FROM customer WHERE email = %s", (session['user_email'],))
        customer = cursor.fetchone()
        if customer:
            customer_id = customer['customer_id']
            cursor.execute("""
                SELECT DISTINCT p.product_id, p.name, p.price
                FROM product p
                WHERE p.category_id IN (
                    SELECT DISTINCT p2.category_id
                    FROM order_detail od
                    JOIN product p2 ON od.product_id = p2.product_id
                    JOIN order_table ot ON od.order_id = ot.order_id
                    WHERE ot.customer_id = %s
                )
                ORDER BY RAND()
                LIMIT 5;
            """, (customer_id,))
            user_recommendations = cursor.fetchall()
    # Top 5 Spending Customers
    cursor.execute("""
        SELECT 
            c.customer_id,
            CONCAT(c.fname, ' ', c.lname) AS full_name,
            c.email,
            SUM(o.total_amount) AS total_spent
        FROM customer c
        JOIN order_table o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id
        ORDER BY total_spent DESC
        LIMIT 5;
    """)
    top_customers = cursor.fetchall()

    
    return render_template('index.html', products = products, most_sold_per_category=most_sold_per_category,
        popular_category=popular_category,
        bought_together=bought_together,
        user_recommendations=user_recommendations, 
        top_customers = top_customers)

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
    print(request.form)

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
        print(cart_id)

        # Get cart items
        cursor.execute("""
            SELECT ci.product_id, ci.quantity, p.name, p.price
            FROM cartitem ci
            JOIN product p ON ci.product_id = p.product_id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        cart_items = cursor.fetchall()
        print("No problem in cartitem")

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
            INSERT INTO order_table (date, total_amount, customer_id)
            VALUES (%s, %s, %s)
        """, (datetime.today().date(), total, customer_id))
        db.commit()
        order_id = cursor.lastrowid
        print("No problem in order_table")

        # Save address
        if save_address:
            cursor.execute("""
                INSERT INTO address (customer_id, zip_code, city, country, street, apt_no)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (customer_id, zip_code, city, country, address, apartment))
        print("No problem in address")

        # Save credit card if info was filled (basic presence check)
        if card_number and exp_date and card_name:
            hashed_card = generate_password_hash(card_number)
            cursor.execute("""
                INSERT INTO credit_card (customer_id, card_number, exp_date, owner_name)
                VALUES (%s, %s, %s, %s)
            """, (customer_id, hashed_card, exp_date, card_name))
        # Insert into order_detail
        for (product_id, quantity, product_name, unit_price) in cart_items:
            cursor.execute("""
                INSERT INTO order_detail (
                    order_id, order_status_id, product_id, fname, lname, email, pnum, zip_code, city, country, street, apt_no,
                    quantity, unit_price
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (order_id, 1, product_id, fname, lname, email, phone, zip_code, city, country, state, apartment, quantity, unit_price))
            print("Nothing is wrong on order detail")
            # TODO: We need to update the product quantity after the purchase!!!
            cursor.execute("UPDATE product SET stock = stock - %s WHERE product_id= %s", (quantity, product_id))
            print("Product updated successfully")
            # Log in `buys` table
            cursor.execute("INSERT IGNORE INTO buys (customer_id, product_id) VALUES (%s, %s)",
                           (customer_id, product_id))
        print("No problem in buys")

        # Mark cart as completed

        cursor.execute("UPDATE cart SET status = %s WHERE cart_id = %s", ('closed', cart_id))
        
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

##################################################### Purchase Page #############################################
@app.route('/purchase')
def purchase():
    loginDialog()
    email = session['user_email']
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Get customer ID
        cursor.execute("SELECT customer_id FROM customer WHERE email = %s", (email,))
        customer = cursor.fetchone()
        if not customer:
            flash("Customer not found.")
            return redirect(url_for('home'))

        customer_id = customer['customer_id']

        # Get Open Order Items
        cursor.execute("""
            SELECT od.order_id, od.product_id, p.name, p.price, od.quantity,
                   (od.quantity * p.price) AS total_price,
                   ot.date AS order_date, os.status_name
            FROM order_table ot
            JOIN order_detail od ON ot.order_id = od.order_id
            JOIN product p ON od.product_id = p.product_id
            JOIN order_status os ON od.order_status_id = os.status_id
            WHERE ot.customer_id = %s AND os.status_name != 'delivered'
            ORDER BY ot.date DESC
        """, (customer_id,))
        open_order_items = cursor.fetchall()

        # Get Past Order Items
        cursor.execute("""
            SELECT od.order_id, od.product_id, p.name, p.price, od.quantity,
                   (od.quantity * p.price) AS total_price,
                   ot.date AS order_date, os.status_name
            FROM order_table ot
            JOIN order_detail od ON ot.order_id = od.order_id
            JOIN product p ON od.product_id = p.product_id
            JOIN order_status os ON od.order_status_id = os.status_id
            WHERE ot.customer_id = %s AND os.status_name != 'closed'
            ORDER BY ot.date DESC
        """, (customer_id,))
        past_order_items = cursor.fetchall()

        return render_template("purchases.html",
                               open_orders=open_order_items,
                               past_orders=past_order_items)

    finally:
        cursor.close()
        db.close()

@app.route('/delivered', methods=['POST'])
def delivered():
    if 'user_email' not in session:
        flash("You must be logged in to confirm delivery.")
        return redirect(url_for('login'))

    product_id = request.form.get('product_id')
    order_id = request.form.get('order_id')

    if not product_id or not order_id:
        flash("Missing order or product information.")
        return redirect(url_for('purchase'))

    db = get_connection()
    cursor = db.cursor()

    try:
        # Update the order_status_id for the delivered item (assuming '2' is the ID for 'close')
        cursor.execute("""
            UPDATE order_detail 
            SET order_status_id = 2 
            WHERE order_id = %s AND product_id = %s
        """, (order_id, product_id))
        db.commit()

        flash("Order marked as delivered.")

    except Exception as e:
        print("Error updating delivery status:", e)
        db.rollback()
        flash("Failed to update delivery status.")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('purchase'))


@app.route('/get_products', methods=['GET'])
def get_products():
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Fetch filters from query string
        category_id = request.args.get('category_id')
        price_min = request.args.get('price_min')
        price_max = request.args.get('price_max')
        sort = request.args.get('sort')

        if sort == 'popularity':
            query = """
                SELECT 
                    p.product_id, p.name, p.price, SUM(od.quantity) AS total_sold
                FROM product p
                JOIN order_detail od ON p.product_id = od.product_id
                WHERE 1=1
            """
        else:
            query = "SELECT product_id, name, price FROM product WHERE 1=1"

        params = []

        # Category filter
        if category_id:
            query += " AND p.category_id = %s" if sort == 'popularity' else " AND category_id = %s"
            params.append(category_id)

        # Price range filters
        if price_min:
            query += " AND p.price >= %s" if sort == 'popularity' else " AND price >= %s"
            params.append(price_min)
        if price_max:
            query += " AND p.price <= %s" if sort == 'popularity' else " AND price <= %s"
            params.append(price_max)

        # Sorting
        if sort == 'price_asc':
            query += " ORDER BY price ASC"
        elif sort == 'price_desc':
            query += " ORDER BY price DESC"
        elif sort == 'newest':
            query += " ORDER BY product_id DESC"
        elif sort == 'popularity':
            query += """
                GROUP BY p.product_id, p.name, p.price
                HAVING SUM(od.quantity) > 0
                ORDER BY total_sold DESC
            """
        else:
            query += " ORDER BY product_id DESC"  # Fallback to newest

        cursor.execute(query, tuple(params))
        products = cursor.fetchall()


        # Fetch all categories for dropdown
        cursor.execute("SELECT category_id, name FROM category")
        categories = cursor.fetchall()

        return render_template('index.html', products=products, categories=categories)

    except Exception as e:
        print("Error fetching products:", e)
        flash("Unable to load products.")
        return render_template('index.html', products=[], categories=[])

    finally:
        cursor.close()
        db.close()



if __name__ == '__main__':
    app.run(debug=True)
    

############################################################################################################       