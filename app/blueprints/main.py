"""
Main Blueprint - Public Routes

Contains all public-facing routes for the STR Compliance Toolkit:
- Home page
- Regulations listing and detail pages
- Updates listing and detail pages with filtering
"""

from flask import Blueprint, render_template, request, session, abort, flash, redirect, url_for
from models import db, Regulation, Update, UserUpdateInteraction
from app.services import RegulationService, UpdateService, UserInteractionService
from app.utils.admin_helpers import public_flash
import logging
from datetime import datetime

# Create main blueprint
main_bp = Blueprint('main', __name__)

# Get logger
logger = logging.getLogger('str_tracker.main')


@main_bp.route('/')
def index():
    """Home page route"""
    try:
        # Get recent updates for homepage
        recent_updates = Update.query.filter(
            db.or_(
                Update.change_type == 'Recent',
                Update.status == 'Recent'
            )
        ).order_by(Update.update_date.desc()).limit(3).all()
        
        # Get recent regulations
        recent_regulations = Regulation.query.order_by(Regulation.last_updated.desc()).limit(3).all()
        
        return render_template('index.html', 
                             recent_updates=recent_updates,
                             recent_regulations=recent_regulations)
    except Exception as e:
        logger.error(f"Error loading home page: {str(e)}", exc_info=True)
        # Still show the page but without dynamic content
        return render_template('index.html', 
                             recent_updates=[],
                             recent_regulations=[])


@main_bp.route('/regulations')
def regulations():
    """Regulations listing page"""
    try:
        # Get all regulations
        from models import Regulation
        regulations = Regulation.query.all()
        
        return render_template('regulations.html',
                             regulations=regulations)
                             
    except Exception as e:
        logger.error(f"Error loading regulations: {str(e)}", exc_info=True)
        public_flash('Error loading regulations. Please try again later.', 'error')
        return render_template('regulations.html',
                             regulations=[])


@main_bp.route('/regulations/<int:regulation_id>')
def regulation_detail(regulation_id):
    """Individual regulation detail page"""
    try:
        regulation = Regulation.query.get_or_404(regulation_id)
        
        # Get related updates for this regulation
        related_updates = Update.query.filter(
            db.or_(
                Update.related_regulation_ids.contains(str(regulation_id)),
                Update.jurisdiction_affected == regulation.location
            )
        ).order_by(Update.update_date.desc()).limit(5).all()
        
        return render_template('regulation_detail.html',
                             regulation=regulation,
                             related_updates=related_updates)
    except Exception as e:
        # Only catch non-HTTP exceptions to avoid interfering with abort()
        if hasattr(e, 'code') and e.code in [404, 403, 500]:
            # Re-raise HTTP exceptions to let error handlers handle them
            raise
        logger.error(f"Error loading regulation detail - ID: {regulation_id} | Error: {str(e)}", exc_info=True)
        public_flash('Error loading regulation details.', 'error')
        return redirect(url_for('main.regulations'))


@main_bp.route('/updates')
def updates():
    """Updates listing page with categorized sections"""
    try:
        # Get categorized updates without filtering
        recent_upcoming_updates = UpdateService.get_recent_upcoming_updates({})
        proposed_updates = UpdateService.get_proposed_updates({})
        
        # Get user interactions for all updates
        user_session = UserInteractionService.get_user_session()
        all_update_ids = [u.id for u in recent_upcoming_updates + proposed_updates]
        update_interactions = UserInteractionService.get_user_interactions(all_update_ids, user_session)
        
        # Get statistics for each section
        recent_upcoming_count = len(recent_upcoming_updates)
        proposed_count = len(proposed_updates)
        total_count = recent_upcoming_count + proposed_count
        
        return render_template('updates.html', 
                             recent_upcoming_updates=recent_upcoming_updates,
                             proposed_updates=proposed_updates,
                             recent_upcoming_count=recent_upcoming_count,
                             proposed_count=proposed_count,
                             total_count=total_count,
                             update_interactions=update_interactions)
    except Exception as e:
        logger.error(f"Error loading updates: {str(e)}", exc_info=True)
        public_flash('Error loading updates. Please try again later.', 'error')
        return render_template('updates.html',
                             recent_upcoming_updates=[],
                             proposed_updates=[],
                             recent_upcoming_count=0,
                             proposed_count=0,
                             total_count=0,
                             update_interactions={})


