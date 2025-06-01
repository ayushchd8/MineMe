from datetime import datetime
import logging
from ..models import SalesforceObject, SalesforceRecord, SyncLog, db
from .salesforce_service import SalesforceService

class SyncService:
    """Service for synchronizing data between Salesforce and the local database."""
    
    def __init__(self, sf_service=None, config=None):
        """Initialize the sync service."""
        self.logger = logging.getLogger(__name__)
        
        if sf_service:
            self.sf_service = sf_service
        elif config:
            self.sf_service = SalesforceService(
                username=config.SF_USERNAME,
                password=config.SF_PASSWORD,
                security_token=config.SF_SECURITY_TOKEN,
                domain=config.SF_DOMAIN
            )
        else:
            raise ValueError("Either sf_service or config must be provided")
    
    def register_object(self, object_api_name):
        """Register a Salesforce object for synchronization."""
        # Check if the object already exists
        existing_obj = SalesforceObject.get_by_api_name(object_api_name)
        if existing_obj:
            self.logger.info(f"Object {object_api_name} already registered")
            return existing_obj
        
        # Get object metadata from Salesforce
        metadata = self.sf_service.get_object_metadata(object_api_name)
        if not metadata:
            self.logger.error(f"Failed to get metadata for {object_api_name}")
            return None
        
        # Create the object in the database
        obj = SalesforceObject(
            name=metadata['name'],
            api_name=metadata['api_name'],
            description=metadata.get('description', '')
        )
        obj.save()
        
        self.logger.info(f"Object {object_api_name} registered successfully")
        return obj
    
    def sync_object(self, object_id=None, object_api_name=None, sync_type='full'):
        """Synchronize a Salesforce object with the local database."""
        # Get the object from the database
        obj = None
        if object_id:
            obj = SalesforceObject.get_by_id(object_id)
        elif object_api_name:
            obj = SalesforceObject.get_by_api_name(object_api_name)
        
        if not obj:
            self.logger.error("Object not found")
            return None
        
        # Create a sync log
        sync_log = SyncLog(
            object_id=obj.id,
            sync_type=sync_type,
            status='started',
            start_time=datetime.utcnow()
        )
        sync_log.save()
        
        try:
            if sync_type == 'full':
                result = self._perform_full_sync(obj, sync_log)
            else:
                result = self._perform_incremental_sync(obj, sync_log)
            
            # Update the sync log
            sync_log.status = 'completed'
            sync_log.end_time = datetime.utcnow()
            sync_log.save()
            
            # Update the object's last sync time
            obj.last_sync_time = datetime.utcnow()
            obj.save()
            
            return result
        except Exception as e:
            self.logger.error(f"Error during sync: {str(e)}")
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.end_time = datetime.utcnow()
            sync_log.save()
            return None
    
    def _perform_full_sync(self, obj, sync_log):
        """Perform a full sync of a Salesforce object."""
        # Get all records from Salesforce
        records = self.sf_service.get_all_records(obj.api_name)
        
        # Update sync log
        sync_log.records_processed = len(records)
        sync_log.save()
        
        # Clear existing records (optional, could also update them)
        # db.session.query(SalesforceRecord).filter_by(object_id=obj.id).delete()
        
        # Process each record
        created_count = 0
        updated_count = 0
        
        for sf_record in records:
            sf_id = sf_record['Id']
            
            # Check if the record already exists
            existing_record = SalesforceRecord.get_by_sf_id(sf_id)
            
            if existing_record:
                # Update existing record
                existing_record.data = sf_record
                existing_record.last_modified_date = datetime.utcnow()
                existing_record.is_deleted = False
                existing_record.save()
                updated_count += 1
            else:
                # Create new record
                new_record = SalesforceRecord(
                    sf_id=sf_id,
                    object_id=obj.id,
                    data=sf_record,
                    last_modified_date=datetime.utcnow()
                )
                new_record.save()
                created_count += 1
        
        # Update sync log
        sync_log.records_created = created_count
        sync_log.records_updated = updated_count
        sync_log.save()
        
        return {
            'processed': len(records),
            'created': created_count,
            'updated': updated_count,
            'deleted': 0
        }
    
    def _perform_incremental_sync(self, obj, sync_log):
        """Perform an incremental sync of a Salesforce object."""
        # Get the last successful sync time
        last_sync = SyncLog.get_latest_successful_sync(obj.id)
        
        if not last_sync or not obj.last_sync_time:
            # If no previous sync, do a full sync
            return self._perform_full_sync(obj, sync_log)
        
        # Get records updated since the last sync
        updated_records = self.sf_service.get_updated_records(obj.api_name, obj.last_sync_time)
        
        # Get records deleted since the last sync
        deleted_records = self.sf_service.get_deleted_records(
            obj.api_name,
            obj.last_sync_time,
            datetime.utcnow()
        )
        
        # Update sync log
        sync_log.records_processed = len(updated_records) + len(deleted_records)
        sync_log.save()
        
        # Process updated records
        created_count = 0
        updated_count = 0
        
        for sf_record in updated_records:
            sf_id = sf_record['Id']
            
            # Check if the record already exists
            existing_record = SalesforceRecord.get_by_sf_id(sf_id)
            
            if existing_record:
                # Update existing record
                existing_record.data = sf_record
                existing_record.last_modified_date = datetime.utcnow()
                existing_record.is_deleted = False
                existing_record.save()
                updated_count += 1
            else:
                # Create new record
                new_record = SalesforceRecord(
                    sf_id=sf_id,
                    object_id=obj.id,
                    data=sf_record,
                    last_modified_date=datetime.utcnow()
                )
                new_record.save()
                created_count += 1
        
        # Process deleted records
        deleted_count = 0
        
        for deleted_info in deleted_records:
            sf_id = deleted_info['id']
            
            # Check if the record exists
            existing_record = SalesforceRecord.get_by_sf_id(sf_id)
            
            if existing_record:
                # Mark record as deleted
                existing_record.is_deleted = True
                existing_record.save()
                deleted_count += 1
        
        # Update sync log
        sync_log.records_created = created_count
        sync_log.records_updated = updated_count
        sync_log.records_deleted = deleted_count
        sync_log.save()
        
        return {
            'processed': len(updated_records) + len(deleted_records),
            'created': created_count,
            'updated': updated_count,
            'deleted': deleted_count
        } 