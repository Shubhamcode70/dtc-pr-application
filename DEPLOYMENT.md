# DTC PR Application - Deployment Guide

## Production Deployment

This guide covers deploying the DTC Purchase Requisition application to production.

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Redis (for Celery task queue)
- 5TB+ storage for file attachments
- SSL certificate for HTTPS

### Pre-Deployment Checklist

- [ ] Database backups configured
- [ ] File storage directories created with proper permissions
- [ ] Environment variables set (.env file)
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Redis instance running
- [ ] Static files collected
- [ ] Database migrations tested

### Environment Configuration

Create `.env` file in project root:

```bash
# Django settings
DEBUG=False
SECRET_KEY=your-very-long-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=dtc_pr_db
DATABASE_USER=postgres
DATABASE_PASSWORD=strong-password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# File storage
FILE_STORAGE_PATH=/mnt/storage/pr_attachments
MAX_FILE_SIZE=52428800  # 50MB

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
```

### Deployment Steps

#### 1. Prepare Server

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3.10 python3.10-venv postgresql postgresql-contrib redis-server nginx supervisor

# Create application directory
sudo mkdir -p /var/www/dtc-pr
cd /var/www/dtc-pr
```

#### 2. Setup Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### 3. Configure Database

```bash
# Create PostgreSQL database
sudo -u postgres createdb dtc_pr_db
sudo -u postgres createuser pr_user
sudo -u postgres psql -c "ALTER USER pr_user WITH PASSWORD 'secure-password'"
sudo -u postgres psql -c "ALTER ROLE pr_user SET client_encoding TO 'utf8'"
sudo -u postgres psql -c "ALTER ROLE pr_user SET default_transaction_isolation TO 'read committed'"
sudo -u postgres psql -c "ALTER ROLE pr_user SET default_transaction_deferrable TO on"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dtc_pr_db TO pr_user"
```

#### 4. Run Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Initialize default data
python manage.py shell < scripts/setup.py
```

#### 5. Collect Static Files

```bash
python manage.py collectstatic --no-input
```

#### 6. Configure Gunicorn

Create `/etc/supervisor/conf.d/dtc-pr-gunicorn.conf`:

```ini
[program:dtc-pr-gunicorn]
directory=/var/www/dtc-pr
command=/var/www/dtc-pr/venv/bin/gunicorn --workers 4 --bind unix:/var/www/dtc-pr/run/gunicorn.sock config.wsgi:application
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dtc-pr/gunicorn.log
user=www-data
```

#### 7. Configure Celery

Create `/etc/supervisor/conf.d/dtc-pr-celery.conf`:

```ini
[program:dtc-pr-celery]
directory=/var/www/dtc-pr
command=/var/www/dtc-pr/venv/bin/celery -A config worker -l info
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dtc-pr/celery.log
user=www-data
```

#### 8. Configure Nginx

Create `/etc/nginx/sites-available/dtc-pr`:

```nginx
upstream dtc_pr_app {
    server unix:/var/www/dtc-pr/run/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    client_max_body_size 50M;
    
    location /static/ {
        alias /var/www/dtc-pr/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /var/www/dtc-pr/media/;
    }
    
    location / {
        proxy_pass http://dtc_pr_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/dtc-pr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 9. Setup SSL Certificate

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

#### 10. Start Services

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start dtc-pr-gunicorn dtc-pr-celery
```

### Monitoring and Maintenance

#### Logs

```bash
# Gunicorn logs
tail -f /var/log/dtc-pr/gunicorn.log

# Celery logs
tail -f /var/log/dtc-pr/celery.log

# Nginx logs
tail -f /var/log/nginx/error.log
```

#### Database Backups

```bash
# Manual backup
pg_dump dtc_pr_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup (add to crontab)
0 2 * * * /usr/bin/pg_dump -U pr_user dtc_pr_db > /backups/dtc_pr_$(date +\%Y\%m\%d).sql
```

#### Performance Monitoring

```bash
# Check system resources
htop

# Check PostgreSQL connections
psql dtc_pr_db -c "SELECT * FROM pg_stat_activity;"

# Monitor Celery tasks
celery -A config events
```

### Troubleshooting

#### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U pr_user -d dtc_pr_db -h localhost

# Check PostgreSQL service
sudo systemctl status postgresql
```

#### Gunicorn Issues

```bash
# Check supervisor status
sudo supervisorctl status dtc-pr-gunicorn

# Restart service
sudo supervisorctl restart dtc-pr-gunicorn

# Check logs for errors
tail -100 /var/log/dtc-pr/gunicorn.log
```

#### File Storage Issues

```bash
# Check disk space
df -h

# Fix permissions
sudo chown -R www-data:www-data /var/www/dtc-pr/media
sudo chmod -R 755 /var/www/dtc-pr/media
```

### Security Hardening

1. Keep system packages updated
2. Configure firewall to allow only necessary ports (80, 443)
3. Regularly backup database and files
4. Monitor audit logs for suspicious activity
5. Use strong passwords and SSH keys
6. Enable 2FA for admin access
7. Regular security audits

### Scaling Considerations

- Use separate database server for high load
- Implement CDN for static files
- Use load balancer (Nginx, HAProxy) for multiple app servers
- Implement caching layer (Redis, Memcached)
- Monitor and optimize database queries
- Consider read replicas for reporting

### Support and Updates

- Regular Django security updates
- PostgreSQL maintenance and updates
- Redis updates and monitoring
- Log rotation and cleanup
- Database vacuum and analyze regularly
