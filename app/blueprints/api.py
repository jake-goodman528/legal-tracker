"""
API Blueprint - REST API Endpoints

Contains all API endpoints for the STR Compliance Toolkit:
- Search endpoints (/api/search/*)
- Export endpoints (/api/export/*)
- Update interaction endpoints (/api/updates/*)
- Notification endpoints (/api/notifications/*)
"""

from flask import Blueprint, request, jsonify, make_response, session, g
from models import (
    db, Regulation, Update, SavedSearch, SearchSuggestion, 
    UserUpdateInteraction, UpdateReminder, NotificationPreference
)
from app.services import (
    SearchService, UpdateService, UserInteractionService, NotificationService
)
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func
import logging
import traceback
import json
import csv
import io
import time
from functools import wraps

# Get specialized loggers
logger = logging.getLogger('str_tracker.api')
performance_logger = logging.getLogger('str_tracker.performance')
security_logger = logging.getLogger('str_tracker.security')

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


def log_api_call(endpoint_name):
    """Decorator to log API calls with comprehensive context"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            request_id = getattr(g, 'request_id', 'unknown')
            
            # Log request start
            logger.info(
                f"API call started - Endpoint: {endpoint_name} | "
                f"Request ID: {request_id} | Method: {request.method} | "
                f"Remote: {request.remote_addr} | "
                f"Args: {request.args.to_dict()} | Query params: {dict(request.args)}"
            )
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                
                # Determine if this was a slow API call
                if duration > 2.0:
                    performance_logger.warning(
                        f"Slow API call - Endpoint: {endpoint_name} | "
                        f"Duration: {duration:.3f}s | Request ID: {request_id}"
                    )
                
                logger.info(
                    f"API call completed - Endpoint: {endpoint_name} | "
                    f"Duration: {duration:.3f}s | Success: True"
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"API call failed - Endpoint: {endpoint_name} | "
                    f"Duration: {duration:.3f}s | Error: {str(e)} | "
                    f"Request ID: {request_id}",
                    exc_info=True
                )
                
                # Return standardized error response
                return jsonify({
                    'success': False,
                    'error': f'API error in {endpoint_name}: {str(e)}',
                    'request_id': request_id
                }), 500
                
        return decorated_function
    return decorator


# Search Endpoints
@api_bp.route('/search/advanced')
@log_api_call('advanced_search')
def advanced_search():
    """Advanced search API endpoint with multiple criteria"""
    # Get search parameters
    search_params = {
        'query': request.args.get('q', '').strip(),
        'categories': request.args.getlist('categories[]'),
        'compliance_levels': request.args.getlist('compliance_levels[]'),
        'property_types': request.args.getlist('property_types[]'),
        'locations': request.args.getlist('locations[]'),
        'jurisdictions': request.args.getlist('jurisdictions[]'),
        'jurisdiction_levels': request.args.getlist('jurisdiction_levels[]'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to'),
        'date_range_days': request.args.get('date_range_days')
    }
    
    logger.info(f"Search parameters received: {search_params}")
    
    # Use SearchService to perform the search
    results = SearchService.advanced_search(search_params)
    
    logger.info(f"Search returned {len(results)} results")
    
    # Convert to dictionaries for JSON response
    regulations_data = [reg.to_dict() for reg in results]
    
    return jsonify({
        'success': True,
        'regulations': regulations_data,
        'count': len(regulations_data),
        'search_criteria': search_params
    })


@api_bp.route('/locations/<jurisdiction_level>')
@log_api_call('get_locations_by_jurisdiction')
def get_locations_by_jurisdiction(jurisdiction_level):
    """Get location options based on jurisdiction level"""
    try:
        from app.services.regulation_service import RegulationService
        
        locations = RegulationService.get_location_options_by_jurisdiction_level(jurisdiction_level)
        
        return jsonify({
            'success': True,
            'jurisdiction_level': jurisdiction_level,
            'locations': locations
        })
        
    except Exception as e:
        logger.error(f"Error getting locations for jurisdiction {jurisdiction_level}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/search/suggestions')
@log_api_call('search_suggestions')
def search_suggestions():
    """Get search suggestions based on user input"""
    query = request.args.get('q', '').strip()
    
    suggestions = SearchService.get_search_suggestions(query)
    
    return jsonify({'suggestions': suggestions})


@api_bp.route('/search/saved')
@log_api_call('get_saved_searches')
def get_saved_searches():
    """Get user's saved searches"""
    user_id = session.get('user_id', 'anonymous')
    logger.info(f"Getting saved searches for user: {user_id}")
    
    try:
        saved_searches = SearchService.get_saved_searches(user_id)
        
        searches_data = [{
            'id': search.id,
            'name': search.name,
            'criteria': search.search_criteria,
            'created_at': search.created_at.isoformat(),
            'last_used': search.last_used.isoformat() if search.last_used else None
        } for search in saved_searches]
        
        logger.info(f"Retrieved {len(searches_data)} saved searches for user {user_id}")
        
        return jsonify({
            'success': True,
            'saved_searches': searches_data
        })
        
    except Exception as e:
        logger.error(f"Get saved searches error for user {user_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve saved searches'
        }), 500


