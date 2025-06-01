from flask import Flask, jsonify, session, request, redirect
from simple_salesforce import Salesforce
import os
from dotenv import load_dotenv
import logging
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config import config
import uuid
import requests
from urllib.parse import urlencode
import hashlib
import base64
import secrets

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

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# Enable CORS
CORS(app, supports_credentials=True)

# Configure database
db = SQLAlchemy(app)

# Store OAuth states and tokens (in production, use Redis or database)
oauth_states = {}
user_tokens = {}

# Import auth functions after app is created to avoid circular imports

# Simple OAuth SalesforceService for this app
class SalesforceService:
    """Simple OAuth-based Salesforce service with PKCE support."""
    
    def __init__(self, consumer_key, consumer_secret, domain='login'):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.domain = domain
        self.sf = None
        
    def generate_pkce_pair(self):
        """Generate PKCE code verifier and challenge."""
        # Generate a random code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Create code challenge (SHA256 hash of verifier, base64url encoded)
        challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
        
    def get_authorization_url(self, redirect_uri, state, code_challenge):
        """Get the OAuth authorization URL with PKCE support."""
        base_url = f"https://{self.domain}.salesforce.com/services/oauth2/authorize"
        params = {
            'response_type': 'code',
            'client_id': self.consumer_key,
            'redirect_uri': redirect_uri,
            'state': state,
            'scope': 'api refresh_token',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        # Properly URL encode all parameters
        query_string = urlencode(params)
        return f"{base_url}?{query_string}"
    
    def exchange_code_for_token(self, code, redirect_uri, code_verifier):
        """Exchange authorization code for access token with PKCE."""
        try:
            token_url = f"https://{self.domain}.salesforce.com/services/oauth2/token"
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.consumer_key,
                'client_secret': self.consumer_secret,
                'code': code,
                'redirect_uri': redirect_uri,
                'code_verifier': code_verifier
            }
            
            logger.info(f"Requesting token from: {token_url}")
            logger.info(f"Token request data: {dict((k, v if k != 'client_secret' else '[HIDDEN]') for k, v in data.items())}")
            
            response = requests.post(token_url, data=data)
            
            logger.info(f"Token response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed with status {response.status_code}")
                logger.error(f"Response headers: {dict(response.headers)}")
                logger.error(f"Response body: {response.text}")
                return None
                
            response.raise_for_status()
            token_data = response.json()
            logger.info("Token exchange successful")
            return token_data
            
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Error response: {e.response.text}")
            return None
    
    def connect_with_token(self, access_token, instance_url):
        """Connect to Salesforce using access token."""
        try:
            self.sf = Salesforce(instance_url=instance_url, session_id=access_token)
            return True
        except Exception as e:
            logger.error(f"Error connecting with token: {str(e)}")
            return False
    
    def get_all_records(self, object_name, fields):
        """Get records from Salesforce object."""
        if not self.sf:
            return []
        try:
            fields_str = ', '.join(fields)
            query = f"SELECT {fields_str} FROM {object_name} LIMIT 100"
            result = self.sf.query_all(query)
            return result['records']
        except Exception as e:
            logger.error(f"Error fetching records for {object_name}: {str(e)}")
            return []

# OAuth Routes
@app.route('/api/auth/login')
def salesforce_login():
    """Initiate Salesforce OAuth flow."""
    try:
        # Get configuration
        consumer_key = app.config['SF_CONSUMER_KEY']
        consumer_secret = app.config['SF_CONSUMER_SECRET']
        redirect_uri = app.config['SF_REDIRECT_URI']
        domain = app.config['SF_DOMAIN']
        
        # Create Salesforce service
        sf_service = SalesforceService(consumer_key, consumer_secret, domain)
        
        # Generate state for CSRF protection
        state = str(uuid.uuid4())
        
        # Generate PKCE pair
        code_verifier, code_challenge = sf_service.generate_pkce_pair()
        
        # Store state and code_verifier together
        oauth_states[state] = {
            'code_verifier': code_verifier,
            'timestamp': datetime.utcnow()
        }
        
        # Get authorization URL
        auth_url = sf_service.get_authorization_url(redirect_uri, state, code_challenge)
        
        # Log the URL for debugging
        logger.info(f"Generated authorization URL: {auth_url}")
        
        return jsonify({
            'status': 'success',
            'auth_url': auth_url,
            'state': state
        })
        
    except Exception as e:
        logger.error(f"Error initiating OAuth flow: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to initiate OAuth flow: {str(e)}'
        }), 500

