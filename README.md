# Server Manager

A comprehensive server management system with a beautiful web interface for managing and monitoring multiple servers.

## 🚀 Features

### Server Management
- Add, edit, and delete server configurations
- Store server credentials securely (encrypted passwords)
- Add notes and descriptions for each server
- Search and filter servers

### Status Monitoring
- Real-time server status detection (ping check)
- Port availability checking (SSH port 22, RDP port 3389, etc.)
- SSH/RDP password verification
- Batch status checking for all servers
- Visual status indicators (Online/Offline/Unknown)

### System Information
- Retrieve OS version information via SSH
- Monitor CPU usage and core count
- Track memory usage (total/used/available)
- Monitor disk usage
- Display server uptime
- One-click system info refresh

### User Authentication
- Secure admin login with JWT tokens
- Session management
- Protected API endpoints

### Beautiful UI
- Modern, responsive design using Element Plus
- Dashboard with statistics cards
- Server list with detailed information
- Interactive dialogs for adding/editing servers
- Real-time status updates
- Color-coded status badges

## 📋 Tech Stack

### Backend
- **Framework**: Python Flask 3.0
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT (PyJWT)
- **SSH Connection**: Paramiko
- **Security**: Bcrypt for user passwords, Cryptography for server password encryption
- **CORS**: Flask-CORS

### Frontend
- **Framework**: Vue 3 (Composition API)
- **UI Library**: Element Plus
- **Build Tool**: Vite
- **HTTP Client**: Axios
- **Router**: Vue Router 4

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the Flask application:
```bash
python app.py
```

The backend API will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Docker Deployment (Optional)

Run both frontend and backend using Docker Compose:

```bash
docker-compose up -d
```

This will start:
- Backend API on `http://localhost:5000`
- Frontend UI on `http://localhost:3000`

## 🔐 Default Credentials

- **Username**: `admin`
- **Password**: `admin123`

**⚠️ Important**: Change the default credentials after first login in a production environment.

## 📚 API Documentation

### Authentication Endpoints

#### POST /api/auth/login
Login with username and password.

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "token": "jwt_token_here",
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```

#### POST /api/auth/logout
Logout current user (requires authentication).

#### GET /api/auth/me
Get current user information (requires authentication).

### Server Management Endpoints

#### GET /api/servers
Get all servers (requires authentication).

#### POST /api/servers
Add a new server (requires authentication).

**Request Body:**
```json
{
  "ip_address": "192.168.1.100",
  "port": 22,
  "username": "root",
  "password": "server_password",
  "notes": "Production web server"
}
```

#### GET /api/servers/:id
Get specific server details (requires authentication).

#### PUT /api/servers/:id
Update server information (requires authentication).

#### DELETE /api/servers/:id
Delete a server (requires authentication).

### Status Check Endpoints

#### POST /api/servers/:id/check
Check status of a specific server (requires authentication).

**Response:**
```json
{
  "server_id": 1,
  "status": {
    "ping": true,
    "port": true,
    "auth": true,
    "overall": "online"
  }
}
```

#### POST /api/servers/check-all
Check status of all servers (requires authentication).

#### POST /api/servers/:id/verify-password
Verify server SSH password (requires authentication).

#### POST /api/servers/:id/check-port
Check if server port is open (requires authentication).

### System Information Endpoints

#### GET /api/servers/:id/system-info
Get detailed system information via SSH (requires authentication).

**Response:**
```json
{
  "os": "Ubuntu 22.04 LTS",
  "cpu": "15.2% (4 cores)",
  "memory": "Total: 8.0G, Used: 2.5G, Free: 5.5G",
  "disk": "Total: 100G, Used: 45G (45%), Free: 55G",
  "uptime": "up 7 days, 14 hours"
}
```

## 🔒 Security Features

- **Password Encryption**: Server passwords are encrypted using Fernet symmetric encryption before storage
- **User Authentication**: Admin passwords are hashed using bcrypt
- **JWT Tokens**: API endpoints are protected with JWT authentication
- **SQL Injection Prevention**: SQLAlchemy ORM prevents SQL injection attacks
- **CORS Protection**: Configured CORS to allow specific origins

## 📝 Configuration

### Backend Configuration (backend/config.py)

Key configuration variables:
- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: JWT token signing key
- `ENCRYPTION_KEY`: Key for encrypting server passwords (must be 32 bytes)
- `DATABASE_URI`: SQLite database location

**⚠️ Important**: Change all secret keys in production environments!

### Frontend Configuration

Environment variables can be set in `.env` file:
```
VITE_API_BASE_URL=http://localhost:5000/api
```

## 🎨 UI Screenshots

The application features:
- Modern login page with gradient background
- Dashboard with server statistics
- Responsive server list with search functionality
- Detailed server information dialogs
- Real-time status updates with color-coded badges

## 🧪 Development

### Running Tests

Backend tests:
```bash
cd backend
python -m pytest
```

Frontend tests:
```bash
cd frontend
npm run test
```

### Building for Production

Frontend build:
```bash
cd frontend
npm run build
```

The built files will be in the `frontend/dist` directory.

## 📄 Project Structure

```
server-manager/
├── backend/
│   ├── app.py                 # Flask application entry point
│   ├── config.py              # Configuration settings
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile            # Docker configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── server.py          # Server database model
│   │   └── user.py            # User database model
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication routes
│   │   └── servers.py         # Server management routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ssh_service.py     # SSH connection service
│   │   └── check_service.py   # Server status checking
│   └── utils/
│       ├── __init__.py
│       └── crypto.py          # Password encryption utilities
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/
│       │   └── index.js       # Vue Router configuration
│       ├── views/
│       │   ├── Login.vue      # Login page
│       │   ├── Dashboard.vue  # Dashboard view
│       │   └── ServerList.vue # Server management page
│       ├── components/
│       │   ├── ServerCard.vue    # Server card component
│       │   ├── ServerForm.vue    # Add/Edit form
│       │   └── StatusBadge.vue   # Status indicator
│       ├── api/
│       │   └── index.js       # API client with Axios
│       └── assets/
│           └── styles/
│               └── main.css   # Global styles
├── docker-compose.yml         # Docker Compose configuration
└── README.md                  # This file
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License.

## 🐛 Troubleshooting

### Backend Issues

- **Database errors**: Delete `server_manager.db` and restart the application to recreate the database
- **SSH connection failures**: Ensure the target server has SSH enabled and the credentials are correct
- **Import errors**: Make sure all dependencies are installed: `pip install -r requirements.txt`

### Frontend Issues

- **API connection errors**: Check that the backend is running on port 5000
- **Build errors**: Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- **CORS errors**: Ensure Flask-CORS is properly configured in the backend

## 📞 Support

For issues and questions, please open an issue on the GitHub repository.