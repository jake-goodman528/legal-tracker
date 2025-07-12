"""
Admin Helper Functions

Utility functions for admin panel functionality including scoped flash messages
to prevent admin messages from appearing on the public site.
"""

from flask import flash as flask_flash, session


def admin_flash(message, category='info'):
    """
    Flash a message that will only be displayed in the admin panel.
    
    Args:
        message (str): The message to display
        category (str): The category of the message (success, error, warning, info)
    """
    # Only flash messages if user is logged in as admin
    if session.get('admin_id'):
        # Prefix the category to scope it to admin
        admin_category = f'admin_{category}'
        flask_flash(message, admin_category)


def public_flash(message, category='info'):
    """
    Flash a message that will only be displayed on the public site.
    
    Args:
        message (str): The message to display
        category (str): The category of the message (success, error, warning, info)
    """
    # Prefix the category to scope it to public
    public_category = f'public_{category}'
    flask_flash(message, public_category)


def get_admin_messages():
    """
    Get flash messages that are scoped to admin only.
    
    Returns:
        list: List of tuples (category, message) for admin messages
    """
    from flask import get_flashed_messages
    
    # Get all messages with categories
    all_messages = get_flashed_messages(with_categories=True)
    
    # Filter for admin messages and strip the prefix
    admin_messages = []
    for category, message in all_messages:
        if category.startswith('admin_'):
            # Strip the 'admin_' prefix
            clean_category = category[6:]
            admin_messages.append((clean_category, message))
    
    return admin_messages


def get_public_messages():
    """
    Get flash messages that are scoped to public only.
    
    Returns:
        list: List of tuples (category, message) for public messages
    """
    from flask import get_flashed_messages
    
    # Get all messages with categories
    all_messages = get_flashed_messages(with_categories=True)
    
    # Filter for public messages and strip the prefix
    public_messages = []
    for category, message in all_messages:
        if category.startswith('public_'):
            # Strip the 'public_' prefix
            clean_category = category[7:]
            public_messages.append((clean_category, message))
    
    return public_messages 