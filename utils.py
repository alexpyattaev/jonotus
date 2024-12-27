import uuid
from flask import abort
import hashlib


# Function to generate a user ID from the client's IP or some unique identifier
def get_user_id(request):
    user_ip = request.remote_addr  # Use IP address for simplicity
    user_agent = request.headers.get('User-Agent')  # Optionally, you can combine with User-Agent or other info
    return hashlib.sha256(f'{user_ip}{user_agent}'.encode()).hexdigest()

def extract_and_validate_uuid(request)->uuid.UUID:
    queue_uuid = request.args.get('uuid')
    if not queue_uuid or len(queue_uuid) > 512:
        abort(400, description="Queue UUID is required.")

    try:
        # Validate if the UUID is correctly formatted
        return uuid.UUID(queue_uuid)
    except ValueError:
        # If the UUID format is incorrect, return an error
        abort(400, description="Invalid UUID format")
