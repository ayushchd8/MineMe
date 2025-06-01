#!/usr/bin/env python3
"""
Quick test to debug credential issue in the consolidated app.
"""
import os
from simple_salesforce import Salesforce

def test_credentials():
    print("Testing credential logic...")
    
    # Use the same logic as in app.py
    username = os.environ.get('SF_USERNAME') or 'ayushchd8@gmail.com'
    password = os.environ.get('SF_PASSWORD') or 'Palak@1211'
    security_token = os.environ.get('SF_SECURITY_TOKEN') or 'eflzwPTc8sxOWPL4c88vZTCm'
    domain = os.environ.get('SF_DOMAIN') or 'login'
    
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Security Token: {security_token}")
    print(f"Domain: {domain}")
    
    print("\nTesting Salesforce connection...")
    try:
        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain
        )
        print("✅ SUCCESS! Connection works.")
        return True
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_credentials()
    print(f"\nResult: {'PASS' if success else 'FAIL'}") 