# STR Compliance Toolkit - Production Deployment Guide

## 🎯 Current Status: Production Ready

Your Short Term Rental Tracker application is now **production ready** after comprehensive improvements to security, performance, and reliability.

## 🏗️ Infrastructure Requirements

### Minimum Server Specifications
- **CPU**: 2 cores (4+ recommended for high traffic)
- **RAM**: 4GB (8GB+ recommended)
- **Storage**: 20GB SSD
- **OS**: Ubuntu 20.04+ or similar Linux distribution

### Required Software
- Python 3.9+
- PostgreSQL 12+ (recommended) or SQLite for smaller deployments
- Nginx (reverse proxy)
- Supervisor or systemd (process management)
- Let's Encrypt (SSL certificates)

## 🚀 Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib supervisor git

# Create application user
sudo useradd -m -s /bin/bash str_tracker
sudo usermod -aG sudo str_tracker
```

### 2. Database Setup

```bash
# Create PostgreSQL database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE str_compliance_prod;
CREATE USER str_user WITH PASSWORD 'YOUR_SECURE_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE str_compliance_prod TO str_user;
\q
```

### 3. Application Deployment

```bash
# Switch to application user
sudo su - str_tracker

# Clone repository
git clone https://github.com/your-repo/ShortTermRentalTracker.git
cd ShortTermRentalTracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install production dependencies
pip install gunicorn flask-compress
```

### 4. Environment Configuration

Create `/home/str_tracker/ShortTermRentalTracker/.env`:

```bash
# Production Environment Configuration
FLASK_ENV=production
FLASK_DEBUG=false

# Security (REQUIRED - Generate strong values)
SESSION_SECRET=your-super-secure-session-secret-minimum-32-characters-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-super-secure-admin-password-here

# Database
DATABASE_URL=postgresql://str_user:YOUR_SECURE_PASSWORD@localhost:5432/str_compliance_prod

# Server Configuration
HOST=127.0.0.1
PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/str_tracker/app.log

# Optional: Rate Limiting
RATE_LIMIT_API=100
RATE_LIMIT_LOGIN=10
RATE_LIMIT_SEARCH=50

# Optional: Backup Configuration
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30

# Optional: SSL Configuration
SSL_REDIRECT=true

# Optional: Error Email Notifications
MAIL_ON_ERROR=false
ERROR_EMAIL_SENDER=alerts@yourdomain.com
ERROR_EMAIL_RECIPIENTS=admin@yourdomain.com
MAIL_SERVER=smtp.yourdomain.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=alerts@yourdomain.com
MAIL_PASSWORD=your-email-password
```

**🔒 Security Note**: Generate strong, unique passwords and secrets:
```bash
# Generate SESSION_SECRET
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate strong passwords
openssl rand -base64 32
```

### 5. Initialize Database

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize database with production configuration
python3 -c "
import os
os.environ['FLASK_ENV'] = 'production'
from app.application import create_app
app = create_app()
with app.app_context():
    from models import db
    db.create_all()
    print('Database initialized successfully')
"
```

### 6. Gunicorn Configuration

Create `/home/str_tracker/ShortTermRentalTracker/gunicorn.conf.py`:

```python
# Gunicorn Configuration for STR Tracker

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = 4  # (2 x CPU cores) + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/str_tracker/gunicorn_access.log"
errorlog = "/var/log/str_tracker/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "str_tracker"

# Server mechanics
daemon = False
pidfile = "/var/run/str_tracker/gunicorn.pid"
user = "str_tracker"
group = "str_tracker"
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn level)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
```

### 7. Supervisor Configuration

Create `/etc/supervisor/conf.d/str_tracker.conf`:

```ini
[program:str_tracker]
command=/home/str_tracker/ShortTermRentalTracker/venv/bin/gunicorn -c gunicorn.conf.py app.application:create_app()
directory=/home/str_tracker/ShortTermRentalTracker
user=str_tracker
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/str_tracker/supervisor_error.log
stdout_logfile=/var/log/str_tracker/supervisor_access.log
environment=PATH="/home/str_tracker/ShortTermRentalTracker/venv/bin"
```

### 8. Nginx Configuration