@main_bp.route('/updates/category/<category>')
def updates_by_category(category):
    """Updates filtered by category"""
    try:
        # Validate category
        valid_categories = UpdateService.get_filter_options()['categories']
        if category not in valid_categories:
            logger.warning(f"Invalid category requested: {category}")
            abort(404)
        
        # Redirect to main updates page with category filter
        return redirect(url_for('main.updates', category=category))
    except Exception as e:
        # Only catch non-HTTP exceptions to avoid interfering with abort()
        if hasattr(e, 'code') and e.code in [404, 403, 500]:
            # Re-raise HTTP exceptions to let error handlers handle them
            raise
        logger.error(f"Error in updates_by_category - Category: {category} | Error: {str(e)}", exc_info=True)
        public_flash('Error loading category updates.', 'error')
        return redirect(url_for('main.updates'))


@main_bp.route('/updates/status/<status>')
def updates_by_status(status):
    """Updates filtered by status"""
    try:
        # Validate status
        valid_statuses = ['Recent', 'Upcoming', 'Proposed']
        if status not in valid_statuses:
            logger.warning(f"Invalid status requested: {status}")
            abort(404)
        
        # Redirect to main updates page with status filter
        return redirect(url_for('main.updates', change_type=status))
    except Exception as e:
        # Only catch non-HTTP exceptions to avoid interfering with abort()
        if hasattr(e, 'code') and e.code in [404, 403, 500]:
            # Re-raise HTTP exceptions to let error handlers handle them
            raise
        logger.error(f"Error in updates_by_status - Status: {status} | Error: {str(e)}", exc_info=True)
        public_flash('Error loading status updates.', 'error')
        return redirect(url_for('main.updates'))


@main_bp.route('/updates/<int:update_id>')
def update_detail(update_id):
    """Individual update detail page with comprehensive error handling"""
    try:
        # Get update using UpdateService
        update = UpdateService.get_update_by_id(update_id)
        if not update:
            logger.warning(f"Update not found - ID: {update_id}")
            abort(404)
        
        # Get related regulations
        related_regulations = update.get_related_regulations()
        
        # Get similar updates (same jurisdiction and category)
        similar_updates = Update.query.filter(
            db.and_(
                Update.id != update_id,
                Update.jurisdiction_affected == update.jurisdiction_affected,
                Update.category == update.category
            )
        ).order_by(Update.update_date.desc()).limit(3).all()
        
        # Mark as read for user interaction tracking
        user_session = UserInteractionService.get_user_session()
        UserInteractionService.mark_update_read(update_id, user_session)
        
        # Get user interaction data
        user_interactions = UserInteractionService.get_user_interactions([update_id], user_session)
        
        return render_template('update_detail.html',
                             update=update,
                             related_regulations=related_regulations,
                             similar_updates=similar_updates,
                             user_interactions=user_interactions)
    except Exception as e:
        # Only catch non-HTTP exceptions to avoid interfering with abort()
        if hasattr(e, 'code') and e.code in [404, 403, 500]:
            # Re-raise HTTP exceptions to let error handlers handle them
            raise
        logger.error(f"Error loading update detail - ID: {update_id} | Error: {str(e)}", exc_info=True)
        public_flash('Error loading update details.', 'error')
        return redirect(url_for('main.updates'))





# Error handlers
@main_bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    logger.warning(f"404 error - Path: {request.path} | Referrer: {request.referrer}")
    return render_template('errors/404.html'), 404


@main_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error - Path: {request.path} | Error: {str(error)}", exc_info=True)
    db.session.rollback()
    return render_template('errors/500.html'), 500


@main_bp.errorhandler(Exception)
def handle_exception(error):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error - Path: {request.path} | Error: {str(error)}", exc_info=True)
    db.session.rollback()
    
    # Return appropriate error page based on error type
    if hasattr(error, 'code'):
        if error.code == 404:
            return render_template('errors/404.html'), 404
        elif error.code == 403:
            return render_template('errors/403.html'), 403
    
    return render_template('errors/500.html'), 500 