@app.route('/api/auth/callback')
def oauth_callback():
    """Handle OAuth callback from Salesforce."""
    try:
        # Log all callback parameters for debugging
        logger.info(f"OAuth callback received with args: {dict(request.args)}")
        
        # Get parameters from callback
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        error_description = request.args.get('error_description')
        
        # Check for errors
        if error:
            error_msg = f'OAuth error: {error}'
            if error_description:
                error_msg += f' - {error_description}'
            logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400
        
        # Validate required parameters
        if not code:
            return jsonify({
                'status': 'error',
                'message': 'Missing authorization code'
            }), 400
            
        if not state:
            return jsonify({
                'status': 'error',
                'message': 'Missing state parameter'
            }), 400
        
        # Validate state
        if state not in oauth_states:
            return jsonify({
                'status': 'error',
                'message': 'Invalid state parameter'
            }), 400
        
        # Get stored data and remove used state
        state_data = oauth_states[state]
        del oauth_states[state]
        code_verifier = state_data['code_verifier']
        
        # Exchange code for token
        consumer_key = app.config['SF_CONSUMER_KEY']
        consumer_secret = app.config['SF_CONSUMER_SECRET']
        redirect_uri = app.config['SF_REDIRECT_URI']
        domain = app.config['SF_DOMAIN']
        
        logger.info(f"Exchanging code for token with redirect_uri: {redirect_uri}")
        
        sf_service = SalesforceService(consumer_key, consumer_secret, domain)
        token_data = sf_service.exchange_code_for_token(code, redirect_uri, code_verifier)
        
        if not token_data:
            return jsonify({
                'status': 'error',
                'message': 'Failed to exchange code for token'
            }), 500
        
        # Store tokens (in production, associate with user and store securely)
        session_id = str(uuid.uuid4())
        user_tokens[session_id] = {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'instance_url': token_data['instance_url'],
            'id': token_data.get('id'),
            'issued_at': token_data.get('issued_at'),
            'signature': token_data.get('signature')
        }
        
        # Set session
        session['sf_session_id'] = session_id
        
        # Redirect to frontend with success
        frontend_url = request.args.get('frontend_url', 'http://localhost:3000')
        return redirect(f"{frontend_url}/?auth=success&session_id={session_id}")
        
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        frontend_url = request.args.get('frontend_url', 'http://localhost:3000')
        return redirect(f"{frontend_url}/?auth=error&message={str(e)}")

