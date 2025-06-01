from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

def setup_scheduler(app, sync_service, config):
    """Set up a scheduler to periodically sync data from Salesforce."""
    logger = logging.getLogger(__name__)
    
    # Create scheduler
    scheduler = BackgroundScheduler()
    
    # Add sync job for each active object
    with app.app_context():
        from ..models import SalesforceObject
        active_objects = SalesforceObject.get_active_objects()
        
        if not active_objects:
            logger.warning("No active Salesforce objects found for scheduling")
            return scheduler
        
        for obj in active_objects:
            # Add job to scheduler
            scheduler.add_job(
                func=sync_object_job,
                args=[app, sync_service, obj.id],
                trigger=IntervalTrigger(seconds=config.SYNC_INTERVAL),
                id=f'sync_{obj.api_name}',
                name=f'Sync {obj.name}',
                replace_existing=True
            )
            logger.info(f"Scheduled sync job for {obj.name} every {config.SYNC_INTERVAL} seconds")
    
    return scheduler

def sync_object_job(app, sync_service, object_id):
    """Job function to sync a Salesforce object."""
    logger = logging.getLogger(__name__)
    
    with app.app_context():
        logger.info(f"Starting scheduled sync for object ID {object_id}")
        result = sync_service.sync_object(object_id=object_id, sync_type='incremental')
        
        if result:
            logger.info(
                f"Sync completed: {result['processed']} records processed, "
                f"{result['created']} created, {result['updated']} updated, "
                f"{result['deleted']} deleted"
            )
        else:
            logger.error("Sync failed") 