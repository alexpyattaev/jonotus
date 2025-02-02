import dataclasses
import datetime
import json

# Custom JSON Encoder for datetime.time
def time_converter(obj):
    if isinstance(obj, datetime.time):
        # Convert time object to string (e.g., 'HH:MM:SS')
        return obj.strftime('%H:%M:%S')
    raise TypeError(f"Type {type(obj)} not serializable")

@dataclasses.dataclass
class Queue:
    name:str
    opening_time: datetime.time
    closing_time: datetime.time
    max_slots:int

    def as_json(self):
        x = dataclasses.asdict(self)
        return json.dumps(x, default=time_converter)

    @classmethod
    def from_json(cls, data):# Custom function to load a Queue object from JSON
        data = json.loads(data)
        # Parse the time strings and convert them to datetime.time objects
        data['opening_time'] = datetime.datetime.strptime(data['opening_time'], '%H:%M:%S').time()
        data['closing_time'] = datetime.datetime.strptime(data['closing_time'], '%H:%M:%S').time()
        # Create Queue object from the dictionary
        return cls(**data)
