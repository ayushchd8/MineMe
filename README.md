# MineMe

A web application for syncing and managing Salesforce data with OAuth authentication.

## Project Structure

- `frontend/`: React frontend application with TypeScript and Tailwind CSS
- `backend/`: Flask API server that connects to Salesforce with OAuth

## Setup and Running Instructions

### Prerequisites

- Python 3.8+
- Node.js 14+
- Docker (for PostgreSQL database)
- Salesforce Connected App with OAuth credentials

### Backend Setup

1. Navigate to the backend directory:
```
cd backend
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Set up PostgreSQL using Docker:
```bash
# Create and start PostgreSQL container
docker run --name mineme-postgres \
  -e POSTGRES_PASSWORD=mineme123 \
  -e POSTGRES_DB=salesforce_sync \
  -e POSTGRES_USER=mineme \
  -p 5433:5432 \
  -d postgres:14
```

4. Create a `.env` file with your configuration:
```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=mineme-sf-sync-secret-key

# Database Configuration (Docker PostgreSQL)
DATABASE_URL=postgresql://mineme:mineme123@localhost:5433/salesforce_sync

# Salesforce OAuth Configuration
SF_CONSUMER_KEY=your_salesforce_consumer_key
SF_CONSUMER_SECRET=your_salesforce_consumer_secret
SF_REDIRECT_URI=http://localhost:5001/api/auth/callback
SF_DOMAIN=login
```

5. Run the Flask application:
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

## Database Management

### PostgreSQL Docker Container

The application uses PostgreSQL running in a Docker container:

```bash
# Start the container
docker start mineme-postgres

# Stop the container
docker stop mineme-postgres

# View container logs
docker logs mineme-postgres

# Connect to database directly
docker exec -it mineme-postgres psql -U mineme -d salesforce_sync

# Remove container (if needed)
docker rm -f mineme-postgres
```

### Container Details
- **Container Name**: `mineme-postgres`
- **Database**: `salesforce_sync`
- **Username**: `mineme`
- **Password**: `mineme123`
- **Host Port**: `5433` (mapped to container port 5432)

## Features

- **OAuth Authentication**: Secure Salesforce login with OAuth 2.0
- **Browse Salesforce Objects**: View available Salesforce objects
- **Data Synchronization**: Sync Salesforce records to local database
- **Dashboard**: View sync status and statistics
- **API Endpoints**: RESTful API for frontend integration

## Salesforce Setup

### Creating a Connected App

1. Log in to Salesforce at https://login.salesforce.com
2. Go to Setup → Apps → App Manager
3. Click "New Connected App"
4. Fill in the required fields:
   - **Connected App Name**: MineMe Sync
   - **API Name**: MineMe_Sync
   - **Contact Email**: your_email@example.com
5. Enable OAuth Settings:
   - **Callback URL**: `http://localhost:5001/api/auth/callback`
   - **Selected OAuth Scopes**: 
     - Access and manage your data (api)
     - Perform requests on your behalf at any time (refresh_token, offline_access)
6. Save and note the **Consumer Key** and **Consumer Secret**

## API Endpoints

### Authentication
- `GET /api/auth/login` - Initiate OAuth flow
- `GET /api/auth/callback` - OAuth callback handler
- `GET /api/auth/status` - Check authentication status
- `POST /api/auth/logout` - Logout user

### Salesforce Integration
- `GET /api/salesforce/status` - Check Salesforce connection
- `GET /api/salesforce/objects` - List available Salesforce objects
- `GET /api/objects` - Get registered sync objects
- `GET /api/leads` - Get Lead records

### Synchronization
- `GET /api/sync/status` - Get sync status for all objects
- `GET /api/sync/logs` - Get sync logs
- `POST /api/sync/object/<id>` - Sync specific object
- `POST /api/sync/all` - Sync all active objects

## Usage

1. Open http://localhost:3000 in your browser
2. Click "Connect to Salesforce" to start OAuth flow
3. Login to Salesforce and authorize the application
4. Browse available Salesforce objects
5. Configure and run synchronization
6. View synchronized records and status

## Troubleshooting

### Authentication Issues
- Verify your Salesforce Connected App credentials
- Check the callback URL matches your Connected App settings
- Ensure you're using the correct Salesforce domain (login vs test)

### Database Issues
- Ensure Docker is running: `docker ps`
- Check if PostgreSQL container is running: `docker logs mineme-postgres`
- Verify database connection string in `.env` file

### Container Issues
```bash
# If port 5433 is busy, use a different port:
docker run --name mineme-postgres -p 5434:5432 ...

# Then update DATABASE_URL in .env:
DATABASE_URL=postgresql://mineme:mineme123@localhost:5434/salesforce_sync
```

### Development
- For development: Use `FLASK_ENV=development`

## License

MIT 
