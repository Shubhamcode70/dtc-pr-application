# Developer Quick Reference

## Quick Command Guide

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python scripts/init_project.py
python manage.py runserver

# Testing
python manage.py test                          # All tests
python manage.py test apps.pr.tests.PRTypeTestCase  # Specific test class
coverage run --source='.' manage.py test      # With coverage
coverage report                               # Show coverage

# Database
python manage.py makemigrations               # Create migrations
python manage.py migrate                      # Apply migrations
python manage.py sqlmigrate apps.pr 0001      # Preview SQL
python manage.py flush --no-input             # Reset (dev only)

# Admin
python manage.py createsuperuser              # Create user
python manage.py changepassword admin         # Change password

# Shell
python manage.py shell_plus                   # Django shell with models preloaded
# Then: from apps.pr.models import *; pr = PurchaseRequisition.objects.first()

# Logs
tail -f logs/pr_app.log                       # Watch logs
```

## Key Model Relationships

```
User (Django)
  ↓ (OneToOne auto-create)
UserProfile
  ├─ role → Role
  └─ approval_limit

PurchaseRequisition
  ├─ requester → User
  ├─ pr_type → PRType
  ├─ approval_chain → ApprovalChain
  ├─ created_by → User
  └─ items → PRItem (reverse)

PRItem
  └─ pr → PurchaseRequisition

PRApproval
  ├─ pr → PurchaseRequisition
  ├─ assigned_to → User
  └─ approved_by → User (nullable)

ApprovalChain
  └─ approval_sequence (JSON field)

Vendor
  ├─ contacts → VendorContact
  └─ quotations → VendorQuotation
```

## RBAC Usage Patterns

### Checking Permissions

```python
from apps.users.permissions import has_role, is_admin, is_approver

# In views
if has_role(user, 'admin'):
    # Admin logic

if is_approver(user):
    # Approver logic

# Multiple roles
if has_any_role(user, ['admin', 'finance']):
    # Either admin or finance
```

### Using Decorators

```python
from apps.users.permissions import require_role, require_admin, require_approver
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
@require_admin
def admin_only_view(request):
    return HttpResponse("Admin only")

@require_approver
def approval_view(request):
    return HttpResponse("Approvers only")

@require_role('finance')
def finance_view(request):
    return HttpResponse("Finance only")
```

### In Templates

```django
{% if user|has_role:"admin" %}
    <button>Admin Panel</button>
{% endif %}

{% if user|is_approver %}
    <a href="/approvals/">Pending Approvals</a>
{% endif %}
```

## PR Workflow

### Creating a PR

```python
from apps.pr.services import PRService
from apps.pr.models import PRType, PRItem

# Create PR
pr = PRService.create_pr(
    requester=request.user,
    pr_type=PRType.objects.get(code='OPEX'),
    department='Operations',
    purpose='Buy office supplies'
)

# Add items
PRItem.objects.create(
    pr=pr,
    item_number=1,
    short_text='Pens',
    quantity=100,
    unit='PC',
    unit_price=10.00,
    created_by=request.user
)

# Submit for approval
pr = PRService.submit_pr(pr, request.user)
# This auto-creates PRApproval records based on ApprovalChain
```

### Approving a PR

```python
from apps.pr.models import PRApproval
from apps.pr.services import PRService

# Get pending approval
approval = PRApproval.objects.get(
    pr_id=pr_id,
    status='pending',
    approval_level=1
)

# Approve
approval = PRService.approve_pr(
    approval=approval,
    user=request.user,
    comments='Approved for purchase'
)

# Rejected (alternative)
approval = PRService.reject_pr(
    approval=approval,
    user=request.user,
    reason='Budget exceeded'
)
```

## ApprovalChain Query Patterns

### Get Applicable Chains

```python
from apps.pr.models import ApprovalChain
from decimal import Decimal

# For a given amount
chains = ApprovalChain.get_applicable_chains(
    Decimal('500000'),  # 5 Lakhs
    pr_type='OPEX'      # Optional
)

# Use highest priority
if chains:
    approval_chain = chains[0]
```

### Create Custom Approval Chain

```python
from apps.pr.models import ApprovalChain
from decimal import Decimal

chain = ApprovalChain.objects.create(
    name='Special Purchase Chain',
    condition_type='amount_range',
    min_amount=Decimal('0'),
    max_amount=Decimal('5000000'),
    approval_sequence=[
        {
            'level': 1,
            'role': 'manager',
            'min_approvers': 1,
            'parallel': False,
            'description': 'Manager approval'
        },
        {
            'level': 2,
            'role': 'approver',
            'min_approvers': 2,
            'parallel': False,
            'description': '2 approvers at level 2'
        }
    ],
    requires_ipc=True,
    requires_cipc=False,
    is_active=True
)
```

## Admin Interface Tips

### Viewing PRs with Line Items
1. Go to `/admin/pr/purchaserequisition/`
2. Click a PR to view inline items
3. Add/edit items directly
4. Change status from dropdown
5. Save to trigger signals

### Managing Approval Chains
1. Go to `/admin/pr/approvalchain/`
2. Click to edit a chain
3. Modify JSON approval_sequence field
4. Save to apply to new PRs
5. Existing PRs keep their original chain

### Assigning Approvers
1. Go to `/admin/auth/user/` → Select user
2. Click their UserProfile
3. Set role: "Approver"
4. Check "Is Approver": ✓
5. Set "Approval Limit": 5000000 (5L)
6. Save

## Audit Trail Access

### View Activity Logs
```python
from apps.audit.models import ActivityLog

