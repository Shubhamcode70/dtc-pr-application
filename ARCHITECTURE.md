# DTC PR Application - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE LAYER (Phase 4+)            │
│  [Web Interface]  [Mobile Interface]  [API Client]              │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                    DJANGO APPLICATION LAYER                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           VIEWS & URL ROUTING (Phase 4+)                │  │
│  │  [User Auth]  [PR Management]  [Approvals]  [Dashboard] │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │         BUSINESS LOGIC SERVICES LAYER (✓ Ready)          │  │
│  │                                                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │  PRService   │  │   Approval   │  │  Vendor      │   │  │
│  │  │  - create    │  │  ChainService│  │  Service     │   │  │
│  │  │  - submit    │  │  - create    │  │  (Phase 7)   │   │  │
│  │  │  - approve   │  │  - validate  │  └──────────────┘   │  │
│  │  │  - reject    │  │  - match     │                      │  │
│  │  └──────────────┘  └──────────────┘                      │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │           MODEL LAYER (✓ Complete)                       │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │ Core Models (BaseModel with audit fields)       │    │  │
│  │  │ [created_at] [updated_at] [created_by]         │    │  │
│  │  │ [updated_by] [is_deleted] [soft_delete_mixin]  │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │                                                           │  │
│  │  ┌──────────────────┐  ┌──────────────────┐            │  │
│  │  │ User Models      │  │ PR Models        │            │  │
│  │  │ ─────────────────│  │ ─────────────────│            │  │
│  │  │ User (Django)    │  │ PRType           │            │  │
│  │  │ Role             │  │ ApprovalChain ⭐  │            │  │
│  │  │ UserProfile      │  │ PR (PR Item*)    │            │  │
│  │  │ PermissionGroup  │  │ PRApproval       │            │  │
│  │  │ LoginAttempt     │  │ PRStatus         │            │  │
│  │  └──────────────────┘  └──────────────────┘            │  │
│  │                                                           │  │
│  │  ┌──────────────────┐  ┌──────────────────┐            │  │
│  │  │ Vendor Models    │  │ File Models      │            │  │
│  │  │ ─────────────────│  │ ─────────────────│            │  │
│  │  │ Vendor           │  │ AttachmentType   │            │  │
│  │  │ VendorContact    │  │ Attachment       │            │  │
│  │  │ VendorQuotation  │  │ FileIndex        │            │  │
│  │  └──────────────────┘  │ AccessLog        │            │  │
│  │                         └──────────────────┘            │  │
│  │                                                           │  │
│  │  ┌──────────────────┐  ┌──────────────────┐            │  │
│  │  │ Audit Models     │  │ Notification     │            │  │
│  │  │ ─────────────────│  │ Models [COMMENT] │            │  │
│  │  │ AuditLog         │  │ ─────────────────│            │  │
│  │  │ ActivityLog      │  │ Template         │            │  │
│  │  │ ApprovalHistory  │  │ Notification     │            │  │
│  │  └──────────────────┘  │ Preference       │            │  │
│  │                         └──────────────────┘            │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│            MIDDLEWARE & UTILITIES LAYER                     │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ RBAC System      │  │ Custom Managers  │               │
│  │ ─────────────────│  │ ─────────────────│               │
│  │ Decorators       │  │ SoftDeleteManager│               │
│  │ - @require_role  │  │ DefaultManager   │               │
│  │ - @require_admin │  │                  │               │
│  │ Mixins           │  │ Soft Delete      │               │
│  │ - RBACMixin      │  │ - auto exclude   │               │
│  │ Functions        │  │ - restore()      │               │
│  │ - has_role()     │  │ - hard_delete()  │               │
│  │ - is_approver()  │  │                  │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Request Logging  │  │ File Storage     │               │
│  │ Middleware       │  │ Backend          │               │
│  │ ─────────────────│  │ ─────────────────│               │
│  │ HTTP request/    │  │ LocalFileBackend │               │
│  │ response log     │  │ - organized paths│               │
│  │ IP & User-Agent  │  │ - SHA256 hashing │               │
│  │ Performance      │  │ - duplicate      │               │
│  │ metrics          │  │   prevention     │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Signal Handlers  │  │ Django Admin     │               │
│  │ ─────────────────│  │ ─────────────────│               │
│  │ Auto UserProfile │  │ Configured for   │               │
│  │ creation         │  │ all models       │               │
│  │ Auto role assign │  │ Inline editing   │               │
│  │ Audit logging    │  │ Custom actions   │               │
│  └──────────────────┘  └──────────────────┘               │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              DATA PERSISTENCE LAYER                         │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │        DATABASE (PostgreSQL)                     │      │
│  │  ┌────────────────────────────────────────────┐ │      │
│  │  │ 25+ Tables with proper relationships       │ │      │
│  │  │ 40+ Indexes for query optimization         │ │      │
│  │  │ Foreign key constraints with policies      │ │      │
│  │  │ Soft delete tracking (is_deleted flag)     │ │      │
│  │  │ Audit fields (created_by, updated_at, etc)│ │      │
│  │  └────────────────────────────────────────────┘ │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │         CACHING LAYER (Redis)                    │      │
│  │  - User permissions (1 hour TTL)                │      │
│  │  - Vendor lists (24 hours TTL)                  │      │
│  │  - Session data                                 │      │
│  │  - Query result caching                         │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │    FILE STORAGE LAYER (Local / S3-ready)        │      │
│  │  - PR attachments                               │      │
│  │  - Organized: YYYY/MM/PR_ID/type/               │      │
│  │  - Unique filename generation                   │      │
│  │  - SHA256 hashing                               │      │
│  └──────────────────────────────────────────────────┘      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│        ASYNCHRONOUS TASK QUEUE (Celery + Redis)             │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Background Tasks │  │ Scheduled Tasks  │               │
│  │ ─────────────────│  │ ─────────────────│               │
│  │ Email sending    │  │ Approval reminders │             │
│  │ File processing  │  │ Report generation │             │
│  │ Bulk operations  │  │ Cache cleanup     │             │
│  └──────────────────┘  └──────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow - Purchase Requisition Workflow

