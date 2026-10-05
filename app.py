from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
import random
import string
import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Change this in production

# MongoDB Connection
# Initialize collections to None to prevent NameError if connection fails
db = None
packages_collection = None
contacts_collection = None
users_collection = None

try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
    # Trigger a connection to check if server is up
    client.server_info() 
    db = client['courier_db']
    packages_collection = db['packages']
    contacts_collection = db['contacts']
    users_collection = db['users'] 
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Helper to generate 10-digit ID
def generate_tracking_id():
    # Generate 10 random digits
    return ''.join(random.choices(string.digits, k=10))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        data = request.json
        if data:
            if contacts_collection is not None:
                data['date'] = datetime.datetime.now()
                contacts_collection.insert_one(data)
                return jsonify({"message": "Message received!"}), 200
            else:
                return jsonify({"error": "Database not connected"}), 500
    return render_template('contact.html')

# --- Authentication ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')

        if role == 'admin':
            # Hardcoded admin credentials as requested
            admin_creds = {
                'mr.yoyo': 'vishnu',
                'murugan': 'murugan@123'
            }
            
            if username in admin_creds and admin_creds[username] == password:
                session['user'] = username
                session['role'] = 'admin'
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template('login.html', error="Invalid Admin Credentials")
        
        elif role == 'employee':
            if users_collection is None:
                 return render_template('login.html', error="Database connection error")

            # Check against database
            user = users_collection.find_one({
                "username": username,
                "password": password, 
                "role": "employee"
            })

            # Check if this matches the old simple password or the DB user
            if user:
                session['user'] = username
                session['role'] = 'employee'
                session['place'] = user.get('place', 'Head Office')
                return redirect(url_for('employee_dashboard'))
            elif password == 'employee' and username == 'employee': # Keep fallback simple login for testing if needed, or remove. Let's keep it for safety but prioritize DB.
                 session['user'] = 'Demo Employee'
                 session['role'] = 'employee'
                 session['place'] = 'Demo Hub'
                 return redirect(url_for('employee_dashboard'))
            else:
                return render_template('login.html', error="Invalid Employee Credentials")
        
        elif role == 'user':
             # Users just track, maybe just redirect home or a user dashboard
             return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- Dashboards ---
@app.route('/admin')
def admin_dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    total_shipments = 0
    recent_shipments = []
    total_employees = 0

    if packages_collection is not None:
        total_shipments = packages_collection.count_documents({})
        recent_shipments = list(packages_collection.find().sort('_id', -1).limit(10))
    
    if users_collection is not None:
        total_employees = users_collection.count_documents({"role": "employee"})
        all_employees = list(users_collection.find({"role": "employee"}))
    else:
        all_employees = []
    
    return render_template('admin.html', 
                           total_shipments=total_shipments, 
                           total_employees=total_employees,
                           shipments=recent_shipments,
                           employees=all_employees)

@app.route('/api/employee/delete', methods=['POST'])
def delete_employee():
    if 'user' not in session or session.get('role') != 'admin':
         return jsonify({"error": "Unauthorized"}), 403

    if users_collection is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json
    username = data.get('username')
    
    if not username:
         return jsonify({"error": "Username required"}), 400
         
    result = users_collection.delete_one({"username": username, "role": "employee"})
    
    if result.deleted_count == 0:
        return jsonify({"error": "Employee not found"}), 404
        
    return jsonify({"message": "Employee deleted successfully"}), 200

@app.route('/employee')
def employee_dashboard():
    if 'user' not in session or session.get('role') not in ['employee', 'admin']:
        return redirect(url_for('login'))
    
    return render_template('employee.html', place_name=session.get('place', 'Unknown'))


# --- API ---
@app.route('/api/employee/create', methods=['POST'])
def create_employee():
    if 'user' not in session or session.get('role') != 'admin':
         return jsonify({"error": "Unauthorized"}), 403

    if users_collection is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    place = data.get('place')

    if not username or not password:
         return jsonify({"error": "Username and Password required"}), 400
    
    if users_collection.find_one({"username": username}):
         return jsonify({"error": "Username already exists"}), 400

    new_employee = {
        "username": username,
        "password": password, # In production hash this!
        "role": "employee",
        "place": place or "General Hub",
        "created_at": datetime.datetime.now()
    }
    
    users_collection.insert_one(new_employee)
    return jsonify({"message": "Employee created successfully"}), 201
