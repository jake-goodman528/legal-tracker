"""
Admin Blueprint - Administrative Interface

Contains all administrative routes for the STR Compliance Toolkit:
- Admin authentication (login/logout)
- Admin dashboard
- Regulation management (CRUD operations)
- Update management (CRUD operations)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Regulation, Update, AdminUser
from forms import LoginForm, RegulationForm, UpdateForm
from werkzeug.security import check_password_hash
from app.services import RegulationService, UpdateService

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def is_admin_logged_in():
    """Helper function to check admin authentication"""
    return 'admin_id' in session


# Authentication Routes
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if is_admin_logged_in():
        return redirect(url_for('admin.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            session['admin_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html', form=form)


@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))


# Dashboard
@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard with statistics"""
    if not is_admin_logged_in():
        flash('Please log in to access admin panel', 'error')
        return redirect(url_for('admin.login'))
    
    # Get statistics using services
    regulation_stats = {'total_regulations': Regulation.query.count()}
    update_stats = UpdateService.get_admin_statistics()
    
    # Combine statistics
    stats = {**regulation_stats, **update_stats}
    
    return render_template('admin/dashboard.html', stats=stats)


# Regulation Management
@admin_bp.route('/regulations')
def manage_regulations():
    """Manage regulations listing"""
    if not is_admin_logged_in():
        flash('Please log in to access admin panel', 'error')
        return redirect(url_for('admin.login'))
    
    regulations = Regulation.query.order_by(Regulation.last_updated.desc()).all()
    return render_template('admin/manage_regulations.html', regulations=regulations)


@admin_bp.route('/regulations/new', methods=['GET', 'POST'])
def new_regulation():
    """Create new regulation"""
    if not is_admin_logged_in():
        flash('Please log in to access admin panel', 'error')
        return redirect(url_for('admin.login'))
    
    form = RegulationForm()
    if form.validate_on_submit():
        # Prepare regulation data
        regulation_data = {
            'jurisdiction_level': form.jurisdiction_level.data,
            'location': form.location.data,
            'title': form.title.data,
            'key_requirements': form.key_requirements.data,
            'last_updated': form.last_updated.data,
            'category': form.category.data,
            'compliance_level': form.compliance_level.data,
            'property_type': form.property_type.data,
            'effective_date': form.effective_date.data,
            'expiry_date': form.expiry_date.data,
            'keywords': form.keywords.data
        }
        
        # Use RegulationService to create regulation
        success, regulation, error = RegulationService.create_regulation(regulation_data)
        
        if success:
            flash('Regulation created successfully!', 'success')
            return redirect(url_for('admin.manage_regulations'))
        else:
            flash(f'Error creating regulation: {error}', 'error')
    
    return render_template('admin/edit_regulation.html', form=form, title='New Regulation')


@admin_bp.route('/regulations/<int:id>/edit', methods=['GET', 'POST'])
def edit_regulation(id):
    """Edit existing regulation"""
    if not is_admin_logged_in():
        flash('Please log in to access admin panel', 'error')
        return redirect(url_for('admin.login'))
    
    regulation = RegulationService.get_regulation_by_id(id)
    if not regulation:
        flash('Regulation not found', 'error')
        return redirect(url_for('admin.manage_regulations'))
    
    form = RegulationForm(obj=regulation)
    
    if form.validate_on_submit():
        # Prepare updated regulation data
        regulation_data = {
            'jurisdiction_level': form.jurisdiction_level.data,
            'location': form.location.data,
            'title': form.title.data,
            'key_requirements': form.key_requirements.data,
            'last_updated': form.last_updated.data,
            'category': form.category.data,
            'compliance_level': form.compliance_level.data,
            'property_type': form.property_type.data,
            'effective_date': form.effective_date.data,
            'expiry_date': form.expiry_date.data,
            'keywords': form.keywords.data
        }
        
        # Use RegulationService to update regulation
        success, updated_regulation, error = RegulationService.update_regulation(id, regulation_data)
        
        if success:
            flash('Regulation updated successfully!', 'success')
            return redirect(url_for('admin.manage_regulations'))
        else:
            flash(f'Error updating regulation: {error}', 'error')
    
    return render_template('admin/edit_regulation.html', form=form, regulation=regulation, title='Edit Regulation')


@admin_bp.route('/regulations/<int:id>/delete', methods=['POST'])
def delete_regulation(id):
    """Delete regulation"""
    if not is_admin_logged_in():
        flash('Please log in to access admin panel', 'error')
        return redirect(url_for('admin.login'))
    
    success, error = RegulationService.delete_regulation(id)
    
    if success:
        flash('Regulation deleted successfully!', 'success')
    else:
        flash(f'Error deleting regulation: {error}', 'error')
    
    return redirect(url_for('admin.manage_regulations'))


# Update Management
@admin_bp.route('/updates')
def manage_updates():
    """Manage updates listing"""
    if not is_admin_logged_in():
        flash('Please log in to access admin panel', 'error')
        return redirect(url_for('admin.login'))
    
    updates = UpdateService.get_all_updates()
    return render_template('admin/manage_updates.html', updates=updates)


@admin_bp.route('/updates/new', methods=['GET', 'POST'])
def new_update():
    """Create new update"""
    if not is_admin_logged_in():
        flash('Please log in to access admin panel', 'error')
        return redirect(url_for('admin.login'))
    
    form = UpdateForm()
    if form.validate_on_submit():
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
            'related_regulation_ids': form.related_regulation_ids.data,
            'tags': form.tags.data,
            'source_url': form.source_url.data,
            'priority': form.priority.data
        }
        
        # Use UpdateService to create update
        success, update, error = UpdateService.create_update(update_data)
        
        if success:
            flash('Update created successfully!', 'success')
            return redirect(url_for('admin.manage_updates'))
        else:
            flash(f'Error creating update: {error}', 'error')
    
    return render_template('admin/edit_update.html', form=form, title='New Update')


@admin_bp.route('/updates/<int:id>/edit', methods=['GET', 'POST'])
def edit_update(id):
    """Edit existing update"""
    if not is_admin_logged_in():
        flash('Please log in to access admin panel', 'error')
        return redirect(url_for('admin.login'))
    
    update = UpdateService.get_update_by_id(id)
    if not update:
        flash('Update not found', 'error')
        return redirect(url_for('admin.manage_updates'))
    
    form = UpdateForm(obj=update)
    
    if form.validate_on_submit():
        # Prepare updated data
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
            'related_regulation_ids': form.related_regulation_ids.data,
            'tags': form.tags.data,
            'source_url': form.source_url.data,
            'priority': form.priority.data
        }
        
        # Use UpdateService to update
        success, updated_update, error = UpdateService.update_update(id, update_data)
        
        if success:
            flash('Update updated successfully!', 'success')
            return redirect(url_for('admin.manage_updates'))
        else:
            flash(f'Error updating update: {error}', 'error')
    
    return render_template('admin/edit_update.html', form=form, update=update, title='Edit Update')


@admin_bp.route('/updates/<int:id>/delete', methods=['POST'])
def delete_update(id):
    """Delete update"""
    if not is_admin_logged_in():
        flash('Please log in to access admin panel', 'error')
        return redirect(url_for('admin.login'))
    
    success, error = UpdateService.delete_update(id)
    
    if success:
        flash('Update deleted successfully!', 'success')
    else:
        flash(f'Error deleting update: {error}', 'error')
    
    return redirect(url_for('admin.manage_updates')) 