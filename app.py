import os
from flask import Flask, render_template, request, jsonify
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'Ancel@230508'),
        database=os.getenv('DB_NAME', 'spend_tracker'),
        port=int(os.getenv('DB_PORT', 3306))
    )

@app.route('/')
def index():
    return render_template('index.html')

# User Login or Registration
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE LOWER(name) = LOWER(%s)", (name,))
    user = cursor.fetchone()

    if not user:
        # Register new user
        cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
        conn.commit()
        user_id = cursor.lastrowid
        status_message = f"Welcome, {name}! Account created."
    else:
        user_id = user['id']
        name = user['name']
        status_message = f"Welcome back, {name}!"

    cursor.close()
    conn.close()
    return jsonify({'user_id': user_id, 'name': name, 'message': status_message}), 200

# Get spends strictly for a specific user ID
@app.route('/api/spends/<int:user_id>', methods=['GET'])
def get_user_spends(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM spends WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    spends = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(spends)

# Add spend for a specific user ID
@app.route('/api/spends', methods=['POST'])
def add_spend():
    data = request.get_json()
    user_id = data.get('user_id')
    item = data.get('item')
    amount = data.get('amount')

    if not user_id or not item or not amount:
        return jsonify({'error': 'User ID, item, and amount are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO spends (user_id, item, amount) VALUES (%s, %s, %s)",
        (user_id, item, amount)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Spend saved successfully'}), 201

# Clear ONLY the specific user's spends (User account remains intact)
@app.route('/api/spends/<int:user_id>', methods=['DELETE'])
def clear_user_spends(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM spends WHERE user_id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Your spends were cleared successfully'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)