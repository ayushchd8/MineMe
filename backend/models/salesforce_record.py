from .base import db, BaseModel
import json

class SalesforceRecord(db.Model, BaseModel):
    """Model representing a record from Salesforce (e.g., a specific Account, Contact, etc.)."""
    
    __tablename__ = 'salesforce_records'
    
    id = db.Column(db.Integer, primary_key=True)
    sf_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    object_id = db.Column(db.Integer, db.ForeignKey('salesforce_objects.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    last_modified_date = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<SalesforceRecord {self.sf_id}>'
    
    @property
    def data_dict(self):
        """Return the data as a dictionary."""
        if isinstance(self.data, str):
            return json.loads(self.data)
        return self.data
    
    @classmethod
    def get_by_sf_id(cls, sf_id):
        """Get a record by its Salesforce ID."""
        return cls.query.filter_by(sf_id=sf_id).first()
    
    @classmethod
    def get_by_object_id(cls, object_id, include_deleted=False):
        """Get all records for a specific Salesforce object."""
        query = cls.query.filter_by(object_id=object_id)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.all() 