@app.route('/api/shipment/create', methods=['POST'])
def create_shipment():
    if 'user' not in session or session.get('role') not in ['employee', 'admin']:
         return jsonify({"error": "Unauthorized"}), 403
    
    if packages_collection is None:
        return jsonify({"error": "Database not connected"}), 500

    data = request.json
    
    # Check if a specific/custom ID was provided
    custom_id = data.get('custom_id')
    
    if custom_id:
        if packages_collection.find_one({"tracking_id": custom_id}):
            return jsonify({"error": f"Tracking ID '{custom_id}' already exists. Please choose another."}), 400
        tracking_id = custom_id
    else:
        tracking_id = generate_tracking_id()
        # Ensure ID currently doesn't exist
        while packages_collection.find_one({"tracking_id": tracking_id}):
            tracking_id = generate_tracking_id()
    
    shipment = {
        "tracking_id": tracking_id,
        "sender": data.get('sender'),
        "sender_mobile": data.get('sender_mobile'),
        "sender_address": data.get('sender_address'),
        "receiver": data.get('receiver'),
        "receiver_mobile": data.get('receiver_mobile'),
        "receiver_address": data.get('receiver_address'),
        "origin": data.get('location'),
        "destination": data.get('receiver_address'),
        
        # New Fields for Cost/Dimensions
        "from_state": data.get('from_state'),
        "to_state": data.get('to_state'),
        "to_city": data.get('to_city'), # Explicit destination city if provided
        "weight": data.get('weight'),
        "length": data.get('length'),
        "width": data.get('width'),
        "height": data.get('height'),
        "service_type": data.get('service_type'),
        "cost_summary": data.get('cost_summary'), # Dict with base, gst, total

        "location": data.get('location'),
        "status": data.get('status', 'In Transit'),
        "created_by": session.get('user'),
        "created_at": datetime.datetime.now(),
        "history": [
            {
                "status": "Created", 
                "location": data.get('location'), 
                "timestamp": datetime.datetime.now()
            }
        ]
    }
    
    packages_collection.insert_one(shipment)
    return jsonify({"message": "Shipment created", "tracking_id": tracking_id}), 201

@app.route('/api/shipment/update', methods=['POST'])
def update_shipment():
    if 'user' not in session or session.get('role') not in ['employee', 'admin']:
         return jsonify({"error": "Unauthorized"}), 403

    if packages_collection is None:
        return jsonify({"error": "Database not connected"}), 500

    data = request.json
    tracking_id = data.get('tracking_id')
    new_location = data.get('location')
    new_status = data.get('status')
    
    if not tracking_id or not new_location:
         return jsonify({"error": "Missing tracking_id or location"}), 400

    update_fields = {"location": new_location}
    if new_status:
        update_fields["status"] = new_status
        
    update_query = {
        "$set": update_fields,
        "$push": {
            "history": {
                "status": new_status or "Updated",
                "location": new_location,
                "timestamp": datetime.datetime.now()
            }
        }
    }

    result = packages_collection.update_one({"tracking_id": tracking_id}, update_query)
    
    if result.matched_count == 0:
        return jsonify({"error": "Shipment not found"}), 404
    
    return jsonify({"message": "Shipment updated"}), 200

@app.route('/api/track/<tracking_id>', methods=['GET'])
def track_package(tracking_id):
    if packages_collection is None:
        return jsonify({"error": "Database not connected"}), 500
        
    package = packages_collection.find_one({"tracking_id": tracking_id}, {"_id": 0})
    if package:
        return jsonify(package), 200
    else:
        return jsonify({"error": "Package not found"}), 404

@app.route('/api/admin/search', methods=['POST'])
def admin_search():
    if 'user' not in session or session.get('role') != 'admin':
         return jsonify({"error": "Unauthorized"}), 403

    if packages_collection is None:
        return jsonify({"error": "Database not connected"}), 500
    
    query = request.json.get('query')
    if not query:
        return jsonify({"error": "Query required"}), 400

    # Search by tracking_id, sender_mobile, or receiver_mobile
    # Using regex for partial match could be good, but exact match is safer for IDs. 
    # Let's try exact match for ID and partial for mobile? Or simple OR query.
    # User said "mobile no or shipment id".
    
    search_filter = {
        "$or": [
            {"tracking_id": query},
            {"sender_mobile": query},
            {"receiver_mobile": query},
            # Allow partial match for mobile if needed, but exact is clearer for now
             {"tracking_id": {"$regex": query, "$options": "i"}} # Case insensitive partial ID
        ]
    }
    
    results = list(packages_collection.find(search_filter).sort('created_at', -1))
    
    # Convert ObjectIds to str if necessary, or just rely on jsonify (pymongo helpers often needed)
    for res in results:
        res['_id'] = str(res['_id'])
        
    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=True)