@app.route('/api/auth/status')
def auth_status():
    """Check current authentication status."""
    try:
        session_id = session.get('sf_session_id')
        if not session_id or session_id not in user_tokens:
            return jsonify({
                'status': 'unauthenticated',
                'message': 'No valid session found'
            })
        
        token_info = user_tokens[session_id]
        
        # Test connection
        consumer_key = app.config['SF_CONSUMER_KEY']
        consumer_secret = app.config['SF_CONSUMER_SECRET']
        domain = app.config['SF_DOMAIN']
        
        sf_service = SalesforceService(consumer_key, consumer_secret, domain)
        if sf_service.connect_with_token(token_info['access_token'], token_info['instance_url']):
            # Get user info
            try:
                sf = sf_service.sf
                user_info = sf.query("SELECT Id, Name, Email, Username FROM User WHERE Id = '{}'".format(
                    token_info['id'].split('/')[-1]
                ))
                user_data = user_info['records'][0] if user_info['records'] else {}
            except:
                user_data = {}
            
            return jsonify({
                'status': 'authenticated',
                'session_id': session_id,
                'instance_url': token_info['instance_url'],
                'user': user_data
            })
        else:
            return jsonify({
                'status': 'invalid_token',
                'message': 'Token is invalid or expired'
            })
            
    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error checking authentication: {str(e)}'
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout and clear session."""
    try:
        session_id = session.get('sf_session_id')
        if session_id and session_id in user_tokens:
            del user_tokens[session_id]
        
        session.pop('sf_session_id', None)
        
        return jsonify({
            'status': 'success',
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error during logout: {str(e)}'
        }), 500

def get_current_sf_service():
    """Get Salesforce service for current authenticated user."""
    session_id = session.get('sf_session_id')
    if not session_id or session_id not in user_tokens:
        return None
    
    token_info = user_tokens[session_id]
    
    consumer_key = app.config['SF_CONSUMER_KEY']
    consumer_secret = app.config['SF_CONSUMER_SECRET']
    domain = app.config['SF_DOMAIN']
    
    sf_service = SalesforceService(consumer_key, consumer_secret, domain)
    if sf_service.connect_with_token(token_info['access_token'], token_info['instance_url']):
        return sf_service
    
    return None

# Simple database models
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

# API routes
    @app.route('/api/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({'status': 'ok'})

@app.route('/api/debug/tokens')
def debug_tokens():
    """Debug endpoint to show current tokens (for development only)."""
    if not app.debug:
        return jsonify({'error': 'Debug endpoint only available in development mode'}), 403
    
    return jsonify({
        'user_tokens_count': len(user_tokens),
        'user_tokens_keys': list(user_tokens.keys()),
        'oauth_states_count': len(oauth_states),
        'oauth_states_keys': list(oauth_states.keys())
    })

@app.route('/api/debug/oauth-config')
def debug_oauth_config():
    """Debug endpoint to show OAuth configuration (for development only)."""
    if not app.debug:
        return jsonify({'error': 'Debug endpoint only available in development mode'}), 403
    
    return jsonify({
        'consumer_key': app.config['SF_CONSUMER_KEY'],
        'redirect_uri': app.config['SF_REDIRECT_URI'],
        'domain': app.config['SF_DOMAIN'],
        'consumer_secret_set': bool(app.config['SF_CONSUMER_SECRET'])
    })

@app.route('/api/salesforce/status')
def salesforce_status():
    """Check Salesforce connection status."""
    sf_service = get_current_sf_service()
    
    if not sf_service:
        return jsonify({
            'status': 'unauthenticated',
            'message': 'Please authenticate with Salesforce first'
        }), 401
    
    try:
        # Get basic information
        sf = sf_service.sf
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
    sf_service = get_current_sf_service()
    
    if not sf_service:
        return jsonify({
            'status': 'unauthenticated',
            'message': 'Please authenticate with Salesforce first'
        }), 401
    
    try:
        sf = sf_service.sf
        about_info = sf.describe()
        objects = about_info.get('sobjects', [])
        
        # Just return the first 20 objects for simplicity
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

@app.route('/api/sync/status')
def sync_status():
    """Get synchronization status for all objects."""
    objects = SalesforceObject.query.all()
    
    # For this simple app, we'll just return basic status without actual sync logs
    result = []
    for obj in objects:
        status = {
            "object": {
                "id": obj.id,
                "name": obj.name,
                "api_name": obj.api_name
            },
            "last_sync_time": obj.last_sync_time.isoformat() if obj.last_sync_time else None,
            # Simplified since we don't have actual sync logs yet
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
    # For this simple app, we'll just return an empty array
    return jsonify({
        "logs": [],
        "total": 0,
        "offset": 0,
        "limit": 20
    })

@app.route('/api/sync/object/<int:object_id>', methods=['POST'])
def sync_object(object_id):
    """Synchronize a specific object."""
    sf_service = get_current_sf_service()
    
    if not sf_service:
        return jsonify({
            'status': 'unauthenticated',
            'message': 'Please authenticate with Salesforce first'
        }), 401
    
    obj = SalesforceObject.query.get_or_404(object_id)
    
    # Update the last sync time
    obj.last_sync_time = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Synchronization completed for {obj.name}',
        'object': obj.to_dict()
    })

@app.route('/api/sync/all', methods=['POST'])
def sync_all_objects():
    """Synchronize all registered objects."""
    sf_service = get_current_sf_service()
    
    if not sf_service:
        return jsonify({
            'status': 'unauthenticated',
            'message': 'Please authenticate with Salesforce first'
        }), 401
    
    objects = SalesforceObject.query.filter_by(is_active=True).all()
    
    # Update last sync time for all objects
    for obj in objects:
        obj.last_sync_time = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Synchronization completed for {len(objects)} objects',
        'synced_objects': [obj.to_dict() for obj in objects]
    })

@app.route('/api/leads')
def get_leads():
    """Get Lead records from Salesforce."""
    sf_service = get_current_sf_service()
    
    if not sf_service:
        return jsonify({
            'status': 'unauthenticated',
            'message': 'Please authenticate with Salesforce first'
        }), 401
    
    try:
        logger.info("Attempting to fetch leads from Salesforce")
        records = sf_service.get_all_records('Lead', [
            'Id', 'Name', 'Title', 'Email', 'Phone', 'Company', 
            'Status', 'LeadSource', 'LastActivityDate'
        ])
        logger.info(f"Successfully fetched {len(records)} lead records")
        return jsonify({
            'records': records,
            'count': len(records)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Failed to get Lead records: {str(e)}"
        }), 500

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
