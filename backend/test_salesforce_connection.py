#!/usr/bin/env python3
"""
Simple script to test Salesforce connection.
"""

from simple_salesforce import Salesforce
import os
from dotenv import load_dotenv
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
    # Get Salesforce credentials
    sf_username = os.environ.get('SF_USERNAME')
    sf_password = os.environ.get('SF_PASSWORD')
    sf_security_token = os.environ.get('SF_SECURITY_TOKEN')
    sf_domain = os.environ.get('SF_DOMAIN', 'login')
    
    # Log the username (masked for security)
    masked_username = sf_username
    logger.info(f"Attempting to connect to Salesforce with username: {masked_username}")
    
    try:
        # Connect to Salesforce
        sf = Salesforce(
            username=sf_username,
            password=sf_password,
            security_token=sf_security_token,
            domain=sf_domain
        )
        
        logger.info("Successfully connected to Salesforce!")
        
        # Get some basic information
        user_info = sf.query("SELECT Id, Name FROM User WHERE Username = '{}'".format(sf_username))
        if user_info and user_info.get('records'):
            user_id = user_info['records'][0]['Id']
            logger.info(f"Salesforce User ID: {user_id}")
        
        # Get organization information
        try:
            org_info = sf.query("SELECT Id, Name FROM Organization LIMIT 1")
            if org_info and org_info.get('records'):
                org_name = org_info['records'][0]['Name']
                logger.info(f"Salesforce Organization Name: {org_name}")
            else:
                logger.info("Salesforce Organization Name: None")
        except Exception as e:
            logger.info("Salesforce Organization Name: None")
        
        # List some standard objects
        describe = sf.describe()
        sobjects = describe.get('sobjects', [])
        
        # Show the first 10 objects
        sample_objects = [obj['name'] for obj in sobjects[:10]]
        logger.info(f"Available Objects: {', '.join(sample_objects)}")
        
        print("✅ Connection successful!")
        return 0
    
    except Exception as e:
        logger.error(f"Failed to connect to Salesforce: {str(e)}")
        print(f"❌ Connection failed: {str(e)}")
        
        # Provide some common troubleshooting tips
        print("\nTroubleshooting tips:")
        print("1. Check if your username and password are correct")
        print("2. Verify that your security token is correct and up-to-date")
        print("3. If you're using a custom domain, make sure it's specified correctly")
        print("4. Check if your IP is allowed in Salesforce (Setup > Security > Network Access)")
        print("5. Try logging in to Salesforce through the web interface to verify credentials")
        
        return 1

if __name__ == "__main__":
    sys.exit(main()) 