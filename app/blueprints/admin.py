"""
Admin Blueprint - Administrative Interface

Contains all administrative routes for the STR Compliance Toolkit:
- Admin authentication (login/logout)
- Admin dashboard
- Regulation management (CRUD operations)
- Update management (CRUD operations)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from models import db, Regulation, Update, AdminUser
from forms import LoginForm, RegulationForm, UpdateForm
from werkzeug.security import check_password_hash
from app.services import RegulationService, UpdateService
import logging
import traceback
import time
from functools import wraps

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
        
        # Combine stats for template compatibility
        combined_stats = {
            'total_regulations': reg_stats.get('total', 0),
            'total_updates': update_stats.get('total', 0),
            'recent_updates': update_stats.get('recent', 0),
            'upcoming_updates': update_stats.get('upcoming', 0),
            'proposed_updates': update_stats.get('proposed', 0),
            'regulation_stats': reg_stats,
            'update_stats': update_stats
        }
        
        logger.info(
            f"Dashboard data loaded - Regulations: {reg_stats.get('total', 0)} | "
            f"Updates: {update_stats.get('total', 0)}"
        )
        
        return render_template('admin/dashboard.html', stats=combined_stats)
                             
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
            'regulation_stats': {},
            'update_stats': {}
        }
        
        return render_template('admin/dashboard.html', stats=default_stats)


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
            # Prepare regulation data with comprehensive fields
            regulation_data = {
                # Core Information
                'jurisdiction_level': form.jurisdiction_level.data,
                'location': form.location.data,
                'title': form.title.data,
                'key_requirements': form.key_requirements.data,
                
                # Compliance Details
                'compliance_level': form.compliance_level.data,
                'property_types': form.property_types.data,
                'status': form.status.data,
                
                # Metadata
                'category': form.category.data,
                'priority': form.priority.data,
                'related_keywords': form.related_keywords.data,
                'compliance_checklist': form.compliance_checklist.data,
                
                # Contact Information
                'local_authority_contact': form.local_authority_contact.data,
                
                # Timestamps
                'last_updated': form.last_updated.data,
                
                # Legacy fields for backward compatibility
                'property_type': form.property_type.data,
                'effective_date': form.effective_date.data,
                'expiry_date': form.expiry_date.data,
                'keywords': form.keywords.data
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
            # Update regulation data with comprehensive fields
            update_data = {
                # Core Information
                'jurisdiction_level': form.jurisdiction_level.data,
                'location': form.location.data,
                'title': form.title.data,
                'key_requirements': form.key_requirements.data,
                
                # Compliance Details
                'compliance_level': form.compliance_level.data,
                'property_types': form.property_types.data,
                'status': form.status.data,
                
                # Metadata
                'category': form.category.data,
                'priority': form.priority.data,
                'related_keywords': form.related_keywords.data,
                'compliance_checklist': form.compliance_checklist.data,
                
                # Contact Information
                'local_authority_contact': form.local_authority_contact.data,
                
                # Timestamps
                'last_updated': form.last_updated.data,
                
                # Legacy fields for backward compatibility
                'property_type': form.property_type.data,
                'effective_date': form.effective_date.data,
                'expiry_date': form.expiry_date.data,
                'keywords': form.keywords.data
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
    """Create new update"""
    form = UpdateForm()
    
    if form.validate_on_submit():
        try:
            # Prepare update data
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
                'action_required': form.action_required.data,
                'action_description': form.action_description.data,
                'property_types': form.property_types.data,
                'tags': form.tags.data,
                'source_url': form.source_url.data,
                'priority': form.priority.data
            }
            
            logger.info(f"Creating new update - Title: {update_data['title']} | Jurisdiction: {update_data['jurisdiction_affected']}")
            
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
        
    return render_template('admin/edit_update.html', form=form, title='New Update')


@admin_bp.route('/updates/<int:update_id>/edit', methods=['GET', 'POST'])
@require_admin_login
@log_admin_action('update_edit')
def edit_update(update_id):
    """Edit existing update"""
    try:
        update = Update.query.get_or_404(update_id)
        form = UpdateForm(obj=update)
        
        logger.info(f"Editing update - ID: {update_id} | Title: {update.title}")
        
        if form.validate_on_submit():
            # Update data
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
                'action_required': form.action_required.data,
                'action_description': form.action_description.data,
                'property_types': form.property_types.data,
                'tags': form.tags.data,
                'source_url': form.source_url.data,
                'priority': form.priority.data
            }
            
            success, updated_update, error = UpdateService.update_update(update_id, update_data)
            
            if success:
                logger.info(f"Successfully updated update - ID: {update_id}")
                flash(f'Update "{updated_update.title}" updated successfully!', 'success')
                return redirect(url_for('admin.manage_updates'))
            else:
                logger.error(f"Failed to update update - ID: {update_id} | Error: {error}")
                flash(f'Error updating update: {error}', 'error')
        
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