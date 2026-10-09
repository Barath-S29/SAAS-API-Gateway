"""
Import every model here so that Base.metadata contains all tables.

This matters specifically for Alembic: alembic/env.py imports
`app.models` (this package) before running autogenerate, and
autogenerate only sees tables whose model classes have actually been
imported somewhere — importing the package itself without this file
listing each module would silently leave tables out of the diff.
"""

from app.models.api_key import ApiKey
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.tenant import Tenant
from app.models.usage_log import UsageLog

__all__ = ["ApiKey", "Invoice", "Plan", "Tenant", "UsageLog"]