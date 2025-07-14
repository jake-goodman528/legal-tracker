"""
API Blueprint - REST API Endpoints

Contains all API endpoints for the STR Compliance Toolkit:
- Location endpoints (/api/locations/*)
- Export endpoints (/api/export/*)
- Update interaction endpoints (/api/updates/*)
"""

from flask import Blueprint, request, jsonify, make_response, session, g
from models import (
    db, Regulation, Update, SavedSearch, SearchSuggestion, 
    UserUpdateInteraction
)
from app.services import (
    RegulationService, UpdateService, UserInteractionService
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


# Removed search and filter endpoints - functionality no longer needed

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


# CSV Export Endpoint
@api_bp.route('/export/csv')
@log_api_call('csv_export')
def export_csv():
    """Export regulations to CSV format"""
    try:
        # Get all regulations
        from models import Regulation
        regulations = Regulation.query.all()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'ID', 'Title', 'Jurisdiction Level', 'Location', 'Category',
            'Compliance Level', 'Property Type', 'Last Updated', 'Overview'
        ])
        
        # Write regulation data
        for regulation in regulations:
            writer.writerow([
                regulation.id,
                regulation.title,
                regulation.jurisdiction_level,
                regulation.location,
                getattr(regulation, 'category', 'General'),
                getattr(regulation, 'compliance_level', 'N/A'),
                getattr(regulation, 'property_type', 'N/A'),
                regulation.last_updated.strftime('%Y-%m-%d') if regulation.last_updated else 'N/A',
                regulation.overview[:100] + '...' if len(regulation.overview) > 100 else regulation.overview
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=regulations.csv'
        
        logger.info(f"CSV export completed - {len(regulations)} regulations exported")
        return response
        
    except Exception as e:
        logger.error(f"CSV export error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Export failed'
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





# Update Search and Management
@api_bp.route('/updates')
@log_api_call('get_updates')
def get_updates():
    """Get all updates"""
    try:
        # Get pagination parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        logger.info(f"Getting updates with limit: {limit}, offset: {offset}")
        
        # Get all updates
        query = Update.query
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        updates = query.order_by(Update.update_date.desc()).offset(offset).limit(limit).all()
        
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
            'total_count': total_count
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