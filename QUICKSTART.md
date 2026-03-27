# DTC PR Application - Quick Start Guide

## Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Redis 6.0+ (optional for development, required for production)
- pip or conda

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Database & Environment
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Initialize Project Data
```bash
python scripts/init_project.py
```

This creates:
- ✓ 5 default roles (Admin, Manager, Requester, Approver, Finance)
- ✓ 4 PR types (CAPEX, OPEX, Maintenance, Service)
- ✓ 3 approval chains with amount-based rules
- ✓ Superuser account (admin/admin123)

### 5. Start Development Server
```bash
python manage.py runserver
```

Access at: http://localhost:8000

## First Login

**URL**: http://localhost:8000/admin/
- **Username**: admin
- **Password**: admin123

⚠️ **CHANGE THIS PASSWORD IMMEDIATELY IN PRODUCTION**

## Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/admin/` | Django Admin Panel |
| `/api/auth/login/` | User Login |
| `/api/dashboard/` | PR Dashboard |
| `/api/pr/list/` | List All PRs |
| `/api/pr/create/` | Create New PR |

## Important Models

### 1. ApprovalChain (CRITICAL)
Defines approval rules based on purchase amount:
```
< 10 Lakhs   → Manager approval
10L - 1 Cr   → Manager + Approver + IPC
> 1 Crore    → Manager + 2 Approvers + IPC + CIPC
```

Access in admin: `/admin/pr/approvalchain/`

### 2. PurchaseRequisition
Main PR entity with line items, approvals, and status tracking.

Access in admin: `/admin/pr/purchaserequisition/`

### 3. UserProfile & Role
User roles control what actions they can perform.

Access in admin: 
- `/admin/users/userprofile/`
- `/admin/users/role/`

## Common Tasks

### Add a New User with Approval Authority
1. Go to `/admin/auth/user/` → Create user
2. Go to `/admin/users/userprofile/` → Edit user's profile
3. Set role: "Approver"
4. Enable "Is Approver": ✓
5. Set "Approval Limit": 5000000 (5 Lakhs for example)

### Create a Purchase Requisition
1. Login as Requester or Approver
2. Navigate to PR creation form
3. Fill in PR details:
   - Department
   - Purpose of Requirement
   - PR Type (CAPEX/OPEX)
4. Add line items (qty, unit, price)
5. Click "Submit" to start approval workflow

### Approve a PR
1. Login as Approver
2. Go to "Pending Approvals" section
3. Click on PR to review
4. Add comments if needed
5. Click "Approve" or "Reject"

## Database Reset (Development Only)
```bash
# Delete all data and start fresh
python manage.py flush --no-input

# Recreate schema
python manage.py migrate

# Reinitialize data
python scripts/init_project.py
```

## Troubleshooting

### Port Already in Use
```bash
# Use different port
python manage.py runserver 8001
```

### Database Connection Error
```bash
# Check PostgreSQL is running
psql -U postgres -h localhost

# Verify credentials in .env match PostgreSQL setup
```

### Missing logs directory
```bash
mkdir -p logs/
```

## Running Tests
```bash
# All tests
python manage.py test

# Specific app
python manage.py test apps.pr

# With coverage
coverage run --source='.' manage.py test
coverage report
```

## Next Steps

1. **Customize Approval Chains** → `/admin/pr/approvalchain/`
2. **Add More Users** → `/admin/auth/user/`
3. **Configure Email** → Set `EMAIL_*` in `.env` and uncomment notification code
4. **Customize PR Fields** → Edit `apps/pr/models.py`
5. **Deploy to Production** → See README.md for deployment guide

## Support

- **Documentation**: See README.md
- **Error Logs**: Check `logs/pr_app.log`
- **Database Queries**: Enable `DEBUG = True` in settings to see query logs

---

**Ready to use!** 🚀

For detailed documentation, see [README.md](README.md)