@api_bp.route('/search/save', methods=['POST'])
@log_api_call('save_search')
def save_search():
    """Save a search configuration"""
    user_id = session.get('user_id', 'anonymous')
    
    try:
        data = request.get_json()
        search_name = data.get('name', '')
        search_criteria = data.get('criteria', {})
        
        logger.info(f"Saving search for user {user_id} - Name: {search_name}")
        
        if not search_name or not search_criteria:
            return jsonify({
                'success': False,
                'error': 'Search name and criteria are required'
            }), 400
        
        success, saved_search, error = SearchService.save_search(user_id, search_name, search_criteria)
        
        if success:
            logger.info(f"Successfully saved search - ID: {saved_search.id} | User: {user_id}")
            return jsonify({
                'success': True,
                'saved_search': {
                    'id': saved_search.id,
                    'name': saved_search.name,
                    'created_at': saved_search.created_at.isoformat()
                }
            })
        else:
            logger.error(f"Failed to save search for user {user_id}: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 400
            
    except Exception as e:
        logger.error(f"Save search error for user {user_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to save search'
        }), 500


@api_bp.route('/search/saved/<int:search_id>/use', methods=['POST'])
@log_api_call('use_saved_search')
def use_saved_search(search_id):
    """Use a saved search and update last_used timestamp"""
    user_id = session.get('user_id', 'anonymous')
    
    logger.info(f"Using saved search - ID: {search_id} | User: {user_id}")
    
    try:
        success, search_criteria, error = SearchService.use_saved_search(user_id, search_id)
        
        if success:
            logger.info(f"Successfully loaded saved search - ID: {search_id}")
            return jsonify({
                'success': True,
                'search_criteria': search_criteria
            })
        else:
            logger.warning(f"Failed to use saved search - ID: {search_id} | Error: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 404
            
    except Exception as e:
        logger.error(f"Use saved search error - ID: {search_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to load saved search'
        }), 500


# Export Endpoints
@api_bp.route('/export/csv')
@log_api_call('csv_export')
def export_csv():
    """Export search results to CSV"""
    try:
        # Get search parameters (same as advanced search)
        search_params = {
            'query': request.args.get('q', '').strip(),
            'categories': request.args.getlist('categories[]'),
            'compliance_levels': request.args.getlist('compliance_levels[]'),
            'property_types': request.args.getlist('property_types[]'),
            'locations': request.args.getlist('locations[]'),
            'jurisdictions': request.args.getlist('jurisdictions[]'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to')
        }
        
        logger.info(f"CSV export requested with params: {search_params}")
        
        # Perform search
        results = SearchService.advanced_search(search_params)
        
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'ID', 'Title', 'Jurisdiction Level', 'Location', 'Category',
            'Compliance Level', 'Property Type', 'Key Requirements',
            'Effective Date', 'Last Updated', 'Keywords'
        ]
        writer.writerow(headers)
        
        # Write data rows
        for reg in results:
            writer.writerow([
                reg.id,
                reg.title,
                reg.jurisdiction_level,
                reg.location,
                reg.category,
                reg.compliance_level,
                reg.property_type,
                reg.key_requirements[:500] if reg.key_requirements else '',  # Truncate long text
                reg.effective_date.strftime('%Y-%m-%d') if reg.effective_date else '',
                reg.last_updated.strftime('%Y-%m-%d') if reg.last_updated else '',
                reg.keywords
            ])
        
        # Prepare response
        output_data = output.getvalue()
        output.close()
        
        logger.info(f"CSV export completed - {len(results)} regulations exported")
        
        response = make_response(output_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=regulations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"CSV export error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Export failed. Please try again.'
        }), 500


