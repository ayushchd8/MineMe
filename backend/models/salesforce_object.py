from .base import db, BaseModel

class SalesforceObject(db.Model, BaseModel):
    """Model representing a Salesforce object type (e.g., Account, Contact, Lead, etc.)."""
    
    __tablename__ = 'salesforce_objects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    api_name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_sync_time = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    records = db.relationship('SalesforceRecord', backref='object', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SalesforceObject {self.api_name}>'
    
    @classmethod
    def get_by_api_name(cls, api_name):
        """Get a Salesforce object by its API name."""
        return cls.query.filter_by(api_name=api_name).first()
    
    @classmethod
    def get_active_objects(cls):
        """Get all active Salesforce objects."""
        return cls.query.filter_by(is_active=True).all() 