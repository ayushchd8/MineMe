from simple_salesforce import Salesforce
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_salesforce_connection():
    """Test connection to Salesforce using just username and password"""
    try:
        sf_username = os.environ.get('SF_USERNAME')
        sf_password = os.environ.get('SF_PASSWORD')
        
        logger.info(f"Attempting to connect to Salesforce with username: {sf_username}")
        
        # Try connecting without a security token
        # This works if your IP is in the trusted IP range in Salesforce
        try:
            sf = Salesforce(
                username=sf_username,
                password=sf_password,
                security_token='',  # Empty token
                domain='login'
            )
            logger.info("Successfully connected without security token!")
        except Exception as e:
            if "security token" in str(e).lower():
                logger.warning("Connection without security token failed. You need to:")
                logger.warning("1. Add your IP to trusted networks in Salesforce, OR")
                logger.warning("2. Get a security token and add it to your .env file")
                return False, str(e)
            else:
                # Some other error
                raise e
            
        # If we get here without an exception, the connection was successful
        # Test basic functionality
        try:
            # Query a common object like User
            result = sf.query("SELECT Id, Name FROM User LIMIT 5")
            users = result.get('records', [])
            logger.info(f"Found {len(users)} users")
            for user in users:
                logger.info(f"User: {user.get('Name')}")
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            
        return True, "Connection successful"
    
    except Exception as e:
        logger.error(f"Failed to connect to Salesforce: {str(e)}")
        return False, str(e)

if __name__ == "__main__":
    success, message = test_salesforce_connection()
    if success:
        print("✅ Connection successful!")
        print("\nTo integrate with the full application:")
        print("1. Make sure your IP is added to trusted IPs in Salesforce, or")
        print("2. Get a security token and add it to the .env file")
        print("\nNext steps:")
        print("1. Run the Flask application: python run.py")
        print("2. Start the React frontend: cd ../frontend && npm start")
    else:
        print(f"❌ Connection failed: {message}")
        
        print("\nTROUBLESHOOTING STEPS:")
        print("1. Verify your Salesforce credentials")
        print("2. Add your IP to trusted IPs in Salesforce:")
        print("   a. Log in to Salesforce")
        print("   b. Go to Setup")
        print("   c. Search for 'Network Access'")
        print("   d. Click on 'Network Access'")
        print("   e. Add your current IP address")
        print("3. OR get a security token:")
        print("   a. Log in to Salesforce")
        print("   b. Click on your profile picture/icon, then 'Settings'")
        print("   c. In the Quick Find box, type 'Reset Security Token'")
        print("   d. Click on 'Reset Security Token'")
        print("   e. Check your email for the new security token")
        print("   f. Update your .env file with the security token") 