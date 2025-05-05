from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
import json
from datetime import datetime
import hashlib
import secrets
import re
import os

app = Flask(__name__, 
    static_url_path='',
    static_folder='static',
    template_folder='templates'
)
# Configure CORS to allow requests from any origin
CORS(app, resources={r"/api/*": {"origins": "*"}})

# In-memory storage (you could replace with a database in production)
products = {}
orders = {}
users = {}
cart = {}

class Store:
    def __init__(self):
        self.products = {}  # Initialize empty products dict
        self.users = {}
        self.orders = {}
        self.sessions = {}
        self.load_data()
        
        # If no products exist, add sample products
        if not self.products:
            print("No products found, adding sample products...")
            self.add_sample_products()
            self.save_data()

    def load_data(self):
        """Load data from JSON files if they exist"""
        try:
            with open('products.json', 'r') as f:
                self.products = json.load(f)
                print(f"Loaded {len(self.products)} products")
        except FileNotFoundError:
            print("No products.json found, will create new one")
            self.products = {}
            
        try:
            with open('users.json', 'r') as f:
                self.users = json.load(f)
        except FileNotFoundError:
            self.users = {}
            
        try:
            with open('orders.json', 'r') as f:
                self.orders = json.load(f)
        except FileNotFoundError:
            self.orders = {}

    def save_data(self):
        """Save data to JSON files"""
        try:
            # Save with pretty printing for readability
            with open('products.json', 'w') as f:
                json.dump(self.products, f, indent=4)
            with open('users.json', 'w') as f:
                json.dump(self.users, f, indent=4)
            with open('orders.json', 'w') as f:
                json.dump(self.orders, f, indent=4)
            print(f"Saved {len(self.products)} products to products.json")
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def hash_password(self, password):
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def generate_session_token(self):
        """Generate a random session token"""
        return secrets.token_urlsafe(32)

    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None

    def validate_password(self, password):
        """
        Validate password requirements:
        - At least 8 characters long
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one number
        - Contains at least one special character
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
            
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
            
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
            
        return True, "Password is valid"

    def register_user(self, email, password):
        """Register a new user"""
        try:
            if not self.validate_email(email):
                return False, "Invalid email format"
            
            # Validate password
            is_valid_password, password_message = self.validate_password(password)
            if not is_valid_password:
                return False, password_message
            
            # Check if email already exists
            for user in self.users.values():
                if user['email'] == email:
                    return False, "Email already registered"

            user_id = str(len(self.users) + 1)
            self.users[user_id] = {
                'email': email,
                'password': self.hash_password(password),
                'created_at': str(datetime.now())
            }
            
            if self.save_data():
                return True, "Registration successful"
            else:
                return False, "Error saving user data"
                
        except Exception as e:
            print(f"Registration error: {e}")
            return False, "An error occurred during registration"

    def authenticate_user(self, email, password):
        """Authenticate a user"""
        for user_id, user in self.users.items():
            if user['email'] == email and user['password'] == self.hash_password(password):
                session_token = self.generate_session_token()
                self.sessions[session_token] = user_id
                return True, session_token
        return False, None

    def get_user_by_token(self, token):
        """Get user ID from session token"""
        return self.sessions.get(token)

    def add_product(self, product_id, name, price, stock):
        """Add a new product to the store"""
        self.products[product_id] = {
            'name': name,
            'price': float(price),
            'stock': int(stock)
        }
        self.save_data()

    def search_products(self, query):
        """Search products by name"""
        query = query.lower()
        return {
            pid: product for pid, product in self.products.items()
            if query in product['name'].lower()
        }

    def add_sample_products(self):
        """Add sample game products to the store"""
        sample_products = [
            # Featured Game (larger display)
            ("1", "Cyberpunk 2077", 59.99, 50, "cyberpunk2077.jpg", "Featured", 
             "Experience the future in this open-world RPG masterpiece", "December 10, 2020"),
            
            # Games on Sale (add release dates)
            ("2", "The Witcher 3", 29.99, 30, "witcher3.jpg", "Sale", 
             "Epic fantasy RPG - Was $49.99", "May 19, 2015", 49.99),
            ("3", "Red Dead Redemption 2", 39.99, 25, "rdr2.jpg", "Sale", 
             "Epic Western adventure - Was $59.99", "October 26, 2018", 59.99),
            ("4", "Elden Ring", 44.99, 40, "eldenring.jpg", "Sale", 
             "Challenging action RPG - Was $69.99", "February 25, 2022", 69.99),
            
            # Regular Games
            ("5", "God of War Ragnarök", 69.99, 45, "gow.jpg", "Regular", 
             "Continue Kratos and Atreus's epic journey", "November 9, 2022"),
            ("6", "Spider-Man 2", 69.99, 35, "spiderman2.jpg", "Regular", 
             "Swing through New York as Peter Parker and Miles Morales", "October 28, 2023"),
            ("7", "Final Fantasy XVI", 59.99, 30, "ff16.jpg", "Regular", 
             "Experience the latest in the legendary RPG series", "June 22, 2023"),
            ("8", "Starfield", 69.99, 40, "starfield.jpg", "Regular", 
             "Explore the cosmos in this epic space RPG", "September 6, 2023"),
            ("9", "Resident Evil 4 Remake", 49.99, 25, "re4.jpg", "Regular", 
             "The classic horror game reimagined", "January 26, 2023"),
            ("10", "Horizon Forbidden West", 49.99, 35, "horizon.jpg", "Regular", 
             "Continue Aloy's journey in this stunning open world", "February 18, 2022"),
            ("11", "Baldur's Gate 3", 59.99, 50, "bg3.jpg", "Regular", 
             "Critically acclaimed D&D-based RPG", "August 3, 2023"),
            ("12", "Street Fighter 6", 39.99, 40, "sf6.jpg", "Regular", 
             "The latest evolution in fighting games", "June 2, 2023"),
            ("13", "Diablo IV", 69.99, 30, "diablo4.jpg", "Regular", 
             "Return to the world of Sanctuary", "June 2, 2023"),
            ("14", "Assassin's Creed Mirage", 49.99, 45, "acmirage.jpg", "Regular", 
             "Return to the series' stealth-action roots", "September 12, 2023"),
            ("15", "Alan Wake 2", 59.99, 35, "alanwake2.jpg", "Regular", 
             "Survive the dark presence in this psychological thriller", "October 17, 2023"),
            ("16", "Mortal Kombat 1", 59.99, 40, "mk1.jpg", "Regular", 
             "Experience the brutal fighting game reboot", "September 19, 2021"),
            ("17", "Star Wars Jedi: Survivor", 54.99, 30, "jedisurvivor.jpg", "Regular", 
             "Continue Cal Kestis's journey", "April 28, 2023"),
            ("18", "Dead Space Remake", 49.99, 25, "deadspace.jpg", "Regular", 
             "The sci-fi horror classic returns", "January 27, 2023"),
            ("19", "Lies of P", 59.99, 35, "liesofp.jpg", "Regular", 
             "Soulslike reimagining of Pinocchio's tale", "September 19, 2023"),
            ("20", "Sea of Stars", 34.99, 50, "seastars.jpg", "Regular", 
             "Classic-style RPG with modern touches", "October 24, 2023")
        ]

        print("Adding sample products...")
        for product in sample_products:
            if len(product) == 9:  # Sale items with original price
                id, name, price, stock, image, category, description, release_date, original_price = product
                self.products[id] = {
                    'name': name,
                    'price': float(price),
                    'stock': int(stock),
                    'image': image,
                    'category': category,
                    'description': description,
                    'releaseDate': release_date,
                    'original_price': float(original_price)
                }
            else:  # Regular and Featured items
                id, name, price, stock, image, category, description, release_date = product
                self.products[id] = {
                    'name': name,
                    'price': float(price),
                    'stock': int(stock),
                    'image': image,
                    'category': category,
                    'description': description,
                    'releaseDate': release_date
                }
        print(f"Added {len(sample_products)} products")

# Initialize store
store = Store()

# After store = Store()
print("Current products:", store.products)

# Routes
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def home():
    return render_template('store_front.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/payment-success')
def payment_success():
    return render_template('payment_success.html')

# Add this route to serve static files
@app.route('/<path:filename>')
def serve_file(filename):
    return send_file(filename)

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(store.products)

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = store.products.get(product_id)
    if product:
        return jsonify(product)
    return jsonify({'error': 'Product not found'}), 404

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    results = store.search_products(query)
    return jsonify(results)

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        success, message = store.register_user(email, password)
        
        if success:
            return jsonify({'message': message}), 201
        return jsonify({'error': message}), 400
        
    except Exception as e:
        print(f"Registration route error: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    success, token = store.authenticate_user(email, password)
    if success:
        return jsonify({'token': token})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Authorization required'}), 401
    
    user_id = store.get_user_by_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid session'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if product_id not in store.products:
        return jsonify({'error': 'Product not found'}), 404
    
    if store.products[product_id]['stock'] < quantity:
        return jsonify({'error': 'Not enough stock'}), 400
    
    # Add to cart logic here (you'll need to implement the cart storage)
    return jsonify({'message': 'Added to cart'})

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint to verify API is working"""
    return jsonify({'message': 'API is working'}), 200

