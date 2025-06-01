from .base import db, BaseModel
from datetime import datetime

class Lead(db.Model, BaseModel):
    """Model for storing Salesforce Lead records."""
    
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    sf_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    
    # Lead specific fields
    name = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(100), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(100), nullable=True)
    lead_source = db.Column(db.String(255), nullable=True)
    last_activity_date = db.Column(db.DateTime, nullable=True)
    
    # Sync tracking
    sf_last_modified_date = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Lead {self.name} ({self.sf_id})>'
    
    def to_dict(self):
        """Convert lead to dictionary for API responses."""
        return {
            'Id': self.sf_id,
            'Name': self.name,
            'Title': self.title,
            'Email': self.email,
            'Phone': self.phone,
            'Company': self.company,
            'Status': self.status,
            'LeadSource': self.lead_source,
            'LastActivityDate': self.last_activity_date.isoformat() if self.last_activity_date else None,
            'last_sync': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_sf_id(cls, sf_id):
        """Get a lead by its Salesforce ID."""
        return cls.query.filter_by(sf_id=sf_id, is_deleted=False).first()
    
    @classmethod
    def get_all_active(cls):
        """Get all active (non-deleted) leads."""
        return cls.query.filter_by(is_deleted=False).all()
    
    @classmethod
    def update_from_sf_data(cls, sf_data):
        """Update or create a lead from Salesforce data."""
        sf_id = sf_data.get('Id')
        if not sf_id:
            return None
            
        lead = cls.get_by_sf_id(sf_id)
        
        if not lead:
            lead = cls(sf_id=sf_id)
        
        # Update fields from Salesforce data
        lead.name = sf_data.get('Name')
        lead.title = sf_data.get('Title')
        lead.email = sf_data.get('Email')
        lead.phone = sf_data.get('Phone')
        lead.company = sf_data.get('Company')
        lead.status = sf_data.get('Status')
        lead.lead_source = sf_data.get('LeadSource')
        
        # Parse LastActivityDate if present
        if sf_data.get('LastActivityDate'):
            try:
                lead.last_activity_date = datetime.fromisoformat(sf_data['LastActivityDate'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        # Parse LastModifiedDate if present  
        if sf_data.get('LastModifiedDate'):
            try:
                lead.sf_last_modified_date = datetime.fromisoformat(sf_data['LastModifiedDate'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        lead.is_deleted = False
        return lead.save() 