"""
Main Blueprint - Public Routes

Contains all public-facing routes for the STR Compliance Toolkit:
- Home page
- Regulations listing and detail pages
- Updates listing
- Notifications page
"""

from flask import Blueprint, render_template, request, session
from models import db, Regulation, Update, SavedSearch, UserUpdateInteraction
from app.services import RegulationService, UpdateService, UserInteractionService

# Create main blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page route"""
    return render_template('index.html')


@main_bp.route('/regulations')
def regulations():
    """Regulations listing page with filtering"""
    # Get filter parameters
    filters = {
        'jurisdiction': request.args.get('jurisdiction', '').strip(),
        'location': request.args.get('location', '').strip(),
        'category': request.args.get('category', '').strip(),
        'search': request.args.get('search', '').strip()
    }
    
    # Use RegulationService to get filtered regulations
    regulations = RegulationService.get_filtered_regulations(filters)
    
    # Get filter options using RegulationService
    filter_options = RegulationService.get_filter_options()
    
    # Get saved searches for quick filters
    saved_searches = RegulationService.get_public_saved_searches()
    
    return render_template('regulations.html',
                         regulations=regulations,
                         all_jurisdictions=filter_options['jurisdictions'],
                         all_locations=filter_options['locations'], 
                         all_categories=filter_options['categories'],
                         current_jurisdiction=filters['jurisdiction'],
                         current_location=filters['location'],
                         current_category=filters['category'],
                         current_search=filters['search'],
                         saved_searches=saved_searches)


@main_bp.route('/regulations/<int:id>')
def regulation_detail(id):
    """Individual regulation detail page"""
    # Get regulation using RegulationService
    regulation = RegulationService.get_regulation_by_id(id)
    if not regulation:
        return "Regulation not found", 404
    
    # Get related regulations
    related_regulations = RegulationService.get_related_regulations(regulation)
    
    # Get detailed content sections
    content_sections = RegulationService.get_regulation_detailed_content(regulation)
    
    return render_template('regulation_detail.html',
                         regulation=regulation,
                         related_regulations=related_regulations,
                         content_sections=content_sections)


@main_bp.route('/updates')
def updates():
    """Updates listing page with filtering"""
    # Get filter parameters
    filters = {
        'status': request.args.get('status', ''),
        'jurisdiction': request.args.get('jurisdiction', ''),
        'category': request.args.get('category', ''),
        'impact': request.args.get('impact', ''),
        'search': request.args.get('search', '')
    }
    
    # Use UpdateService to get filtered updates
    updates = UpdateService.get_filtered_updates(filters)
    
    # Get filter options
    filter_options = UpdateService.get_filter_options()
    
    # Get user interactions for these updates
    user_session = UserInteractionService.get_user_session()
    update_ids = [u.id for u in updates]
    update_interactions = UserInteractionService.get_user_interactions(update_ids, user_session)
    
    return render_template('updates.html', 
                         updates=updates,
                         statuses=filter_options['statuses'],
                         jurisdictions=filter_options['jurisdictions'],
                         categories=filter_options['categories'],
                         impact_levels=filter_options['impact_levels'],
                         current_status=filters['status'],
                         current_jurisdiction=filters['jurisdiction'],
                         current_category=filters['category'],
                         current_impact=filters['impact'],
                         current_search=filters['search'],
                         update_interactions=update_interactions)


@main_bp.route('/notifications')
def notifications():
    """Notifications page"""
    return render_template('notifications.html') 