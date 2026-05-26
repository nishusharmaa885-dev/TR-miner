from flask import Flask, jsonify, send_from_directory
import os

app = Flask(__name__, static_folder='.')

# Get port from environment variable (Render sets this automatically)
port = int(os.environ.get('PORT', 5000))

@app.route('/')
def home():
    return jsonify({
        'message': 'Hello from Flask on Render!',
        'status': 'success',
        'environment': os.environ.get('ENVIRONMENT', 'development')
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/info')
def info():
    return jsonify({
        'app': 'Flask Render App',
        'version': '1.0.0',
        'python_version': os.sys.version
    })

@app.route('/index.html')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def serve_style():
    return send_from_directory('.', 'style.css')

@app.route('/app.js')
def serve_js():
    return send_from_directory('.', 'app.js')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