@app.route('/api/order', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        
        # Validate order data
        required_fields = ['name', 'email', 'address', 'city', 'postal', 'cart']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create order in database
        order_id = str(len(store.orders) + 1)
        store.orders[order_id] = {
            'user_info': {
                'name': data['name'],
                'email': data['email'],
                'address': data['address'],
                'city': data['city'],
                'postal': data['postal']
            },
            'cart': data['cart'],
            'status': 'pending',
            'created_at': str(datetime.now())
        }
        
        # Update product stock
        for item in data['cart']:
            product_id = item['id']
            quantity = item['quantity']
            if product_id in store.products:
                if store.products[product_id]['stock'] >= quantity:
                    store.products[product_id]['stock'] -= quantity
                else:
                    return jsonify({'error': f'Not enough stock for product: {store.products[product_id]["name"]}'}), 400
        
        # Save changes
        store.save_data()
        
        return jsonify({'message': 'Order created successfully', 'order_id': order_id}), 201
        
    except Exception as e:
        print(f"Order creation error: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/game/<game_id>')
def game_detail(game_id):
    game = store.products.get(game_id)
    if game:
        return render_template('game_detail.html', game=game, game_id=game_id)
    return "Game not found", 404

@app.route('/api/search')
def search_api():
    query = request.args.get('q', '').lower()
    results = []
    
    if query:
        for id, game in store.products.items():
            if query in game['name'].lower() or query in game['description'].lower():
                results.append({
                    'id': id,
                    **game
                })
    
    return jsonify({
        'results': results
    })

@app.route('/search')
def search_page():
    query = request.args.get('q', '')
    results = []
    
    if query:
        for id, game in store.products.items():
            if query.lower() in game['name'].lower() or query.lower() in game['description'].lower():
                results.append({
                    'id': id,
                    **game
                })
    
    return render_template('search_results.html', query=query, results=results)

if __name__ == '__main__':
    # Delete existing products.json to force reset
    if os.path.exists('products.json'):
        os.remove('products.json')
        print("Deleted existing products.json")

    # Create required directories if they don't exist
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)

    # Create an empty favicon.ico if it doesn't exist
    favicon_path = os.path.join('static', 'favicon.ico')
    if not os.path.exists(favicon_path):
        with open(favicon_path, 'wb') as f:
            f.write(b'')  # Write empty file

    # Initialize store
    store = Store()

    app.run(debug=True)