# Update Interaction Endpoints
@api_bp.route('/updates/<int:update_id>/bookmark', methods=['POST'])
@log_api_call('toggle_bookmark')
def toggle_bookmark(update_id):
    """Toggle bookmark status for an update"""
    user_id = session.get('user_id', 'anonymous')
    
    logger.info(f"Toggling bookmark - Update ID: {update_id} | User: {user_id}")
    
    try:
        success, is_bookmarked, error = UserInteractionService.toggle_bookmark(user_id, update_id)
        
        if success:
            action = "bookmarked" if is_bookmarked else "unbookmarked"
            logger.info(f"Successfully {action} update - ID: {update_id} | User: {user_id}")
            
            return jsonify({
                'success': True,
                'is_bookmarked': is_bookmarked,
                'message': f'Update {action} successfully'
            })
        else:
            logger.error(f"Failed to toggle bookmark - Update ID: {update_id} | Error: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 400
            
    except Exception as e:
        logger.error(f"Toggle bookmark error - Update ID: {update_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to update bookmark status'
        }), 500


@api_bp.route('/updates/<int:update_id>/reminder', methods=['POST'])
@log_api_call('set_reminder')
def set_reminder(update_id):
    """Set a reminder for an update"""
    user_id = session.get('user_id', 'anonymous')
    
    try:
        data = request.get_json()
        reminder_date = data.get('reminder_date')
        reminder_message = data.get('message', '')
        
        logger.info(f"Setting reminder - Update ID: {update_id} | User: {user_id} | Date: {reminder_date}")
        
        if not reminder_date:
            return jsonify({
                'success': False,
                'error': 'Reminder date is required'
            }), 400
        
        success, reminder, error = UserInteractionService.set_reminder(
            user_id, update_id, reminder_date, reminder_message
        )
        
        if success:
            logger.info(f"Successfully set reminder - ID: {reminder.id} | Update: {update_id}")
            return jsonify({
                'success': True,
                'reminder': {
                    'id': reminder.id,
                    'reminder_date': reminder.reminder_date.isoformat(),
                    'message': reminder.message
                }
            })
        else:
            logger.error(f"Failed to set reminder - Update ID: {update_id} | Error: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 400
            
    except Exception as e:
        logger.error(f"Set reminder error - Update ID: {update_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to set reminder'
        }), 500


# Update Search and Management
@api_bp.route('/updates/search')
@log_api_call('search_updates')
def search_updates():
    """Search updates with filters including all new fields"""
    try:
        search_params = {
            'query': request.args.get('q', ''),
            'status': request.args.getlist('status[]'),
            'categories': request.args.getlist('categories[]'),
            'jurisdictions': request.args.getlist('jurisdictions[]'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'impact_levels': request.args.getlist('impact_levels[]'),
            'action_required': request.args.get('action_required'),
            'priorities': request.args.getlist('priorities[]'),
            'decision_statuses': request.args.getlist('decision_statuses[]'),
            'change_types': request.args.getlist('change_types[]'),
            'affected_operators': request.args.getlist('affected_operators[]')
        }
        
        logger.info(f"Update search with params: {search_params}")
        
        results = UpdateService.search_updates(search_params)
        
        # Include all new fields in the response
        updates_data = []
        for update in results:
            update_data = {
                'id': update.id,
                'title': update.title,
                'description': update.description,
                'jurisdiction_affected': update.jurisdiction_affected,
                'update_date': update.update_date.strftime('%Y-%m-%d') if update.update_date else None,
                'status': update.status,
                'category': update.category,
                'impact_level': update.impact_level,
                'action_required': update.action_required,
                'priority': update.priority,
                'change_type': update.change_type,
                'decision_status': update.decision_status,
                'potential_impact': update.potential_impact,
                'affected_operators': update.affected_operators,
                'effective_date': update.effective_date.strftime('%Y-%m-%d') if update.effective_date else None,
                'deadline_date': update.deadline_date.strftime('%Y-%m-%d') if update.deadline_date else None,
                'compliance_deadline': update.compliance_deadline.strftime('%Y-%m-%d') if update.compliance_deadline else None,
                'expected_decision_date': update.expected_decision_date.strftime('%Y-%m-%d') if update.expected_decision_date else None,
                'tags': update.tags,
                'source_url': update.source_url,
                'related_regulation_ids': update.related_regulation_ids
            }
            updates_data.append(update_data)
        
        logger.info(f"Update search returned {len(updates_data)} results")
        
        return jsonify({
            'success': True,
            'updates': updates_data,
            'count': len(updates_data),
            'search_params': search_params
        })
        
    except Exception as e:
        logger.error(f"Update search error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Update search failed',
            'details': str(e)
        }), 500


