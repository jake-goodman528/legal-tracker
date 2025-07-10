"""
API Blueprint - REST API Endpoints

Contains all API endpoints for the STR Compliance Toolkit:
- Search endpoints (/api/search/*)
- Export endpoints (/api/export/*)
- Update interaction endpoints (/api/updates/*)
- Notification endpoints (/api/notifications/*)
"""

from flask import Blueprint, request, jsonify, make_response, session
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
import json
import csv
import io

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


# Search Endpoints
@api_bp.route('/search/advanced')
def advanced_search():
    """Advanced search API endpoint with multiple criteria"""
    try:
        # Get search parameters
        search_params = {
            'query': request.args.get('q', '').strip(),
            'categories': request.args.getlist('categories[]'),
            'compliance_levels': request.args.getlist('compliance_levels[]'),
            'property_types': request.args.getlist('property_types[]'),
            'locations': request.args.getlist('locations[]'),
            'jurisdictions': request.args.getlist('jurisdictions[]'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'date_range_days': request.args.get('date_range_days')
        }
        
        # Use SearchService to perform the search
        results = SearchService.advanced_search(search_params)
        
        # Convert to dictionaries for JSON response
        regulations_data = [reg.to_dict() for reg in results]
        
        return jsonify({
            'success': True,
            'results': regulations_data,
            'count': len(regulations_data),
            'search_criteria': search_params
        })
        
    except Exception as e:
        logging.error(f"Advanced search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Search failed. Please try again.'
        }), 500


@api_bp.route('/search/suggestions')
def search_suggestions():
    """Get search suggestions based on user input"""
    query = request.args.get('q', '').strip()
    
    suggestions = SearchService.get_search_suggestions(query)
    
    return jsonify({'suggestions': suggestions})


@api_bp.route('/search/saved')
def get_saved_searches():
    """Get public saved searches"""
    try:
        searches = SearchService.get_saved_searches()
        
        return jsonify({
            'success': True,
            'saved_searches': searches
        })
        
    except Exception as e:
        logging.error(f"Get saved searches error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get saved searches'
        }), 500


@api_bp.route('/search/save', methods=['POST'])
def save_search():
    """Save a search for later use"""
    try:
        data = request.get_json()
        
        success, message, search_id = SearchService.save_search(
            name=data['name'],
            description=data.get('description', ''),
            criteria=data['criteria'],
            is_public=data.get('is_public', False)
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'search_id': search_id
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
    except Exception as e:
        logging.error(f"Save search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to save search'
        }), 500


@api_bp.route('/search/saved/<int:search_id>/use', methods=['POST'])
def use_saved_search(search_id):
    """Use a saved search and update its usage count"""
    try:
        success, criteria, error = SearchService.use_saved_search(search_id)
        
        if success:
            return jsonify({
                'success': True,
                'criteria': criteria
            })
        else:
            return jsonify({
                'success': False,
                'error': error
            }), 500
        
    except Exception as e:
        logging.error(f"Use saved search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load saved search'
        }), 500


# Export Endpoints
@api_bp.route('/export/csv')
def export_csv():
    """Export search results to CSV"""
    try:
        # Get the same search parameters as advanced search
        search_params = {
            'query': request.args.get('q', '').strip(),
            'categories': request.args.getlist('categories[]'),
            'compliance_levels': request.args.getlist('compliance_levels[]'),
            'property_types': request.args.getlist('property_types[]'),
            'locations': request.args.getlist('locations[]'),
            'jurisdictions': request.args.getlist('jurisdictions[]'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'date_range_days': request.args.get('date_range_days')
        }
        
        # Get results using SearchService
        results = SearchService.advanced_search(search_params)
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Title', 'Location', 'Jurisdiction Level', 'Category', 
            'Compliance Level', 'Property Type', 'Key Requirements',
            'Effective Date', 'Expiry Date', 'Last Updated', 'Keywords'
        ])
        
        # Write data rows
        for regulation in results:
            writer.writerow([
                regulation.title,
                regulation.location,
                regulation.jurisdiction_level,
                regulation.category,
                regulation.compliance_level,
                regulation.property_type,
                regulation.key_requirements,
                regulation.effective_date.strftime('%Y-%m-%d') if regulation.effective_date else '',
                regulation.expiry_date.strftime('%Y-%m-%d') if regulation.expiry_date else '',
                regulation.last_updated.strftime('%Y-%m-%d') if regulation.last_updated else '',
                regulation.keywords or ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=str_regulations_{datetime.now().strftime("%Y%m%d")}.csv'
        response.headers['Content-Type'] = 'text/csv'
        
        return response
        
    except Exception as e:
        logging.error(f"CSV export error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Export failed'
        }), 500


# Update Interaction Endpoints
@api_bp.route('/updates/<int:update_id>/bookmark', methods=['POST'])
def bookmark_update(update_id):
    """Toggle bookmark status for an update"""
    try:
        data = request.get_json()
        is_bookmarked = data.get('is_bookmarked', False)
        
        success, result_bookmarked, error = UserInteractionService.toggle_bookmark(
            update_id, is_bookmarked
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Bookmark updated successfully',
                'is_bookmarked': result_bookmarked
            })
        else:
            return jsonify({
                'success': False,
                'error': error
            }), 500
        
    except Exception as e:
        logging.error(f"Error updating bookmark: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update bookmark'
        }), 500


