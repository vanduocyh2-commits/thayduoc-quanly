from flask import Flask, send_from_directory, request, jsonify
import os
import json

app = Flask(__name__)

DATA_FILE = 'database.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"classes": [], "exams": [], "grades": []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {"classes": [], "exams": [], "grades": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(load_data())

@app.route('/api/data', methods=['POST'])
def update_data():
    req_data = request.json
    save_data(req_data)
    return jsonify({"status": "success", "message": "Đã lưu dữ liệu thành công!"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)