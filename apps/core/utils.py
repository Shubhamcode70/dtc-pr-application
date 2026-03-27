"""
Utility functions for the application
"""

import hashlib
import os
from datetime import datetime
from django.utils.text import slugify


def generate_file_hash(file_obj):
    """Generate SHA256 hash of a file"""
    hasher = hashlib.sha256()
    for chunk in file_obj.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()


def generate_unique_filename(original_filename):
    """Generate a unique filename using timestamp and hash"""
    name, ext = os.path.splitext(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{slugify(name)}-{timestamp}{ext}"


def get_file_storage_path(pr_id):
    """
    Get the storage path for PR attachments
    Structure: pr_attachments/YYYY/MM/PR_ID/
    """
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    return f"pr_attachments/{year}/{month}/PR_{pr_id}"


def format_currency(amount):
    """Format amount as Indian Rupees"""
    if amount is None:
        return "₹0"
    return f"₹{amount:,.2f}"


def calculate_grand_total(items):
    """Calculate grand total from PR items"""
    return sum(item.total_value for item in items if item.total_value)