@api_bp.route('/updates')
@log_api_call('get_updates')
def get_updates():
    """Get all updates with optional filtering"""
    try:
        # Get filter parameters
        filters = {
            'status': request.args.get('status'),
            'category': request.args.get('category'),
            'jurisdiction': request.args.get('jurisdiction'),
            'impact_level': request.args.get('impact_level'),
            'priority': request.args.get('priority'),
            'decision_status': request.args.get('decision_status'),
            'change_type': request.args.get('change_type'),
            'action_required': request.args.get('action_required'),
            'limit': request.args.get('limit', 50, type=int),
            'offset': request.args.get('offset', 0, type=int)
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        logger.info(f"Getting updates with filters: {filters}")
        
        # Build query
        query = Update.query
        
        # Apply filters
        if filters.get('status'):
            query = query.filter(Update.status == filters['status'])
        if filters.get('category'):
            query = query.filter(Update.category == filters['category'])
        if filters.get('jurisdiction'):
            query = query.filter(Update.jurisdiction_affected == filters['jurisdiction'])
        if filters.get('impact_level'):
            query = query.filter(Update.impact_level == filters['impact_level'])
        if filters.get('priority'):
            query = query.filter(Update.priority == filters['priority'])
        if filters.get('decision_status'):
            query = query.filter(Update.decision_status == filters['decision_status'])
        if filters.get('change_type'):
            query = query.filter(Update.change_type == filters['change_type'])
        if filters.get('action_required'):
            query = query.filter(Update.action_required == (filters['action_required'].lower() == 'true'))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        updates = query.order_by(Update.update_date.desc()).offset(filters['offset']).limit(filters['limit']).all()
        
        # Format response with all fields
        updates_data = []
        for update in updates:
            update_data = {
                'id': update.id,
                'title': update.title,
                'description': update.description,
                'jurisdiction_affected': update.jurisdiction_affected,
                'update_date': update.update_date.strftime('%Y-%m-%d') if update.update_date else None,
                'status': update.status,
                'category': update.category,
                'impact_level': update.impact_level,
                'action_required': update.action_required,
                'action_description': update.action_description,
                'priority': update.priority,
                'change_type': update.change_type,
                'decision_status': update.decision_status,
                'potential_impact': update.potential_impact,
                'affected_operators': update.affected_operators,
                'effective_date': update.effective_date.strftime('%Y-%m-%d') if update.effective_date else None,
                'deadline_date': update.deadline_date.strftime('%Y-%m-%d') if update.deadline_date else None,
                'compliance_deadline': update.compliance_deadline.strftime('%Y-%m-%d') if update.compliance_deadline else None,
                'expected_decision_date': update.expected_decision_date.strftime('%Y-%m-%d') if update.expected_decision_date else None,
                'property_types': update.property_types,
                'tags': update.tags,
                'source_url': update.source_url,
                'related_regulation_ids': update.related_regulation_ids
            }
            updates_data.append(update_data)
        
        logger.info(f"Retrieved {len(updates_data)} updates (total: {total_count})")
        
        return jsonify({
            'success': True,
            'updates': updates_data,
            'count': len(updates_data),
            'total_count': total_count,
            'filters': filters
        })
        
    except Exception as e:
        logger.error(f"Get updates error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve updates',
            'details': str(e)
        }), 500


