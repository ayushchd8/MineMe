from .base import db, BaseModel
from datetime import datetime

class SyncLog(db.Model, BaseModel):
    """Model for tracking synchronization operations."""
    
    __tablename__ = 'sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    object_type = db.Column(db.String(100), nullable=False)  # e.g., 'Lead', 'Contact'
    sync_type = db.Column(db.String(50), nullable=False)  # 'full' or 'incremental'
    status = db.Column(db.String(50), nullable=False)  # 'started', 'completed', 'failed'
    
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    
    records_processed = db.Column(db.Integer, default=0)
    records_created = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    records_deleted = db.Column(db.Integer, default=0)
    
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<SyncLog {self.object_type} {self.sync_type} {self.status}>'
    
    def to_dict(self):
        """Convert sync log to dictionary for API responses."""
        return {
            'id': self.id,
            'object_type': self.object_type,
            'sync_type': self.sync_type,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'records_processed': self.records_processed,
            'records_created': self.records_created,
            'records_updated': self.records_updated,
            'records_deleted': self.records_deleted,
            'error_message': self.error_message
        }
    
    @classmethod
    def get_latest_successful_sync(cls, object_type):
        """Get the latest successful sync for an object type."""
        return cls.query.filter_by(
            object_type=object_type,
            status='completed'
        ).order_by(cls.end_time.desc()).first()
    
    @classmethod
    def get_recent_logs(cls, object_type=None, limit=10):
        """Get recent sync logs."""
        query = cls.query
        if object_type:
            query = query.filter_by(object_type=object_type)
        return query.order_by(cls.start_time.desc()).limit(limit).all() 