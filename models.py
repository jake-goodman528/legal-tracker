"""
Database Models

Defines all SQLAlchemy models for the STR Compliance Toolkit including:
- Regulation: Core regulation and compliance data
- Update: Regulatory updates and announcements  
- UserUpdateInteraction: User interaction tracking (bookmarks, read status)
- UpdateReminder: User-set reminders for deadlines
- NotificationPreference: User notification settings
- AdminUser: Administrative user accounts
- SavedSearch: Saved search configurations
- SearchSuggestion: Search suggestion tracking
"""

from typing import Dict, List, Optional, Any
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import json

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Regulation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jurisdiction_level = db.Column(db.String(50), nullable=False)  # National, State, Local
    location = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    key_requirements = db.Column(db.Text, nullable=False)
    last_updated = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Legal')  # Legal, Licensing, Taxes, Zoning, Occupancy, Registration, Discrimination
    compliance_level = db.Column(db.String(20), nullable=False, default='Mandatory')  # Mandatory, Recommended, Optional
    property_type = db.Column(db.String(50), nullable=False, default='Both')  # Residential, Commercial, Both
    effective_date = db.Column(db.Date, nullable=True)  # When regulation becomes effective
    expiry_date = db.Column(db.Date, nullable=True)  # When regulation expires (if applicable)
    keywords = db.Column(db.Text, nullable=True)  # Comma-separated keywords for better search
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<Regulation {self.title}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert regulation object to dictionary for JSON serialization.
        
        Returns:
            Dictionary containing all regulation fields with proper type conversion.
        """
        return {
            'id': self.id,
            'jurisdiction_level': self.jurisdiction_level,
            'location': self.location,
            'title': self.title,
            'key_requirements': self.key_requirements,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'category': self.category,
            'compliance_level': self.compliance_level,
            'property_type': self.property_type,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'keywords': self.keywords
        }

class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    jurisdiction_affected = db.Column(db.String(100), nullable=False)
    update_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Recent, Upcoming, Proposed
    
    # Enhanced fields
    category = db.Column(db.String(50), nullable=False, default='Regulatory Changes')  # Regulatory Changes, Tax Updates, Licensing Changes, Court Decisions, Industry News
    impact_level = db.Column(db.String(10), nullable=False, default='Medium')  # High, Medium, Low
    effective_date = db.Column(db.Date, nullable=True)  # When the change becomes effective
    deadline_date = db.Column(db.Date, nullable=True)  # Deadline for compliance/action
    action_required = db.Column(db.Boolean, default=False)  # Whether action is required
    action_description = db.Column(db.Text, nullable=True)  # Description of required action
    property_types = db.Column(db.String(100), nullable=False, default='Both')  # Residential, Commercial, Both
    related_regulation_ids = db.Column(db.Text, nullable=True)  # Comma-separated IDs of related regulations
    tags = db.Column(db.Text, nullable=True)  # Comma-separated tags for better categorization
    source_url = db.Column(db.String(500), nullable=True)  # Official source URL
    priority = db.Column(db.Integer, default=3)  # 1=High, 2=Medium, 3=Low (for sorting)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Update {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'jurisdiction_affected': self.jurisdiction_affected,
            'update_date': self.update_date.isoformat() if self.update_date else None,
            'status': self.status,
            'category': self.category,
            'impact_level': self.impact_level,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'deadline_date': self.deadline_date.isoformat() if self.deadline_date else None,
            'action_required': self.action_required,
            'action_description': self.action_description,
            'property_types': self.property_types,
            'related_regulation_ids': self.related_regulation_ids,
            'tags': self.tags,
            'source_url': self.source_url,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_related_regulations(self):
        """Get related regulation objects"""
        if not self.related_regulation_ids:
            return []
        try:
            regulation_ids = [int(rid.strip()) for rid in self.related_regulation_ids.split(',') if rid.strip()]
            return Regulation.query.filter(Regulation.id.in_(regulation_ids)).all()
        except (ValueError, AttributeError):
            return []
    
    def get_tags_list(self):
        """Get tags as a list"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

class UserUpdateInteraction(db.Model):
    """Track user interactions with updates"""
    id = db.Column(db.Integer, primary_key=True)
    update_id = db.Column(db.Integer, db.ForeignKey('update.id'), nullable=False)
    user_session = db.Column(db.String(255), nullable=False)  # Session ID or user identifier
    is_read = db.Column(db.Boolean, default=False)
    is_bookmarked = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    bookmarked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    update = db.relationship('Update', backref='user_interactions')
    
    __table_args__ = (db.UniqueConstraint('update_id', 'user_session', name='unique_user_update'),)

    def __repr__(self):
        return f'<UserUpdateInteraction update_id={self.update_id} user={self.user_session}>'

class UpdateReminder(db.Model):
    """Store reminders for updates with deadlines"""
    id = db.Column(db.Integer, primary_key=True)
    update_id = db.Column(db.Integer, db.ForeignKey('update.id'), nullable=False)
    user_session = db.Column(db.String(255), nullable=False)
    reminder_date = db.Column(db.Date, nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False)  # 'deadline', 'effective_date', 'custom'
    is_sent = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(255), nullable=True)  # Optional email for notifications
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    update = db.relationship('Update', backref='reminders')

    def __repr__(self):
        return f'<UpdateReminder update_id={self.update_id} date={self.reminder_date}>'

class NotificationPreference(db.Model):
    """User notification preferences"""
    id = db.Column(db.Integer, primary_key=True)
    user_session = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=True)
    locations = db.Column(db.Text, nullable=True)  # Comma-separated list of locations to watch
    categories = db.Column(db.Text, nullable=True)  # Comma-separated list of categories to watch
    impact_levels = db.Column(db.Text, nullable=True)  # Comma-separated list of impact levels to watch
    notify_new_updates = db.Column(db.Boolean, default=True)
    notify_deadlines = db.Column(db.Boolean, default=True)
    notify_weekly_digest = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<NotificationPreference user={self.user_session}>'

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f'<AdminUser {self.username}>'

class SavedSearch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    search_criteria = db.Column(db.Text, nullable=False)  # JSON string of search parameters
    is_public = db.Column(db.Boolean, default=False)  # Whether this search is available to all users
    use_count = db.Column(db.Integer, default=0)  # How many times this search has been used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SavedSearch {self.name}>'
    
    def get_search_criteria(self):
        """Parse the JSON search criteria"""
        try:
            return json.loads(self.search_criteria)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_search_criteria(self, criteria_dict):
        """Set search criteria from dictionary"""
        self.search_criteria = json.dumps(criteria_dict)

class SearchSuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    suggestion_text = db.Column(db.String(200), nullable=False, unique=True)
    suggestion_type = db.Column(db.String(50), nullable=False)  # title, location, category, keyword
    frequency = db.Column(db.Integer, default=1)  # How often this suggestion appears
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SearchSuggestion {self.suggestion_text}>'