@api_bp.route('/updates/<int:update_id>')
@log_api_call('get_update')
def get_update(update_id):
    """Get a single update by ID with all fields"""
    try:
        update = Update.query.get(update_id)
        if not update:
            logger.warning(f"Update not found - ID: {update_id}")
            return jsonify({
                'success': False,
                'error': 'Update not found'
            }), 404
        
        # Get related regulations
        related_regulations = update.get_related_regulations()
        
        update_data = {
            'id': update.id,
            'title': update.title,
            'description': update.description,
            'jurisdiction_affected': update.jurisdiction_affected,
            'update_date': update.update_date.strftime('%Y-%m-%d') if update.update_date else None,
            'status': update.status,
            'category': update.category,
            'impact_level': update.impact_level,
            'action_required': update.action_required,
            'action_description': update.action_description,
            'priority': update.priority,
            'change_type': update.change_type,
            'decision_status': update.decision_status,
            'potential_impact': update.potential_impact,
            'affected_operators': update.affected_operators,
            'effective_date': update.effective_date.strftime('%Y-%m-%d') if update.effective_date else None,
            'deadline_date': update.deadline_date.strftime('%Y-%m-%d') if update.deadline_date else None,
            'compliance_deadline': update.compliance_deadline.strftime('%Y-%m-%d') if update.compliance_deadline else None,
            'expected_decision_date': update.expected_decision_date.strftime('%Y-%m-%d') if update.expected_decision_date else None,
            'property_types': update.property_types,
            'tags': update.tags,
            'source_url': update.source_url,
            'related_regulation_ids': update.related_regulation_ids,
            'related_regulations': [
                {
                    'id': reg.id,
                    'title': reg.title,
                    'jurisdiction': reg.jurisdiction
                } for reg in related_regulations
            ]
        }
        
        logger.info(f"Retrieved update - ID: {update_id}")
        
        return jsonify({
            'success': True,
            'update': update_data
        })
        
    except Exception as e:
        logger.error(f"Get update error - ID: {update_id} | Error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve update',
            'details': str(e)
        }), 500


@api_bp.route('/updates/bookmarked')
@log_api_call('get_bookmarked_updates')
def get_bookmarked_updates():
    """Get user's bookmarked updates"""
    user_id = session.get('user_id', 'anonymous')
    
    logger.info(f"Getting bookmarked updates for user: {user_id}")
    
    try:
        bookmarked_updates = UserInteractionService.get_bookmarked_updates(user_id)
        
        updates_data = [{
            'id': update.id,
            'title': update.title,
            'description': update.description,
            'update_date': update.update_date.strftime('%Y-%m-%d'),
            'status': update.status,
            'jurisdiction_affected': update.jurisdiction_affected
        } for update in bookmarked_updates]
        
        logger.info(f"Retrieved {len(updates_data)} bookmarked updates for user {user_id}")
        
        return jsonify({
            'success': True,
            'bookmarked_updates': updates_data
        })
        
    except Exception as e:
        logger.error(f"Get bookmarked updates error for user {user_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve bookmarked updates'
        }), 500


# Notification Endpoints
@api_bp.route('/notifications/preferences', methods=['GET', 'POST'])
@log_api_call('notification_preferences')
def manage_notification_preferences():
    """Get or update notification preferences"""
    user_id = session.get('user_id', 'anonymous')
    
    if request.method == 'GET':
        logger.info(f"Getting notification preferences for user: {user_id}")
        
        try:
            preferences = NotificationService.get_notification_preferences(user_id)
            return jsonify({
                'success': True,
                'preferences': preferences
            })
            
        except Exception as e:
            logger.error(f"Get notification preferences error for user {user_id}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve notification preferences'
            }), 500
    
    else:  # POST
        try:
            data = request.get_json()
            logger.info(f"Updating notification preferences for user {user_id}: {data}")
            
            success, error = NotificationService.update_notification_preferences(user_id, data)
            
            if success:
                logger.info(f"Successfully updated notification preferences for user {user_id}")
                return jsonify({
                    'success': True,
                    'message': 'Notification preferences updated successfully'
                })
            else:
                logger.error(f"Failed to update notification preferences for user {user_id}: {error}")
                return jsonify({
                    'success': False,
                    'error': error
                }), 400
                
        except Exception as e:
            logger.error(f"Update notification preferences error for user {user_id}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to update notification preferences'
            }), 500


