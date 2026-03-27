# DTC Purchase Requisition (PR) Application

A production-grade Purchase Requisition management system built with Django, PostgreSQL, and modern architecture best practices.

## Features

### Core Functionality
- **PR Lifecycle Management**: Create, submit, approve, and track purchase requisitions
- **Role-Based Access Control (RBAC)**: Admin, Manager, Requester, Approver, and Finance roles
- **Multi-Level Approval Workflow**: Configurable approval chains based on amount thresholds
- **File Management**: Secure attachment handling with organized storage structure
- **Vendor Management**: Master vendor data and quotation tracking
- **Audit Logging**: Complete activity trail for compliance and tracking
- **Dashboard & Analytics**: Real-time PR statistics and approval metrics

### Non-Functional
- **Scalability**: Built for 500+ concurrent users with connection pooling
- **Performance**: Optimized queries, caching, and database indexing
- **Security**: HTTPS enforcement, CSRF protection, SQL injection prevention
- **Maintainability**: Clean architecture with modular apps and separation of concerns

## Architecture

```
pr_application/
├── config/              # Django settings and URLs
├── apps/
│   ├── core/           # Base models with audit fields
│   ├── users/          # Authentication and RBAC
│   ├── pr/             # Purchase Requisition models and logic
│   ├── vendor/         # Vendor management
│   ├── attachments/    # File storage and handling
│   ├── audit/          # Audit logging and activity tracking
│   ├── notifications/  # Email notifications (commented)
│   └── dashboard/      # Analytics and dashboards
├── templates/          # Django HTML templates
├── static/            # CSS, JavaScript, images
└── media/             # User-uploaded files
```

## Technology Stack

- **Backend**: Django 5.x with Django REST Framework
- **Database**: PostgreSQL with connection pooling
- **Task Queue**: Celery + Redis (for async operations)
- **File Storage**: Local filesystem (swappable for S3)
- **Caching**: Redis
- **Frontend**: Django Templates + HTMX
- **Authentication**: Django sessions (no JWT)

## Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Redis 6.0+

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata initial_data  # If available
```

### 4. Create Initial Data
```bash
python manage.py shell
```

```python
from apps.users.models import Role
from apps.pr.models import PRType

# Create roles
Role.objects.create(name='admin', description='Administrator')
Role.objects.create(name='manager', description='Manager')
Role.objects.create(name='requester', description='Requester')
Role.objects.create(name='approver', description='Approver')
Role.objects.create(name='finance', description='Finance Officer')

# Create PR types
PRType.objects.create(code='CAPEX', name='Capital Expenditure', type='capex')
PRType.objects.create(code='OPEX', name='Operating Expenditure', type='opex')
```

### 5. Run Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` and login with your superuser credentials.

## Key Models

### ApprovalChain (CRITICAL)
Defines approval rules based on amount thresholds and PR types. Each chain specifies:
- Amount range (min/max)
- Approval levels and required roles
- IPC/CIPC approval requirements
- Parallel or sequential approval

### PurchaseRequisition
The main PR entity with:
- Basic details (requester, department, purpose)
- Line items with calculations
- Multi-level approvals
- Status tracking

### PRApproval
Tracks approval workflow:
- Assignment to approvers
- Approval/rejection with comments
- Timeline (assigned, due, completion dates)

## File Storage

Files are organized as:
```
media/pr_attachments/
└── YYYY/MM/PR_ID/
    ├── quotations/
    ├── comparison_sheets/
    └── rfq/
```

Storage backend is swappable - currently local, ready for S3 migration.

## Security Features

- CSRF token protection on all forms
- SQL injection prevention via Django ORM
- XSS prevention with template auto-escaping
- HTTPS enforcement in production
- Session-based authentication with secure cookies
- File upload validation and scanning
- Audit logging of all sensitive operations

## Performance Optimization

- Database connection pooling (PgBouncer)
- Query optimization with select_related/prefetch_related
- Indexed database fields on frequently queried columns
- Redis caching for user permissions and vendor data
- Pagination on list views (50 items default)
- Asynchronous file processing via Celery

## API Endpoints

See `config/urls.py` for complete URL configuration.

### Authentication
- `POST /api/auth/login/` - User login
- `GET /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile
- `GET /api/auth/permissions/` - Get user permissions

### PR Management
- `GET /api/pr/list/` - List all PRs
- `POST /api/pr/create/` - Create new PR
- `GET /api/pr/<id>/` - Get PR details
- `PUT /api/pr/<id>/update/` - Update PR
- `POST /api/pr/<id>/submit/` - Submit for approval

### Approvals
- `GET /api/pr/<id>/approvers/` - Get pending approvers
- `POST /api/approval/<id>/approve/` - Approve PR
- `POST /api/approval/<id>/reject/` - Reject PR

### File Management
- `POST /api/attachments/upload/` - Upload file
- `GET /api/attachments/<id>/download/` - Download file
- `DELETE /api/attachments/<id>/` - Delete file

## Notifications

Email notification system is implemented but commented. To enable:

1. Configure email credentials in `.env`:
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

2. Uncomment notification services in:
   - `apps/notifications/services.py`
   - `apps/notifications/tasks.py`

3. Restart Celery and Django

## Testing

Run tests with:
```bash
python manage.py test
```

For coverage:
```bash
coverage run --source='.' manage.py test
coverage report
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in `.env`
- [ ] Configure proper `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Enable HTTPS with `SECURE_SSL_REDIRECT=True`
- [ ] Configure PostgreSQL with proper backups
- [ ] Set up Redis for caching and sessions
- [ ] Configure Celery worker
- [ ] Set up log rotation
- [ ] Configure email credentials for notifications
- [ ] Run database migrations: `python manage.py migrate`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Set up Gunicorn and Nginx

### Docker Deployment
```bash
docker-compose up -d
```

## Contributing

1. Follow Django and Python best practices
2. Write tests for new features
3. Maintain test coverage > 80%
4. Document API endpoints and complex logic
5. Use pre-commit hooks for code formatting

## Support

For issues and feature requests, create an issue in the repository.

## License

MIT License - See LICENSE file for details

## Roadmap

- [ ] Phase 3: Complete ApprovalChain implementation and testing
- [ ] Phase 4: PR CRUD operations and form handling
- [ ] Phase 5: Full approval workflow implementation
- [ ] Phase 6: File management enhancements
- [ ] Phase 7: Vendor management system
- [ ] Phase 8: Dashboard and reporting
- [ ] Phase 9: Email notifications and Celery integration
- [ ] Phase 10: Production deployment and optimization