@api_bp.route('/updates/<int:update_id>/reminder', methods=['POST'])
def set_update_reminder(update_id):
    """Set a reminder for an update"""
    try:
        data = request.get_json()
        reminder_date = datetime.strptime(data['reminder_date'], '%Y-%m-%d').date()
        
        success, reminder, error = UserInteractionService.set_reminder(
            update_id=update_id,
            reminder_date=reminder_date,
            reminder_type=data.get('reminder_type', 'custom'),
            email=data.get('email', ''),
            notes=data.get('notes', '')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Reminder set successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
    except Exception as e:
        logging.error(f"Error setting reminder: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to set reminder'
        }), 500


@api_bp.route('/updates/search')
def search_updates():
    """Advanced search within updates"""
    try:
        search_params = {
            'query_text': request.args.get('q', ''),
            'category': request.args.get('category', ''),
            'impact': request.args.get('impact', ''),
            'status': request.args.get('status', ''),
            'jurisdiction': request.args.get('jurisdiction', ''),
            'has_deadline': request.args.get('has_deadline', ''),
            'action_required': request.args.get('action_required', '')
        }
        
        updates = UpdateService.search_updates(search_params)
        
        results = []
        for update in updates:
            update_dict = update.to_dict()
            results.append(update_dict)
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logging.error(f"Error searching updates: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Search failed'
        }), 500


@api_bp.route('/updates/bookmarked')
def get_bookmarked_updates():
    """Get user's bookmarked updates"""
    try:
        updates = UserInteractionService.get_bookmarked_updates()
        results = [update.to_dict() for update in updates]
        
        return jsonify({
            'success': True,
            'bookmarked_updates': results,
            'count': len(results)
        })
        
    except Exception as e:
        logging.error(f"Error getting bookmarked updates: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get bookmarked updates'
        }), 500


# Notification Endpoints
@api_bp.route('/notifications/preferences', methods=['GET', 'POST'])
def notification_preferences():
    """Get or update notification preferences"""
    try:
        if request.method == 'GET':
            preferences = NotificationService.get_notification_preferences()
            
            return jsonify({
                'success': True,
                'preferences': preferences
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            
            success, error = NotificationService.update_notification_preferences(data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Notification preferences updated'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': error
                }), 500
            
    except Exception as e:
        logging.error(f"Error managing notification preferences: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to manage notification preferences'
        }), 500


@api_bp.route('/notifications/alerts')
def get_notification_alerts():
    """Get notifications for urgent updates and deadlines"""
    try:
        alerts = NotificationService.get_notification_alerts()
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts)
        })
        
    except Exception as e:
        logging.error(f"Error getting notification alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get alerts'
        }), 500


@api_bp.route('/notifications/weekly-digest')
def generate_weekly_digest():
    """Generate weekly digest of updates"""
    try:
        digest = NotificationService.generate_weekly_digest()
        
        return jsonify({
            'success': True,
            'digest': digest
        })
        
    except Exception as e:
        logging.error(f"Error generating weekly digest: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate digest'
        }), 500 