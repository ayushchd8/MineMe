from datetime import datetime
import logging
from models import Lead, SyncLog, db

logger = logging.getLogger(__name__)

class LeadSyncService:
    """Service for synchronizing Lead data between Salesforce and the local database."""
    
    def __init__(self, sf_service):
        """Initialize the lead sync service with a Salesforce service."""
        self.sf_service = sf_service
    
    def sync_leads(self, sync_type='incremental'):
        """Synchronize leads from Salesforce to local database."""
        # Create sync log
        sync_log = SyncLog(
            object_type='Lead',
            sync_type=sync_type,
            status='started',
            start_time=datetime.utcnow()
        )
        sync_log.save()
        
        try:
            if sync_type == 'full':
                result = self._perform_full_sync(sync_log)
            else:
                result = self._perform_incremental_sync(sync_log)
            
            # Update sync log
            sync_log.status = 'completed'
            sync_log.end_time = datetime.utcnow()
            sync_log.records_processed = result['processed']
            sync_log.records_created = result['created']
            sync_log.records_updated = result['updated']
            sync_log.records_deleted = result['deleted']
            sync_log.save()
            
            logger.info(f"Lead sync completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Lead sync failed: {str(e)}")
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.end_time = datetime.utcnow()
            sync_log.save()
            raise
    
    def _perform_full_sync(self, sync_log):
        """Perform a full sync of all leads."""
        logger.info("Starting full lead sync")
        
        # Get all leads from Salesforce
        try:
            sf_leads = self.sf_service.get_all_records('Lead', [
                'Id', 'Name', 'Title', 'Email', 'Phone', 'Company', 
                'Status', 'LeadSource', 'LastActivityDate', 'LastModifiedDate'
            ])
        except Exception as e:
            logger.error(f"Failed to fetch leads from Salesforce: {str(e)}")
            raise
        
        created_count = 0
        updated_count = 0
        
        for sf_lead in sf_leads:
            try:
                existing_lead = Lead.get_by_sf_id(sf_lead['Id'])
                
                if existing_lead:
                    # Update existing lead
                    Lead.update_from_sf_data(sf_lead)
                    updated_count += 1
                else:
                    # Create new lead
                    Lead.update_from_sf_data(sf_lead)
                    created_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing lead {sf_lead.get('Id', 'unknown')}: {str(e)}")
                continue
        
        return {
            'processed': len(sf_leads),
            'created': created_count,
            'updated': updated_count,
            'deleted': 0
        }
    
    def _perform_incremental_sync(self, sync_log):
        """Perform an incremental sync of leads."""
        # Check if we have a previous successful sync
        last_sync = SyncLog.get_latest_successful_sync('Lead')
        
        if not last_sync:
            logger.info("No previous sync found, performing full sync")
            return self._perform_full_sync(sync_log)
        
        # Get the last sync time (use a buffer of 5 minutes to avoid missing records)
        last_sync_time = last_sync.start_time
        if last_sync_time:
            # Subtract 5 minutes as buffer for timezone/timing issues
            from datetime import timedelta
            last_sync_time = last_sync_time - timedelta(minutes=5)
        
        logger.info(f"Starting incremental lead sync from {last_sync_time}")
        
        try:
            # Get leads updated since last sync
            sf_leads = self.sf_service.get_updated_records_since('Lead', last_sync_time, [
                'Id', 'Name', 'Title', 'Email', 'Phone', 'Company', 
                'Status', 'LeadSource', 'LastActivityDate', 'LastModifiedDate'
            ])
        except Exception as e:
            logger.error(f"Failed to fetch updated leads from Salesforce: {str(e)}")
            # Fall back to full sync if incremental fails
            logger.info("Falling back to full sync")
            return self._perform_full_sync(sync_log)
        
        created_count = 0
        updated_count = 0
        
        for sf_lead in sf_leads:
            try:
                existing_lead = Lead.get_by_sf_id(sf_lead['Id'])
                
                if existing_lead:
                    # Update existing lead
                    Lead.update_from_sf_data(sf_lead)
                    updated_count += 1
                else:
                    # Create new lead
                    Lead.update_from_sf_data(sf_lead)
                    created_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing lead {sf_lead.get('Id', 'unknown')}: {str(e)}")
                continue
        
        return {
            'processed': len(sf_leads),
            'created': created_count,
            'updated': updated_count,
            'deleted': 0  # We don't handle deletions in this simple implementation
        } 