```
┌────────────────────────────────────────────────────────────┐
│  REQUESTER creates PR                                      │
│  ↓                                                         │
│  [Form Submission] → PRService.create_pr()               │
│                     └─→ status: DRAFT                     │
│                                                           │
│  REQUESTER adds PRItems (multiple)                        │
│  ↓                                                         │
│  [Add Items] → PRItem.objects.create()                   │
│               └─→ auto-calc total_value = qty × price   │
│                                                           │
│  REQUESTER submits PR                                     │
│  ↓                                                         │
│  [Submit] → PRService.submit_pr()                        │
│            ├─→ Calculate grand_total (sum of items)     │
│            ├─→ status: SUBMITTED                         │
│            ├─→ Find ApprovalChain based on amount       │
│            │   ⭐ ApprovalChain.get_applicable_chains() │
│            │      Matches on:                            │
│            │      - Amount range                         │
│            │      - PR type                              │
│            │      - Department                           │
│            │      - Selects highest priority             │
│            │                                              │
│            ├─→ Create PRApproval records                │
│            │   For each level in approval_sequence:     │
│            │   - Find users with required role          │
│            │   - Verify approval_limit >= PR amount     │
│            │   - Create approval (status: PENDING)      │
│            │                                              │
│            └─→ Create ActivityLog entry                  │
│                Log: "PR submitted for approval"          │
│                                                          │
│  APPROVER reviews PR                                     │
│  ↓                                                        │
│  [View Pending] → PRApproval.objects.filter(           │
│                   assigned_to=approver,                 │
│                   status='pending'                      │
│                 )                                        │
│                                                          │
│  APPROVER approves or rejects                           │
│  ├─ APPROVE:                                            │
│  │  ↓                                                    │
│  │  [Approve] → PRService.approve_pr()                 │
│  │             ├─→ approval.status: APPROVED           │
│  │             ├─→ Check if all approvals at this level│
│  │             ├─→ If yes, create approvals for next   │
│  │             │   level (if any)                      │
│  │             ├─→ If no more levels:                  │
│  │             │   pr.status: APPROVED                 │
│  │             └─→ ActivityLog: "Level X approved"    │
│  │                                                      │
│  └─ REJECT:                                             │
│     ↓                                                    │
│     [Reject] → PRService.reject_pr()                   │
│                ├─→ approval.status: REJECTED           │
│                ├─→ pr.status: REJECTED                 │
│                ├─→ Mark other approvals: ESCALATED    │
│                └─→ ActivityLog: "PR rejected"         │
│                                                        │
│  PR APPROVED (all levels complete)                     │
│  ↓                                                      │
│  [Approved] → PurchaseRequisition created in SAP      │
│              or marked PR_CREATED in system            │
│              status: CLOSED                            │
│                                                        │
└────────────────────────────────────────────────────────────┘
```

