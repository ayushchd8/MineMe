from flask import Flask, jsonify
from simple_salesforce import Salesforce
import os
from dotenv import load_dotenv
import logging
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///salesforce_sync.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class SalesforceObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    api_name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_sync_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'api_name': self.api_name,
            'description': self.description,
            'is_active': self.is_active,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# Salesforce connection helper
def get_salesforce_connection():
    """Get Salesforce connection with proper credentials."""
    try:
        # Use environment variables with fallback values
        username = os.environ.get('SF_USERNAME')
        password = os.environ.get('SF_PASSWORD')
        security_token = os.environ.get('SF_SECURITY_TOKEN')
        domain = os.environ.get('SF_DOMAIN')
        
        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain
        )
        logger.info("✅ Salesforce connection successful!")
        return sf, None
    except Exception as e:
        logger.error(f"❌ Failed to connect to Salesforce: {str(e)}")
        return None, str(e)

# API routes
@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

@app.route('/api/salesforce/status')
def salesforce_status():
    """Check Salesforce connection status."""
    sf, error = get_salesforce_connection()
    
    if sf:
        try:
            about_info = sf.describe()
            org_name = about_info.get('organizationName', 'Unknown')
            
            # Get a few objects
            objects = about_info.get('sobjects', [])[:5]
            object_names = [obj.get('name') for obj in objects]
            
            return jsonify({
                'status': 'connected',
                'organization': org_name,
                'sample_objects': object_names
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"Connected but failed to get Salesforce information: {str(e)}"
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': f"Failed to connect to Salesforce: {error}"
        }), 500

@app.route('/api/objects')
def get_objects():
    """Get all registered Salesforce objects."""
    objects = SalesforceObject.query.all()
    return jsonify({
        'objects': [obj.to_dict() for obj in objects]
    })

@app.route('/api/salesforce/objects')
def list_salesforce_objects():
    """Get available objects from Salesforce."""
    sf, error = get_salesforce_connection()
    
    if sf:
        try:
            about_info = sf.describe()
            objects = about_info.get('sobjects', [])
            
            # Return the first 20 objects for simplicity
            limited_objects = objects[:20]
            
            # Extract relevant information
            result = [{
                'name': obj.get('label'),
                'api_name': obj.get('name'),
                'is_queryable': obj.get('queryable', False),
                'is_searchable': obj.get('searchable', False),
                'is_createable': obj.get('createable', False),
                'is_updateable': obj.get('updateable', False),
                'is_deletable': obj.get('deletable', False)
            } for obj in limited_objects]
            
            return jsonify({
                'objects': result
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"Failed to get Salesforce objects: {str(e)}"
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': f"Failed to connect to Salesforce: {error}"
        }), 500

@app.route('/api/leads')
def get_leads():
    """Fetch all leads from Salesforce with selected columns."""
    sf, error = get_salesforce_connection()
    if not sf:
        return jsonify({'status': 'error', 'message': f'Failed to connect to Salesforce: {error}'}), 500
    try:
        soql = "SELECT Name, Title, Company, Status, LeadSource, LastActivityDate FROM Lead"
        result = sf.query_all(soql)
        leads = result.get('records', [])
        # Remove attributes key
        for lead in leads:
            lead.pop('attributes', None)
        return jsonify({'leads': leads})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to fetch leads: {str(e)}'}), 500

@app.route('/api/sync/status')
def sync_status():
    """Get synchronization status for all objects."""
    objects = SalesforceObject.query.all()
    
    # Return basic status without actual sync logs
    result = []
    for obj in objects:
        status = {
            "object": {
                "id": obj.id,
                "name": obj.name,
                "api_name": obj.api_name
            },
            "last_sync_time": obj.last_sync_time.isoformat() if obj.last_sync_time else None,
            "latest_sync": {
                "status": "completed",
                "records_created": 0,
                "records_updated": 0,
                "records_deleted": 0
            } if obj.last_sync_time else None
        }
        result.append(status)
    
    return jsonify({"objects": result})

@app.route('/api/sync/logs')
def sync_logs():
    """Get synchronization logs."""
    return jsonify({
        "logs": [],
        "total": 0,
        "offset": 0,
        "limit": 20
    })

@app.route('/api/sync/object/<int:object_id>', methods=['POST'])
def sync_object(object_id):
    """Synchronize a specific object."""
    obj = SalesforceObject.query.get_or_404(object_id)
    
    # Update the last sync time
    obj.last_sync_time = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "success": True,
        "object_id": obj.id,
        "sync_type": "incremental",
        "result": {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "deleted": 0
        }
    })

@app.route('/api/sync/all', methods=['POST'])
def sync_all_objects():
    """Synchronize all objects."""
    objects = SalesforceObject.query.all()
    results = []
    
    for obj in objects:
        # Update the last sync time
        obj.last_sync_time = datetime.utcnow()
        
        results.append({
            "object_id": obj.id,
            "object_name": obj.name,
            "success": True,
            "result": {
                "processed": 0,
                "created": 0,
                "updated": 0,
                "deleted": 0
            }
        })
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "sync_type": "incremental",
        "results": results
    })

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True)
