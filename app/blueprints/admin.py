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
                flash(f"An error occurred during {action_type}: {str(e)}", 'error')
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
            flash('Please log in to access admin panel', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


# Authentication Routes
@admin_bp.route('/login', methods=['GET', 'POST'])
@log_admin_action('login')
def login():
    """Admin login page"""
    if is_admin_logged_in():
        logger.info(f"Already logged in admin redirected to dashboard - Admin ID: {session.get('admin_id')}")
        return redirect(url_for('admin.dashboard'))
    
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
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            security_logger.warning(
                f"Failed admin login attempt - Username: {username} | "
                f"Remote: {request.remote_addr} | User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
            )
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html', form=form)


@admin_bp.route('/logout')
@require_admin_login
@log_admin_action('logout')
def logout():
    """Admin logout"""
    admin_id = session.get('admin_id')
    security_logger.info(f"Admin logout - Admin ID: {admin_id}")
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@require_admin_login
@log_admin_action('dashboard_access')
def dashboard():
    """Admin dashboard with statistics"""
    try:
        # Get statistics from services
        reg_stats = RegulationService.get_admin_statistics()
        update_stats = UpdateService.get_admin_statistics()
        
        # Get recent updates for activity feed (last 5)
        recent_updates = Update.query.order_by(Update.update_date.desc()).limit(5).all()
        
        # Calculate upcoming deadlines (next 30 days)
        thirty_days_from_now = datetime.now().date() + timedelta(days=30)
        
        upcoming_deadlines_count = Update.query.filter(
            db.or_(
                db.and_(Update.deadline_date.isnot(None), Update.deadline_date <= thirty_days_from_now),
                db.and_(Update.compliance_deadline.isnot(None), Update.compliance_deadline <= thirty_days_from_now),
                db.and_(Update.expected_decision_date.isnot(None), Update.expected_decision_date <= thirty_days_from_now)
            )
        ).count()
        
        # Count updates by type
        recent_count = Update.query.filter(
            db.or_(
                Update.change_type == 'Recent',
                Update.status == 'Recent'
            )
        ).count()
        
        upcoming_count = Update.query.filter(
            db.or_(
                Update.change_type == 'Upcoming',
                Update.status == 'Upcoming'
            )
        ).count()
        
        proposed_count = Update.query.filter(
            db.or_(
                Update.change_type == 'Proposed',
                Update.status == 'Proposed'
            )
        ).count()
        
        # Combine stats for template compatibility
        combined_stats = {
            'total_regulations': reg_stats.get('total', 0),
            'total_updates': update_stats.get('total', 0),
            'recent_updates': recent_count,
            'upcoming_updates': upcoming_count,
            'proposed_updates': proposed_count,
            'upcoming_deadlines': upcoming_deadlines_count,
            'regulation_stats': reg_stats,
            'update_stats': update_stats
        }
        
        logger.info(
            f"Dashboard data loaded - Regulations: {reg_stats.get('total', 0)} | "
            f"Updates: {update_stats.get('total', 0)} | "
            f"Upcoming Deadlines: {upcoming_deadlines_count} | "
            f"Recent Activity: {len(recent_updates)}"
        )
        
        return render_template('admin/dashboard.html', 
                             stats=combined_stats, 
                             recent_updates=recent_updates)
                             
    except Exception as e:
        logger.error(f"Error loading dashboard data: {str(e)}", exc_info=True)
        flash('Error loading dashboard data', 'error')
        
        # Provide safe defaults
        default_stats = {
            'total_regulations': 0,
            'total_updates': 0,
            'recent_updates': 0,
            'upcoming_updates': 0,
            'proposed_updates': 0,
            'upcoming_deadlines': 0,
            'regulation_stats': {},
            'update_stats': {}
        }
        
        return render_template('admin/dashboard.html', 
                             stats=default_stats, 
                             recent_updates=[])


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
        
        return render_template('admin/manage_regulations_temp.html', regulations=regulations)
        
    except Exception as e:
        logger.error(f"Error in manage_regulations: {str(e)}", exc_info=True)
        flash(f"Error loading regulations: {str(e)}", 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/regulations/new', methods=['GET', 'POST'])
@require_admin_login
@log_admin_action('regulation_create')
def new_regulation():
    """Create new regulation"""
    form = RegulationForm()
    
    if form.validate_on_submit():
        try:
            # Prepare regulation data with new template fields
            regulation_data = {
                # Core Information
                'jurisdiction': form.jurisdiction.data,
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
                flash(f'Regulation "{regulation.title}" created successfully!', 'success')
                return redirect(url_for('admin.manage_regulations'))
            else:
                logger.error(f"Failed to create regulation - Error: {error}")
                flash(f'Error creating regulation: {error}', 'error')
                
        except Exception as e:
            logger.error(f"Exception in new_regulation: {str(e)}", exc_info=True)
            flash(f'Error creating regulation: {str(e)}', 'error')
        
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
        
        if form.validate_on_submit():
            # Update regulation data with new template fields
            update_data = {
                # Core Information
                'jurisdiction': form.jurisdiction.data,
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
                flash(f'Regulation "{updated_regulation.title}" updated successfully!', 'success')
                return redirect(url_for('admin.manage_regulations'))
            else:
                logger.error(f"Failed to update regulation - ID: {regulation_id} | Error: {error}")
                flash(f'Error updating regulation: {error}', 'error')
        
        return render_template('admin/edit_regulation.html', form=form, regulation=regulation, title='Edit Regulation')
        
    except Exception as e:
        logger.error(f"Error in edit_regulation - ID: {regulation_id} | Error: {str(e)}", exc_info=True)
        flash(f'Error editing regulation: {str(e)}', 'error')
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
            flash(f'Regulation "{regulation_title}" deleted successfully!', 'success')
        else:
            logger.error(f"Failed to delete regulation - ID: {regulation_id} | Error: {error}")
            flash(f'Error deleting regulation: {error}', 'error')
            
    except Exception as e:
        logger.error(f"Error in delete_regulation - ID: {regulation_id} | Error: {str(e)}", exc_info=True)
        flash(f'Error deleting regulation: {str(e)}', 'error')
    
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
        flash(f"Error loading updates: {str(e)}", 'error')
        return redirect(url_for('admin.dashboard'))





@admin_bp.route('/updates/new', methods=['GET', 'POST'])
@require_admin_login
@log_admin_action('update_create')
def new_update():
    """Create new update with all fields"""
    form = UpdateForm()
    
    if form.validate_on_submit():
        try:
            # Prepare update data with all new fields
            update_data = {
                'title': form.title.data,
                'description': form.description.data,
                'jurisdiction_affected': form.jurisdiction_affected.data,
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
                'expected_decision_date': getattr(form, 'expected_decision_date', None) and form.expected_decision_date.data,
                'potential_impact': getattr(form, 'potential_impact', None) and form.potential_impact.data,
                'decision_status': getattr(form, 'decision_status', None) and form.decision_status.data,
                'change_type': getattr(form, 'change_type', None) and form.change_type.data,
                'compliance_deadline': getattr(form, 'compliance_deadline', None) and form.compliance_deadline.data,
                'affected_operators': getattr(form, 'affected_operators', None) and form.affected_operators.data,
                'related_regulation_ids': getattr(form, 'related_regulation_ids', None) and form.related_regulation_ids.data,
                # New template fields
                'summary': getattr(form, 'summary', None) and form.summary.data,
                'full_text': getattr(form, 'full_text', None) and form.full_text.data,
                'compliance_requirements': getattr(form, 'compliance_requirements', None) and form.compliance_requirements.data,
                'implementation_timeline': getattr(form, 'implementation_timeline', None) and form.implementation_timeline.data,
                'official_sources': getattr(form, 'official_sources', None) and form.official_sources.data,
                'expert_analysis': getattr(form, 'expert_analysis', None) and form.expert_analysis.data,
                'kaystreet_commitment': getattr(form, 'kaystreet_commitment', None) and form.kaystreet_commitment.data
            }
            
            logger.info(f"Creating new update - Title: {update_data['title']} | Jurisdiction: {update_data['jurisdiction_affected']} | Status: {update_data['status']}")
            
            success, update, error = UpdateService.create_update(update_data)
            
            if success:
                logger.info(f"Successfully created update - ID: {update.id} | Title: {update.title}")
                flash(f'Update "{update.title}" created successfully!', 'success')
                return redirect(url_for('admin.manage_updates'))
            else:
                logger.error(f"Failed to create update - Error: {error}")
                flash(f'Error creating update: {error}', 'error')
                
        except Exception as e:
            logger.error(f"Exception in new_update: {str(e)}", exc_info=True)
            flash(f'Error creating update: {str(e)}', 'error')
        
    # Log form validation errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                logger.warning(f"Form validation error - Field: {field} | Error: {error}")
                flash(f'{field}: {error}', 'error')
    
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
        
        if form.validate_on_submit():
            # Update data with all new fields
            update_data = {
                'title': form.title.data,
                'description': form.description.data,
                'jurisdiction_affected': form.jurisdiction_affected.data,
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
                'expected_decision_date': getattr(form, 'expected_decision_date', None) and form.expected_decision_date.data,
                'potential_impact': getattr(form, 'potential_impact', None) and form.potential_impact.data,
                'decision_status': getattr(form, 'decision_status', None) and form.decision_status.data,
                'change_type': getattr(form, 'change_type', None) and form.change_type.data,
                'compliance_deadline': getattr(form, 'compliance_deadline', None) and form.compliance_deadline.data,
                'affected_operators': getattr(form, 'affected_operators', None) and form.affected_operators.data,
                'related_regulation_ids': getattr(form, 'related_regulation_ids', None) and form.related_regulation_ids.data,
                # New template fields
                'summary': getattr(form, 'summary', None) and form.summary.data,
                'full_text': getattr(form, 'full_text', None) and form.full_text.data,
                'compliance_requirements': getattr(form, 'compliance_requirements', None) and form.compliance_requirements.data,
                'implementation_timeline': getattr(form, 'implementation_timeline', None) and form.implementation_timeline.data,
                'official_sources': getattr(form, 'official_sources', None) and form.official_sources.data,
                'expert_analysis': getattr(form, 'expert_analysis', None) and form.expert_analysis.data,
                'kaystreet_commitment': getattr(form, 'kaystreet_commitment', None) and form.kaystreet_commitment.data
            }
            
            success, updated_update, error = UpdateService.update_update(update_id, update_data)
            
            if success:
                logger.info(f"Successfully updated update - ID: {update_id}")
                flash(f'Update "{updated_update.title}" updated successfully!', 'success')
                return redirect(url_for('admin.manage_updates'))
            else:
                logger.error(f"Failed to update update - ID: {update_id} | Error: {error}")
                flash(f'Error updating update: {error}', 'error')
        
        # Log form validation errors
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    logger.warning(f"Form validation error - Field: {field} | Error: {error}")
                    flash(f'{field}: {error}', 'error')
        
        return render_template('admin/edit_update.html', form=form, update=update, title='Edit Update')
        
    except Exception as e:
        logger.error(f"Error in edit_update - ID: {update_id} | Error: {str(e)}", exc_info=True)
        flash(f'Error editing update: {str(e)}', 'error')
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
            flash(f'Update "{update_title}" deleted successfully!', 'success')
        else:
            logger.error(f"Failed to delete update - ID: {update_id} | Error: {error}")
            flash(f'Error deleting update: {error}', 'error')
            
    except Exception as e:
        logger.error(f"Error in delete_update - ID: {update_id} | Error: {str(e)}", exc_info=True)
        flash(f'Error deleting update: {str(e)}', 'error')
    
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
                update = Update.query.get(update_id)
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
        
        update = Update.query.get(update_id)
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
        flash(f'Error exporting updates: {str(e)}', 'error')
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
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if not file.filename.lower().endswith('.csv'):
            flash('Please upload a CSV file', 'error')
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
            flash(f'Successfully imported {success_count} updates', 'success')
        
        if error_count > 0:
            error_summary = f'Failed to import {error_count} updates'
            if len(errors) <= 10:
                error_summary += ': ' + '; '.join(errors)
            else:
                error_summary += f'. First 10 errors: {"; ".join(errors[:10])}'
            flash(error_summary, 'error')
        
        logger.info(f"CSV import completed - Success: {success_count} | Errors: {error_count}")
        
        if success_count > 0:
            return redirect(url_for('admin.manage_updates'))
        else:
            return redirect(request.url)
            
    except Exception as e:
        logger.error(f"Error in import_updates_csv: {str(e)}", exc_info=True)
        flash(f'Error importing CSV: {str(e)}', 'error')
        return redirect(request.url)


@admin_bp.route('/updates/deadline-reminders')
@require_admin_login
@log_admin_action('deadline_reminders')
def deadline_reminders():
    """View upcoming deadline reminders"""
    try:
        
        # Get updates with deadlines in the next 30 days
        thirty_days_from_now = datetime.now().date() + timedelta(days=30)
        
        upcoming_deadlines = Update.query.filter(
            db.or_(
                db.and_(Update.deadline_date.isnot(None), Update.deadline_date <= thirty_days_from_now),
                db.and_(Update.compliance_deadline.isnot(None), Update.compliance_deadline <= thirty_days_from_now),
                db.and_(Update.expected_decision_date.isnot(None), Update.expected_decision_date <= thirty_days_from_now)
            )
        ).order_by(
            db.case(
                (Update.deadline_date.isnot(None), Update.deadline_date),
                (Update.compliance_deadline.isnot(None), Update.compliance_deadline),
                else_=Update.expected_decision_date
            )
        ).all()
        
        # Calculate days until deadline for each update
        today = datetime.now().date()
        for update in upcoming_deadlines:
            deadline_date = update.deadline_date or update.compliance_deadline or update.expected_decision_date
            if deadline_date:
                update.days_until = (deadline_date - today).days
            else:
                update.days_until = 999
        
        logger.info(f"Retrieved {len(upcoming_deadlines)} updates with upcoming deadlines")
        
        return render_template('admin/deadline_reminders.html', updates=upcoming_deadlines)
        
    except Exception as e:
        logger.error(f"Error in deadline_reminders: {str(e)}", exc_info=True)
        flash(f'Error loading deadline reminders: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard')) 