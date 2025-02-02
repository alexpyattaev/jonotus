from io import BytesIO
from flask import  render_template, Response, request, jsonify, redirect, url_for
import re
import os
import uuid
import datetime
import qrcode

from utils import extract_and_validate_uuid
from config import QUEUE_DIR
from data_storage_classes import Queue

# Much crutches
from __main__ import app

def qrcode_url(host, queue_uuid):
    return f"{request.scheme}://{request.host}/queue?uuid={queue_uuid}"

@app.route('/qr_code')
def qr_code_maker():
    queue_uuid = extract_and_validate_uuid(request)
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


def parse_time(time_str)->datetime.time:
    # Regex pattern to match the HH:MM format
    pattern = r"^(\d{2}):(\d{2})$"
    try:
        # Try to match the pattern
        match = re.match(pattern, time_str)
        assert match is not None
        # Extract the hours and minutes and convert them to integers
        hours = int(match.group(1))
        minutes = int(match.group(2))
        return datetime.time(hours,minutes)
    except:
        raise ValueError(f"Invalid time for HH:MM format: {time_str}")

def validate_str(s, name, max_len:int=512)->list[str]:
    errors = []
    if s is None or not s.strip():
        errors.append(f"{name} is required and cannot be empty.")
    elif len(s) > 512:
        errors.append(f"{name} too long, please use less characters")
    return errors


def submit(request):
    # Get form data
    queue_name = request.form.get('queue_name')
    opening_time = request.form.get('opening_time')
    closing_time = request.form.get('closing_time')
    max_slots = request.form.get('max_slots')
    # Validation
    errors = []
    errors.extend(validate_str (queue_name, "Queue name"))

    try:
        opening_time = parse_time(opening_time)
    except Exception:
        errors.append("Opening time is required and must be in HH:MM format.")

    try:
        closing_time = parse_time(closing_time)
    except Exception:
        errors.append("Closing time is required and must be in HH:MM format.")

    if opening_time >= closing_time:
        errors.append("Opening time must be earlier than closing time.")

    try:
        max_slots = int(max_slots)
        assert( max_slots >= 0)
    except ValueError:
        errors.append("Max slots must be a non-negative integer.")

    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    # Store the submitted data

    queue = Queue(
        name= queue_name,
        opening_time= opening_time,
        closing_time= closing_time,
        max_slots =max_slots)
    # Generate a new UUID for the queue and save as a JSON file
    queue_id = str(uuid.uuid4())
    queue_file = os.path.join(QUEUE_DIR, f"{queue_id}.json")
    with open(queue_file, 'w') as f:
        f.write(queue.as_json())

    return redirect(url_for('show_queue_code') + f"?uuid={queue_id}")