# Recent PR activity
ActivityLog.objects.filter(
    pr_id=pr_id
).order_by('-created_at')[:10]

# Approver actions
ActivityLog.objects.filter(
    event__in=['approval_completed', 'pr_approved']
).order_by('-created_at')
```

### View Approval History
```python
from apps.pr.models import PRStatus

# PR status changes
PRStatus.objects.filter(pr_id=pr_id).order_by('created_at')

# See who changed what and when
for status in pr.prstatus_set.all():
    print(f"{status.changed_by}: {status.from_status} → {status.to_status}")
```

## File Upload Pattern

```python
from apps.attachments.models import Attachment, AttachmentType

# Create attachment
attachment = Attachment.objects.create(
    pr=pr,
    attachment_type=AttachmentType.objects.get(name='Quotation'),
    file=request.FILES['quotation'],
    uploaded_by=request.user,
    file_name='vendor_quote.pdf'
)

# Access file
file_path = attachment.file.url
file_hash = attachment.file_hash
```

## Notification Pattern (When Enabled)

```python
from apps.notifications.services import EmailNotificationService
from apps.notifications.tasks import send_notification

# Send approval request
EmailNotificationService.send_approval_request(
    pr=pr,
    approver=approver_user,
    approval_chain=approval_chain
)

# Or use Celery async
send_notification.delay(
    template_name='pr_approved',
    recipient_id=pr.requester.id,
    context={'pr_number': pr.pr_number}
)
```

## Common Queries

```python
# Get all pending PRs for approver
from apps.pr.models import PRApproval
PRApproval.objects.filter(
    assigned_to=request.user,
    status='pending'
).select_related('pr')

# Get PRs by status
from apps.pr.models import PurchaseRequisition
prs = PurchaseRequisition.objects.filter(
    status='pending_approval'
).order_by('-created_at')

# Get PRs above certain amount
prs = PurchaseRequisition.objects.filter(
    grand_total__gte=1000000
).select_related('requester', 'approval_chain')

# Get PRs by requester
my_prs = request.user.purchaserequisition_set.all()

# Get pending approvals in priority order
approvals = PRApproval.objects.filter(
    assigned_to=request.user,
    status='pending'
).select_related('pr__approval_chain').order_by(
    'approval_level', '-pr__grand_total'
)
```

## Testing Your Code

### Write Unit Tests

```python
from django.test import TestCase
from apps.pr.models import PurchaseRequisition, PRType
from apps.pr.services import PRService

class PRTestCase(TestCase):
    def setUp(self):
        self.pr_type = PRType.objects.create(
            code='TEST',
            name='Test Type',
            type='test'
        )
    
    def test_pr_creation(self):
        pr = PRService.create_pr(
            requester=self.user,
            pr_type=self.pr_type,
            department='Test',
            purpose='Test PR'
        )
        self.assertEqual(pr.status, 'draft')
        self.assertTrue(pr.pr_number.startswith('PR/'))
```

### Run Tests

```bash
# All tests
python manage.py test

# With verbose output
python manage.py test -v 2

# Stop on first failure
python manage.py test --failfast

# With coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

## Environment Variables (from .env)

```
DEBUG=False                          # Set to False in production
ENVIRONMENT=production               # or 'development'

DATABASE_URL=postgresql://user:pass@localhost/pr_db
REDIS_URL=redis://localhost:6379/0

SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

EMAIL_BACKEND=smtp                  # When configuring email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Useful Django Admin Shortcuts

```
/admin/                                      # Dashboard
/admin/auth/user/                           # Users
/admin/users/userprofile/                   # User profiles & roles
/admin/users/role/                          # Roles
/admin/pr/purchaserequisition/              # PRs
/admin/pr/approvalchain/                    # Approval chains
/admin/pr/prapproval/                       # Approvals
/admin/pr/prtype/                           # PR types
/admin/vendor/vendor/                       # Vendors
/admin/attachments/attachment/              # Files
/admin/audit/auditlog/                      # Audit logs
/admin/audit/activitylog/                   # Activity logs
```

## Debug Mode

```python
# Temporary debug output
import logging
logger = logging.getLogger(__name__)

logger.info(f"PR status: {pr.status}")
logger.error(f"Error approving PR: {str(e)}")

# View in console or logs/pr_app.log
```

## Common Errors & Solutions

| Error | Solution |
|-------|----------|
| `ApprovalChain.DoesNotExist` | Check if matching chain exists for amount/PR type |
| `User matching query does not exist` | User must exist before assigning approval |
| `PRApproval.status is not 'pending'` | Can't approve/reject if already processed |
| `No approvers available` | Check approver role setup and approval limit |
| `File upload failed` | Check media directory exists and is writable |
| `Email not sending` | Verify EMAIL_* env vars in .env |

## Git Workflow

```bash
# Check current branch
git status

# See changes
git diff

# Stage changes
git add .

# Commit with message
git commit -m "Add PR approval workflow"

# Push to branch (v0 handles this)
git push
```

## Performance Tips

1. **Use select_related()** for ForeignKey queries
2. **Use prefetch_related()** for reverse relations
3. **Add indexes** on frequently filtered fields
4. **Cache permissions** in Redis (1 hour TTL)
5. **Use QuerySet.only()** to limit fields
6. **Monitor slow queries** in DEBUG mode

## Additional Resources

- **Django Docs**: https://docs.djangoproject.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Celery Docs**: https://docs.celeryproject.org/
- **Project README**: See README.md

---

**Happy coding!** 🚀

For questions, check IMPLEMENTATION_STATUS.md or README.md
