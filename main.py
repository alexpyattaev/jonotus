from flask import Flask, request,redirect, make_response, jsonify, render_template, url_for, abort
import hashlib
import uuid
import re
import os
import json
import jwt

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management
# Directory to store queue JSON files
QUEUE_DIR = "queues"
os.makedirs(QUEUE_DIR, exist_ok=True)

SEQUENCE_NUMBERS_DIR = "sequence_numbers"
os.makedirs(SEQUENCE_NUMBERS_DIR, exist_ok=True)

JWT_SECRET_KEY = "your_secret_key"  # Replace with a strong, secure key
JWT_ALGORITHM = "HS256"

# Utility to generate a JWT
def generate_jwt(data):
    return jwt.encode(data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

# Utility to decode a JWT
def decode_jwt(token):
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Utility function to validate a queue UUID
def try_load_queue(queue_uuid):
    """
    Load the content of a queue by its UUID.

    Args:
        queue_uuid (str): The UUID of the queue.

    Returns:
        dict: The queue content if successfully loaded, or None if the queue does not exist.

    Raises:
        ValueError: If the queue_uuid is invalid.
    """
    if not queue_uuid:
        abort(400, description="Queue UUID must be provided.")

    queue_file = os.path.join(QUEUE_DIR, f"{queue_uuid}.json")

    if not os.path.exists(queue_file):
        abort(404, description=f"Queue with UUID {queue_uuid} does not exist.")

    try:
        with open(queue_file, 'r') as f:
            queue_content = json.load(f)
        return queue_content
    except json.JSONDecodeError:
        abort(500, description=f"Queue file {queue_uuid} contains invalid JSON.")
    except Exception as e:
        abort(500, description=f"Unexpected error while loading queue: {e}")

# Utility function to get the next sequence number for a queue
def get_next_sequence_number(queue_uuid):
    sequence_file = os.path.join(SEQUENCE_NUMBERS_DIR, f"{queue_uuid}")

    # If the sequence file does not exist, initialize it to 1
    if not os.path.exists(sequence_file):
        with open(sequence_file, 'w') as f:
            f.write('1')
        return 1

    # Read the current sequence number, increment it, and save
    with open(sequence_file, 'r+') as f:
        current_sequence = int(f.read().strip())
        next_sequence = current_sequence + 1
        f.seek(0)
        f.write(str(next_sequence))
        f.truncate()

    return next_sequence

@app.route('/delete_cookie')
def delete_cookie():
    queue_uuid = request.args.get('uuid')
    if not queue_uuid or len(queue_uuid) > 512:
        abort(400, description="Queue UUID is required.")

    # Create a response object
    response = make_response(jsonify({
        'message': 'User cookie has been deleted.'
    }))

    # Delete the user_id cookie
    response.delete_cookie(queue_uuid)

    return response



# Regex pattern for HH:MM validation
time_pattern = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")

# Route to handle form submission
@app.route('/submit', methods=['POST'])
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
    return redirect(url_for('show_queues'))

@app.route('/new')
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

# Function to generate a user ID from the client's IP or some unique identifier
def get_user_id():
    user_ip = request.remote_addr  # Use IP address for simplicity
    user_agent = request.headers.get('User-Agent')  # Optionally, you can combine with User-Agent or other info
    return hashlib.sha256(f'{user_ip}{user_agent}'.encode()).hexdigest()


@app.route('/get_sequence_number')
def get_sequence_number():
    # Get queue UUID from query parameter
    queue_uuid = request.args.get('uuid')
    if not queue_uuid:
        abort(400, description="Queue UUID is required.")

    # Check if the queue exists
    queue = try_load_queue(queue_uuid)

    # Get user ID (hashed based on client information)
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = get_user_id()  # Function to generate a unique user ID

    encoded_jwt = request.cookies.get(queue_uuid, None)
    if encoded_jwt is not None:
        decoded_jwt = decode_jwt(encoded_jwt)
    else:
        decoded_jwt = None
    if decoded_jwt:
        sequence_number = decoded_jwt["sequence_number"]
    else:
        sequence_number = get_next_sequence_number(queue_uuid)

    # Generate a JWT with the queue UUID and position
    jwt_data = {
        "sequence_number": sequence_number
    }
    encoded_jwt = generate_jwt(jwt_data)


    # Create a response object
    response = make_response(jsonify({
        'sequence_number': sequence_number
    }))

    # Set the user ID in a cookie for future visits
    response.set_cookie('user_id', user_id)
    response.set_cookie(queue_uuid, encoded_jwt)

    return response

@app.route('/')
def index():
    queue_uuid = request.args.get('uuid')
    if not queue_uuid:
        abort(400, description="Queue UUID is required.")
    # Render the HTML page
    return render_template('index.html', queue_uuid=queue_uuid)

if __name__ == '__main__':
    app.run(debug=True)
