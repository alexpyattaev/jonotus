from flask import Flask, request, render_template
import os
import json

app = Flask(__name__)

import register_queue
import queue_position
from utils import extract_and_validate_uuid

from config import QUEUE_DIR, SEQUENCE_NUMBERS_DIR

@app.route('/')
def new_queue():
    return render_template('register.html')


# Route to display all the queues
@app.route('/queues')
def show_queues():
    # List all JSON files in the queues directory
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
    return register_queue.submit(request)

@app.route('/queue')
def current_queue():
    queue_uuid = extract_and_validate_uuid(request)
    queue = queue_position.try_load_queue(queue_uuid)
    return render_template('current_queue.html', queue_uuid=str(queue_uuid), queue_name = queue.name)

if __name__ == '__main__':
    os.makedirs(QUEUE_DIR, exist_ok=True)
    os.makedirs(SEQUENCE_NUMBERS_DIR, exist_ok=True)
    app.run(debug=True)
