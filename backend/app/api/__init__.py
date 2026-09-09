"""
API routers for the Legal Metrology Inspection application.

Routers:
- health: Health check endpoint
- scans: Scan management and field extraction
- violations: Violation detection and listing
- fields: Extracted field retrieval
- reports: Compliance report generation
"""

from . import fields, health, reports, scans, violations

__all__ = ["health", "scans", "violations", "fields", "reports"]
