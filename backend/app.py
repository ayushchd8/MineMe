from flask import Flask, jsonify, session, request, redirect
from simple_salesforce import Salesforce
import os
from dotenv import load_dotenv
import logging
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import requests
from urllib.parse import urlencode
import hashlib
import base64
import secrets

# Import our models and services
from models import db, Lead, SyncLog
from services.lead_sync_service import LeadSyncService

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
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-in-production')

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://username:password@localhost:5432/mineme')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure Salesforce OAuth
app.config['SF_CONSUMER_KEY'] = os.environ.get('SF_CONSUMER_KEY')
app.config['SF_CONSUMER_SECRET'] = os.environ.get('SF_CONSUMER_SECRET')
app.config['SF_REDIRECT_URI'] = os.environ.get('SF_REDIRECT_URI', 'http://localhost:5001/api/auth/callback')
app.config['SF_DOMAIN'] = os.environ.get('SF_DOMAIN', 'login')

# Initialize database
db.init_app(app)

# Enable CORS
CORS(app, supports_credentials=True)

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
            query = f"SELECT {fields_str} FROM {object_name}"
            result = self.sf.query_all(query)
            return result['records']
        except Exception as e:
            logger.error(f"Error fetching records for {object_name}: {str(e)}")
            return []
    
    def get_updated_records_since(self, object_name, last_sync_time, fields):
        """Get records updated since the last sync time with specific fields."""
        if not self.sf:
            return []
        
        try:
            # Convert datetime to SOQL format
            if last_sync_time:
                # Format date for SOQL (Salesforce expects ISO format)
                last_sync_str = last_sync_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                # If no last sync time, get all records
                last_sync_str = '1970-01-01T00:00:00Z'
            
            # Build SOQL query with specific fields
            fields_str = ', '.join(fields)
            query = f"SELECT {fields_str} FROM {object_name} WHERE LastModifiedDate >= {last_sync_str} ORDER BY LastModifiedDate ASC"
            
            logger.info(f"Executing SOQL query: {query}")
            
            # Execute query
            result = self.sf.query_all(query)
            records = result['records']
            
            # Remove attributes from each record
            for record in records:
                record.pop('attributes', None)
            
            logger.info(f"Retrieved {len(records)} updated records")
            return records
            
        except Exception as e:
            logger.error(f"Error fetching updated records for {object_name}: {str(e)}")
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
        
        # Get organization information using SOQL query
        try:
            org_query = "SELECT Name, Id FROM Organization LIMIT 1"
            org_result = sf.query(org_query)
            org_name = org_result['records'][0]['Name'] if org_result['records'] else 'Unknown Organization'
        except Exception as e:
            logger.warning(f"Could not fetch organization name: {str(e)}")
            # Fallback: try to get from user identity info
            try:
                identity_url = sf.sf_instance + sf.sf_version + 'chatter/users/me'
                identity_response = sf.restful('chatter/users/me')
                org_name = identity_response.get('companyName', 'Unknown Organization')
            except:
                org_name = 'Unknown Organization'
        
        # Get a few objects
        about_info = sf.describe()
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

@app.route('/api/leads')
def get_leads():
    """Get Lead records from local database."""
    try:
        leads = Lead.get_all_active()
        return jsonify({
            'records': [lead.to_dict() for lead in leads],
            'count': len(leads),
            'source': 'database'
        })
    except Exception as e:
        logger.error(f"Error fetching leads from database: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to get Lead records: {str(e)}"
        }), 500

@app.route('/api/sync/leads', methods=['POST'])
def sync_leads():
    """Manually trigger lead synchronization."""
    sf_service = get_current_sf_service()
    
    if not sf_service:
        return jsonify({
            'status': 'unauthenticated',
            'message': 'Please authenticate with Salesforce first'
        }), 401
    
    try:
        # Get sync type from request (default to incremental)
        sync_type = request.json.get('sync_type', 'incremental') if request.json else 'incremental'
        
        # Create lead sync service
        lead_sync = LeadSyncService(sf_service)
        
        # Perform sync
        result = lead_sync.sync_leads(sync_type=sync_type)
        
        return jsonify({
            'status': 'success',
            'message': f'Lead sync completed successfully',
            'sync_type': sync_type,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error during lead sync: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Lead sync failed: {str(e)}"
        }), 500

@app.route('/api/sync/status')
def sync_status():
    """Get synchronization status and recent logs."""
    try:
        # Get recent sync logs
        recent_logs = SyncLog.get_recent_logs('Lead', limit=5)
        latest_sync = SyncLog.get_latest_successful_sync('Lead')
        
        return jsonify({
            'object_type': 'Lead',
            'latest_sync': latest_sync.to_dict() if latest_sync else None,
            'recent_logs': [log.to_dict() for log in recent_logs],
            'total_leads': Lead.query.filter_by(is_deleted=False).count()
        })
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to get sync status: {str(e)}"
        }), 500

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created/verified")

# Debug endpoints to inspect database data
@app.route('/api/debug/leads')
def debug_leads():
    """Debug endpoint to view all leads in database."""
    if not app.debug:
        return jsonify({'error': 'Debug endpoint only available in development mode'}), 403
    
    try:
        leads = Lead.get_all_active()
        return jsonify({
            'total_leads': len(leads),
            'leads': [lead.to_dict() for lead in leads]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/sync-logs')
def debug_sync_logs():
    """Debug endpoint to view sync logs."""
    if not app.debug:
        return jsonify({'error': 'Debug endpoint only available in development mode'}), 403
    
    try:
        logs = SyncLog.get_recent_logs('Lead', limit=20)
        return jsonify({
            'total_logs': len(logs),
            'logs': [log.to_dict() for log in logs]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/database-stats')
def debug_database_stats():
    """Debug endpoint to view database statistics."""
    if not app.debug:
        return jsonify({'error': 'Debug endpoint only available in development mode'}), 403
    
    try:
        total_leads = Lead.query.count()
        active_leads = Lead.query.filter_by(is_deleted=False).count()
        deleted_leads = Lead.query.filter_by(is_deleted=True).count()
        total_sync_logs = SyncLog.query.count()
        successful_syncs = SyncLog.query.filter_by(status='completed').count()
        failed_syncs = SyncLog.query.filter_by(status='failed').count()
        
        return jsonify({
            'leads': {
                'total': total_leads,
                'active': active_leads,
                'deleted': deleted_leads
            },
            'sync_logs': {
                'total': total_sync_logs,
                'successful': successful_syncs,
                'failed': failed_syncs
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
