# Database & Migrations Guide

> **Purpose**: Comprehensive guide for database schema management in Flash Sale Engine.  
> **Audience**: Backend developers, DevOps engineers.  
> **Status**: Philosophy and conventions only - no migration code.

---

## Table of Contents

1. [Why Alembic](#why-alembic)
2. [Migration Philosophy](#migration-philosophy)
3. [Naming Conventions](#naming-conventions)
4. [Breaking Changes](#breaking-changes)
5. [Rollback Strategies](#rollback-strategies)
6. [Common Production Mistakes](#common-production-mistakes)
7. [Quick Reference](#quick-reference)

---

## Why Alembic

### What is Alembic?

Alembic is the database migration tool for SQLAlchemy. It tracks schema changes as versioned Python scripts, allowing controlled, repeatable database evolution.

### Why Not Raw SQL Scripts?

| Approach | Problem |
|----------|---------|
| Raw SQL files | No dependency tracking, manual ordering |
| Django-style auto-migrations | SQLAlchemy doesn't have this built-in |
| ORM sync (`create_all`) | Destroys data, no rollback, no history |
| Manual DDL | Human error, no audit trail |

### Why Alembic Specifically?

```
✅ Native SQLAlchemy integration
✅ Python-based migrations (use ORM models)
✅ Dependency chain (upgrade/downgrade paths)
✅ Auto-generation from model changes
✅ Environment-aware (dev/staging/prod configs)
✅ Transaction-safe migrations
✅ Async support (critical for our stack)
```

### Alembic vs Alternatives

| Tool | Pros | Cons | Verdict |
|------|------|------|---------|
| **Alembic** | SQLAlchemy native, Python | Learning curve | ✅ Best for us |
| Flyway | SQL-first, simple | Java dependency, no ORM awareness | ❌ |
| Liquibase | XML/YAML, enterprise | Heavy, complex | ❌ |
| Django migrations | Auto-detect, easy | Django-only | ❌ |
| Prisma Migrate | Modern, TypeScript | Not Python | ❌ |

---

## Migration Philosophy

### Core Principles

#### 1. Migrations Are Immutable

Once a migration is deployed to any shared environment (staging/prod), it is **FROZEN**.

```
❌ NEVER: Edit a deployed migration
✅ ALWAYS: Create a new migration to fix issues
```

**Why?** Other developers and environments have already run it. Editing creates divergence.

#### 2. Forward-Only in Production

Production databases should ideally never roll back. Design migrations to be:
- Additive (add columns, tables)
- Non-destructive (rename, not delete)
- Backward-compatible (old code works with new schema)

#### 3. Small, Focused Migrations

```
❌ BAD:  "Refactor entire user system"
✅ GOOD: "Add phone column to users table"
✅ GOOD: "Create index on users.email"
✅ GOOD: "Add orders table"
```

**Why?**
- Easier to review
- Easier to debug failures
- Easier to rollback specific changes
- Faster to execute

#### 4. Data Migrations Separate from Schema

```
Migration 1: Add new column (nullable)
Migration 2: Backfill data
Migration 3: Add NOT NULL constraint
```

Never combine schema + data in one migration. Data migrations can be slow and need different error handling.

#### 5. Test Migrations on Production-Like Data

Dev database with 10 rows ≠ Production with 10 million rows.

```
❌ "Works on my machine"
✅ Test on staging with production data volume
✅ Estimate migration time before deploying
```

---

## Naming Conventions

### Migration File Names

Alembic generates: `{revision_id}_{slug}.py`

**Slug Format**: `{action}_{target}_{detail}`

```
# Good examples
001_create_users_table.py
002_add_email_index_to_users.py
003_create_products_table.py
004_add_stock_column_to_products.py
005_create_orders_table.py
006_add_foreign_key_orders_users.py
007_rename_price_to_unit_price_products.py
008_drop_deprecated_legacy_column.py

# Bad examples
001_changes.py              # Too vague
002_fix.py                  # What fix?
003_update_stuff.py         # Meaningless
004_john_changes.py         # Developer name irrelevant
```

### Action Verbs

| Action | Use When |
|--------|----------|
| `create` | New table |
| `add` | New column, index, constraint |
| `drop` | Removing (use sparingly!) |
| `rename` | Changing names |
| `alter` | Changing column type/properties |
| `backfill` | Data migration |
| `fix` | Correcting previous migration |

### Table Names

```python
# Plural, snake_case
users           ✅
products        ✅
order_items     ✅
product_images  ✅

# Avoid
User            ❌ (singular, PascalCase)
OrderItem       ❌ (PascalCase)
tbl_users       ❌ (Hungarian notation)
```

### Column Names

```python
# snake_case, descriptive
created_at      ✅
updated_at      ✅
user_id         ✅ (foreign key)
is_active       ✅ (boolean prefix)
has_shipped     ✅ (boolean prefix)
total_amount    ✅

# Avoid
createdAt       ❌ (camelCase)
UserID          ❌ (PascalCase)
active          ❌ (ambiguous for boolean)
amt             ❌ (abbreviation)
```

### Index Names

```
ix_{table}_{column}              # Single column
ix_{table}_{col1}_{col2}         # Composite
uq_{table}_{column}              # Unique constraint
fk_{table}_{column}_{ref_table}  # Foreign key
pk_{table}                       # Primary key (usually auto)
```

**Examples:**
```
ix_users_email
ix_orders_user_id_created_at
uq_users_email
fk_orders_user_id_users
```

---

## Breaking Changes

### What is a Breaking Change?

A schema change that makes existing application code fail:

| Change Type | Breaking? | Example |
|-------------|-----------|---------|
| Add nullable column | ❌ No | `ALTER TABLE users ADD phone VARCHAR` |
| Add NOT NULL column | ⚠️ Maybe | Fails if no default value |
| Drop column | ✅ Yes | Old code still reads it |
| Rename column | ✅ Yes | Old code uses old name |
| Change column type | ⚠️ Maybe | `VARCHAR(50)` → `VARCHAR(100)` is safe |
| Add table | ❌ No | Old code doesn't know about it |
| Drop table | ✅ Yes | Old code still queries it |

### The Expand-Contract Pattern

For breaking changes, use a multi-phase approach:

#### Phase 1: Expand (Add New)

```
Migration: Add new column/table alongside old
Code: Write to BOTH old and new
Duration: Until all code deployed
```

#### Phase 2: Migrate (Move Data)

```
Migration: Backfill new from old
Code: Read from NEW, write to BOTH
Duration: Until backfill complete
```

#### Phase 3: Contract (Remove Old)

```
Migration: Drop old column/table
Code: Use only new
Duration: Permanent
```

### Example: Renaming a Column

**Goal**: Rename `users.name` → `users.full_name`

```
❌ WRONG (causes downtime):
   ALTER TABLE users RENAME COLUMN name TO full_name;
   Deploy new code.
   # Old pods still running → crash
```

```
✅ CORRECT (zero downtime):

Week 1 - Expand:
   Migration: ADD full_name VARCHAR(100)
   Code: Write to both name AND full_name
   
Week 2 - Migrate:
   Migration: UPDATE users SET full_name = name WHERE full_name IS NULL
   Code: Read from full_name, write to both
   
Week 3 - Contract:
   Code: Use only full_name (deploy 100%)
   Migration: DROP COLUMN name
```

### Example: Changing Column Type

**Goal**: Change `products.price` from `INTEGER` (cents) to `DECIMAL(10,2)` (dollars)

```
Week 1:
   Migration: ADD price_decimal DECIMAL(10,2)
   Code: Write to both (convert cents → dollars)

Week 2:
   Migration: Backfill price_decimal = price / 100.0
   Code: Read from price_decimal

Week 3:
   Migration: DROP price, RENAME price_decimal → price
   Code: Clean up conversion logic
```

---

## Rollback Strategies

### The Rollback Myth

> "We'll just rollback if something goes wrong"

**Reality check:**
- Rollbacks often fail in production
- Data written after migration may be lost
- Rollback code may not be tested
- Some changes are irreversible

### Types of Rollbacks

#### 1. Schema Rollback (Alembic Downgrade)

```bash
alembic downgrade -1  # Go back one revision
```

**When it works:**
- Migration only added things
- No data was written to new columns
- Tested the downgrade path

**When it fails:**
- Data already exists in new columns
- Code already deployed that uses new schema
- Migration had data changes

#### 2. Application Rollback (Deploy Old Code)

Roll back the application, not the database.

```
✅ Works when:
   - Schema change is backward-compatible
   - Old code can work with new schema

❌ Fails when:
   - Column was removed
   - Column type changed incompatibly
```

#### 3. Forward Fix

Don't rollback - fix forward with a new migration.

```
Problem: Migration added broken constraint
Fix: New migration to remove/fix constraint

# Instead of:
alembic downgrade -1

# Do:
alembic revision -m "fix_broken_constraint"
alembic upgrade head
```

### Rollback Decision Tree

```
Migration failed in production?
│
├─ Did it partially complete?
│  ├─ Yes → DO NOT rollback (data inconsistency risk)
│  │        → Fix forward or restore from backup
│  └─ No  → Safe to retry or rollback
│
├─ Is the change reversible?
│  ├─ Added column    → Yes (can drop)
│  ├─ Dropped column  → No (data gone)
│  ├─ Changed type    → Maybe (data truncation?)
│  └─ Renamed         → Yes (can rename back)
│
└─ Is old code compatible?
   ├─ Yes → Rollback code first, then schema
   └─ No  → Fix forward, don't rollback
```

### Pre-Rollback Checklist

Before attempting any rollback:

1. **Snapshot current state** - Backup right now, not yesterday's backup
2. **Check downgrade function** - Is it implemented? Tested?
3. **Count affected rows** - Will rollback lose data?
4. **Check running queries** - Long-running transactions may block
5. **Coordinate with team** - Everyone aware?
6. **Have incident channel open** - Communication ready

---

## Common Production Mistakes

### Mistake 1: Locking the Entire Table

```sql
-- ❌ This locks the table for the entire duration
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
-- 10 million rows → locked for minutes

-- ✅ In PostgreSQL, adding nullable column is instant
ALTER TABLE users ADD COLUMN phone VARCHAR(20);  -- Actually fast!

-- ⚠️ But adding with DEFAULT locks in older PostgreSQL
ALTER TABLE users ADD COLUMN phone VARCHAR(20) DEFAULT '';  -- SLOW
```

**Fix**: PostgreSQL 11+ handles `DEFAULT` efficiently. For older versions:
```sql
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
-- Then backfill in batches
```

### Mistake 2: Adding NOT NULL Without Default

```sql
-- ❌ Fails if table has existing rows
ALTER TABLE products ADD COLUMN sku VARCHAR(50) NOT NULL;

-- ✅ Add nullable first, backfill, then add constraint
ALTER TABLE products ADD COLUMN sku VARCHAR(50);
UPDATE products SET sku = 'SKU-' || id WHERE sku IS NULL;
ALTER TABLE products ALTER COLUMN sku SET NOT NULL;
```

### Mistake 3: Blocking Index Creation

```sql
-- ❌ Locks table while building index
CREATE INDEX ix_orders_user_id ON orders(user_id);

-- ✅ Non-blocking (PostgreSQL)
CREATE INDEX CONCURRENTLY ix_orders_user_id ON orders(user_id);
```

**Note**: `CONCURRENTLY` takes longer but doesn't lock.

### Mistake 4: Forgetting Foreign Key Index

```sql
-- Creates foreign key but no index
ALTER TABLE orders ADD CONSTRAINT fk_user 
    FOREIGN KEY (user_id) REFERENCES users(id);

-- ❌ JOINs on user_id are now slow (no index)
-- ❌ DELETE FROM users is slow (must scan orders)
```

**Fix**: Always create index on FK columns:
```sql
CREATE INDEX ix_orders_user_id ON orders(user_id);
```

### Mistake 5: Large Data Migrations in One Transaction

```python
# ❌ Holds transaction open for hours, blocks everything
def upgrade():
    op.execute("UPDATE orders SET status = 'legacy' WHERE status IS NULL")
    # 50 million rows → 2 hour transaction → table locked
```

```python
# ✅ Batch in chunks
def upgrade():
    connection = op.get_bind()
    while True:
        result = connection.execute("""
            UPDATE orders SET status = 'legacy'
            WHERE id IN (
                SELECT id FROM orders 
                WHERE status IS NULL 
                LIMIT 10000
            )
        """)
        if result.rowcount == 0:
            break
        connection.commit()  # Release locks between batches
```

### Mistake 6: Ignoring Migration Time

```
Dev testing:   "Migration took 0.5 seconds"
Production:    Migration took 45 minutes, site down
```

**Fix**: 
- Always estimate: `EXPLAIN ANALYZE` your changes
- Test with production data volume
- Schedule long migrations during maintenance window

### Mistake 7: Dropping Columns Too Early

```
Monday:    Deploy code that doesn't use column
Tuesday:   Drop column in migration
Wednesday: Rollback code due to bug
           → OLD CODE CRASHES (column gone)
```

**Fix**: Wait at least 2 weeks before dropping columns. Old code must be completely gone from all environments.

### Mistake 8: Not Testing Downgrade

```python
def downgrade():
    pass  # "We never rollback anyway"
    
# Production: NEED TO ROLLBACK
# Reality: downgrade() does nothing, manual fix required
```

**Fix**: Always implement and test `downgrade()`:
```python
def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(20)))

def downgrade():
    op.drop_column('users', 'phone')
```

### Mistake 9: Running Migrations During Peak Traffic

```
12:00 PM - Lunch rush, 10,000 orders/minute
12:05 PM - Deploy with migration
12:06 PM - Table locked for index creation
12:07 PM - All orders timing out
12:08 PM - Incident declared
```

**Fix**:
- Schedule migrations during low-traffic windows
- Use `CONCURRENTLY` for indexes
- Consider maintenance mode for destructive changes

### Mistake 10: No Migration Dry Run

```bash
# ❌ Just run it and hope
alembic upgrade head

# ✅ Preview first
alembic upgrade head --sql > migration_preview.sql
# Review the SQL, then:
alembic upgrade head
```

---

## Quick Reference

### Command Cheatsheet

```bash
# Create new migration (auto-detect changes)
alembic revision --autogenerate -m "description"

# Create empty migration (manual)
alembic revision -m "description"

# Apply all pending migrations
alembic upgrade head

# Apply next migration only
alembic upgrade +1

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads

# Generate SQL without executing
alembic upgrade head --sql
```

### Migration Template

```python
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    # ### commands auto generated by Alembic ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic ###
    pass
    # ### end Alembic commands ###
```

### Pre-Deploy Checklist

- [ ] Migration tested locally
- [ ] Migration tested on staging with prod-like data
- [ ] Downgrade function implemented and tested
- [ ] Estimated execution time acceptable
- [ ] Backward compatible with current code
- [ ] Team notified of upcoming migration
- [ ] Deployment scheduled during low-traffic window
- [ ] Rollback plan documented
- [ ] Monitoring dashboards ready

### Production Incident Response

```
1. DON'T PANIC
2. Check if migration completed or failed mid-way
3. If failed mid-way → DO NOT retry yet
4. Assess data state manually
5. Decide: rollback vs fix-forward
6. Communicate status to team
7. Execute decision with pair review
8. Post-mortem after resolution
```

---

> **Remember**: The best migration is the one you never have to rollback. Design for safety, not speed.
