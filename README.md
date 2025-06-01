# MineMe - Salesforce Lead Management System

A clean, modern web application for syncing and managing Salesforce leads with automatic background synchronization.

## 🚀 Features

- **OAuth Authentication** - Secure Salesforce login with PKCE
- **Automatic Sync** - Initial full sync + incremental sync every 60 seconds
- **Local Storage** - PostgreSQL database for fast lead access
- **Real-time UI** - React with Tailwind CSS for modern interface
- **Manual Controls** - Full sync and incremental sync buttons
- **Sync Monitoring** - Visual indicators and sync status tracking

## 🏗️ Architecture

### Backend (Flask)
- **OAuth-based Salesforce integration** with session management
- **PostgreSQL database** for lead storage and sync logs
- **RESTful API** for frontend communication
- **Debug endpoints** for database inspection

### Frontend (React + TypeScript)
- **Modern React** with hooks and context
- **Tailwind CSS** for styling
- **Automatic sync** with visual feedback
- **Responsive design** for all devices

## 📁 Project Structure

```
MineMe/
├── backend/
│   ├── app.py                 # Main Flask application with OAuth
│   ├── models/
│   │   ├── base.py           # Database base model
│   │   ├── lead.py           # Lead model with Salesforce mapping
│   │   └── sync_log.py       # Sync operation tracking
│   ├── services/
│   │   └── lead_sync_service.py  # Lead synchronization logic
│   └── requirements.txt      # Python dependencies
└── frontend/
    ├── src/
    │   ├── components/       # React components
    │   ├── contexts/         # React context (Auth)
    │   ├── api/             # API communication
    │   └── types/           # TypeScript interfaces
    └── package.json         # Node.js dependencies
```

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker (for PostgreSQL database)
- Salesforce Connected App (OAuth)

### Database Setup (PostgreSQL with Docker)

1. **Start PostgreSQL container:**
```bash
# Create and start PostgreSQL container
docker run --name mineme-postgres \
  -e POSTGRES_PASSWORD=mineme123 \
  -e POSTGRES_DB=salesforce_sync \
  -e POSTGRES_USER=mineme \
  -p 5433:5432 \
  -d postgres:14
```

2. **Container management commands:**
```bash
# Start existing container
docker start mineme-postgres

# Stop container
docker stop mineme-postgres

# View logs
docker logs mineme-postgres

# Connect to database directly
docker exec -it mineme-postgres psql -U mineme -d salesforce_sync
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Create .env file with your configuration
cat > .env << EOF
# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-change-in-production

# Database Configuration (Docker PostgreSQL)
DATABASE_URL=postgresql://mineme:mineme123@localhost:5433/salesforce_sync

# Salesforce OAuth Configuration
SF_CONSUMER_KEY=your_salesforce_consumer_key
SF_CONSUMER_SECRET=your_salesforce_consumer_secret
SF_REDIRECT_URI=http://localhost:5001/api/auth/callback
SF_DOMAIN=login
EOF

# Start the Flask server
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install

# Create .env file (optional - uses defaults)
echo "REACT_APP_API_URL=http://localhost:5001/api" > .env

# Start the development server
npm start
```

### Salesforce Connected App Setup

To use OAuth authentication, you need to create a Connected App in Salesforce:

1. **Log in to Salesforce** at https://login.salesforce.com
2. **Go to Setup** → Apps → App Manager
3. **Click "New Connected App"**
4. **Fill in basic information:**
   - Connected App Name: `MineMe Sync`
   - API Name: `MineMe_Sync`
   - Contact Email: `your_email@example.com`
5. **Enable OAuth Settings:**
   - Callback URL: `http://localhost:5001/api/auth/callback`
   - Selected OAuth Scopes:
     - Access and manage your data (api)
     - Perform requests on your behalf at any time (refresh_token, offline_access)
6. **Save and get credentials:**
   - Copy the **Consumer Key** and **Consumer Secret**
   - Add them to your `.env` file

## 🔧 API Endpoints

### Authentication
- `GET /api/auth/login` - Initiate OAuth flow
- `GET /api/auth/callback` - OAuth callback handler
- `GET /api/auth/status` - Check authentication status
- `POST /api/auth/logout` - Logout user

### Data Management
- `GET /api/leads` - Get leads from local database
- `POST /api/sync/leads` - Trigger manual sync
- `GET /api/sync/status` - Get sync status and logs

### Debug (Development only)
- `GET /api/debug/leads` - View all leads in database
- `GET /api/debug/sync-logs` - View sync operation logs
- `GET /api/debug/database-stats` - Database statistics

## 🔄 Sync Behavior

1. **First Visit**: Automatic full sync to populate database
2. **Background Sync**: Incremental sync every 60 seconds
3. **Manual Sync**: Full or incremental sync on demand
4. **Smart Fallback**: Incremental sync falls back to full sync if needed

## 🎯 Key Benefits

- **Performance**: Local database eliminates API wait times
- **Reliability**: Data available even if Salesforce is down
- **Efficiency**: Incremental sync minimizes API usage
- **User Experience**: Real-time feel with automatic updates

## 🚀 Usage

1. Visit http://localhost:3000
2. Click "Login with Salesforce" to authenticate
3. Navigate to "Dashboard" to view leads
4. Data syncs automatically every minute
5. Use manual sync buttons for immediate updates

## 🔍 Database Inspection

Use debug endpoints to inspect stored data:
```bash
# View database statistics
curl http://localhost:5001/api/debug/database-stats

# View all leads
curl http://localhost:5001/api/debug/leads

# View sync logs
curl http://localhost:5001/api/debug/sync-logs
```

## 🐛 Troubleshooting

### Docker Issues
```bash
# Check if Docker is running
docker ps

# Check if PostgreSQL container exists
docker ps -a | grep mineme-postgres

# If port 5433 is busy, use a different port
docker run --name mineme-postgres -p 5434:5432 ... 
# Then update DATABASE_URL: postgresql://mineme:mineme123@localhost:5434/salesforce_sync

# Remove and recreate container if needed
docker rm -f mineme-postgres
# Then run the docker run command again
```

### Authentication Issues
- Verify Salesforce Connected App credentials in `.env`
- Check callback URL matches: `http://localhost:5001/api/auth/callback`
- Ensure you're using correct Salesforce domain (`login` vs `test`)
- Check browser console for OAuth errors

### Database Connection Issues
```bash
# Test database connection
docker exec -it mineme-postgres psql -U mineme -d salesforce_sync -c "SELECT 1;"

# Check container logs for errors
docker logs mineme-postgres

# Restart container if needed
docker restart mineme-postgres
```

### API Issues
```bash
# Test backend health
curl http://localhost:5001/api/health

# Check backend logs for errors
# (Backend runs in terminal - check console output)

# Test authentication status
curl http://localhost:5001/api/auth/status
```

## 📝 License

MIT License - see LICENSE file for details. 
