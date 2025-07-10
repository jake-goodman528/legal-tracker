"""
Notification Service

Handles all notification-related business logic:
- Notification preferences management
- Alert generation for urgent updates
- Weekly digest generation
- Deadline notifications
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from flask import session, request
from models import db, NotificationPreference, Update
import logging


class NotificationService:
    """Service class for handling notification operations"""
    
    @staticmethod
    def get_user_session():
        """
        Get or create a user session identifier
        
        Returns:
            str: User session identifier
        """
        return session.get('user_id', request.remote_addr)
    
    @staticmethod
    def get_notification_preferences(user_session=None):
        """
        Get notification preferences for a user
        
        Args:
            user_session (str, optional): User session identifier
            
        Returns:
            dict: Notification preferences dictionary
        """
        try:
            if user_session is None:
                user_session = NotificationService.get_user_session()
            
            prefs = NotificationPreference.query.filter_by(user_session=user_session).first()
            
            if not prefs:
                # Create default preferences
                prefs = NotificationPreference(
                    user_session=user_session,
                    notify_new_updates=True,
                    notify_deadlines=True,
                    notify_weekly_digest=False
                )
                db.session.add(prefs)
                db.session.commit()
            
            return {
                'email': prefs.email,
                'locations': prefs.locations.split(',') if prefs.locations else [],
                'categories': prefs.categories.split(',') if prefs.categories else [],
                'impact_levels': prefs.impact_levels.split(',') if prefs.impact_levels else [],
                'notify_new_updates': prefs.notify_new_updates,
                'notify_deadlines': prefs.notify_deadlines,
                'notify_weekly_digest': prefs.notify_weekly_digest
            }
            
        except Exception as e:
            logging.error(f"Error getting notification preferences: {str(e)}")
            return {
                'email': '',
                'locations': [],
                'categories': [],
                'impact_levels': [],
                'notify_new_updates': True,
                'notify_deadlines': True,
                'notify_weekly_digest': False
            }
    
    @staticmethod
    def update_notification_preferences(preferences_data, user_session=None):
        """
        Update notification preferences for a user
        
        Args:
            preferences_data (dict): Dictionary containing preferences data
            user_session (str, optional): User session identifier
            
        Returns:
            tuple: (success: bool, error: str or None)
        """
        try:
            if user_session is None:
                user_session = NotificationService.get_user_session()
            
            prefs = NotificationPreference.query.filter_by(user_session=user_session).first()
            if not prefs:
                prefs = NotificationPreference(user_session=user_session)
                db.session.add(prefs)
            
            # Update preferences
            prefs.email = preferences_data.get('email', '')
            prefs.locations = ','.join(preferences_data.get('locations', []))
            prefs.categories = ','.join(preferences_data.get('categories', []))
            prefs.impact_levels = ','.join(preferences_data.get('impact_levels', []))
            prefs.notify_new_updates = preferences_data.get('notify_new_updates', True)
            prefs.notify_deadlines = preferences_data.get('notify_deadlines', True)
            prefs.notify_weekly_digest = preferences_data.get('notify_weekly_digest', False)
            prefs.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            logging.error(f"Error updating notification preferences: {str(e)}")
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def get_notification_alerts(user_session=None):
        """
        Get notification alerts for urgent updates and deadlines
        
        Args:
            user_session (str, optional): User session identifier
            
        Returns:
            list: List of alert dictionaries
        """
        try:
            if user_session is None:
                user_session = NotificationService.get_user_session()
            
            # Get user preferences
            prefs = NotificationPreference.query.filter_by(user_session=user_session).first()
            
            alerts = []
            
            # Check for upcoming deadlines (within next 7 days)
            upcoming_deadline_date = datetime.now().date() + timedelta(days=7)
            deadline_updates = Update.query.filter(
                Update.deadline_date.isnot(None),
                Update.deadline_date <= upcoming_deadline_date,
                Update.deadline_date >= datetime.now().date()
            ).all()
            
            for update in deadline_updates:
                # Check if user should be notified about this update
                should_notify = True
                
                if prefs:
                    # Filter by user's location preferences
                    if prefs.locations:
                        user_locations = [loc.strip().lower() for loc in prefs.locations.split(',')]
                        if not any(loc in update.jurisdiction_affected.lower() for loc in user_locations):
                            should_notify = False
                    
                    # Filter by user's category preferences  
                    if prefs.categories and should_notify:
                        user_categories = [cat.strip() for cat in prefs.categories.split(',')]
                        if update.category not in user_categories:
                            should_notify = False
                    
                    # Filter by user's impact level preferences
                    if prefs.impact_levels and should_notify:
                        user_impacts = [imp.strip() for imp in prefs.impact_levels.split(',')]
                        if update.impact_level not in user_impacts:
                            should_notify = False
                
                if should_notify:
                    days_until_deadline = (update.deadline_date - datetime.now().date()).days
                    urgency = 'high' if days_until_deadline <= 3 else 'medium'
                    
                    alerts.append({
                        'id': update.id,
                        'title': update.title,
                        'type': 'deadline',
                        'urgency': urgency,
                        'deadline_date': update.deadline_date.isoformat(),
                        'days_until_deadline': days_until_deadline,
                        'jurisdiction': update.jurisdiction_affected,
                        'impact_level': update.impact_level,
                        'category': update.category,
                        'action_required': update.action_required,
                        'message': f"Deadline approaching in {days_until_deadline} day{'s' if days_until_deadline != 1 else ''}"
                    })
            
            # Check for high-priority new updates (last 3 days)
            three_days_ago = datetime.now().date() - timedelta(days=3)
            new_updates = Update.query.filter(
                Update.update_date >= three_days_ago,
                Update.priority == 1  # High priority
            ).all()
            
            for update in new_updates:
                # Apply same filtering logic
                should_notify = True
                
                if prefs:
                    if prefs.locations:
                        user_locations = [loc.strip().lower() for loc in prefs.locations.split(',')]
                        if not any(loc in update.jurisdiction_affected.lower() for loc in user_locations):
                            should_notify = False
                    
                    if prefs.categories and should_notify:
                        user_categories = [cat.strip() for cat in prefs.categories.split(',')]
                        if update.category not in user_categories:
                            should_notify = False
                    
                    if prefs.impact_levels and should_notify:
                        user_impacts = [imp.strip() for imp in prefs.impact_levels.split(',')]
                        if update.impact_level not in user_impacts:
                            should_notify = False
                
                if should_notify:
                    alerts.append({
                        'id': update.id,
                        'title': update.title,
                        'type': 'new_update',
                        'urgency': 'high',
                        'update_date': update.update_date.isoformat(),
                        'jurisdiction': update.jurisdiction_affected,
                        'impact_level': update.impact_level,
                        'category': update.category,
                        'status': update.status,
                        'message': f"New high-priority {update.status.lower()} update"
                    })
            
            # Sort alerts by urgency and date
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            alerts.sort(key=lambda x: (priority_order.get(x['urgency'], 2), x.get('deadline_date', x.get('update_date'))))
            
            return alerts
            
        except Exception as e:
            logging.error(f"Error getting notification alerts: {str(e)}")
            return []
    
    @staticmethod
    def generate_weekly_digest():
        """
        Generate weekly digest of updates
        
        Returns:
            dict: Weekly digest data
        """
        try:
            # Get updates from the past week
            week_ago = datetime.now().date() - timedelta(days=7)
            weekly_updates = Update.query.filter(
                Update.update_date >= week_ago
            ).order_by(Update.priority.asc(), Update.update_date.desc()).all()
            
            # Group updates by category
            digest = {
                'week_start': week_ago.isoformat(),
                'week_end': datetime.now().date().isoformat(),
                'total_updates': len(weekly_updates),
                'by_category': {},
                'high_priority': [],
                'upcoming_deadlines': [],
                'summary': ''
            }
            
            for update in weekly_updates:
                category = update.category
                if category not in digest['by_category']:
                    digest['by_category'][category] = []
                
                digest['by_category'][category].append({
                    'id': update.id,
                    'title': update.title,
                    'jurisdiction': update.jurisdiction_affected,
                    'impact_level': update.impact_level,
                    'status': update.status,
                    'action_required': update.action_required
                })
                
                # Track high priority items
                if update.priority == 1:
                    digest['high_priority'].append(update.title)
            
            # Get upcoming deadlines for next 2 weeks
            two_weeks_ahead = datetime.now().date() + timedelta(days=14)
            upcoming_deadlines = Update.query.filter(
                Update.deadline_date.isnot(None),
                Update.deadline_date >= datetime.now().date(),
                Update.deadline_date <= two_weeks_ahead
            ).order_by(Update.deadline_date.asc()).all()
            
            for deadline_update in upcoming_deadlines:
                days_until = (deadline_update.deadline_date - datetime.now().date()).days
                digest['upcoming_deadlines'].append({
                    'id': deadline_update.id,
                    'title': deadline_update.title,
                    'deadline_date': deadline_update.deadline_date.isoformat(),
                    'days_until': days_until,
                    'jurisdiction': deadline_update.jurisdiction_affected,
                    'action_required': deadline_update.action_required
                })
            
            # Generate summary
            summary_parts = []
            if digest['total_updates'] > 0:
                summary_parts.append(f"{digest['total_updates']} new updates this week")
            if len(digest['high_priority']) > 0:
                summary_parts.append(f"{len(digest['high_priority'])} high-priority items")
            if len(digest['upcoming_deadlines']) > 0:
                summary_parts.append(f"{len(digest['upcoming_deadlines'])} upcoming deadlines")
            
            digest['summary'] = '; '.join(summary_parts) if summary_parts else 'No significant updates this week'
            
            return digest
            
        except Exception as e:
            logging.error(f"Error generating weekly digest: {str(e)}")
            return {
                'week_start': (datetime.now().date() - timedelta(days=7)).isoformat(),
                'week_end': datetime.now().date().isoformat(),
                'total_updates': 0,
                'by_category': {},
                'high_priority': [],
                'upcoming_deadlines': [],
                'summary': 'Error generating digest'
            }
    
    @staticmethod
    def get_digest_subscribers():
        """
        Get list of users who have opted in for weekly digest
        
        Returns:
            list: List of NotificationPreference objects with digest enabled
        """
        try:
            return NotificationPreference.query.filter_by(
                notify_weekly_digest=True
            ).filter(
                NotificationPreference.email.isnot(None),
                NotificationPreference.email != ''
            ).all()
            
        except Exception as e:
            logging.error(f"Error getting digest subscribers: {str(e)}")
            return [] 