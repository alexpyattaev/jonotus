from flask import Blueprint, request, make_response, jsonify, abort
import os
import json
import jwt

from config import JWT_SECRET_KEY, JWT_ALGORITHM, QUEUE_DIR, SEQUENCE_NUMBERS_DIR
from data_storage_classes import Queue
from utils import extract_and_validate_uuid, get_user_id
from queue_manager import QueueManager

# Initialize queue manager
queue_manager = QueueManager()

bp = Blueprint('queue', __name__)


def generate_jwt(data):
    return jwt.encode(data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt(token):
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def try_load_queue(queue_uuid)->Queue:
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
            return Queue.from_json(f.read())
    except json.JSONDecodeError:
        abort(500, description=f"Queue file {queue_uuid} contains invalid JSON.")
    except Exception as e:
        abort(500, description=f"Unexpected error while loading queue: {e}")


def get_next_sequence_number(queue_uuid)->int:
    sequence_file = os.path.join(SEQUENCE_NUMBERS_DIR, f"{queue_uuid}")

    if not os.path.exists(sequence_file):
        with open(sequence_file, 'w') as f:
            f.write('1')
        return 1

   
    with open(sequence_file, 'r+') as f:
        current_sequence = int(f.read().strip())
        next_sequence = current_sequence + 1
        f.seek(0)
        f.write(str(next_sequence))
        f.truncate()

    return next_sequence

@bp.route('/delete_cookie')
def delete_cookie():
    queue_uuid = request.args.get('uuid')
    if not queue_uuid or len(queue_uuid) > 512:
        abort(400, description="Queue UUID is required.")

  
    response = make_response(jsonify({
        'message': 'User cookie has been deleted.'
    }))

   
    response.delete_cookie(queue_uuid)

    return response

@bp.route('/get_sequence_number')
def get_sequence_number():
    queue_uuid = extract_and_validate_uuid(request)
    # Track queue access when user gets a sequence number
    queue_manager.track_access(str(queue_uuid))

    queue = try_load_queue(queue_uuid)

   
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = get_user_id(request) 

    encoded_jwt = request.cookies.get(str(queue_uuid), None)
    if encoded_jwt is not None:
        decoded_jwt = decode_jwt(encoded_jwt)
    else:
        decoded_jwt = None
    if decoded_jwt:
        sequence_number = int(decoded_jwt["sequence_number"])
    else:
        sequence_number = get_next_sequence_number(queue_uuid)
    if queue.max_slots > 0 and sequence_number > queue.max_slots:
        abort(400, "Out of slots for today!")

    
    jwt_data = {
        "sequence_number": sequence_number
    }
    encoded_jwt = generate_jwt(jwt_data)

   
    response = make_response(jsonify({
        'sequence_number': sequence_number
    }))

    
    response.set_cookie('user_id', user_id)
    response.set_cookie(str(queue_uuid), encoded_jwt)

    return response
