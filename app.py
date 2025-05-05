from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
import secrets
from collections import deque
import paypalrestsdk

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session management
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # Session lasts 30 days
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookie over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protect against CSRF
CORS(app)

# PayPal SDK Configuration
paypalrestsdk.configure({
    "mode": "sandbox",  # sandbox or live
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
})

# File paths
PRODUCTS_FILE = 'data/products.json'
USERS_FILE = 'data/users.json'
ORDERS_FILE = 'data/orders.json'
RECENTLY_VIEWED_FILE = 'data/recently_viewed.json'
WISHLISTS_FILE = 'data/wishlists.json'
CARTS_FILE = 'data/carts.json'

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Initialize JSON files if they don't exist
def init_json_file(file_path, default_content):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump(default_content, f, indent=4)
    else:
        # Verify the file has the correct structure
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if file_path == ORDERS_FILE and (not isinstance(data, dict) or 'orders' not in data):
                    with open(file_path, 'w') as f:
                        json.dump({"orders": []}, f, indent=4)
        except (json.JSONDecodeError, FileNotFoundError):
            with open(file_path, 'w') as f:
                json.dump(default_content, f, indent=4)

# Initialize products with sample data
sample_products = {
    "1": {
        "name": "Cyberpunk 2077",
        "description": "An open-world action-adventure RPG set in Night City",
        "price": 59.99,
        "stock": 50,
        "category": "Featured",
        "releaseDate": "2020-12-10",
        "genres": ["RPG", "Action", "Open World", "Sci-Fi"]
    },
    "2": {
        "name": "The Witcher 3",
        "description": "Epic fantasy RPG with a compelling narrative",
        "price": 39.99,
        "original_price": 59.99,
        "stock": 30,
        "category": "Sale",
        "releaseDate": "2015-05-19",
        "genres": ["RPG", "Action", "Open World", "Fantasy"]
    },
    "3": {
        "name": "Red Dead Redemption 2",
        "description": "Epic Western-themed action game",
        "price": 49.99,
        "stock": 25,
        "category": "Regular",
        "releaseDate": "2018-10-26",
        "genres": ["Action", "Adventure", "Open World"]
    },
    "4": {
        "name": "Elden Ring",
        "description": "Action RPG set in a dark fantasy world",
        "price": 59.99,
        "stock": 40,
        "category": "Regular",
        "releaseDate": "2022-02-25",
        "genres": ["RPG", "Action", "Open World", "Fantasy"]
    },
    "5": {
        "name": "God of War",
        "description": "Action-adventure game based on Norse mythology",
        "price": 49.99,
        "original_price": 59.99,
        "stock": 35,
        "category": "Sale",
        "releaseDate": "2018-04-20",
        "genres": ["Action", "Adventure", "Fantasy"]
    },
    "6": {
        "name": "FIFA 23",
        "description": "Latest installment in the FIFA series",
        "price": 59.99,
        "stock": 45,
        "category": "Regular",
        "releaseDate": "2022-09-30",
        "genres": ["Sports", "Simulation"]
    },
    "7": {
        "name": "Resident Evil Village",
        "description": "Survival horror game with intense action",
        "price": 49.99,
        "stock": 20,
        "category": "Regular",
        "releaseDate": "2021-05-07",
        "genres": ["Horror", "Action", "Adventure"]
    },
    "8": {
        "name": "Street Fighter 6",
        "description": "Classic fighting game series returns",
        "price": 59.99,
        "stock": 30,
        "category": "Regular",
        "releaseDate": "2023-06-02",
        "genres": ["Fighting", "Action"]
    }
}

init_json_file(PRODUCTS_FILE, sample_products)
init_json_file(USERS_FILE, {"users": []})
init_json_file(ORDERS_FILE, {"orders": []})
init_json_file(RECENTLY_VIEWED_FILE, {"user_views": {}})
init_json_file(WISHLISTS_FILE, {"user_wishlists": {}})
init_json_file(CARTS_FILE, {"user_carts": {}})