@api_bp.route('/notifications/alerts')
@log_api_call('get_notification_alerts')
def get_notification_alerts():
    """Get current notification alerts"""
    user_id = session.get('user_id', 'anonymous')
    
    logger.info(f"Getting notification alerts for user: {user_id}")
    
    try:
        alerts = NotificationService.get_notification_alerts(user_id)
        return jsonify({
            'success': True,
            'alerts': alerts
        })
        
    except Exception as e:
        logger.error(f"Get notification alerts error for user {user_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve alerts'
        }), 500


@api_bp.route('/notifications/weekly-digest')
@log_api_call('weekly_digest')
def generate_weekly_digest():
    """Generate weekly digest for user"""
    user_id = session.get('user_id', 'anonymous')
    
    logger.info(f"Generating weekly digest for user: {user_id}")
    
    try:
        digest = NotificationService.generate_weekly_digest(user_id)
        return jsonify({
            'success': True,
            'digest': digest
        })
        
    except Exception as e:
        logger.error(f"Weekly digest error for user {user_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to generate weekly digest'
        }), 500


# Client Error Tracking Endpoint
@api_bp.route('/client-errors', methods=['POST'])
def report_client_error():
    """Receive and log client-side errors"""
    start_time = time.time()
    request_id = getattr(g, 'request_id', 'unknown')
    
    # Log API call start
    logger.info(
        f"API call started - Endpoint: client_error_report | "
        f"Request ID: {request_id} | Method: {request.method} | "
        f"Remote: {request.remote_addr}"
    )
    
    try:
        # Try to get JSON data with better error handling
        try:
            data = request.get_json(force=True)
        except Exception as json_error:
            logger.error(f"Failed to parse JSON in client error report: {str(json_error)}")
            return jsonify({
                'success': False,
                'error': f'Invalid JSON data: {str(json_error)}'
            }), 400
        
        if not data:
            logger.warning("Received empty client error report")
            return jsonify({
                'success': False,
                'error': 'No data received'
            }), 400
            
        if 'error' not in data:
            logger.warning(f"Client error report missing 'error' field: {data}")
            return jsonify({
                'success': False,
                'error': 'Error data is required'
            }), 400
        
        error_data = data['error']
        level = data.get('level', 'error')
        session_id = data.get('session_id', 'unknown')
        page_info = data.get('page_info', {})
        
        # Create structured log entry
        client_error_log = {
            'type': 'client_error',
            'session_id': session_id,
            'error_type': error_data.get('type', 'unknown'),
            'message': error_data.get('message', 'No message'),
            'filename': error_data.get('filename'),
            'line': error_data.get('lineno'),
            'column': error_data.get('colno'),
            'stack': error_data.get('stack'),
            'user_agent': error_data.get('userAgent'),
            'url': page_info.get('url'),
            'referrer': page_info.get('referrer'),
            'viewport': page_info.get('viewport'),
            'screen': page_info.get('screen'),
            'timestamp': error_data.get('timestamp'),
            'remote_addr': request.remote_addr
        }
        
        # Log based on severity level
        if level == 'error':
            logger.error(f"Client Error Report: {client_error_log}")
        elif level == 'warning':
            logger.warning(f"Client Warning Report: {client_error_log}")
        else:
            logger.info(f"Client Info Report: {client_error_log}")
        
        # For API errors, log additional context
        if error_data.get('type') == 'api_error':
            api_logger = logging.getLogger('str_tracker.api.client_errors')
            api_logger.error(
                f"Client API Error - Endpoint: {error_data.get('endpoint')} | "
                f"Status: {error_data.get('status')} | "
                f"Message: {error_data.get('message')} | "
                f"Session: {session_id}"
            )
        
        duration = time.time() - start_time
        logger.info(
            f"API call completed - Endpoint: client_error_report | "
            f"Duration: {duration:.3f}s | Success: True"
        )
        
        return jsonify({
            'success': True,
            'message': 'Error report received'
        })
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"API call failed - Endpoint: client_error_report | "
            f"Duration: {duration:.3f}s | Error: {str(e)} | "
            f"Request ID: {request_id}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'Failed to process error report'
        }), 500 