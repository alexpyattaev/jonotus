from flask import Flask, request,redirect, make_response, jsonify, render_template, url_for
import hashlib
import uuid
import itertools
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management

# Dictionary to store user sequence numbers (for demonstration purposes)
user_sequence = {

}
new_sequence_number_issuer = itertools.count(start=1)


@app.route('/delete_cookie')
def delete_cookie():
    # Create a response object
    response = make_response(jsonify({
        'message': 'User cookie has been deleted.'
    }))
    # Get the user_id from the cookie
    user_id = request.cookies.get('user_id')

    if user_id and user_id in user_sequence:
        # Remove the user from the sequence mapping when the cookie is deleted
        del user_sequence[user_id]
    # Delete the user_id cookie
    response.delete_cookie('user_id')

    return response


# This will hold the queue data in memory (you can replace this with a database)
queues = []

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

    if not queue_name or not queue_name.strip():
        errors.append("Queue name is required and cannot be empty.")

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
    queues.append({
        'queue_name': queue_name,
        'opening_time': opening_time,
        'closing_time': closing_time,
        'max_slots': max_slots
    })

    #return jsonify({'success': True, 'message': 'Queue submitted successfully.'}), 200
    # Redirect to a page that shows all queues (optional)
    return redirect(url_for('show_queues'))

@app.route('/new')
def new_queue():
    return render_template('register.html')


# Route to display all the queues
@app.route('/queues')
def show_queues():
    return render_template('queues.html', queues=queues)

# Function to generate a user ID from the client's IP or some unique identifier
def get_user_id():
    user_ip = request.remote_addr  # Use IP address for simplicity
    user_agent = request.headers.get('User-Agent')  # Optionally, you can combine with User-Agent or other info
    return hashlib.sha256(f'{user_ip}{user_agent}'.encode()).hexdigest()

@app.route('/get_sequence_number')
def get_sequence_number():
    # Get user ID (hashed based on client information)
    user_id = get_user_id()

    # Check if the user already has a sequence number stored
    if user_id in user_sequence:
        sequence_number = user_sequence[user_id]
    else:
        # If not, assign a new sequence number and store it
        sequence_number = next(new_sequence_number_issuer)
        user_sequence[user_id] = sequence_number

    # Create a response object
    response = make_response(jsonify({
        'sequence_number': sequence_number
    }))

    # Set the user ID in a cookie for future visits
    response.set_cookie('user_id', user_id)

    return response

@app.route('/')
def index():
        # Render the HTML page
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