## ApprovalChain Decision Logic ⭐ CRITICAL

```
┌────────────────────────────────────────────────┐
│  PR SUBMITTED: grand_total = 5,50,000          │
│  PR Type: OPEX                                 │
│  Department: Operations                        │
└────────────┬───────────────────────────────────┘
             ↓
    ┌────────────────────────────────────────────┐
    │ ApprovalChain.get_applicable_chains()      │
    │ Find all chains that MATCH:                │
    │ ├─ Condition type: amount_range            │
    │ ├─ 5,50,000 between min & max              │
    │ └─ Optional: pr_type=OPEX match            │
    │                                             │
    │ AVAILABLE CHAINS:                          │
    │ ┌─────────────────────────────┐           │
    │ │ Chain 1: < 10L              │           │
    │ │ min: 0, max: 10,00,000      │           │
    │ │ ✓ MATCHES (5,50,000 < 10L)  │           │
    │ │ priority: 10                │           │
    │ └─────────────────────────────┘           │
    │ ┌─────────────────────────────┐           │
    │ │ Chain 2: 10L - 1Cr          │           │
    │ │ min: 10,00,000, max: 1Cr    │           │
    │ │ ✗ NO MATCH (5,50,000 < 10L) │           │
    │ └─────────────────────────────┘           │
    │ ┌─────────────────────────────┐           │
    │ │ Chain 3: > 1Cr              │           │
    │ │ min: 1Cr+                   │           │
    │ │ ✗ NO MATCH                  │           │
    │ └─────────────────────────────┘           │
    │                                             │
    │ RESULT: [Chain 1]                         │
    └────────────┬────────────────────────────────┘
                 ↓
    ┌────────────────────────────────────────────┐
    │ SELECTED CHAIN: "Small Purchase (< 10L)"   │
    │                                             │
    │ approval_sequence: [                       │
    │   {                                         │
    │     "level": 1,                            │
    │     "role": "manager",                     │
    │     "min_approvers": 1,                    │
    │     "parallel": false                      │
    │   }                                         │
    │ ]                                          │
    │                                             │
    │ requires_ipc: false                        │
    │ requires_cipc: false                       │
    └────────────┬────────────────────────────────┘
                 ↓
    ┌────────────────────────────────────────────┐
    │ CREATE APPROVAL RECORDS                    │
    │                                             │
    │ For Level 1 (role: manager):               │
    │ ├─ Find users with role='manager'          │
    │ ├─ Check approval_limit >= 5,50,000        │
    │ ├─ Select first available approver         │
    │ │  (Sorted by: seniority/priority)        │
    │ ├─ Create PRApproval:                      │
    │ │  - approval_level: 1                     │
    │ │  - assigned_to: Manager User             │
    │ │  - status: PENDING                       │
    │ │  - due_date: +3 days                     │
    │ └─ Create ActivityLog: "Sent to Manager"   │
    │                                             │
    │ No more levels → Await Level 1 approval    │
    └────────────────────────────────────────────┘
```

## RBAC Permission Flow

