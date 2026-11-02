import os
import json
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__, static_folder='.', static_url_path='')
DB_FILE = 'database.json'

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Legacy bulk-data API is disabled until server-side authentication and
# per-role authorization are implemented. The browser portal uses Firebase
# directly; exposing the complete database here bypasses its access rules.
@app.route('/api/data', methods=['GET', 'POST'])
def handle_data():
    response = jsonify({"status": "error", "message": "Legacy data endpoint disabled: authentication required"})
    response.headers['Cache-Control'] = 'no-store'
    return response, 403

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)