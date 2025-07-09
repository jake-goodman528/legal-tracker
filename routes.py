from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import app, db
from models import Regulation, Update, AdminUser
from forms import LoginForm, RegulationForm, UpdateForm
from werkzeug.security import check_password_hash
from datetime import datetime
import logging

# Helper function to check admin authentication
def is_admin_logged_in():
    return 'admin_id' in session

# Public Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/regulations')
def regulations():
    # Get filter parameters
    jurisdiction_filter = request.args.get('jurisdiction', '')
    location_filter = request.args.get('location', '')
    search_query = request.args.get('search', '')
    
    # Build query
    query = Regulation.query
    
    if jurisdiction_filter:
        query = query.filter(Regulation.jurisdiction_level == jurisdiction_filter)
    
    if location_filter:
        query = query.filter(Regulation.location.ilike(f'%{location_filter}%'))
    
    if search_query:
        query = query.filter(
            db.or_(
                Regulation.title.ilike(f'%{search_query}%'),
                Regulation.key_requirements.ilike(f'%{search_query}%')
            )
        )
    
    regulations = query.order_by(Regulation.jurisdiction_level, Regulation.location).all()
    
    # Get unique values for filters
    all_jurisdictions = db.session.query(Regulation.jurisdiction_level).distinct().all()
    all_locations = db.session.query(Regulation.location).distinct().all()
    
    return render_template('regulations.html', 
                         regulations=regulations,
                         jurisdictions=[j[0] for j in all_jurisdictions],
                         locations=[l[0] for l in all_locations],
                         current_jurisdiction=jurisdiction_filter,
                         current_location=location_filter,
                         current_search=search_query)

@app.route('/updates')
def updates():
    status_filter = request.args.get('status', '')
    jurisdiction_filter = request.args.get('jurisdiction', '')
    
    query = Update.query
    
    if status_filter:
        query = query.filter(Update.status == status_filter)
    
    if jurisdiction_filter:
        query = query.filter(Update.jurisdiction_affected.ilike(f'%{jurisdiction_filter}%'))
    
    updates = query.order_by(Update.update_date.desc()).all()
    
    # Get unique values for filters
    all_statuses = db.session.query(Update.status).distinct().all()
    all_jurisdictions = db.session.query(Update.jurisdiction_affected).distinct().all()
    
    return render_template('updates.html',
                         updates=updates,
                         statuses=[s[0] for s in all_statuses],
                         jurisdictions=[j[0] for j in all_jurisdictions],
                         current_status=status_filter,
                         current_jurisdiction=jurisdiction_filter)

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if is_admin_logged_in():
        return redirect(url_for('admin_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            session['admin_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html', form=form)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin_logged_in():
        flash('Please log in to access admin panel', 'error')
        return redirect(url_for('admin_login'))
    
    # Get statistics
    total_regulations = Regulation.query.count()
    total_updates = Update.query.count()
    recent_updates = Update.query.filter(Update.status == 'Recent').count()
    upcoming_updates = Update.query.filter(Update.status == 'Upcoming').count()
    proposed_updates = Update.query.filter(Update.status == 'Proposed').count()
    
    stats = {
        'total_regulations': total_regulations,
        'total_updates': total_updates,
        'recent_updates': recent_updates,
        'upcoming_updates': upcoming_updates,
        'proposed_updates': proposed_updates
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/regulations')
def admin_manage_regulations():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    regulations = Regulation.query.order_by(Regulation.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/manage_regulations.html', regulations=regulations)

@app.route('/admin/regulations/new', methods=['GET', 'POST'])
def admin_new_regulation():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    form = RegulationForm()
    if form.validate_on_submit():
        regulation = Regulation(
            jurisdiction_level=form.jurisdiction_level.data,
            location=form.location.data,
            title=form.title.data,
            key_requirements=form.key_requirements.data,
            last_updated=form.last_updated.data
        )
        db.session.add(regulation)
        db.session.commit()
        flash('Regulation added successfully!', 'success')
        return redirect(url_for('admin_manage_regulations'))
    
    return render_template('admin/edit_regulation.html', form=form, title='Add New Regulation')

@app.route('/admin/regulations/<int:id>/edit', methods=['GET', 'POST'])
def admin_edit_regulation(id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    regulation = Regulation.query.get_or_404(id)
    form = RegulationForm(obj=regulation)
    
    if form.validate_on_submit():
        regulation.jurisdiction_level = form.jurisdiction_level.data
        regulation.location = form.location.data
        regulation.title = form.title.data
        regulation.key_requirements = form.key_requirements.data
        regulation.last_updated = form.last_updated.data
        db.session.commit()
        flash('Regulation updated successfully!', 'success')
        return redirect(url_for('admin_manage_regulations'))
    
    return render_template('admin/edit_regulation.html', form=form, regulation=regulation, title='Edit Regulation')

@app.route('/admin/regulations/<int:id>/delete', methods=['POST'])
def admin_delete_regulation(id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    regulation = Regulation.query.get_or_404(id)
    db.session.delete(regulation)
    db.session.commit()
    flash('Regulation deleted successfully!', 'success')
    return redirect(url_for('admin_manage_regulations'))

@app.route('/admin/updates')
def admin_manage_updates():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    updates = Update.query.order_by(Update.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/manage_updates.html', updates=updates)

@app.route('/admin/updates/new', methods=['GET', 'POST'])
def admin_new_update():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    form = UpdateForm()
    if form.validate_on_submit():
        update = Update(
            title=form.title.data,
            description=form.description.data,
            jurisdiction_affected=form.jurisdiction_affected.data,
            update_date=form.update_date.data,
            status=form.status.data
        )
        db.session.add(update)
        db.session.commit()
        flash('Update added successfully!', 'success')
        return redirect(url_for('admin_manage_updates'))
    
    return render_template('admin/edit_update.html', form=form, title='Add New Update')

@app.route('/admin/updates/<int:id>/edit', methods=['GET', 'POST'])
def admin_edit_update(id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    update = Update.query.get_or_404(id)
    form = UpdateForm(obj=update)
    
    if form.validate_on_submit():
        update.title = form.title.data
        update.description = form.description.data
        update.jurisdiction_affected = form.jurisdiction_affected.data
        update.update_date = form.update_date.data
        update.status = form.status.data
        db.session.commit()
        flash('Update modified successfully!', 'success')
        return redirect(url_for('admin_manage_updates'))
    
    return render_template('admin/edit_update.html', form=form, update=update, title='Edit Update')

@app.route('/admin/updates/<int:id>/delete', methods=['POST'])
def admin_delete_update(id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    update = Update.query.get_or_404(id)
    db.session.delete(update)
    db.session.commit()
    flash('Update deleted successfully!', 'success')
    return redirect(url_for('admin_manage_updates'))
