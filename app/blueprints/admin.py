"""
Admin Blueprint - Administrative Interface

Contains all administrative routes for the STR Compliance Toolkit:
- Admin authentication (login/logout)
- Admin dashboard
- Regulation management (CRUD operations)
- Update management (CRUD operations)
- Bulk operations for updates
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify, make_response
from models import db, Regulation, Update, AdminUser
from forms import LoginForm, RegulationForm, UpdateForm
from werkzeug.security import check_password_hash
from app.services import RegulationService, UpdateService
from app.utils.admin_helpers import admin_flash
from functools import wraps
import logging
import traceback
import time
import csv
import io
from functools import wraps
from datetime import datetime, timedelta
# Get specialized loggers
logger = logging.getLogger('str_tracker.admin')
performance_logger = logging.getLogger('str_tracker.performance')
security_logger = logging.getLogger('str_tracker.security')

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def log_admin_action(action_type):
    """Decorator to log admin actions with context"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            request_id = getattr(g, 'request_id', 'unknown')
            admin_id = session.get('admin_id', 'anonymous')
            
            logger.info(
                f"Admin action started - Type: {action_type} | "
                f"Admin ID: {admin_id} | Request ID: {request_id} | "
                f"Endpoint: {request.endpoint} | Args: {kwargs}"
            )
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Admin action completed - Type: {action_type} | "
                    f"Duration: {duration:.3f}s | Success: True"
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Admin action failed - Type: {action_type} | "
                    f"Duration: {duration:.3f}s | Error: {str(e)} | "
                    f"Traceback: {traceback.format_exc()}"
                )
                
                # Flash error to user
                admin_flash(f"An error occurred during {action_type}: {str(e)}", 'error')
                raise
                
        return decorated_function
    return decorator


def is_admin_logged_in():
    """Helper function to check admin authentication"""
    return 'admin_id' in session


