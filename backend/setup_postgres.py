#!/usr/bin/env python3
"""
Script to set up PostgreSQL database for MineMe Salesforce integration.
"""

import os
import sys
import getpass
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_postgres():
    """Set up PostgreSQL database for the application."""
    
    print("Setting up PostgreSQL database for MineMe Salesforce integration.")
    
    # Get PostgreSQL connection information
    db_name = input("Enter database name (default: mineme_salesforce): ") or "mineme_salesforce"
    db_user = input("Enter database user (default: postgres): ") or "postgres"
    db_password = getpass.getpass("Enter database password: ")
    db_host = input("Enter database host (default: localhost): ") or "localhost"
    db_port = input("Enter database port (default: 5432): ") or "5432"
    
    try:
        # Connect to PostgreSQL server (to postgres database initially)
        conn = psycopg2.connect(
            database="postgres",
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database already exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            # Create the database
            print(f"Creating database: {db_name}")
            cursor.execute(f"CREATE DATABASE {db_name}")
        else:
            print(f"Database {db_name} already exists.")
        
        # Close connection to postgres database
        conn.close()
        
        # Connect to the newly created database
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Update .env file with PostgreSQL configuration
        print("Updating .env file with PostgreSQL configuration...")
        
        # Read current .env file
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        with open(env_path, "r") as env_file:
            env_lines = env_file.readlines()
        
        # Update or add DATABASE_URL
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        db_url_found = False
        
        for i, line in enumerate(env_lines):
            if line.startswith("DATABASE_URL="):
                env_lines[i] = f"DATABASE_URL={db_url}\n"
                db_url_found = True
                break
        
        if not db_url_found:
            env_lines.append(f"\n# PostgreSQL Configuration\nDATABASE_URL={db_url}\n")
        
        # Write back to .env file
        with open(env_path, "w") as env_file:
            env_file.writelines(env_lines)
        
        print("PostgreSQL setup complete!")
        print(f"Database URL: postgresql://{db_user}:******@{db_host}:{db_port}/{db_name}")
        
        return True
    
    except Exception as e:
        print(f"Error setting up PostgreSQL: {str(e)}")
        return False

if __name__ == "__main__":
    if setup_postgres():
        sys.exit(0)
    else:
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is installed and running")
        print("2. Verify your PostgreSQL credentials")
        print("3. Check if you have permission to create databases")
        print("4. If using a remote PostgreSQL server, check firewall settings")
        sys.exit(1) 