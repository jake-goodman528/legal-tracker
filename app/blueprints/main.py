"""
Main Blueprint - Public Routes

Contains all public-facing routes for the STR Compliance Toolkit:
- Home page
- Regulations listing and detail pages
- Updates listing and detail pages with filtering
- Notifications page
"""

from flask import Blueprint, render_template, request, session, abort, flash, redirect, url_for
from models import db, Regulation, Update, SavedSearch, UserUpdateInteraction
from app.services import RegulationService, UpdateService, UserInteractionService
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
    """Regulations listing page with filtering"""
    try:
        logger.info("DEBUG: Starting regulations route")
        
        # Get sample regulations directly from database
        from models import Regulation
        regulations = Regulation.query.all()
        logger.info(f"DEBUG: Found {len(regulations)} regulations in database")
        
        # Hardcode everything to eliminate variables
        return render_template('regulations.html',
                             regulations=regulations,
                             all_jurisdictions=['State', 'Local'],
                             all_locations=['California', 'San Francisco'], 
                             all_categories=[],
                             current_jurisdiction='',
                             current_location='',
                             current_category='',
                             current_search='',
                             saved_searches=[])
                             
    except Exception as e:
        logger.error(f"Error loading regulations: {str(e)}", exc_info=True)
        flash('Error loading regulations. Please try again later.', 'error')
        return render_template('regulations.html',
                             regulations=[],
                             all_jurisdictions=[],
                             all_locations=[], 
                             all_categories=[],
                             current_jurisdiction='',
                             current_location='',
                             current_category='',
                             current_search='',
                             saved_searches=[])


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
        flash('Error loading regulation details.', 'error')
        return redirect(url_for('main.regulations'))


@main_bp.route('/updates')
def updates():
    """Updates listing page with categorized sections and comprehensive filtering"""
    try:
        # Get filter parameters with enhanced filtering
        filters = {
            'status': request.args.get('status', ''),
            'jurisdiction': request.args.get('jurisdiction', ''),
            'category': request.args.get('category', ''),
            'impact': request.args.get('impact', ''),
            'priority': request.args.get('priority', ''),
            'decision_status': request.args.get('decision_status', ''),
            'search': request.args.get('search', ''),
            'date_from': request.args.get('date_from', ''),
            'date_to': request.args.get('date_to', ''),
            'section': request.args.get('section', ''),  # Filter by section
            'action_required': request.args.get('action_required', ''),
            'change_type': request.args.get('change_type', '')
        }
        
        # Get categorized updates
        recent_upcoming_updates = UpdateService.get_recent_upcoming_updates(filters)
        proposed_updates = UpdateService.get_proposed_updates(filters)
        
        # If filtering by section, only show that section
        if filters['section'] == 'recent':
            proposed_updates = []
        elif filters['section'] == 'proposed':
            recent_upcoming_updates = []
        
        # Get filter options
        filter_options = UpdateService.get_filter_options()
        
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
                             statuses=filter_options['statuses'],
                             jurisdictions=filter_options['jurisdictions'],
                             categories=filter_options['categories'],
                             impact_levels=filter_options['impact_levels'],
                             decision_statuses=filter_options.get('decision_statuses', []),
                             priorities=filter_options.get('priorities', []),
                             current_status=filters['status'],
                             current_jurisdiction=filters['jurisdiction'],
                             current_category=filters['category'],
                             current_impact=filters['impact'],
                             current_priority=filters['priority'],
                             current_decision_status=filters['decision_status'],
                             current_search=filters['search'],
                             current_date_from=filters['date_from'],
                             current_date_to=filters['date_to'],
                             current_section=filters['section'],
                             current_action_required=filters['action_required'],
                             current_change_type=filters['change_type'],
                             update_interactions=update_interactions)
    except Exception as e:
        logger.error(f"Error loading updates: {str(e)}", exc_info=True)
        flash('Error loading updates. Please try again later.', 'error')
        return render_template('updates.html',
                             recent_upcoming_updates=[],
                             proposed_updates=[],
                             recent_upcoming_count=0,
                             proposed_count=0,
                             total_count=0,
                             statuses=[],
                             jurisdictions=[],
                             categories=[],
                             impact_levels=[],
                             decision_statuses=[],
                             priorities=[],
                             current_status='',
                             current_jurisdiction='',
                             current_category='',
                             current_impact='',
                             current_priority='',
                             current_decision_status='',
                             current_search='',
                             current_date_from='',
                             current_date_to='',
                             current_section='',
                             current_action_required='',
                             current_change_type='',
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
        flash('Error loading category updates.', 'error')
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
        flash('Error loading status updates.', 'error')
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
        flash('Error loading update details.', 'error')
        return redirect(url_for('main.updates'))


@main_bp.route('/notifications')
def notifications():
    """Notifications page"""
    try:
        # Get user session for notifications
        user_session = UserInteractionService.get_user_session()
        
        # Get user's bookmarked updates
        bookmarked_updates = UserInteractionService.get_bookmarked_updates(user_session)
        
        # Get recent updates with action required
        action_required_updates = Update.query.filter(
            Update.action_required == True
        ).order_by(Update.update_date.desc()).limit(10).all()
        
        # Get upcoming deadlines
        from datetime import datetime, timedelta
        thirty_days_from_now = datetime.now().date() + timedelta(days=30)
        
        upcoming_deadlines = Update.query.filter(
            db.or_(
                db.and_(Update.deadline_date.isnot(None), Update.deadline_date <= thirty_days_from_now),
                db.and_(Update.compliance_deadline.isnot(None), Update.compliance_deadline <= thirty_days_from_now),
                db.and_(Update.expected_decision_date.isnot(None), Update.expected_decision_date <= thirty_days_from_now)
            )
        ).order_by(Update.deadline_date.asc()).all()
        
        return render_template('notifications.html',
                             bookmarked_updates=bookmarked_updates,
                             action_required_updates=action_required_updates,
                             upcoming_deadlines=upcoming_deadlines)
    except Exception as e:
        logger.error(f"Error loading notifications: {str(e)}", exc_info=True)
        flash('Error loading notifications.', 'error')
        return render_template('notifications.html',
                             bookmarked_updates=[],
                             action_required_updates=[],
                             upcoming_deadlines=[])


@main_bp.route('/test-regulations')
def test_regulations():
    """Test route to debug regulations issue"""
    try:
        from models import Regulation
        regulations = Regulation.query.all()
        
        result = {
            'count': len(regulations),
            'regulations': [{'id': r.id, 'title': r.title, 'location': r.location} for r in regulations]
        }
        
        return f"<h1>Test Results</h1><pre>{result}</pre>"
        
    except Exception as e:
        return f"<h1>Error</h1><pre>{str(e)}</pre>"


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