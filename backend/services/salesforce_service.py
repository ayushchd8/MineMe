from simple_salesforce import Salesforce
from datetime import datetime, timedelta
import logging

class SalesforceService:
    """Service for interacting with the Salesforce API."""
    
    def __init__(self, username, password, security_token, domain='login'):
        """Initialize the Salesforce service with credentials."""
        self.username = username
        self.password = password
        self.security_token = security_token
        self.domain = domain
        self.sf = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """Establish a connection to Salesforce."""
        try:
            self.sf = Salesforce(
                username=self.username,
                password=self.password,
                security_token=self.security_token,
                domain=self.domain
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Salesforce: {str(e)}")
            return False
    
    def get_object_metadata(self, object_name):
        """Get metadata for a Salesforce object."""
        if not self.sf:
            if not self.connect():
                return None
        
        try:
            object_desc = getattr(self.sf, object_name).describe()
            return {
                'name': object_desc['label'],
                'api_name': object_desc['name'],
                'description': object_desc.get('description', ''),
                'fields': [
                    {
                        'name': field['label'],
                        'api_name': field['name'],
                        'type': field['type'],
                        'required': not field['nillable']
                    }
                    for field in object_desc['fields']
                ]
            }
        except Exception as e:
            self.logger.error(f"Error fetching metadata for {object_name}: {str(e)}")
            return None
    
    def get_all_records(self, object_name, fields='*'):
        """Get all records for a Salesforce object."""
        if not self.sf:
            if not self.connect():
                return []
        
        try:
            if fields == '*':
                # Get all fields from object metadata
                metadata = self.get_object_metadata(object_name)
                if not metadata:
                    return []
                
                fields = [field['api_name'] for field in metadata['fields']]
            
            # Build SOQL query
            fields_str = ', '.join(fields)
            query = f"SELECT {fields_str} FROM {object_name}"
            
            # Execute query
            result = self.sf.query_all(query)
            return result['records']
        except Exception as e:
            self.logger.error(f"Error fetching records for {object_name}: {str(e)}")
            return []
    
    def get_updated_records(self, object_name, last_sync_time, fields='*'):
        """Get records updated since the last sync time."""
        if not self.sf:
            if not self.connect():
                return []
        
        try:
            # Adjust timezone if needed
            if last_sync_time.tzinfo is None:
                last_sync_time = last_sync_time.replace(tzinfo=datetime.utcnow().astimezone().tzinfo)
            
            # Format date for SOQL
            last_sync_str = last_sync_time.strftime('%Y-%m-%dT%H:%M:%S%z')
            
            if fields == '*':
                # Get all fields from object metadata
                metadata = self.get_object_metadata(object_name)
                if not metadata:
                    return []
                
                fields = [field['api_name'] for field in metadata['fields']]
            
            # Build SOQL query
            fields_str = ', '.join(fields)
            query = f"SELECT {fields_str} FROM {object_name} WHERE LastModifiedDate >= {last_sync_str}"
            
            # Execute query
            result = self.sf.query_all(query)
            return result['records']
        except Exception as e:
            self.logger.error(f"Error fetching updated records for {object_name}: {str(e)}")
            return []
    
    def get_deleted_records(self, object_name, start_date, end_date=None):
        """Get records deleted between start_date and end_date."""
        if not self.sf:
            if not self.connect():
                return []
        
        try:
            if end_date is None:
                end_date = datetime.utcnow()
            
            # Adjust timezone if needed
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=datetime.utcnow().astimezone().tzinfo)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=datetime.utcnow().astimezone().tzinfo)
            
            deleted_records = self.sf.get_deleted_records(object_name, start_date, end_date)
            return deleted_records.get('deletedRecords', [])
        except Exception as e:
            self.logger.error(f"Error fetching deleted records for {object_name}: {str(e)}")
            return [] 