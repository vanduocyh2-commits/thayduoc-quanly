import os
from pathlib import Path
from flask import Flask, send_from_directory, abort, jsonify

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=None)

# Only public frontend assets may be served. Never expose database.json,
# source code, environment files, or deployment credentials.
PUBLIC_EXTENSIONS = {'.html', '.css', '.js', '.mjs', '.png', '.jpg',
                     '.jpeg', '.gif', '.svg', '.webp', '.ico', '.woff',
                     '.woff2', '.ttf', '.pdf', '.map'}

@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/data', methods=['GET', 'POST'])
def handle_data():
    response = jsonify({
        'status': 'error',
        'message': 'Legacy bulk-data endpoint disabled: authentication required'
    })
    response.headers['Cache-Control'] = 'no-store'
    return response, 403

@app.route('/<path:filename>')
def public_asset(filename):
    parts = Path(filename).parts
    if (not parts or any(part.startswith('.') for part in parts)
            or Path(filename).suffix.lower() not in PUBLIC_EXTENSIONS
            or filename.lower() == 'database.json'):
        abort(404)
    return send_from_directory(BASE_DIR, filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