```
┌──────────────────────────────────┐
│ REQUEST RECEIVED                 │
│ user: john_user                  │
└────────────┬─────────────────────┘
             ↓
    ┌────────────────────────────────┐
    │ Check Permissions              │
    │                                │
    │ 1. Get UserProfile             │
    │    UserProfile.objects.get(    │
    │      user=john_user            │
    │    )                           │
    │                                │
    │ 2. Get Role                    │
    │    profile.role = "approver"   │
    │                                │
    │ 3. Check Approval Authority    │
    │    approval_limit = 20,00,000  │
    │    is_approver = True          │
    └────────────┬─────────────────────┘
                 ↓
    ┌────────────────────────────────┐
    │ DECISION TREE                  │
    │                                │
    │ @require_approver decorator    │
    │ ├─ Check: is_approver(user)    │
    │ │  └─ Checks profile.is_approver│
    │ │     and approval_limit > 0   │
    │ │     ✓ ALLOWED                │
    │ │                              │
    │ @require_role('finance')       │
    │ ├─ Check: has_role(user, 'f')  │
    │ │  └─ Checks profile.role.name │
    │ │     ✗ NOT ALLOWED            │
    │ │                              │
    │ Can approve amount < 20,00,000?│
    │ ├─ Check: approval_limit       │
    │ │  └─ If PR amount < limit     │
    │ │     ✓ ALLOWED                │
    │ │  └─ If PR amount >= limit    │
    │ │     ✗ NOT ALLOWED            │
    └────────────┬─────────────────────┘
                 ↓
    ┌────────────────────────────────┐
    │ GRANT/DENY ACCESS              │
    │                                │
    │ ✓ Allowed → Execute view       │
    │ ✗ Denied  → Redirect to login/ │
    │            deny page           │
    └────────────────────────────────┘
```

## Database Schema (Simplified)

```
┌─────────────────────────┐
│   users_role            │
├─────────────────────────┤
│ id [PK]                 │
│ name (admin, requester) │
│ description             │
│ is_active               │
└─────────────┬───────────┘
              │ (1:N)
              │
┌─────────────▼──────────────────┐
│   users_userprofile            │
├────────────────────────────────┤
│ id [PK]                        │
│ user_id [FK: User]             │
│ role_id [FK: Role]             │
│ is_approver                    │
│ approval_limit                 │
│ created_at, updated_at         │
│ created_by, updated_by         │
└────────────────────────────────┘


┌─────────────────────────┐
│   pr_prtype             │
├─────────────────────────┤
│ id [PK]                 │
│ code (CAPEX, OPEX)      │
│ name                    │
│ type                    │
│ description             │
└────────────┬────────────┘
             │ (1:N)
             │
┌────────────▼─────────────────────┐
│   pr_approvalchain ⭐            │
├───────────────────────────────────┤
│ id [PK]                           │
│ name                              │
│ condition_type                    │
│ min_amount, max_amount            │
│ approval_sequence [JSON]          │
│ requires_ipc, requires_cipc       │
│ priority                          │
│ is_active                         │
└───────┬───────────────────────────┘
        │ (1:N)
        │
┌───────▼────────────────────────────┐
│   pr_purchaserequisition           │
├────────────────────────────────────┤
│ id [PK]                            │
│ pr_number (unique)                 │
│ uuid                               │
│ requester_id [FK: User]            │
│ pr_type_id [FK: PRType]            │
│ approval_chain_id [FK: Chain]      │
│ department                         │
│ purpose_of_requirement             │
│ status (DRAFT, SUBMITTED, etc)     │
│ grand_total                        │
│ request_date, submitted_date       │
│ approval_completed_date            │
│ created_at, updated_at             │
│ created_by, updated_by             │
│ is_deleted, deleted_at, deleted_by │
└───────┬────────────────────────────┘
        │ (1:N)
        │
┌───────▼──────────────────────────┐
│   pr_pritem                      │
├──────────────────────────────────┤
│ id [PK]                          │
│ pr_id [FK: PR]                   │
│ item_number                      │
│ short_text                       │
│ quantity                         │
│ unit                             │
│ unit_price                       │
│ total_value (auto-calc)          │
│ asset_code, cost_center          │
│ created_at, updated_at           │
│ created_by                       │
└──────────────────────────────────┘


┌───────────────────────────────────┐
│   pr_prapproval                   │
├───────────────────────────────────┤
│ id [PK]                           │
│ pr_id [FK: PR]                    │
│ approval_level                    │
│ assigned_to_id [FK: User]         │
│ status (PENDING, APPROVED, etc)   │
│ approved_by_id [FK: User]         │
│ approval_date                     │
│ comments                          │
│ assigned_date, due_date           │
│ created_at                        │
└───────────────────────────────────┘


┌───────────────────────────────────┐
│   audit_activitylog               │
├───────────────────────────────────┤
│ id [PK]                           │
│ pr_id [FK: PR]                    │
│ user_id [FK: User]                │
│ event (submitted, approved, etc)  │
│ description                       │
│ created_at                        │
└───────────────────────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────┐
│  BACKEND FRAMEWORK                      │
│  Django 5.x                             │
│  Django REST Framework                  │
│  Django Admin                           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  PYTHON UTILITIES                       │
│  Celery (Task Queue)                    │
│  redis-py (Redis Client)                │
│  psycopg2 (PostgreSQL Driver)           │
│  Pillow (Image Processing)              │
│  python-dateutil (Date Utils)           │
│  pytz (Timezone Support)                │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  PRODUCTION DATABASES                   │
│  PostgreSQL 12+ (Primary)               │
│  Redis 6.0+ (Caching/Sessions)          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  DEVELOPMENT TOOLS                      │
│  pytest (Testing)                       │
│  coverage (Code Coverage)               │
│  black (Code Formatting)                │
│  flake8 (Linting)                       │
│  django-debug-toolbar (Profiling)       │
│  django-extensions (Management Tools)   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  DEPLOYMENT READY                       │
│  Gunicorn (WSGI Server)                 │
│  Daphne (ASGI Server)                   │
│  Nginx (Reverse Proxy)                  │
│  Docker (Containerization - Ready)      │
│  Environment-based Config               │
└─────────────────────────────────────────┘
```