def require_admin_login(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_logged_in():
            security_logger.warning(
                f"Unauthorized admin access attempt - URL: {request.url} | "
                f"Remote: {request.remote_addr} | User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
            )
            admin_flash('Please log in to access admin panel', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


# Authentication Routes
@admin_bp.route('/login', methods=['GET', 'POST'])
@log_admin_action('login')
def login():
    """Admin login page"""
    if is_admin_logged_in():
        logger.info(f"Already logged in admin redirected to regulations - Admin ID: {session.get('admin_id')}")
        return redirect(url_for('admin.manage_regulations'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        logger.info(f"Login attempt for username: {username}")
        
        user = AdminUser.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['admin_id'] = user.id
            security_logger.info(
                f"Successful admin login - Username: {username} | "
                f"Admin ID: {user.id} | Remote: {request.remote_addr}"
            )
            admin_flash('Login successful!', 'success')
            return redirect(url_for('admin.manage_regulations'))
        else:
            security_logger.warning(
                f"Failed admin login attempt - Username: {username} | "
                f"Remote: {request.remote_addr} | User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
            )
            admin_flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html', form=form)


@admin_bp.route('/logout')
@require_admin_login
@log_admin_action('logout')
def logout():
    """Admin logout"""
    admin_id = session.get('admin_id')
    security_logger.info(f"Admin logout - Admin ID: {admin_id}")
    session.clear()
    admin_flash('Logged out successfully', 'info')
    return redirect(url_for('admin.login'))


# Default admin route redirect to manage regulations
@admin_bp.route('/')
@require_admin_login
def index():
    """Default admin route - redirect to manage regulations"""
    return redirect(url_for('admin.manage_regulations'))


# Regulation Management
@admin_bp.route('/regulations')
@require_admin_login
@log_admin_action('regulations_management')
def manage_regulations():
    """Manage regulations listing"""
    try:
        start_time = time.time()
        regulations = Regulation.query.order_by(Regulation.last_updated.desc()).all()
        load_time = time.time() - start_time
        
        logger.info(f"Successfully loaded {len(regulations)} regulations for admin management in {load_time:.3f}s")
        
        if load_time > 1.0:
            performance_logger.warning(f"Slow regulation loading - Duration: {load_time:.3f}s | Count: {len(regulations)}")
        
        return render_template('admin/manage_regulations.html', regulations=regulations)
        
    except Exception as e:
        logger.error(f"Error in manage_regulations: {str(e)}", exc_info=True)
        admin_flash(f"Error loading regulations: {str(e)}", 'error')
        return redirect(url_for('admin.index'))


@admin_bp.route('/regulations/new', methods=['GET', 'POST'])
@require_admin_login
@log_admin_action('regulation_create')
def new_regulation():
    """Create new regulation"""
    form = RegulationForm()
    
    # CRITICAL: Populate location choices IMMEDIATELY after form creation
    if request.method == 'POST':
        form.populate_location_choices()
    
    if form.validate_on_submit():
        try:
            # Prepare regulation data with new template fields
            regulation_data = {
                # Core Information
                'jurisdiction': form.jurisdiction.data,
                'jurisdiction_level': form.jurisdiction_level.data,
                'location': form.location.data,
                'title': form.title.data,
                'last_updated': form.last_updated.data,
                
                # Rich Text Content Fields
                'overview': form.overview.data,
                'detailed_requirements': form.detailed_requirements.data,
                'compliance_steps': form.compliance_steps.data,
                'required_forms': form.required_forms.data,
                'penalties_non_compliance': form.penalties_non_compliance.data,
                'recent_changes': form.recent_changes.data
            }
            
            logger.info(f"Creating new regulation - Title: {regulation_data['title']} | Location: {regulation_data['location']}")
            
            success, regulation, error = RegulationService.create_regulation(regulation_data)
            
            if success:
                logger.info(f"Successfully created regulation - ID: {regulation.id} | Title: {regulation.title}")
                admin_flash(f'Regulation "{regulation.title}" created successfully!', 'success')
                return redirect(url_for('admin.manage_regulations'))
            else:
                logger.error(f"Failed to create regulation - Error: {error}")
                admin_flash(f'Error creating regulation: {error}', 'error')
                
        except Exception as e:
            logger.error(f"Exception in new_regulation: {str(e)}", exc_info=True)
            admin_flash(f'Error creating regulation: {str(e)}', 'error')
        
    return render_template('admin/edit_regulation.html', form=form, title='New Regulation')


@admin_bp.route('/regulations/<int:regulation_id>/edit', methods=['GET', 'POST'])
@require_admin_login
@log_admin_action('regulation_edit')
def edit_regulation(regulation_id):
    """Edit existing regulation"""
    try:
        regulation = Regulation.query.get_or_404(regulation_id)
        form = RegulationForm(obj=regulation)
        
        logger.info(f"Editing regulation - ID: {regulation_id} | Title: {regulation.title}")
        
        # CRITICAL: Populate location choices IMMEDIATELY after form creation
        if request.method == 'POST':
            form.populate_location_choices()
        # Also populate for initial GET request to show current location
        elif request.method == 'GET' and regulation.jurisdiction_level:
            form.jurisdiction_level.data = regulation.jurisdiction_level
            form.populate_location_choices()
        
        if form.validate_on_submit():
            # Update regulation data with new template fields
            update_data = {
                # Core Information
                'jurisdiction': form.jurisdiction.data,
                'jurisdiction_level': form.jurisdiction_level.data,
                'location': form.location.data,
                'title': form.title.data,
                'last_updated': form.last_updated.data,
                
                # Rich Text Content Fields
                'overview': form.overview.data,
                'detailed_requirements': form.detailed_requirements.data,
                'compliance_steps': form.compliance_steps.data,
                'required_forms': form.required_forms.data,
                'penalties_non_compliance': form.penalties_non_compliance.data,
                'recent_changes': form.recent_changes.data
            }
            
            success, updated_regulation, error = RegulationService.update_regulation(regulation_id, update_data)
            
            if success:
                logger.info(f"Successfully updated regulation - ID: {regulation_id}")
                admin_flash(f'Regulation "{updated_regulation.title}" updated successfully!', 'success')
                return redirect(url_for('admin.manage_regulations'))
            else:
                logger.error(f"Failed to update regulation - ID: {regulation_id} | Error: {error}")
                admin_flash(f'Error updating regulation: {error}', 'error')
        
        return render_template('admin/edit_regulation.html', form=form, regulation=regulation, title='Edit Regulation')
        
    except Exception as e:
        logger.error(f"Error in edit_regulation - ID: {regulation_id} | Error: {str(e)}", exc_info=True)
        admin_flash(f'Error editing regulation: {str(e)}', 'error')
        return redirect(url_for('admin.manage_regulations'))


@admin_bp.route('/regulations/<int:regulation_id>/delete', methods=['POST'])
@require_admin_login
@log_admin_action('regulation_delete')
def delete_regulation(regulation_id):
    """Delete regulation"""
    try:
        regulation = Regulation.query.get_or_404(regulation_id)
        regulation_title = regulation.title
        
        logger.info(f"Deleting regulation - ID: {regulation_id} | Title: {regulation_title}")
        
        success, error = RegulationService.delete_regulation(regulation_id)
        
        if success:
            logger.info(f"Successfully deleted regulation - ID: {regulation_id} | Title: {regulation_title}")
            admin_flash(f'Regulation "{regulation_title}" deleted successfully!', 'success')
        else:
            logger.error(f"Failed to delete regulation - ID: {regulation_id} | Error: {error}")
            admin_flash(f'Error deleting regulation: {error}', 'error')
            
    except Exception as e:
        logger.error(f"Error in delete_regulation - ID: {regulation_id} | Error: {str(e)}", exc_info=True)
        admin_flash(f'Error deleting regulation: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_regulations'))


# Update Management
@admin_bp.route('/updates')
@require_admin_login
@log_admin_action('updates_management')
def manage_updates():
    """Manage updates listing"""
    try:
        start_time = time.time()
        updates = Update.query.order_by(Update.update_date.desc()).all()
        load_time = time.time() - start_time
        
        logger.info(f"Successfully loaded {len(updates)} updates for admin management in {load_time:.3f}s")
        
        if load_time > 1.0:
            performance_logger.warning(f"Slow update loading - Duration: {load_time:.3f}s | Count: {len(updates)}")
        
        return render_template('admin/manage_updates.html', updates=updates)
        
    except Exception as e:
        logger.error(f"Error in manage_updates: {str(e)}", exc_info=True)
        admin_flash(f"Error loading updates: {str(e)}", 'error')
        return redirect(url_for('admin.index'))





@admin_bp.route('/updates/new', methods=['GET', 'POST'])
@require_admin_login
@log_admin_action('update_create')
def new_update():
    """Create new update with all fields"""
    form = UpdateForm()
    
    # CRITICAL: Populate location choices IMMEDIATELY after form creation
    if request.method == 'POST':
        # Set jurisdiction_level to match jurisdiction since they're the same
        form.jurisdiction_level.data = form.jurisdiction.data
        form.populate_location_choices()
    
    # Log basic form submission info
    if request.method == 'POST':
        logger.info("=== NEW UPDATE FORM SUBMISSION ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Form submission received")
    
    if form.validate_on_submit():
        try:
            logger.info("=== STARTING UPDATE CREATION PROCESS ===")
            
            # Prepare update data with all new fields
            update_data = {
                'title': form.title.data,
                'description': form.description.data,
                'jurisdiction_affected': form.jurisdiction_affected.data,
                'jurisdiction_level': form.jurisdiction_level.data,  # Fixed: use jurisdiction_level field
                'update_date': form.update_date.data,
                'status': form.status.data,
                'category': form.category.data,
                'impact_level': form.impact_level.data,
                'effective_date': form.effective_date.data,
                'deadline_date': form.deadline_date.data,
                'action_required': form.action_required.data == 'True',  # Convert string to boolean
                'action_description': form.action_description.data,
                'property_types': form.property_types.data,
                'tags': form.tags.data,
                'source_url': form.source_url.data,
                'priority': form.priority.data,
                # New fields
                'expected_decision_date': form.expected_decision_date.data if hasattr(form, 'expected_decision_date') else None,
                'potential_impact': form.potential_impact.data if hasattr(form, 'potential_impact') else None,
                'decision_status': form.decision_status.data if hasattr(form, 'decision_status') else None,
                'change_type': form.change_type.data if hasattr(form, 'change_type') else None,
                'compliance_deadline': form.compliance_deadline.data if hasattr(form, 'compliance_deadline') else None,
                'affected_operators': form.affected_operators.data if hasattr(form, 'affected_operators') else None,
                'related_regulation_ids': form.related_regulation_ids.data if hasattr(form, 'related_regulation_ids') else None,
                # New template fields
                'summary': form.summary.data if hasattr(form, 'summary') else None,
                'full_text': form.full_text.data if hasattr(form, 'full_text') else None,
                'compliance_requirements': form.compliance_requirements.data if hasattr(form, 'compliance_requirements') else None,
                'implementation_timeline': form.implementation_timeline.data if hasattr(form, 'implementation_timeline') else None,
                'official_sources': form.official_sources.data if hasattr(form, 'official_sources') else None,
                'expert_analysis': form.expert_analysis.data if hasattr(form, 'expert_analysis') else None,
                'kaystreet_commitment': form.kaystreet_commitment.data if hasattr(form, 'kaystreet_commitment') else None
            }
            
            logger.info("=== PREPARED UPDATE DATA ===")
            for field_name, field_value in update_data.items():
                if field_value is None:
                    logger.info(f"Data field '{field_name}': None")
                else:
                    logger.info(f"Data field '{field_name}': '{field_value}' (type: {type(field_value)}, length: {len(str(field_value))})")
            
            logger.info(f"Creating new update - Title: {update_data['title']} | Jurisdiction: {update_data['jurisdiction_affected']} | Status: {update_data['status']}")
            
            logger.info("=== CALLING UPDATE SERVICE ===")
            success, update, error = UpdateService.create_update(update_data)
            
            if success:
                logger.info(f"Successfully created update - ID: {update.id} | Title: {update.title}")
                admin_flash(f'Update "{update.title}" created successfully!', 'success')
                return redirect(url_for('admin.manage_updates'))
            else:
                logger.error(f"Failed to create update - Error: {error}")
                admin_flash(f'Error creating update: {error}', 'error')
                
        except Exception as e:
            logger.error(f"Exception in new_update: {str(e)}", exc_info=True)
            admin_flash(f'Error creating update: {str(e)}', 'error')
        
    # Log form validation errors
    if form.errors:
        logger.warning("=== FORM VALIDATION ERRORS SUMMARY ===")
        for field, errors in form.errors.items():
            for error in errors:
                logger.warning(f"Form validation error - Field: {field} | Error: {error}")
                admin_flash(f'{field}: {error}', 'error')
    
    return render_template('admin/edit_update.html', form=form, title='New Update')


@admin_bp.route('/updates/<int:update_id>/edit', methods=['GET', 'POST'])
@require_admin_login
@log_admin_action('update_edit')
def edit_update(update_id):
    """Edit existing update with all fields"""
    try:
        update = Update.query.get_or_404(update_id)
        form = UpdateForm(obj=update)
        
        logger.info(f"Editing update - ID: {update_id} | Title: {update.title}")
        
        # CRITICAL: Populate location choices IMMEDIATELY after form creation
        if request.method == 'POST':
            # Set jurisdiction_level to match jurisdiction since they're the same
            form.jurisdiction_level.data = form.jurisdiction.data
            form.populate_location_choices()
        # Also populate for initial GET request to show current location
        elif request.method == 'GET' and update.jurisdiction_level:
            form.jurisdiction.data = update.jurisdiction_level
            form.jurisdiction_level.data = update.jurisdiction_level
            form.populate_location_choices()
        
        if form.validate_on_submit():
            # Update data with all new fields
            update_data = {
                'title': form.title.data,
                'description': form.description.data,
                'jurisdiction_affected': form.jurisdiction_affected.data,
                'jurisdiction_level': form.jurisdiction_level.data,  # Fixed: use jurisdiction_level field
                'update_date': form.update_date.data,
                'status': form.status.data,
                'category': form.category.data,
                'impact_level': form.impact_level.data,
                'effective_date': form.effective_date.data,
                'deadline_date': form.deadline_date.data,
                'action_required': form.action_required.data == 'True',  # Convert string to boolean
                'action_description': form.action_description.data,
                'property_types': form.property_types.data,
                'tags': form.tags.data,
                'source_url': form.source_url.data,
                'priority': form.priority.data,
                # New fields
                'expected_decision_date': form.expected_decision_date.data if hasattr(form, 'expected_decision_date') else None,
                'potential_impact': form.potential_impact.data if hasattr(form, 'potential_impact') else None,
                'decision_status': form.decision_status.data if hasattr(form, 'decision_status') else None,
                'change_type': form.change_type.data if hasattr(form, 'change_type') else None,
                'compliance_deadline': form.compliance_deadline.data if hasattr(form, 'compliance_deadline') else None,
                'affected_operators': form.affected_operators.data if hasattr(form, 'affected_operators') else None,
                'related_regulation_ids': form.related_regulation_ids.data if hasattr(form, 'related_regulation_ids') else None,
                # New template fields
                'summary': form.summary.data if hasattr(form, 'summary') else None,
                'full_text': form.full_text.data if hasattr(form, 'full_text') else None,
                'compliance_requirements': form.compliance_requirements.data if hasattr(form, 'compliance_requirements') else None,
                'implementation_timeline': form.implementation_timeline.data if hasattr(form, 'implementation_timeline') else None,
                'official_sources': form.official_sources.data if hasattr(form, 'official_sources') else None,
                'expert_analysis': form.expert_analysis.data if hasattr(form, 'expert_analysis') else None,
                'kaystreet_commitment': form.kaystreet_commitment.data if hasattr(form, 'kaystreet_commitment') else None
            }
            
            success, updated_update, error = UpdateService.update_update(update_id, update_data)
            
            if success:
                logger.info(f"Successfully updated update - ID: {update_id}")
                admin_flash(f'Update "{updated_update.title}" updated successfully!', 'success')
                return redirect(url_for('admin.manage_updates'))
            else:
                logger.error(f"Failed to update update - ID: {update_id} | Error: {error}")
                admin_flash(f'Error updating update: {error}', 'error')
        
        # Log form validation errors
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    logger.warning(f"Form validation error - Field: {field} | Error: {error}")
                    admin_flash(f'{field}: {error}', 'error')
        
        return render_template('admin/edit_update.html', form=form, update=update, title='Edit Update')
        
    except Exception as e:
        logger.error(f"Error in edit_update - ID: {update_id} | Error: {str(e)}", exc_info=True)
        admin_flash(f'Error editing update: {str(e)}', 'error')
        return redirect(url_for('admin.manage_updates'))


@admin_bp.route('/updates/<int:update_id>/delete', methods=['POST'])
@require_admin_login
@log_admin_action('update_delete')
def delete_update(update_id):
    """Delete update"""
    try:
        update = Update.query.get_or_404(update_id)
        update_title = update.title
        
        logger.info(f"Deleting update - ID: {update_id} | Title: {update_title}")
        
        success, error = UpdateService.delete_update(update_id)
        
        if success:
            logger.info(f"Successfully deleted update - ID: {update_id} | Title: {update_title}")
            admin_flash(f'Update "{update_title}" deleted successfully!', 'success')
        else:
            logger.error(f"Failed to delete update - ID: {update_id} | Error: {error}")
            admin_flash(f'Error deleting update: {error}', 'error')
            
    except Exception as e:
        logger.error(f"Error in delete_update - ID: {update_id} | Error: {str(e)}", exc_info=True)
        admin_flash(f'Error deleting update: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_updates'))


# Bulk Operations for Updates
@admin_bp.route('/updates/bulk-status-change', methods=['POST'])
@require_admin_login
@log_admin_action('bulk_status_change')
def bulk_status_change():
    """Bulk change status of multiple updates"""
    try:
        data = request.get_json()
        update_ids = data.get('update_ids', [])
        new_status = data.get('new_status')
        
        if not update_ids or not new_status:
            return jsonify({'success': False, 'error': 'Missing required data'})
        
        logger.info(f"Bulk status change - IDs: {update_ids} | New Status: {new_status}")
        
        success_count = 0
        error_count = 0
        
        for update_id in update_ids:
            try:
                update = db.session.get(Update, update_id)
                if update:
                    # Update both status and change_type for consistency
                    update.status = new_status
                    update.change_type = new_status
                    db.session.commit()
                    success_count += 1
                else:
                    error_count += 1
                    logger.warning(f"Update not found for bulk status change - ID: {update_id}")
            except Exception as e:
                error_count += 1
                logger.error(f"Error updating status for update ID {update_id}: {str(e)}")
        
        if success_count > 0:
            logger.info(f"Bulk status change completed - Success: {success_count} | Errors: {error_count}")
            return jsonify({'success': True, 'message': f'Updated {success_count} updates successfully'})
        else:
            return jsonify({'success': False, 'error': 'No updates were changed'})
            
    except Exception as e:
        logger.error(f"Error in bulk_status_change: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/updates/bulk-delete', methods=['POST'])
@require_admin_login
@log_admin_action('bulk_delete')
def bulk_delete():
    """Bulk delete multiple updates"""
    try:
        data = request.get_json()
        update_ids = data.get('update_ids', [])
        
        if not update_ids:
            return jsonify({'success': False, 'error': 'No updates selected'})
        
        logger.info(f"Bulk delete - IDs: {update_ids}")
        
        success_count = 0
        error_count = 0
        
        for update_id in update_ids:
            try:
                success, error = UpdateService.delete_update(update_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    logger.error(f"Error deleting update ID {update_id}: {error}")
            except Exception as e:
                error_count += 1
                logger.error(f"Exception deleting update ID {update_id}: {str(e)}")
        
        if success_count > 0:
            logger.info(f"Bulk delete completed - Success: {success_count} | Errors: {error_count}")
            return jsonify({'success': True, 'message': f'Deleted {success_count} updates successfully'})
        else:
            return jsonify({'success': False, 'error': 'No updates were deleted'})
            
    except Exception as e:
        logger.error(f"Error in bulk_delete: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/updates/quick-status-change', methods=['POST'])
@require_admin_login
@log_admin_action('quick_status_change')
def quick_status_change():
    """Quick change status of a single update"""
    try:
        data = request.get_json()
        update_id = data.get('update_id')
        new_status = data.get('new_status')
        
        if not update_id or not new_status:
            return jsonify({'success': False, 'error': 'Missing required data'})
        
        logger.info(f"Quick status change - ID: {update_id} | New Status: {new_status}")
        
        update = db.session.get(Update, update_id)
        if not update:
            return jsonify({'success': False, 'error': 'Update not found'})
        
        # Update both status and change_type for consistency
        update.status = new_status
        update.change_type = new_status
        db.session.commit()
        
        logger.info(f"Successfully changed status - ID: {update_id} | Status: {new_status}")
        return jsonify({'success': True, 'message': 'Status updated successfully'})
        
    except Exception as e:
        logger.error(f"Error in quick_status_change: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/updates/export-csv')
@require_admin_login
@log_admin_action('export_csv')
def export_updates_csv():
    """Export updates to CSV"""
    try:
        updates = Update.query.order_by(Update.update_date.desc()).all()
        
        logger.info(f"Exporting {len(updates)} updates to CSV")
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID',
            'Title',
            'Description',
            'Jurisdiction',
            'Status',
            'Change Type',
            'Category',
            'Impact Level',
            'Update Date',
            'Effective Date',
            'Deadline Date',
            'Expected Decision Date',
            'Compliance Deadline',
            'Decision Status',
            'Potential Impact',
            'Affected Operators',
            'Action Required',
            'Action Description',
            'Property Types',
            'Priority',
            'Tags',
            'Source URL',
            'Related Regulation IDs'
        ])
        
        # Write data rows
        for update in updates:
            writer.writerow([
                update.id,
                update.title,
                update.description,
                update.jurisdiction_affected,
                update.status,
                update.change_type,
                update.category,
                update.impact_level,
                update.update_date.strftime('%Y-%m-%d') if update.update_date else '',
                update.effective_date.strftime('%Y-%m-%d') if update.effective_date else '',
                update.deadline_date.strftime('%Y-%m-%d') if update.deadline_date else '',
                update.expected_decision_date.strftime('%Y-%m-%d') if update.expected_decision_date else '',
                update.compliance_deadline.strftime('%Y-%m-%d') if update.compliance_deadline else '',
                update.decision_status or '',
                update.potential_impact or '',
                update.affected_operators or '',
                'Yes' if update.action_required else 'No',
                update.action_description or '',
                update.property_types,
                update.priority,
                update.tags or '',
                update.source_url or '',
                update.related_regulation_ids or ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=updates_export.csv'
        
        logger.info(f"Successfully exported {len(updates)} updates to CSV")
        return response
        
    except Exception as e:
        logger.error(f"Error in export_updates_csv: {str(e)}", exc_info=True)
        admin_flash(f'Error exporting updates: {str(e)}', 'error')
        return redirect(url_for('admin.manage_updates'))


@admin_bp.route('/updates/import-csv', methods=['GET', 'POST'])
@require_admin_login
@log_admin_action('import_csv')
def import_updates_csv():
    """Import updates from CSV"""
    if request.method == 'GET':
        return render_template('admin/import_updates.html')
    
    try:
        # Check if file was uploaded
        if 'csv_file' not in request.files:
            admin_flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['csv_file']
        if file.filename == '':
            admin_flash('No file selected', 'error')
            return redirect(request.url)
        
        if not file.filename.lower().endswith('.csv'):
            admin_flash('Please upload a CSV file', 'error')
            return redirect(request.url)
        
        logger.info(f"Starting CSV import - File: {file.filename}")
        
        # Read CSV content
        content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        
        success_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is header
            try:
                # Skip rows with empty title
                if not row.get('Title', '').strip():
                    continue
                
                # Parse dates
                def parse_date(date_str):
                    if not date_str or date_str.strip() == '':
                        return None
                    try:
                        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                    except ValueError:
                        return None
                
                # Create update data
                update_data = {
                    'title': row.get('Title', '').strip(),
                    'description': row.get('Description', '').strip(),
                    'jurisdiction_affected': row.get('Jurisdiction', '').strip(),
                    'status': row.get('Status', 'Recent').strip(),
                    'change_type': row.get('Change Type', row.get('Status', 'Recent')).strip(),
                    'category': row.get('Category', 'Regulatory Changes').strip(),
                    'impact_level': row.get('Impact Level', 'Medium').strip(),
                    'update_date': parse_date(row.get('Update Date', '')),
                    'effective_date': parse_date(row.get('Effective Date', '')),
                    'deadline_date': parse_date(row.get('Deadline Date', '')),
                    'expected_decision_date': parse_date(row.get('Expected Decision Date', '')),
                    'compliance_deadline': parse_date(row.get('Compliance Deadline', '')),
                    'decision_status': row.get('Decision Status', '').strip() or None,
                    'potential_impact': row.get('Potential Impact', '').strip() or None,
                    'affected_operators': row.get('Affected Operators', '').strip() or None,
                    'action_required': row.get('Action Required', 'No').strip().lower() in ['yes', 'true', '1'],
                    'action_description': row.get('Action Description', '').strip() or None,
                    'property_types': row.get('Property Types', 'Both').strip(),
                    'priority': row.get('Priority', '3').strip(),
                    'tags': row.get('Tags', '').strip() or None,
                    'source_url': row.get('Source URL', '').strip() or None,
                    'related_regulation_ids': row.get('Related Regulation IDs', '').strip() or None
                }
                
                # Validate required fields
                if not update_data['title']:
                    errors.append(f"Row {row_num}: Title is required")
                    error_count += 1
                    continue
                
                if not update_data['description']:
                    errors.append(f"Row {row_num}: Description is required")
                    error_count += 1
                    continue
                
                if not update_data['jurisdiction_affected']:
                    errors.append(f"Row {row_num}: Jurisdiction is required")
                    error_count += 1
                    continue
                
                # Set update_date to today if not provided
                if not update_data['update_date']:
                    update_data['update_date'] = datetime.now().date()
                
                # Create update using service
                success, update, error = UpdateService.create_update(update_data)
                
                if success:
                    success_count += 1
                    logger.info(f"Successfully imported update - Row {row_num}: {update.title}")
                else:
                    error_count += 1
                    errors.append(f"Row {row_num}: {error}")
                    logger.error(f"Failed to import update - Row {row_num}: {error}")
                    
            except Exception as e:
                error_count += 1
                error_msg = f"Row {row_num}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Exception importing update - {error_msg}")
        
        # Report results
        if success_count > 0:
            admin_flash(f'Successfully imported {success_count} updates', 'success')
        
        if error_count > 0:
            error_summary = f'Failed to import {error_count} updates'
            if len(errors) <= 10:
                error_summary += ': ' + '; '.join(errors)
            else:
                error_summary += f'. First 10 errors: {"; ".join(errors[:10])}'
            admin_flash(error_summary, 'error')
        
        logger.info(f"CSV import completed - Success: {success_count} | Errors: {error_count}")
        
        if success_count > 0:
            return redirect(url_for('admin.manage_updates'))
        else:
            return redirect(request.url)
            
    except Exception as e:
        logger.error(f"Error in import_updates_csv: {str(e)}", exc_info=True)
        admin_flash(f'Error importing CSV: {str(e)}', 'error')
        return redirect(request.url)


 