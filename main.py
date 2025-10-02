from flask import Flask, request, render_template
import os
import json

app = Flask(__name__)

from register_queue import bp as register_bp, submit
from queue_position import bp as queue_bp, try_load_queue
from utils import extract_and_validate_uuid

from config import QUEUE_DIR, SEQUENCE_NUMBERS_DIR

app.register_blueprint(register_bp)
app.register_blueprint(queue_bp)

@app.route('/')
def new_queue():
    return render_template('register.html')



@app.route('/queues')
def show_queues():
    
    queues = []
    for filename in os.listdir(QUEUE_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(QUEUE_DIR, filename)
            with open(file_path, 'r') as f:
                queue_data = json.load(f)
                queues.append(queue_data)
    return render_template('queues.html', queues=queues)

@app.route('/new_queue_form_submit', methods=['POST'])
def new_queue_form_submit():
    print("submitting")
    return submit(request)

@app.route('/queue')
def current_queue():
    queue_uuid = extract_and_validate_uuid(request)
    queue = try_load_queue(queue_uuid)
    return render_template('current_queue.html', queue_uuid=str(queue_uuid), queue_name = queue.name)

if __name__ == '__main__':
    os.makedirs(QUEUE_DIR, exist_ok=True)
    os.makedirs(SEQUENCE_NUMBERS_DIR, exist_ok=True)
    # Enable debug mode and allow external access
    app.debug = True
    app.run(host='0.0.0.0', port=8080, threaded=True)