## Performance Optimizations

```
┌──────────────────────────────────────────┐
│ DATABASE LAYER                           │
│                                          │
│ ✓ 40+ Indexes on frequently queried cols│
│ ✓ Connection pooling (PgBouncer)        │
│ ✓ Query optimization with .select_      │
│   related() and .prefetch_related()     │
│ ✓ Composite indexes on common filters   │
│ ✓ Soft delete with is_deleted index    │
│                                          │
│ Example indexes:                         │
│ - PurchaseRequisition: pr_number, status│
│ - PRApproval: pr, assigned_to, status  │
│ - AuditLog: user, model_name, created  │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ CACHING LAYER                            │
│                                          │
│ ✓ User permissions cache (1h TTL)       │
│ ✓ Vendor list cache (24h TTL)           │
│ ✓ Session storage in Redis              │
│ ✓ Query result caching                  │
│                                          │
│ Avoids N+1 queries:                     │
│ - Always use select_related()           │
│ - Use prefetch_related() for M2M        │
│ - Cache calculated values               │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ APPLICATION LAYER                        │
│                                          │
│ ✓ Async task processing (Celery)        │
│ ✓ Background notifications              │
│ ✓ Batch file processing                 │
│ ✓ Report generation async               │
│                                          │
│ Use cases:                               │
│ - send_notification.delay(...)          │
│ - process_file_async.delay(...)         │
│ - generate_report.delay(...)            │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ SCALABILITY                              │
│                                          │
│ ✓ Stateless design for horizontal scale │
│ ✓ Designed for 500+ concurrent users    │
│ ✓ Connection pooling prevents limits    │
│ ✓ Redis sessions for multi-server       │
│ ✓ Database read replicas (ready)        │
└──────────────────────────────────────────┘
```

## Security Implementation

