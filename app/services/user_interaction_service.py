"""
User Interaction Service

Handles all user interaction business logic:
- Update bookmarking
- User session handling
- User interaction tracking
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from flask import session, request
from models import db, UserUpdateInteraction, Update
import logging


class UserInteractionService:
    """Service class for handling user interactions"""
    
    @staticmethod
    def get_user_session():
        """
        Get or create a user session identifier
        
        Returns:
            str: User session identifier
        """
        return session.get('user_id', request.remote_addr)
    
    @staticmethod
    def mark_update_read(update_id, user_session=None):
        """
        Mark an update as read by the user
        
        Args:
            update_id (int): ID of the update to mark as read
            user_session (str, optional): User session identifier
            
        Returns:
            tuple: (success: bool, error: str or None)
        """
        try:
            if user_session is None:
                user_session = UserInteractionService.get_user_session()
            
            # Get or create user interaction
            interaction = UserUpdateInteraction.query.filter_by(
                update_id=update_id,
                user_session=user_session
            ).first()
            
            if not interaction:
                interaction = UserUpdateInteraction(
                    update_id=update_id,
                    user_session=user_session
                )
                db.session.add(interaction)
            
            interaction.is_read = True
            interaction.read_at = datetime.utcnow()
            interaction.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            logging.error(f"Error marking update as read: {str(e)}")
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def toggle_bookmark(update_id, is_bookmarked, user_session=None):
        """
        Toggle bookmark status for an update
        
        Args:
            update_id (int): ID of the update to bookmark/unbookmark
            is_bookmarked (bool): Whether to bookmark or unbookmark
            user_session (str, optional): User session identifier
            
        Returns:
            tuple: (success: bool, is_bookmarked: bool, error: str or None)
        """
        try:
            if user_session is None:
                user_session = UserInteractionService.get_user_session()
            
            # Get or create user interaction
            interaction = UserUpdateInteraction.query.filter_by(
                update_id=update_id,
                user_session=user_session
            ).first()
            
            if not interaction:
                interaction = UserUpdateInteraction(
                    update_id=update_id,
                    user_session=user_session
                )
                db.session.add(interaction)
            
            interaction.is_bookmarked = is_bookmarked
            if is_bookmarked:
                interaction.bookmarked_at = datetime.utcnow()
            else:
                interaction.bookmarked_at = None
            interaction.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return True, is_bookmarked, None
            
        except Exception as e:
            logging.error(f"Error updating bookmark: {str(e)}")
            db.session.rollback()
            return False, False, str(e)
    

    
    @staticmethod
    def get_user_interactions(update_ids, user_session=None):
        """
        Get user interactions for a list of updates
        
        Args:
            update_ids (list): List of update IDs
            user_session (str, optional): User session identifier
            
        Returns:
            dict: Dictionary mapping update_id to UserUpdateInteraction
        """
        try:
            if user_session is None:
                user_session = UserInteractionService.get_user_session()
            
            if not update_ids:
                return {}
            
            interactions = UserUpdateInteraction.query.filter(
                UserUpdateInteraction.update_id.in_(update_ids),
                UserUpdateInteraction.user_session == user_session
            ).all()
            
            return {interaction.update_id: interaction for interaction in interactions}
            
        except Exception as e:
            logging.error(f"Error getting user interactions: {str(e)}")
            return {}
    
    @staticmethod
    def get_bookmarked_updates(user_session=None):
        """
        Get user's bookmarked updates
        
        Args:
            user_session (str, optional): User session identifier
            
        Returns:
            list: List of Update objects that are bookmarked
        """
        try:
            if user_session is None:
                user_session = UserInteractionService.get_user_session()
            
            bookmarked_interactions = UserUpdateInteraction.query.filter_by(
                user_session=user_session,
                is_bookmarked=True
            ).all()
            
            update_ids = [interaction.update_id for interaction in bookmarked_interactions]
            updates = Update.query.filter(Update.id.in_(update_ids)).order_by(Update.priority.asc()).all()
            
            return updates
            
        except Exception as e:
            logging.error(f"Error getting bookmarked updates: {str(e)}")
            return []
    

    
    @staticmethod
    def generate_share_content(update_id, share_type='link'):
        """
        Generate shareable content for an update
        
        Args:
            update_id (int): ID of the update to share
            share_type (str): Type of sharing ('link', 'email', 'export')
            
        Returns:
            tuple: (success: bool, content: dict, error: str or None)
        """
        try:
            update = Update.query.get_or_404(update_id)
            
            if share_type == 'link':
                from flask import url_for
                share_url = url_for('main.updates', _external=True) + f'#update-{update_id}'
                
                return True, {
                    'share_url': share_url,
                    'message': 'Share link generated'
                }, None
            
            elif share_type == 'email':
                subject = f"STR Compliance Update: {update.title}"
                body = f"""
                {update.title}
                
                Jurisdiction: {update.jurisdiction_affected}
                Status: {update.status}
                Impact Level: {update.impact_level}
                
                {update.description}
                
                {'Action Required: ' + update.action_description if update.action_required and update.action_description else ''}
                
                View full details at: {url_for('main.updates', _external=True)}
                """
                
                return True, {
                    'email_subject': subject,
                    'email_body': body,
                    'message': 'Email content generated'
                }, None
            
            elif share_type == 'export':
                export_data = {
                    'title': update.title,
                    'description': update.description,
                    'jurisdiction': update.jurisdiction_affected,
                    'status': update.status,
                    'category': update.category,
                    'impact_level': update.impact_level,
                    'update_date': update.update_date.isoformat() if update.update_date else None,
                    'effective_date': update.effective_date.isoformat() if update.effective_date else None,
                    'deadline_date': update.deadline_date.isoformat() if update.deadline_date else None,
                    'action_required': update.action_required,
                    'action_description': update.action_description,
                    'source_url': update.source_url,
                    'tags': update.get_tags_list() if hasattr(update, 'get_tags_list') else []
                }
                
                return True, {
                    'export_data': export_data,
                    'message': 'Export data generated'
                }, None
            
            else:
                return False, {}, 'Invalid share type'
                
        except Exception as e:
            logging.error(f"Error generating share content: {str(e)}")
            return False, {}, str(e) 