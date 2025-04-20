from mongoengine import Document, StringField, BooleanField, DateTimeField
from datetime import datetime

class PropertyListing(Document):
    # Required fields
    url = StringField(required=True, unique=True)
    broker = StringField(required=True)
    
    # Optional fields
    address = StringField()
    price = StringField()
    area = StringField()
    bedrooms = StringField()
    energy_label = StringField()
    furnished = BooleanField(default=False)
    including_bills = BooleanField(default=False)
    status = StringField()
    available_from = StringField()
    
    # Metadata
    created_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'property_listings',
        'indexes': [
            'url',
            'broker',
            ('broker', 'created_at'),
        ],
        'ordering': ['-created_at']
    }