# Helper functions
def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"orders": []} if file_path == ORDERS_FILE else {}

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def get_products():
    return load_json(PRODUCTS_FILE)

def get_users():
    return load_json(USERS_FILE)

def get_orders():
    try:
        with open(ORDERS_FILE, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"orders": []}
            if "orders" not in data:
                data["orders"] = []
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"orders": []}

def get_recently_viewed():
    return load_json(RECENTLY_VIEWED_FILE)

def get_wishlists():
    return load_json(WISHLISTS_FILE)

def get_carts():
    return load_json(CARTS_FILE)

def save_recently_viewed(data):
    with open(RECENTLY_VIEWED_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def save_wishlists(data):
    with open(WISHLISTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def save_carts(data):
    save_json(CARTS_FILE, data)

# Routes
@app.route('/')
def store_front():
    return render_template('store_front.html')

@app.route('/game/<game_id>')
def game_detail(game_id):
    products = get_products()
    game = products.get(game_id)
    if game:
        # Add to recently viewed if user is logged in
        if 'user_id' in session:
            recently_viewed = get_recently_viewed()
            user_id = session['user_id']
            
            # Initialize user's recently viewed list if it doesn't exist
            if user_id not in recently_viewed['user_views']:
                recently_viewed['user_views'][user_id] = []
            
            # Remove the game if it's already in the list
            user_views = recently_viewed['user_views'][user_id]
            user_views = [view for view in user_views if view['game_id'] != game_id]
            
            # Add the new view at the beginning
            user_views.insert(0, {
                'game_id': game_id,
                'viewed_at': datetime.now().isoformat()
            })
            
            # Keep only the 4 most recent views
            recently_viewed['user_views'][user_id] = user_views[:4]
            
            # Save the updated recently viewed data
            save_recently_viewed(recently_viewed)
            
        return render_template('game_detail.html', game=game, game_id=game_id)
    return render_template('404.html'), 404

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('checkout.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = get_users()
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if email exists
        user = next((user for user in users['users'] if user['email'] == email), None)
        
        if not user:
            return render_template('login.html', 
                                error="Email not found. Please register if you don't have an account.",
                                show_register=True,
                                email=email)
        
        # Check password if email exists
        if user['password'] != password:
            return render_template('login.html', 
                                error="Incorrect password. Please try again.",
                                email=email)
        
        # Successful login
        session.permanent = True
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['last_activity'] = datetime.now().isoformat()
        
        # Sync cart with database
        carts = get_carts()
        user_id = user['id']
        if user_id in carts['user_carts']:
            # Merge session cart with database cart
            session_cart = session.get('cart', [])
            db_cart = carts['user_carts'][user_id]
            merged_cart = list(set(session_cart + db_cart))  # Remove duplicates
            session['cart'] = merged_cart
            carts['user_carts'][user_id] = merged_cart
            save_carts(carts)
        else:
            # If no database cart, save session cart
            if 'cart' in session:
                carts['user_carts'][user_id] = session['cart']
                save_carts(carts)
        
        return redirect(url_for('store_front'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = get_users()
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        if any(user['email'] == email for user in users['users']):
            return render_template('register.html', error="Email already registered")
        
        # Create new user
        new_user = {
            'id': str(len(users['users']) + 1),
            'username': username,
            'email': email,
            'password': password,  # In a real app, hash this password!
            'created_at': datetime.now().isoformat()
        }
        
        users['users'].append(new_user)
        save_json(USERS_FILE, users)
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    # Save cart to database if user is logged in
    if 'user_id' in session:
        carts = get_carts()
        user_id = session['user_id']
        if 'cart' in session:
            carts['user_carts'][user_id] = session['cart']
            save_carts(carts)
    
    session.clear()
    return redirect(url_for('store_front'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    users = get_users()
    user = next((user for user in users['users'] if user['id'] == session['user_id']), None)
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # Get user's orders
    orders_data = get_orders()
    user_orders = [order for order in orders_data["orders"] if order["user_id"] == session["user_id"]]
    
    return render_template('profile.html', user=user, orders=user_orders)

@app.route('/api/products')
def api_products():
    products = get_products()
    return jsonify(products)

@app.route('/search')
def search_page():
    query = request.args.get('q', '').lower()
    products = get_products()
    exact_matches = []
    related_matches = []
    
    if query:
        for id, game in products.items():
            game_with_id = {**game, 'id': id}
            
            # Check for exact match in name
            if query == game['name'].lower():
                exact_matches.append(game_with_id)
            # Check for partial matches in name or description
            elif (query in game['name'].lower() or 
                  query in game['description'].lower()):
                related_matches.append(game_with_id)
    
    # Combine results with exact matches first
    all_results = exact_matches + related_matches
    
    return render_template(
        'search_results.html',
        query=query,
        results=all_results,
        exact_match=len(exact_matches) > 0
    )

@app.route('/api/search')
def search_api():
    query = request.args.get('q', '').lower()
    products = get_products()
    exact_matches = []
    related_matches = []
    
    if query:
        for id, game in products.items():
            game_with_id = {**game, 'id': id}
            
            # Exact name matches
            if query == game['name'].lower():
                exact_matches.append(game_with_id)
            # Partial matches in name or description
            elif (query in game['name'].lower() or 
                  query in game['description'].lower()):
                related_matches.append(game_with_id)
    
    return jsonify({
        'results': exact_matches + related_matches,
        'exact_match': len(exact_matches) > 0
    })

@app.route('/api/place-order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401
    
    data = request.get_json()
    orders = get_orders()
    
    new_order = {
        'id': str(len(orders['orders']) + 1),
        'user_id': session['user_id'],
        'items': data['items'],
        'total': data['total'],
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'payment_method': data.get('payment_method', 'credit_card'),
        'payment_id': data.get('payment_id', None)
    }
    
    orders['orders'].append(new_order)
    save_json(ORDERS_FILE, orders)
    
    # Update product stock
    products = get_products()
    for item in data['items']:
        product_id = item['id']
        quantity = item['quantity']
        if product_id in products:
            products[product_id]['stock'] -= quantity
    
    save_json(PRODUCTS_FILE, products)
    
    return jsonify({
        'message': 'Order placed successfully', 
        'order_id': new_order['id']
    })

@app.route('/api/recently-viewed')
def get_user_recently_viewed():
    if 'user_id' not in session:
        return jsonify([])
    
    recently_viewed = get_recently_viewed()
    user_id = session['user_id']
    
    if user_id not in recently_viewed['user_views']:
        return jsonify([])
    
    # Get the full game details for each recently viewed game
    products = get_products()
    viewed_games = []
    
    for view in recently_viewed['user_views'][user_id]:
        game_id = view['game_id']
        if game_id in products:
            game_data = products[game_id].copy()
            game_data['id'] = game_id
            viewed_games.append(game_data)
    
    return jsonify(viewed_games)

@app.route('/wishlist')
def wishlist_page():
    if 'user_id' not in session:
        return redirect('/login')
    
    wishlists = get_wishlists()
    user_id = session['user_id']
    user_wishlist = wishlists.get('user_wishlists', {}).get(user_id, [])
    
    # Get full product details for wishlist items
    products = get_products()
    wishlist_items = []
    for item_id in user_wishlist:
        if item_id in products:
            product = products[item_id].copy()
            product['id'] = item_id
            wishlist_items.append(product)
    
    return render_template('wishlist.html', items=wishlist_items)

@app.route('/api/wishlist/toggle/<product_id>', methods=['POST'])
def toggle_wishlist(product_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    wishlists = get_wishlists()
    
    if user_id not in wishlists['user_wishlists']:
        wishlists['user_wishlists'][user_id] = []
    
    user_wishlist = wishlists['user_wishlists'][user_id]
    
    if product_id in user_wishlist:
        user_wishlist.remove(product_id)
        is_in_wishlist = False
    else:
        user_wishlist.append(product_id)
        is_in_wishlist = True
    
    save_wishlists(wishlists)
    return jsonify({
        'success': True,
        'is_in_wishlist': is_in_wishlist
    })

@app.route('/api/wishlist/status/<product_id>')
def wishlist_status(product_id):
    if 'user_id' not in session:
        return jsonify({'is_in_wishlist': False})
    
    user_id = session['user_id']
    wishlists = get_wishlists()
    user_wishlist = wishlists.get('user_wishlists', {}).get(user_id, [])
    
    return jsonify({
        'is_in_wishlist': product_id in user_wishlist
    })

@app.route('/legal-disclosure')
def legal_disclosure():
    return render_template('legal_disclosure.html', now=datetime.now)

@app.route('/api/delete-account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    try:
        # Delete user's orders
        orders = get_orders()['orders']
        orders = [order for order in orders if order['user_id'] != user_id]
        
        # Delete user's wishlist items
        wishlists = get_wishlists()
        user_wishlist = wishlists['user_wishlists'].get(user_id, [])
        user_wishlist = [item for item in user_wishlist if item != user_id]
        
        # Delete user's cart items
        carts = get_carts()
        user_cart = carts['user_carts'].get(user_id, [])
        user_cart = [item for item in user_cart if item != user_id]
        
        # Delete the user
        users = get_users()['users']
        users = [user for user in users if user['id'] != user_id]
        
        # Clear session
        session.clear()
        
        # Update JSON files
        save_json(ORDERS_FILE, {"orders": orders})
        save_json(WISHLISTS_FILE, {"user_wishlists": {user_id: user_wishlist}})
        save_json(USERS_FILE, {"users": users})
        save_json(CARTS_FILE, {"user_carts": {user_id: user_cart}})
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Missing password fields'}), 400
    
    users = get_users()
    user = next((user for user in users['users'] if user['id'] == session['user_id']), None)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    if user['password'] != current_password:
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
    
    # Update password
    user['password'] = new_password
    save_json(USERS_FILE, users)
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    game_id = data.get('game_id')
    
    if not game_id:
        return jsonify({'success': False, 'message': 'No game specified'}), 400
    
    # Get product details
    products = get_products()
    if game_id not in products:
        return jsonify({'success': False, 'message': 'Game not found'}), 404
    
    # Initialize cart in session if it doesn't exist
    if 'cart' not in session:
        session['cart'] = []
    
    # Add game to cart (allow duplicates)
    session['cart'].append(game_id)
    session.modified = True
    
    # If user is logged in, sync with database
    if 'user_id' in session:
        carts = get_carts()
        user_id = session['user_id']
        if user_id not in carts['user_carts']:
            carts['user_carts'][user_id] = []
        carts['user_carts'][user_id] = session['cart']
        save_carts(carts)
    
    return jsonify({
        'success': True,
        'message': 'Game added to cart',
        'cart_count': len(session['cart'])
    })

@app.route('/api/cart/count')
def get_cart_count():
    # Get count from session
    cart_count = len(session.get('cart', []))
    
    # If user is logged in, ensure session cart matches database
    if 'user_id' in session:
        carts = get_carts()
        user_id = session['user_id']
        if user_id in carts['user_carts']:
            session['cart'] = carts['user_carts'][user_id]
            cart_count = len(session['cart'])
    
    return jsonify({'count': cart_count})

@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    game_id = data.get('game_id')
    
    print(f"Attempting to remove game_id: {game_id}")  # Debug log
    
    if not game_id:
        return jsonify({'success': False, 'message': 'No game specified'}), 400
    
    # Initialize cart in session if it doesn't exist
    if 'cart' not in session:
        session['cart'] = []
    
    print(f"Current session cart: {session['cart']}")  # Debug log
    
    # Remove game from cart
    if game_id in session['cart']:
        print(f"Found game_id {game_id} in session cart")  # Debug log
        session['cart'].remove(game_id)
        print(f"Session cart after removal: {session['cart']}")  # Debug log
        
        # If user is logged in, sync with database
        if 'user_id' in session:
            print(f"User is logged in, syncing with database")  # Debug log
            carts = get_carts()
            user_id = session['user_id']
            if user_id in carts['user_carts']:
                print(f"User cart in database: {carts['user_carts'][user_id]}")  # Debug log
                if game_id in carts['user_carts'][user_id]:
                    print(f"Removing game_id {game_id} from database cart")  # Debug log
                    carts['user_carts'][user_id].remove(game_id)
                    save_carts(carts)
                    print(f"Database cart after removal: {carts['user_carts'][user_id]}")  # Debug log
        
        # Force session to update
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Game removed from cart',
            'cart_count': len(session['cart'])
        })
    
    print(f"Game_id {game_id} not found in cart")  # Debug log
    return jsonify({
        'success': False,
        'message': 'Game not in cart'
    }), 400

@app.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    # Clear session cart
    session['cart'] = []
    
    # If user is logged in, clear database cart
    if 'user_id' in session:
        carts = get_carts()
        user_id = session['user_id']
        if user_id in carts['user_carts']:
            carts['user_carts'][user_id] = []
            save_carts(carts)
    
    return jsonify({
        'success': True,
        'message': 'Cart cleared',
        'cart_count': 0
    })

@app.route('/api/cart')
def get_cart():
    # Get cart from session
    cart_items = session.get('cart', [])
    
    # If user is logged in, ensure session cart matches database
    if 'user_id' in session:
        carts = get_carts()
        user_id = session['user_id']
        if user_id in carts['user_carts']:
            cart_items = carts['user_carts'][user_id]
            session['cart'] = cart_items
    
    # Get product details for each item in cart
    products = get_products()
    items = []
    for game_id in cart_items:
        if game_id in products:
            game = products[game_id].copy()
            game['id'] = game_id
            items.append(game)
    
    return jsonify({'items': items})

@app.route('/guest-checkout')
def guest_checkout():
    return render_template('guest_checkout.html')

@app.route('/api/guest-checkout', methods=['POST'])
def process_guest_checkout():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'shipping', 'payment']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
    
    # Get cart items
    cart_items = session.get('cart', [])
    if not cart_items:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400
    
    # Get product details
    products = get_products()
    order_items = []
    total = 0
    
    for item_id in cart_items:
        if item_id in products:
            product = products[item_id]
            order_items.append({
                'id': item_id,
                'name': product['name'],
                'price': product['price'],
                'quantity': 1
            })
            total += product['price']
    
    # Create order
    orders = get_orders()
    new_order = {
        'id': str(len(orders['orders']) + 1),
        'email': data['email'],
        'shipping': data['shipping'],
        'items': order_items,
        'total': total,
        'tax': total * 0.1,
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'payment_method': 'credit_card',
        'is_guest': True
    }
    
    orders['orders'].append(new_order)
    save_json(ORDERS_FILE, orders)
    
    # Update product stock
    for item in order_items:
        product_id = item['id']
        if product_id in products:
            products[product_id]['stock'] -= 1
    
    save_json(PRODUCTS_FILE, products)
    
    # Clear cart
    session['cart'] = []
    
    return jsonify({
        'success': True,
        'message': 'Order placed successfully',
        'order_id': new_order['id']
    })

# Add a before_request handler to update last activity
@app.before_request
def update_last_activity():
    if 'user_id' in session:
        session['last_activity'] = datetime.now().isoformat()

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