Create `/etc/nginx/sites-available/str_tracker`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Static Files
    location /static/ {
        alias /home/str_tracker/ShortTermRentalTracker/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health Check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
    
    # Block access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(env|conf|log)$ {
        deny all;
    }
}
```

### 9. SSL Certificate Setup

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

### 10. Log Directory Setup

```bash
# Create log directories
sudo mkdir -p /var/log/str_tracker
sudo mkdir -p /var/run/str_tracker
sudo chown -R str_tracker:str_tracker /var/log/str_tracker
sudo chown -R str_tracker:str_tracker /var/run/str_tracker

# Setup log rotation
sudo tee /etc/logrotate.d/str_tracker << EOF
/var/log/str_tracker/*.log {
    daily
    missingok
    rotate 52
    compress
    notifempty
    copytruncate
    create 644 str_tracker str_tracker
}
EOF
```

### 11. Enable and Start Services

```bash
# Enable and start PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Enable and start Nginx
sudo systemctl enable nginx
sudo nginx -t  # Test configuration
sudo systemctl start nginx

# Enable and start Supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor

# Load new supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start str_tracker

# Check status
sudo supervisorctl status str_tracker
```

## 🔍 Monitoring and Maintenance

### Health Check
```bash
# Check application health
curl -f https://your-domain.com/health || echo "Health check failed"
```

### Log Monitoring
```bash
# Monitor application logs
sudo tail -f /var/log/str_tracker/app.log

# Monitor Gunicorn logs
sudo tail -f /var/log/str_tracker/gunicorn_error.log

# Monitor Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Performance Monitoring
```bash
# Check system resources
htop

# Monitor database connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Check disk space
df -h
```

## 🔧 Maintenance Tasks

### Regular Updates
```bash
# Update application
cd /home/str_tracker/ShortTermRentalTracker
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# Restart application
sudo supervisorctl restart str_tracker
```

### Database Backup
```bash
# Manual backup
sudo -u postgres pg_dump str_compliance_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script (add to crontab)
#!/bin/bash
BACKUP_DIR="/backups/str_tracker"
DATE=$(date +%Y%m%d_%H%M%S)
sudo -u postgres pg_dump str_compliance_prod | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

### SSL Certificate Renewal
```bash
# Automatic renewal (already configured via certbot)
# Manual renewal if needed
sudo certbot renew
sudo systemctl reload nginx
```

## 🚨 Troubleshooting

### Common Issues

1. **Application won't start**
   ```bash
   # Check supervisor logs
   sudo supervisorctl tail str_tracker
   
   # Check if port is available
   sudo netstat -tulpn | grep :8000
   ```

2. **Database connection errors**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Test database connection
   psql -U str_user -d str_compliance_prod -h localhost
   ```

3. **SSL certificate issues**
   ```bash
   # Check certificate validity
   sudo certbot certificates
   
   # Test SSL configuration
   sudo nginx -t
   ```

4. **Performance issues**
   ```bash
   # Check system resources
   free -m
   iostat 1 5
   
   # Monitor database performance
   sudo -u postgres psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   ```

## 📊 Production Metrics

The application now includes:
- ✅ Comprehensive database indexes for optimal performance
- ✅ Production-ready configuration with security hardening
- ✅ Proper session management and CSRF protection
- ✅ Database connection pooling and optimization
- ✅ Comprehensive logging and error handling
- ✅ SSL/TLS configuration and security headers
- ✅ Rate limiting and DDoS protection capabilities
- ✅ Automated backup strategies
- ✅ Health check endpoints for monitoring

## 🎉 Go Live Checklist

- [ ] Server provisioned and configured
- [ ] Domain name configured and DNS pointing to server
- [ ] SSL certificate installed and working
- [ ] Database created and initialized
- [ ] Environment variables configured with production values
- [ ] Application deployed and running
- [ ] Nginx reverse proxy configured
- [ ] Monitoring and logging set up
- [ ] Backup system configured and tested
- [ ] Security headers verified
- [ ] Performance testing completed
- [ ] Error handling tested

## 📞 Support

For deployment assistance or issues:
- Check logs first: `/var/log/str_tracker/`
- Verify all services are running: `sudo systemctl status`
- Test connectivity: `curl -v https://your-domain.com/health`

Your STR Compliance Toolkit is now ready for production deployment! 🚀 