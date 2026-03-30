from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import os

# Load environment from .env (local development)
from dotenv import load_dotenv
load_dotenv()

# Import local database helpers
from database import init_database, add_contact, get_visitor_count, increment_visitor_count, get_all_contacts

app = Flask(__name__, static_folder='.')
CORS(app)

# Initialize database on startup
init_database()

# Serve static files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    """Serve the standalone admin HTML page."""
    return send_from_directory('.', 'admin.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# API Routes

@app.route('/api/contacts', methods=['GET'])
def list_contacts():
    """Return all contact messages for the admin dashboard."""
    try:
        contacts = get_all_contacts()
        # Normalize to simple dicts for JSON
        serialized = [
            {
                'id': c['id'],
                'name': c['name'],
                'email': c['email'],
                'message': c['message'],
            }
            for c in contacts
        ]
        return jsonify({'success': True, 'contacts': serialized}), 200
    except Exception as e:
        print(f"Error fetching contacts: {e}")
        return jsonify({'success': False, 'error': 'Failed to load contacts'}), 500

@app.route('/api/contact', methods=['POST'])
def contact():
    """Handle contact form submissions"""
    try:
        data = request.get_json()
        
        # Validate input
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        if not name or not email or not message:
            return jsonify({'error': 'All fields are required', 'success': False}), 400
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email address', 'success': False}), 400
        
        # Save to database
        success = add_contact(name, email, message)
        
        if success:
            return jsonify({
                'message': 'Message sent successfully! I will get back to you soon.',
                'success': True
            }), 200
        else:
            return jsonify({'error': 'Failed to save message. Please try again.', 'success': False}), 500
            
    except Exception as e:
        print(f"Error in contact endpoint: {e}")
        return jsonify({'error': 'Internal server error', 'success': False}), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    """Return visitor statistics"""
    try:
        # Increment visitor count on each visit
        visitor_count = increment_visitor_count()
        
        return jsonify({
            'visitors': visitor_count,
            'success': True
        }), 200
        
    except Exception as e:
        print(f"Error in stats endpoint: {e}")
        return jsonify({'error': 'Internal server error', 'success': False}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Server is running'
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"Starting server on 0.0.0.0:{port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
