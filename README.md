# Jonotus Queue Management System

A Flask-based queue management system for creating and managing queues with QR code support. This system allows organizations to create digital queues and users to track their position using QR codes.

## Features

- Create and manage digital queues
- Generate QR codes for queue access
- Real-time queue position tracking
- Multiple queue support
- Web-based interface
- Docker deployment support

## Prerequisites

- Python 3.13+
- Flask
- PyJWT
- Pillow
- qrcode
- Docker (for containerized deployment)

## Installation

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/alexpyattaev/jonotus.git
cd jonotus
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

The application will be available at `http://localhost:5000`

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t jonotus .
```

2. Run the container:
```bash
docker run -d -p 5000:5000 --name jonotus_app jonotus
```

## Project Structure

```
jonotus/
├── main.py                 # Main application entry point
├── config.py              # Configuration settings
├── register_queue.py      # Queue registration functionality
├── queue_position.py      # Queue position management
├── utils.py              # Utility functions
├── data_storage_classes.py # Data models
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── templates/            # HTML templates
│   ├── register.html
│   ├── queues.html
│   ├── current_queue.html
│   └── show_queue_code.html
├── static/              # Static assets
│   └── style.css
├── queues/             # Queue data storage directory
└── sequence_numbers/   # Sequence number storage directory
```

## Usage

1. **Creating a New Queue**
   - Visit the homepage
   - Fill in queue details (name, opening time, closing time, max slots)
   - Submit to create queue

2. **Managing Queues**
   - Access `/queues` to view all active queues
   - Use QR codes for queue position tracking
   - Monitor queue status and positions

## Development

The project uses Flask blueprints for modularity:
- `register_bp`: Handles queue registration
- `queue_bp`: Manages queue positions

## Queue Management

The system includes automatic queue management features:
- Maximum 1 million queues by default (configurable)
- Automatic cleanup of least accessed queues when limit is exceeded
- Usage tracking with access count and timestamp
- JSON-based storage for queue usage data

### Testing
```bash
pytest tests/test_queue_cleanup.py -v
```

Tests verify:
- Queue limit enforcement
- Automatic cleanup of least used queues
- Usage tracking accuracy

## Data Storage

- Queue data is stored in JSON format in the `queues` directory
- Sequence numbers are maintained in the `sequence_numbers` directory
- Queue usage data stored in `queues/_queue_usage.json`

## Security

- JWT-based authentication for queue access
- QR code validation
- Rate limiting for abuse prevention

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the terms specified by the repository owner.

## Authors

- alexpyattaev