```
┌──────────────────────────────────────────┐
│ AUTHENTICATION                           │
│                                          │
│ ✓ Django session-based auth             │
│ ✓ PBKDF2 password hashing               │
│ ✓ Secure HTTP-only cookies              │
│ ✓ CSRF token protection                 │
│ ✓ Login attempt tracking                │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ AUTHORIZATION (RBAC)                     │
│                                          │
│ ✓ Role-based decorators                 │
│ ✓ Permission mixins                     │
│ ✓ View-level checks                     │
│ ✓ Approval limit enforcement            │
│ ✓ Department-level access               │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ DATA PROTECTION                          │
│                                          │
│ ✓ SQL injection: ORM prevents            │
│ ✓ XSS: Template auto-escaping            │
│ ✓ CSRF: Token on all forms              │
│ ✓ Path traversal: Filename sanitization │
│ ✓ File upload validation                │
│ ✓ Type whitelisting                     │
│                                          │
│ Encrypted:                               │
│ ✓ Session data (Redis)                  │
│ ✓ Password hashing                      │
│ ✓ HTTPS in production                   │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ AUDIT & COMPLIANCE                       │
│                                          │
│ ✓ Immutable audit logs                  │
│ ✓ User tracking on all changes          │
│ ✓ Soft delete preserves data            │
│ ✓ Status transition audit               │
│ ✓ Approval trail tracking               │
│ ✓ File access logging                   │
│ ✓ Login attempt tracking                │
└──────────────────────────────────────────┘
```

## Deployment Architecture (Production Ready)

```
┌─────────────────────────────────────────────────┐
│              CLIENT LAYER                       │
│  [Web Browser] [Mobile] [API Client]            │
└──────────────────┬──────────────────────────────┘
                   │ HTTPS
┌──────────────────▼──────────────────────────────┐
│         REVERSE PROXY / LOAD BALANCER           │
│  Nginx / HAProxy                                │
│  - SSL/TLS termination                          │
│  - Load balancing                               │
│  - Static file serving                          │
│  - Compression                                  │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────────┐  ┌───────▼──────────┐
│  Gunicorn Worker │  │  Gunicorn Worker │  (n replicas)
│  [Django App]    │  │  [Django App]    │
│  Port: 8000      │  │  Port: 8000      │
└────────┬─────────┘  └───────┬──────────┘
         │                    │
         └────────┬───────────┘
                  │
        ┌─────────▼──────────┐
        │  Celery Workers    │
        │  (Background tasks)│
        │  - Notifications  │
        │  - File processing│
        │  - Reports        │
        └────────────────────┘
                  │
        ┌─────────┴──────────────┐
        │                        │
┌───────▼────────────┐  ┌────────▼──────────┐
│  PostgreSQL DB     │  │  Redis Cache      │
│  (Read replicas)   │  │  - Sessions       │
│  - Main data       │  │  - Permissions    │
│  - Audit logs      │  │  - Task queue     │
└────────────────────┘  └───────────────────┘

┌────────────────────────────────────────┐
│  FILE STORAGE                          │
│  - Local: /var/www/media/              │
│  - S3 Ready: Swappable backend         │
│  - Organized: YYYY/MM/PR_ID/type/      │
│  - Backup: Daily incremental           │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  LOGGING & MONITORING                  │
│  - App logs: /var/log/pr_app.log       │
│  - Access logs: Nginx                  │
│  - Error tracking: Sentry (optional)   │
│  - Metrics: Prometheus (optional)      │
└────────────────────────────────────────┘
```

---

## Next Phases

```
Phase 1-2 ✅ COMPLETE
└─ Foundation & Core Architecture

Phase 3 🚀 IN PROGRESS
└─ PR Models & ApprovalChain (CRITICAL)

Phase 4 ⏳ NEXT
├─ PR CRUD Views
├─ Forms & Validation
├─ Line item management
└─ API endpoints

Phase 5 ⏳
├─ Approval workflow UI
├─ Dashboard integration
└─ Notification integration

Phase 6-10 ⏳
├─ File management
├─ Vendor management
├─ Analytics
├─ Testing
└─ Deployment
```

---

**Status**: Foundation complete, ready for Phase 4 implementation 🚀
