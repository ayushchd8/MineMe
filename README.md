# MineMe

A web application for syncing and managing Salesforce data.

## Project Structure

- `frontend/`: React frontend application with TypeScript and Tailwind CSS
- `backend/`: Flask API server that connects to Salesforce

## Setup and Running Instructions

### Backend Setup

1. Navigate to the backend directory:
```
cd backend
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Create a `.env` file with your Salesforce credentials:
```
SF_USERNAME=your_salesforce_username
SF_PASSWORD=your_salesforce_password
SF_SECURITY_TOKEN=your_salesforce_security_token
SF_DOMAIN=login
DATABASE_URL=postgresql://username:password@localhost:5432/mineme
```

4. Run the Flask application:
```
python app.py
```

The server will start at http://localhost:5001

### Frontend Setup

1. Navigate to the frontend directory:
```
cd frontend
```

2. Install dependencies:
```
npm install
```

3. Create a `.env` file:
```
REACT_APP_API_URL=http://localhost:5001/api
```

4. Start the development server:
```
npm start
```

The frontend will be available at http://localhost:3000

## Features

- Connect to Salesforce using API credentials
- Browse and select Salesforce objects for synchronization
- View and manage synchronized records
- Configure synchronization settings
- Dashboard with sync status and statistics

## Requirements

- Python 3.8+
- Node.js 14+
- PostgreSQL (optional, SQLite can be used for development)
- Salesforce account with API access

## Salesforce Setup

### Obtaining a Security Token

1. Log in to Salesforce at https://login.salesforce.com
2. Click on your profile picture/icon, then 'Settings'
3. In the Quick Find box on the left, type 'Reset Security Token'
4. Click on 'Reset Security Token'
5. Check your email for the new security token
6. Update your `.env` file with the new security token

### Allowing API Access

If you don't want to use a security token, you can whitelist your IP address:

1. Log in to Salesforce
2. Go to Setup
3. Search for 'Network Access'
4. Add your IP address to the trusted IP range

## Usage

1. Open http://localhost:3000 in your browser
2. The home page will show the Salesforce connection status
3. If connected, you can browse available Salesforce objects
4. Select objects to synchronize
5. View and manage synchronized records

## Troubleshooting

### Salesforce Connection Issues

- Verify your Salesforce credentials are correct
- Make sure your security token is up-to-date
- Check if your IP is allowed in Salesforce
- Try logging in to Salesforce through the web interface

### Database Issues

- For SQLite, ensure the application has write permission to the directory
- For PostgreSQL, verify connection parameters and database existence

## License

MIT 
