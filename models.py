"""
Database Models

Defines all SQLAlchemy models for the STR Compliance Toolkit including:
- Regulation: Core regulation and compliance data
- Update: Regulatory updates and announcements  
- UserUpdateInteraction: User interaction tracking (bookmarks, read status)
- AdminUser: Administrative user accounts

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
    __tablename__ = 'regulations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Core Information - Required fields
    jurisdiction = db.Column(db.String(100), nullable=False, index=True)  # Often queried
    jurisdiction_level = db.Column(db.String(20), nullable=False, default='Local', index=True)  # Often filtered
    location = db.Column(db.String(100), nullable=False, index=True)  # Often queried
    title = db.Column(db.String(200), nullable=False, index=True)  # Often searched
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # Often sorted
    
    # Rich Text Content Fields - Support formatting (bold, indent, numbering, bullet points, etc.)
    overview = db.Column(db.Text, nullable=True)  # Overview - formatted content
    detailed_requirements = db.Column(db.Text, nullable=True)  # Detailed Requirements - formatted content
    compliance_steps = db.Column(db.Text, nullable=True)  # Compliance Steps - formatted content
    required_forms = db.Column(db.Text, nullable=True)  # Required Forms - formatted content
    penalties_non_compliance = db.Column(db.Text, nullable=True)  # Penalties for Non Compliance - formatted content
    recent_changes = db.Column(db.Text, nullable=True)  # Recent Changes - formatted content
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
            'jurisdiction': self.jurisdiction,
            'jurisdiction_level': self.jurisdiction_level,
            'location': self.location,
            'title': self.title,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'overview': self.overview,
            'detailed_requirements': self.detailed_requirements,
            'compliance_steps': self.compliance_steps,
            'required_forms': self.required_forms,
            'penalties_non_compliance': self.penalties_non_compliance,
            'recent_changes': self.recent_changes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)  # Often searched
    description = db.Column(db.Text, nullable=False)
    jurisdiction_affected = db.Column(db.String(100), nullable=False, index=True)  # Often filtered
    jurisdiction_level = db.Column(db.String(20), nullable=False, default='Local', index=True)  # Often filtered
    update_date = db.Column(db.Date, nullable=False, index=True)  # Often sorted
    status = db.Column(db.String(20), nullable=False, index=True)  # Often filtered - Recent, Upcoming, Proposed
    
    # Enhanced fields
    category = db.Column(db.String(50), nullable=False, default='Regulatory Changes', index=True)  # Often filtered
    impact_level = db.Column(db.String(10), nullable=False, default='Medium', index=True)  # Often filtered
    effective_date = db.Column(db.Date, nullable=True, index=True)  # Often sorted
    deadline_date = db.Column(db.Date, nullable=True, index=True)  # Often sorted
    action_required = db.Column(db.Boolean, default=False)  # Whether action is required
    action_description = db.Column(db.Text, nullable=True)  # Description of required action
    property_types = db.Column(db.String(100), nullable=False, default='Both')  # Residential, Commercial, Both
    related_regulation_ids = db.Column(db.Text, nullable=True)  # Comma-separated IDs of related regulations
    tags = db.Column(db.Text, nullable=True)  # Comma-separated tags for better categorization
    source_url = db.Column(db.String(500), nullable=True)  # Official source URL
    priority = db.Column(db.Integer, default=3, index=True)  # Often sorted - 1=High, 2=Medium, 3=Low
    
    # New fields for expanded functionality
    expected_decision_date = db.Column(db.Date, nullable=True, index=True)  # Often sorted
    potential_impact = db.Column(db.Text, nullable=True)  # Impact assessment for proposed changes
    decision_status = db.Column(db.String(20), nullable=True, index=True)  # Often filtered
    change_type = db.Column(db.String(20), nullable=False, default='Recent', index=True)  # Often filtered
    compliance_deadline = db.Column(db.Date, nullable=True, index=True)  # Often sorted
    affected_operators = db.Column(db.Text, nullable=True)  # Description of which operators are affected
    
    # New template fields for structured public-facing display
    summary = db.Column(db.Text, nullable=True)  # Brief summary for the Summary section
    full_text = db.Column(db.Text, nullable=True)  # Full detailed text of the update
    compliance_requirements = db.Column(db.Text, nullable=True)  # Specific compliance requirements
    implementation_timeline = db.Column(db.Text, nullable=True)  # Timeline for implementation
    official_sources = db.Column(db.Text, nullable=True)  # Official sources and references
    expert_analysis = db.Column(db.Text, nullable=True)  # Kaystreet Management's interpretation
    kaystreet_commitment = db.Column(db.Text, nullable=True)  # Kaystreet Management's commitment statement
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Update {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'jurisdiction_affected': self.jurisdiction_affected,
            'jurisdiction_level': self.jurisdiction_level,
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
            'expected_decision_date': self.expected_decision_date.isoformat() if self.expected_decision_date else None,
            'potential_impact': self.potential_impact,
            'decision_status': self.decision_status,
            'change_type': self.change_type,
            'compliance_deadline': self.compliance_deadline.isoformat() if self.compliance_deadline else None,
            'affected_operators': self.affected_operators,
            'summary': self.summary,
            'full_text': self.full_text,
            'compliance_requirements': self.compliance_requirements,
            'implementation_timeline': self.implementation_timeline,
            'official_sources': self.official_sources,
            'expert_analysis': self.expert_analysis,
            'kaystreet_commitment': self.kaystreet_commitment,
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
    update_id = db.Column(db.Integer, db.ForeignKey('update.id'), nullable=False, index=True)  # Often queried
    user_session = db.Column(db.String(255), nullable=False, index=True)  # Often queried
    is_read = db.Column(db.Boolean, default=False, index=True)  # Often filtered
    is_bookmarked = db.Column(db.Boolean, default=False, index=True)  # Often filtered
    read_at = db.Column(db.DateTime, nullable=True)
    bookmarked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    update = db.relationship('Update', backref='user_interactions')
    
    __table_args__ = (
        db.UniqueConstraint('update_id', 'user_session', name='unique_user_update'),
        db.Index('idx_user_bookmarks', 'user_session', 'is_bookmarked'),  # Composite index for bookmark queries
        db.Index('idx_user_read_status', 'user_session', 'is_read'),  # Composite index for read status queries
    )

    def __repr__(self):
        return f'<UserUpdateInteraction update_id={self.update_id} user={self.user_session}>'



class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)  # Often queried for login
    password_hash = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f'<AdminUser {self.username}>'



def get_location_options_by_jurisdiction(jurisdiction_level):
    """
    Get location options based on jurisdiction level.
    
    Args:
        jurisdiction_level (str): 'National', 'State', or 'Local'
        
    Returns:
        list: List of location options appropriate for the jurisdiction level
    """
    if jurisdiction_level == 'National':
        return [
            'USA',
            'Canada',
            'Mexico',
            'United Kingdom',
            'Australia',
            'European Union'
        ]
    elif jurisdiction_level == 'State':
        return [
            'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
            'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
            'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
            'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
            'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
            'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
            'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
            'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
            'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
            'West Virginia', 'Wisconsin', 'Wyoming'
        ]
    elif jurisdiction_level == 'Local':
        return [
            'Tampa', 'St. Petersburg', 'Clearwater', 'Sarasota', 'Orlando',
            'Miami', 'Fort Lauderdale', 'Jacksonville', 'Tallahassee',
            'Gainesville', 'Naples', 'Key West', 'Pensacola', 'Daytona Beach',
            'New York City', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
            'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose',
            'Austin', 'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco',
            'Indianapolis', 'Seattle', 'Denver', 'Washington DC', 'Boston',
            'Nashville', 'Baltimore', 'Louisville', 'Portland', 'Oklahoma City',
            'Milwaukee', 'Las Vegas', 'Albuquerque', 'Tucson', 'Fresno',
            'Sacramento', 'Kansas City', 'Mesa', 'Virginia Beach', 'Atlanta',
            'Colorado Springs', 'Raleigh', 'Omaha', 'Miami Beach', 'Long Beach',
            'Minneapolis', 'Tulsa', 'Cleveland', 'Wichita', 'Arlington'
        ]
    else:
        return []

def get_jurisdiction_level_from_location(location):
    """
    Determine jurisdiction level based on location name.
    
    Args:
        location (str): The location name
        
    Returns:
        str: 'National', 'State', or 'Local'
    """
    national_locations = ['USA', 'Canada', 'Mexico', 'United Kingdom', 'Australia', 'European Union']
    state_locations = [
        'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
        'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
        'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
        'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
        'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
        'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
        'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
        'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
        'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
        'West Virginia', 'Wisconsin', 'Wyoming'
    ]
    
    if location in national_locations:
        return 'National'
    elif location in state_locations:
        return 'State'
    else:
        return 'Local'
