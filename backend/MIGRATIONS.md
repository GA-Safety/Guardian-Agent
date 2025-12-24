# Database Migrations Guide

## Current Status

✅ **All tables are already in PostgreSQL!** The initial migration has been applied.

## Alembic Commands

### Check Current Migration Version
```bash
cd backend
alembic current
```

### View Migration History
```bash
cd backend
alembic history
```

### Apply All Pending Migrations
```bash
cd backend
alembic upgrade head
```

### Create a New Migration
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Apply Specific Migration
```bash
cd backend
alembic upgrade <revision_id>
```

### Rollback One Migration
```bash
cd backend
alembic downgrade -1
```

### Rollback to Specific Version
```bash
cd backend
alembic downgrade <revision_id>
```

## Verify Tables in Database

### Using Python
```bash
source .venv/bin/activate
python -c "
from backend.app.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tables:', sorted(tables))
"
```

### Using psql
```bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt"
```

## Current Tables

- `users` - Base user accounts
- `protected_users` - Elderly users being protected
- `guardians` - Family members who monitor protected users
- `messages` - Analyzed SMS messages
- `shared_messages` - Messages shared with guardians
- `guardian_invitations` - Guardian invitation codes

## Environment Setup

Make sure your `.env` file has:
```
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=your_username
DB_PASSWORD=your_password
```

