from io import BytesIO
from flask import Flask, render_template, Response, request, abort, jsonify, redirect, url_for
import json
import qrcode
import re
import os
import uuid

from utils import extract_and_validate_uuid
from config import QUEUE_DIR

# Much crutches
from __main__ import app

def qrcode_url(host, queue_uuid):
    return f"{request.scheme}://{request.host}/queue?uuid={queue_uuid}"

@app.route('/qr_code')
def qr_code_maker():
    queue_uuid = extract_and_validate_uuid(request)
    print(queue_uuid)
    # Generate a QR code
    qr = qrcode.QRCode(
        version=1,  # controls the size of the QR code
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qrcode_url (request.host, queue_uuid))
    qr.make(fit=True)

    # Convert QR code to an image and save it in memory (in a byte buffer)
    img = qr.make_image(fill='black', back_color='white')
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Return the image as a response to display it on the web page
    return Response(img_io, mimetype='image/png')

@app.route('/show_queue_code')
def show_queue_code():
    queue_uuid = extract_and_validate_uuid(request)
    url = qrcode_url(request, queue_uuid)
    return render_template('show_queue_code.html',queue_uuid= queue_uuid, url=url)

# Regex pattern for HH:MM validation
time_pattern = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")

def submit():
    # Get form data
    queue_name = request.form.get('queue_name')
    opening_time = request.form.get('opening_time')
    closing_time = request.form.get('closing_time')
    max_slots = request.form.get('max_slots')
    # Validation
    errors = []

    if queue_name is None or not queue_name.strip():
        errors.append("Queue name is required and cannot be empty.")
    elif len(queue_name) > 512:
        return 400

    # Validate opening_time
    if not opening_time or not time_pattern.match(opening_time):
        errors.append("Opening time is required and must be in HH:MM format.")

    # Validate closing_time
    if not closing_time or not time_pattern.match(closing_time):
        errors.append("Closing time is required and must be in HH:MM format.")

    # Ensure opening_time is before closing_time
    if opening_time and closing_time:
        if opening_time >= closing_time:
            errors.append("Opening time must be earlier than closing time.")

    # Validate max_slots
    if max_slots:
        try:
            max_slots = int(max_slots)
            if max_slots <= 0:
                errors.append("Max slots must be a positive integer.")
        except ValueError:
            errors.append("Max slots must be an integer.")
    else:
        max_slots = 10000  # Default value if not provided
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400
    # Store the submitted data
    queue_data = {
        'queue_name': queue_name,
        'opening_time': opening_time,
        'closing_time': closing_time,
        'max_slots': max_slots
    }
    # Generate a new UUID for the queue and save as a JSON file
    queue_id = str(uuid.uuid4())
    queue_file = os.path.join(QUEUE_DIR, f"{queue_id}.json")
    with open(queue_file, 'w') as f:
        json.dump(queue_data, f)
    #return jsonify({'success': True, 'message': 'Queue submitted successfully.'}), 200
    # Redirect to a page that shows all queues (optional)
    return redirect(url_for('current_queue') + f"?uuid={queue_id}")
