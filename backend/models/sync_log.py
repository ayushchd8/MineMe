from .base import db, BaseModel

class SyncLog(db.Model, BaseModel):
    """Model for logging synchronization events with Salesforce."""
    
    __tablename__ = 'sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('salesforce_objects.id'), nullable=True)
    sync_type = db.Column(db.String(50), nullable=False)  # full, incremental
    records_processed = db.Column(db.Integer, default=0)
    records_created = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    records_deleted = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), nullable=False, default='started')  # started, completed, failed
    error_message = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    object = db.relationship('SalesforceObject', backref='sync_logs')
    
    def __repr__(self):
        return f'<SyncLog {self.id} - {self.sync_type} - {self.status}>'
    
    @classmethod
    def get_latest_successful_sync(cls, object_id=None):
        """Get the latest successful sync log for a specific object or all objects."""
        query = cls.query.filter_by(status='completed')
        if object_id:
            query = query.filter_by(object_id=object_id)
        return query.order_by(cls.end_time.desc()).first() 