from flask import render_template, request, redirect, url_for, flash, session, jsonify, make_response, current_app, Blueprint
from models import db, Regulation, Update, AdminUser, SavedSearch, SearchSuggestion, UserUpdateInteraction, UpdateReminder, NotificationPreference
from forms import LoginForm, RegulationForm, UpdateForm
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import logging
import json
import csv
import io
from sqlalchemy import or_, and_, func

# Create a blueprint for routes
bp = Blueprint('main', __name__)

# Helper function to check admin authentication
def is_admin_logged_in():
    return 'admin_id' in session

# Public Routes
@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/regulations')
def regulations():
    # Get filter parameters
    jurisdiction_filter = request.args.get('jurisdiction', '').strip()
    location_filter = request.args.get('location', '').strip()
    category_filter = request.args.get('category', '').strip()
    search_query = request.args.get('search', '').strip()
    
    # Build query
    query = Regulation.query
    
    if jurisdiction_filter:
        query = query.filter(Regulation.jurisdiction_level == jurisdiction_filter)
    
    if location_filter:
        query = query.filter(Regulation.location.ilike(f'%{location_filter}%'))
    
    if category_filter:
        query = query.filter(Regulation.category == category_filter)
    
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
    all_categories = db.session.query(Regulation.category).distinct().all()
    
    # Get saved searches for quick filters
    saved_searches = SavedSearch.query.filter_by(is_public=True).all()
    
    return render_template('regulations.html', 
                         regulations=regulations,
                         jurisdictions=[j[0] for j in all_jurisdictions],
                         locations=[l[0] for l in all_locations],
                         categories=[c[0] for c in all_categories],
                         current_jurisdiction=jurisdiction_filter,
                         current_location=location_filter,
                         current_category=category_filter,
                         current_search=search_query,
                         saved_searches=saved_searches)

@bp.route('/api/search/advanced')
def advanced_search():
    """Advanced search API endpoint with multiple criteria"""
    try:
        # Get search parameters
        search_query = request.args.get('q', '').strip()
        categories = request.args.getlist('categories[]')
        compliance_levels = request.args.getlist('compliance_levels[]')
        property_types = request.args.getlist('property_types[]')
        locations = request.args.getlist('locations[]')
        jurisdictions = request.args.getlist('jurisdictions[]')
        
        # Date range filtering
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        date_range_days = request.args.get('date_range_days')
        
        # Build query
        query = Regulation.query
        
        # Text search across multiple fields
        if search_query:
            search_conditions = []
            search_terms = search_query.split()
            
            for term in search_terms:
                term_pattern = f'%{term}%'
                search_conditions.append(
                    or_(
                        Regulation.title.ilike(term_pattern),
                        Regulation.key_requirements.ilike(term_pattern),
                        Regulation.keywords.ilike(term_pattern),
                        Regulation.location.ilike(term_pattern)
                    )
                )
            
            if search_conditions:
                query = query.filter(and_(*search_conditions))
        
        # Category filtering
        if categories:
            query = query.filter(Regulation.category.in_(categories))
        
        # Compliance level filtering
        if compliance_levels:
            query = query.filter(Regulation.compliance_level.in_(compliance_levels))
        
        # Property type filtering
        if property_types:
            if len(property_types) == 1 and property_types[0] != 'Both':
                query = query.filter(
                    or_(
                        Regulation.property_type == property_types[0],
                        Regulation.property_type == 'Both'
                    )
                )
            elif 'Both' not in property_types:
                query = query.filter(Regulation.property_type.in_(property_types))
        
        # Location filtering
        if locations:
            location_conditions = [Regulation.location.ilike(f'%{loc}%') for loc in locations]
            query = query.filter(or_(*location_conditions))
        
        # Jurisdiction filtering
        if jurisdictions:
            query = query.filter(Regulation.jurisdiction_level.in_(jurisdictions))
        
        # Date range filtering
        if date_from and date_to:
            query = query.filter(
                Regulation.last_updated.between(date_from, date_to)
            )
        elif date_range_days:
            cutoff_date = datetime.now().date() - timedelta(days=int(date_range_days))
            query = query.filter(Regulation.last_updated >= cutoff_date)
        
        # Execute query and get results
        results = query.order_by(Regulation.last_updated.desc()).all()
        
        # Convert to dictionaries for JSON response
        regulations_data = [reg.to_dict() for reg in results]
        
        # Update search suggestions
        if search_query:
            update_search_suggestions(search_query, results)
        
        return jsonify({
            'success': True,
            'regulations': regulations_data,
            'count': len(regulations_data),
            'query_info': {
                'search_query': search_query,
                'categories': categories,
                'compliance_levels': compliance_levels,
                'property_types': property_types,
                'locations': locations,
                'jurisdictions': jurisdictions
            }
        })
        
    except Exception as e:
        logging.error(f"Advanced search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Search failed. Please try again.',
            'details': str(e)
        }), 500

@bp.route('/api/search/suggestions')
def search_suggestions():
    """Get search suggestions based on user input"""
    query = request.args.get('q', '').strip().lower()
    
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    suggestions = []
    
    # Get suggestions from regulation titles
    title_matches = db.session.query(Regulation.title).filter(
        Regulation.title.ilike(f'%{query}%')
    ).distinct().limit(5).all()
    
    for match in title_matches:
        suggestions.append({
            'text': match[0],
            'type': 'title',
            'category': 'Regulation Titles'
        })
    
    # Get suggestions from locations
    location_matches = db.session.query(Regulation.location).filter(
        Regulation.location.ilike(f'%{query}%')
    ).distinct().limit(5).all()
    
    for match in location_matches:
        suggestions.append({
            'text': match[0],
            'type': 'location',
            'category': 'Locations'
        })
    
    # Get suggestions from categories
    category_matches = db.session.query(Regulation.category).filter(
        Regulation.category.ilike(f'%{query}%')
    ).distinct().limit(5).all()
    
    for match in category_matches:
        suggestions.append({
            'text': match[0],
            'type': 'category',
            'category': 'Categories'
        })
    
    # Get suggestions from keywords
    keyword_matches = db.session.query(Regulation.keywords).filter(
        Regulation.keywords.ilike(f'%{query}%')
    ).distinct().limit(3).all()
    
    for match in keyword_matches:
        if match[0]:
            keywords = [k.strip() for k in match[0].split(',')]
            for keyword in keywords:
                if query in keyword.lower():
                    suggestions.append({
                        'text': keyword,
                        'type': 'keyword',
                        'category': 'Keywords'
                    })
    
    # Remove duplicates and limit results
    seen = set()
    unique_suggestions = []
    for suggestion in suggestions:
        key = (suggestion['text'], suggestion['type'])
        if key not in seen:
            seen.add(key)
            unique_suggestions.append(suggestion)
            if len(unique_suggestions) >= 10:
                break
    
    return jsonify({'suggestions': unique_suggestions})

@bp.route('/api/search/save', methods=['POST'])
def save_search():
    """Save a search for later use"""
    try:
        data = request.get_json()
        
        # Check if search name already exists
        existing = SavedSearch.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'A search with this name already exists'
            }), 400
        
        # Create new saved search
        saved_search = SavedSearch(
            name=data['name'],
            description=data.get('description', ''),
            is_public=data.get('is_public', False)
        )
        saved_search.set_search_criteria(data['criteria'])
        
        db.session.add(saved_search)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Search saved successfully',
            'search_id': saved_search.id
        })
        
    except Exception as e:
        logging.error(f"Save search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to save search'
        }), 500

@bp.route('/api/search/saved')
def get_saved_searches():
    """Get all saved searches"""
    searches = SavedSearch.query.filter_by(is_public=True).order_by(
        SavedSearch.use_count.desc()
    ).all()
    
    search_data = []
    for search in searches:
        search_data.append({
            'id': search.id,
            'name': search.name,
            'description': search.description,
            'criteria': search.get_search_criteria(),
            'use_count': search.use_count,
            'last_used': search.last_used.isoformat() if search.last_used else None
        })
    
    return jsonify({'saved_searches': search_data})

@bp.route('/api/search/saved/<int:search_id>/use', methods=['POST'])
def use_saved_search(search_id):
    """Use a saved search and update its usage count"""
    try:
        saved_search = SavedSearch.query.get_or_404(search_id)
        
        # Update usage statistics
        saved_search.use_count += 1
        saved_search.last_used = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'criteria': saved_search.get_search_criteria()
        })
        
    except Exception as e:
        logging.error(f"Use saved search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load saved search'
        }), 500

@bp.route('/api/export/csv')
def export_csv():
    """Export filtered regulations to CSV"""
    try:
        # Get the same filters as the regulations route
        jurisdiction_filter = request.args.get('jurisdiction', '').strip()
        location_filter = request.args.get('location', '').strip()
        category_filter = request.args.get('category', '').strip()
        search_query = request.args.get('search', '').strip()
        
        # Build the same query as regulations route
        query = Regulation.query
        
        if jurisdiction_filter:
            query = query.filter(Regulation.jurisdiction_level == jurisdiction_filter)
        
        if location_filter:
            query = query.filter(Regulation.location.ilike(f'%{location_filter}%'))
        
        if category_filter:
            query = query.filter(Regulation.category == category_filter)
        
        if search_query:
            query = query.filter(
                db.or_(
                    Regulation.title.ilike(f'%{search_query}%'),
                    Regulation.key_requirements.ilike(f'%{search_query}%')
                )
            )
        
        regulations = query.order_by(Regulation.jurisdiction_level, Regulation.location).all()
        
        # Create CSV output
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Jurisdiction Level', 'Location', 'Title', 
            'Category', 'Compliance Level', 'Property Type',
            'Key Requirements', 'Last Updated', 'Keywords'
        ])
        
        # Write data
        for reg in regulations:
            writer.writerow([
                reg.id,
                reg.jurisdiction_level,
                reg.location,
                reg.title,
                reg.category,
                reg.compliance_level,
                reg.property_type,
                reg.key_requirements,
                reg.last_updated.strftime('%Y-%m-%d') if reg.last_updated else '',
                reg.keywords or ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=regulations_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response.headers['Content-type'] = 'text/csv'
        
        return response
        
    except Exception as e:
        logging.error(f"CSV export error: {str(e)}")
        flash('Export failed. Please try again.', 'danger')
        return redirect(url_for('main.regulations'))

@bp.route('/api/export/pdf')
def export_pdf():
    """Export filtered regulations to PDF"""
    try:
        # Get the same filters as the regulations route
        jurisdiction_filter = request.args.get('jurisdiction', '').strip()
        location_filter = request.args.get('location', '').strip()
        category_filter = request.args.get('category', '').strip()
        search_query = request.args.get('search', '').strip()
        
        # Build the same query as regulations route
        query = Regulation.query
        
        if jurisdiction_filter:
            query = query.filter(Regulation.jurisdiction_level == jurisdiction_filter)
        
        if location_filter:
            query = query.filter(Regulation.location.ilike(f'%{location_filter}%'))
        
        if category_filter:
            query = query.filter(Regulation.category == category_filter)
        
        if search_query:
            query = query.filter(
                db.or_(
                    Regulation.title.ilike(f'%{search_query}%'),
                    Regulation.key_requirements.ilike(f'%{search_query}%')
                )
            )
        
        regulations = query.order_by(Regulation.jurisdiction_level, Regulation.location).all()
        
        # Generate HTML content for PDF
        html_content = generate_pdf_html(regulations, {
            'jurisdiction': jurisdiction_filter,
            'location': location_filter,
            'category': category_filter,
            'search': search_query
        })
        
        # Create PDF using simple HTML to PDF conversion
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        response.headers['Content-Disposition'] = f'inline; filename=regulations_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        
        return response
        
    except Exception as e:
        logging.error(f"PDF export error: {str(e)}")
        flash('PDF export failed. Please try again.', 'danger')
        return redirect(url_for('main.regulations'))

def generate_pdf_html(regulations, filters):
    """Generate HTML content for PDF export"""
    filter_summary = []
    if filters['jurisdiction']:
        filter_summary.append(f"Jurisdiction: {filters['jurisdiction']}")
    if filters['location']:
        filter_summary.append(f"Location: {filters['location']}")
    if filters['category']:
        filter_summary.append(f"Category: {filters['category']}")
    if filters['search']:
        filter_summary.append(f"Search: {filters['search']}")
    
    filter_text = " | ".join(filter_summary) if filter_summary else "All Regulations"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>STR Compliance Report - {datetime.now().strftime('%Y-%m-%d')}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 40px;
                color: #333;
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #0d6efd;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #0d6efd;
                font-size: 28px;
                margin: 0 0 10px 0;
            }}
            .header .subtitle {{
                color: #666;
                font-size: 16px;
                margin: 5px 0;
            }}
            .filter-info {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 25px;
                border-left: 4px solid #0d6efd;
            }}
            .regulation {{
                page-break-inside: avoid;
                margin-bottom: 25px;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                overflow: hidden;
            }}
            .regulation-header {{
                background: #0d6efd;
                color: white;
                padding: 15px;
                font-weight: bold;
                font-size: 18px;
            }}
            .regulation-meta {{
                background: #f8f9fa;
                padding: 10px 15px;
                border-bottom: 1px solid #dee2e6;
                font-size: 14px;
            }}
            .regulation-meta span {{
                display: inline-block;
                margin-right: 20px;
                color: #666;
            }}
            .category-badge {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                color: white;
                margin-left: 10px;
            }}
            .category-legal {{ background: #dc3545; }}
            .category-licensing {{ background: #fd7e14; }}
            .category-taxes {{ background: #0d6efd; }}
            .category-zoning {{ background: #6f42c1; }}
            .category-occupancy {{ background: #6c757d; }}
            .category-registration {{ background: #198754; }}
            .category-discrimination {{ background: #dc3545; }}
            .jurisdiction-badge {{
                display: inline-block;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
                color: white;
                text-transform: uppercase;
            }}
            .jurisdiction-national {{ background: #dc3545; }}
            .jurisdiction-state {{ background: #fd7e14; }}
            .jurisdiction-local {{ background: #20c997; }}
            .regulation-content {{
                padding: 15px;
            }}
            .requirements {{
                background: #fff;
                padding: 15px;
                border-radius: 6px;
                margin-top: 10px;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
            @media print {{
                body {{ margin: 20px; }}
                .regulation {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏛️ Short-Term Rental Compliance Report</h1>
            <div class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
            <div class="subtitle">Total Regulations: {len(regulations)}</div>
        </div>
        
        <div class="filter-info">
            <strong>Applied Filters:</strong> {filter_text}
        </div>
    """
    
    for regulation in regulations:
        category_class = f"category-{regulation.category.lower().replace(' ', '-')}"
        jurisdiction_class = f"jurisdiction-{regulation.jurisdiction_level.lower()}"
        
        html += f"""
        <div class="regulation">
            <div class="regulation-header">
                {regulation.title}
            </div>
            <div class="regulation-meta">
                <span><strong>Location:</strong> {regulation.location}</span>
                <span><strong>Jurisdiction:</strong> 
                    <span class="jurisdiction-badge {jurisdiction_class}">
                        {regulation.jurisdiction_level}
                    </span>
                </span>
                <span><strong>Category:</strong>
                    <span class="category-badge {category_class}">
                        {regulation.category}
                    </span>
                </span>
                <span><strong>Last Updated:</strong> {regulation.last_updated.strftime('%Y-%m-%d')}</span>
                <span><strong>Compliance Level:</strong> {getattr(regulation, 'compliance_level', 'Mandatory')}</span>
            </div>
            <div class="regulation-content">
                <div class="requirements">
                    <strong>Key Requirements:</strong><br>
                    {regulation.key_requirements.replace(chr(10), '<br>')}
                </div>
            </div>
        </div>
        """
    
    html += f"""
        <div class="footer">
            <p>This report was generated by the STR Compliance Toolkit.</p>
            <p>For the most current information, please verify with official government sources.</p>
            <p>Report generated from database last updated on {datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
    </body>
    </html>
    """
    
    return html

def update_search_suggestions(query, results):
    """Update search suggestions based on search query and results"""
    try:
        # Extract individual terms
        terms = query.lower().split()
        
        for term in terms:
            if len(term) >= 3:  # Only store terms with 3+ characters
                suggestion = SearchSuggestion.query.filter_by(
                    suggestion_text=term,
                    suggestion_type='search_term'
                ).first()
                
                if suggestion:
                    suggestion.frequency += 1
                    suggestion.last_used = datetime.utcnow()
                else:
                    suggestion = SearchSuggestion(
                        suggestion_text=term,
                        suggestion_type='search_term',
                        frequency=1
                    )
                    db.session.add(suggestion)
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error updating search suggestions: {str(e)}")

@bp.route('/regulations/<int:id>')
def regulation_detail(id):
    regulation = Regulation.query.get_or_404(id)
    
    # Get detailed content based on regulation type and location
    detailed_content = get_regulation_detailed_content(regulation)
    
    # Get related regulations (same jurisdiction level or location)
    related_regulations = Regulation.query.filter(
        db.or_(
            db.and_(Regulation.jurisdiction_level == regulation.jurisdiction_level, Regulation.id != regulation.id),
            db.and_(Regulation.location == regulation.location, Regulation.id != regulation.id)
        )
    ).limit(5).all()
    
    return render_template('regulation_detail.html', 
                         regulation=regulation, 
                         detailed_content=detailed_content,
                         related_regulations=related_regulations)

def get_regulation_detailed_content(regulation):
    """Generate detailed content based on regulation type and location"""
    content = {
        'overview': '',
        'requirements': [],
        'process_details': [],
        'contact_info': {},
        'official_links': []
    }
    
    # National regulations
    if regulation.jurisdiction_level == 'National':
        if 'Fair Housing' in regulation.title:
            content['overview'] = "The Fair Housing Act prohibits discrimination in housing-related activities, including short-term rentals. This federal law ensures equal access to housing regardless of protected characteristics."
            content['requirements'] = [
                "Prohibition of discriminatory practices in advertising, screening, and guest selection",
                "Equal treatment of all guests regardless of race, color, religion, sex, national origin, familial status, or disability",
                "Reasonable accommodations for guests with disabilities",
                "Accessible advertising language that doesn't indicate preferences or limitations",
                "Non-discriminatory house rules and policies",
                "Equal enforcement of rental terms and conditions"
            ]
            content['process_details'] = [
                "Review all marketing materials for discriminatory language",
                "Implement standardized guest screening criteria",
                "Train staff on fair housing requirements",
                "Document all guest interactions and decisions",
                "Establish clear complaint resolution procedures"
            ]
            content['contact_info'] = {
                'agency': 'U.S. Department of Housing and Urban Development (HUD)',
                'phone': '1-800-669-9777',
                'website': 'https://www.hud.gov/fairhousing',
                'email': 'fairhousing@hud.gov'
            }
            content['official_links'] = [
                'https://www.hud.gov/program_offices/fair_housing_equal_opp/fair_housing_act_overview',
                'https://www.justice.gov/crt/fair-housing-act-2'
            ]
        elif 'ADA' in regulation.title:
            content['overview'] = "The Americans with Disabilities Act requires places of public accommodation to be accessible to individuals with disabilities. Short-term rentals may need to comply with ADA requirements."
            content['requirements'] = [
                "Physical accessibility features for guests with mobility impairments",
                "Reasonable modifications to policies for service animals",
                "Effective communication with guests who have hearing or vision impairments",
                "Auxiliary aids and services when needed",
                "Non-discriminatory treatment of guests with disabilities",
                "Accessible parking spaces where applicable"
            ]
            content['process_details'] = [
                "Conduct accessibility assessment of property",
                "Install necessary accessibility features (ramps, grab bars, etc.)",
                "Develop service animal policy",
                "Train staff on disability accommodations",
                "Maintain accessible communication methods"
            ]
            content['contact_info'] = {
                'agency': 'U.S. Department of Justice - Civil Rights Division',
                'phone': '1-800-514-0301',
                'website': 'https://www.ada.gov',
                'email': 'ada.information@usdoj.gov'
            }
            content['official_links'] = [
                'https://www.ada.gov/business/',
                'https://www.ada.gov/regs2010/titleIII_2010/titleIII_2010_regulations.htm'
            ]
        elif 'Tax' in regulation.title:
            content['overview'] = "Federal tax requirements for short-term rental operators include income reporting, deduction claiming, and compliance with IRS regulations for rental property."
            content['requirements'] = [
                "Report all rental income on federal tax returns",
                "File Schedule E for rental property income and expenses",
                "Comply with 14-day rule for personal use vs. rental use",
                "Maintain detailed records of income and expenses",
                "Pay estimated quarterly taxes if applicable",
                "Issue 1099s to service providers when required"
            ]
            content['process_details'] = [
                "Set up bookkeeping system for rental income/expenses",
                "Track personal vs. rental use days",
                "Keep receipts for all deductible expenses",
                "Calculate depreciation for rental property",
                "File appropriate tax forms by deadlines",
                "Consult tax professional for complex situations"
            ]
            content['contact_info'] = {
                'agency': 'Internal Revenue Service (IRS)',
                'phone': '1-800-829-1040',
                'website': 'https://www.irs.gov',
                'email': 'Contact via website'
            }
            content['official_links'] = [
                'https://www.irs.gov/businesses/small-businesses-self-employed/tips-on-rental-real-estate-income-deductions-and-recordkeeping',
                'https://www.irs.gov/forms-pubs/about-schedule-e-form-1040'
            ]
    
    # State regulations (Florida)
    elif regulation.jurisdiction_level == 'State' and regulation.location == 'Florida':
        if 'Licensing' in regulation.title:
            content['overview'] = "Florida requires short-term rental operators to obtain proper business licenses and comply with state licensing requirements."
            content['requirements'] = [
                "Obtain Florida business license (if applicable)",
                "Register with Florida Department of Revenue for tax purposes",
                "Comply with local licensing requirements",
                "Maintain current license status",
                "Display license information when required",
                "Renew licenses according to schedule"
            ]
            content['process_details'] = [
                "Determine if business license is required for your operation",
                "Complete application with required documentation",
                "Pay applicable fees and taxes",
                "Submit to background check if required",
                "Receive and display license",
                "Set up renewal reminders"
            ]
            content['contact_info'] = {
                'agency': 'Florida Department of Business and Professional Regulation',
                'phone': '850-487-1395',
                'website': 'https://www.myfloridalicense.com',
                'email': 'customer.contact@myfloridalicense.com'
            }
        elif 'Tax' in regulation.title:
            content['overview'] = "Florida imposes sales tax and tourist development tax on short-term rental accommodations, requiring registration and regular remittance."
            content['requirements'] = [
                "Register for Florida sales tax permit",
                "Collect 6% state sales tax on rental charges",
                "Collect applicable tourist development tax (varies by county)",
                "File monthly sales tax returns",
                "Remit taxes by the 20th of following month",
                "Maintain detailed tax records for audit purposes"
            ]
            content['process_details'] = [
                "Apply for sales tax certificate online",
                "Determine local tourist development tax rates",
                "Set up tax collection in booking system",
                "File DR-15 sales tax returns monthly",
                "Pay taxes electronically when possible",
                "Keep records for minimum 3 years"
            ]
            content['contact_info'] = {
                'agency': 'Florida Department of Revenue',
                'phone': '850-488-6800',
                'website': 'https://floridarevenue.com',
                'email': 'DORCustomerService@floridarevenue.com'
            }
        elif 'Insurance' in regulation.title:
            content['overview'] = "Florida requires short-term rental operators to maintain adequate insurance coverage to protect against liability and property damage."
            content['requirements'] = [
                "Commercial general liability insurance (minimum $1 million per occurrence)",
                "Property insurance covering short-term rental use",
                "Workers compensation if employees are hired",
                "Umbrella policy for additional protection (recommended)",
                "Insurance must cover short-term rental activities specifically",
                "Proof of insurance may be required for licensing"
            ]
            content['process_details'] = [
                "Notify current insurance company of short-term rental use",
                "Shop for commercial short-term rental policies",
                "Review coverage limits and exclusions",
                "Obtain certificates of insurance",
                "Update coverage annually or as needed",
                "Maintain continuous coverage"
            ]
            content['contact_info'] = {
                'agency': 'Florida Office of Insurance Regulation',
                'phone': '850-413-3089',
                'website': 'https://www.floir.com',
                'email': 'Ask.OIR@floir.com'
            }
    
    # Local regulations
    elif regulation.jurisdiction_level == 'Local':
        location = regulation.location
        
        # Common local regulation content structure
        content['overview'] = f"Local regulations in {location} govern short-term rental operations through permitting, zoning compliance, and operational requirements."
        
        if 'Permit' in regulation.title:
            content['requirements'] = [
                f"Obtain short-term rental permit from {location}",
                "Submit completed application with required documentation",
                "Pay applicable permit fees and taxes",
                "Pass safety and zoning inspections",
                "Comply with property maintenance standards",
                "Renew permit annually or as required"
            ]
            content['process_details'] = [
                "Check zoning eligibility for short-term rentals",
                "Gather required documents (deed, insurance, etc.)",
                "Schedule pre-application meeting if available",
                "Submit application with all required materials",
                "Coordinate inspections with city/county staff",
                "Receive permit and post as required"
            ]
        elif 'Zoning' in regulation.title:
            content['requirements'] = [
                f"Verify property is in zone allowing short-term rentals in {location}",
                "Comply with density and spacing requirements",
                "Meet setback and parking requirements",
                "Adhere to occupancy limitations",
                "Follow noise and disturbance ordinances",
                "Maintain property according to zoning standards"
            ]
        elif 'Occupancy' in regulation.title:
            content['requirements'] = [
                f"Adhere to maximum occupancy limits set by {location}",
                "Provide adequate parking for maximum occupancy",
                "Maintain noise levels within acceptable limits",
                "Implement quiet hours enforcement",
                "Post house rules regarding occupancy and behavior",
                "Respond promptly to neighbor complaints"
            ]
        elif 'Registration' in regulation.title:
            content['requirements'] = [
                f"Register short-term rental with {location} authorities",
                "Provide property owner and operator information",
                "Submit proof of insurance and business license",
                "Pay registration fees and taxes",
                "Update registration when ownership changes",
                "Maintain current contact information on file"
            ]
        
        # Default contact info for local jurisdictions
        content['contact_info'] = {
            'agency': f'{location} Planning/Zoning Department',
            'phone': 'Contact local city/county offices',
            'website': f'Official {location} government website',
            'email': 'Contact via local government website'
        }
    
    return content

@bp.route('/updates')
def updates():
    # Get filter parameters
    status_filter = request.args.get('status', '')
    jurisdiction_filter = request.args.get('jurisdiction', '')
    category_filter = request.args.get('category', '')
    impact_filter = request.args.get('impact', '')
    search_query = request.args.get('search', '')
    
    # Build query
    query = Update.query
    
    if status_filter:
        query = query.filter(Update.status == status_filter)
    
    if jurisdiction_filter:
        query = query.filter(Update.jurisdiction_affected.ilike(f'%{jurisdiction_filter}%'))
    
    if category_filter:
        query = query.filter(Update.category == category_filter)
    
    if impact_filter:
        query = query.filter(Update.impact_level == impact_filter)
    
    if search_query:
        search_terms = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Update.title.ilike(search_terms),
                Update.description.ilike(search_terms),
                Update.tags.ilike(search_terms),
                Update.jurisdiction_affected.ilike(search_terms)
            )
        )
    
    # Order by priority (1=high, 2=medium, 3=low) then by date
    updates = query.order_by(Update.priority.asc(), Update.update_date.desc()).all()
    
    # Get filter options
    statuses = ['Recent', 'Upcoming', 'Proposed']
    jurisdictions = [u.jurisdiction_affected for u in Update.query.distinct(Update.jurisdiction_affected).all()]
    categories = ['Regulatory Changes', 'Tax Updates', 'Licensing Changes', 'Court Decisions', 'Industry News']
    impact_levels = ['High', 'Medium', 'Low']
    
    # Get user session for interactions
    user_session = session.get('user_id', request.remote_addr)
    
    # Get user interactions for these updates
    update_interactions = {}
    if updates:
        interactions = UserUpdateInteraction.query.filter(
            UserUpdateInteraction.update_id.in_([u.id for u in updates]),
            UserUpdateInteraction.user_session == user_session
        ).all()
        
        for interaction in interactions:
            update_interactions[interaction.update_id] = interaction
    
    return render_template('updates.html', 
                         updates=updates, 
                         statuses=statuses,
                         jurisdictions=jurisdictions,
                         categories=categories,
                         impact_levels=impact_levels,
                         current_status=status_filter,
                         current_jurisdiction=jurisdiction_filter,
                         current_category=category_filter,
                         current_impact=impact_filter,
                         current_search=search_query,
                         update_interactions=update_interactions)

@bp.route('/api/updates/<int:update_id>/mark-read', methods=['POST'])
def mark_update_read(update_id):
    """Mark an update as read"""
    try:
        user_session = session.get('user_id', request.remote_addr)
        
        interaction = UserUpdateInteraction.query.filter_by(
            update_id=update_id,
            user_session=user_session
        ).first()
        
        if not interaction:
            interaction = UserUpdateInteraction(
                update_id=update_id,
                user_session=user_session,
                is_read=True,
                read_at=datetime.utcnow()
            )
            db.session.add(interaction)
        else:
            interaction.is_read = True
            interaction.read_at = datetime.utcnow()
            interaction.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Update marked as read'
        })
        
    except Exception as e:
        logging.error(f"Error marking update as read: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to mark update as read'
        }), 500

@bp.route('/api/updates/<int:update_id>/bookmark', methods=['POST'])
def bookmark_update(update_id):
    """Toggle bookmark status for an update"""
    try:
        user_session = session.get('user_id', request.remote_addr)
        
        interaction = UserUpdateInteraction.query.filter_by(
            update_id=update_id,
            user_session=user_session
        ).first()
        
        if not interaction:
            interaction = UserUpdateInteraction(
                update_id=update_id,
                user_session=user_session,
                is_bookmarked=True,
                bookmarked_at=datetime.utcnow()
            )
            db.session.add(interaction)
            bookmarked = True
        else:
            interaction.is_bookmarked = not interaction.is_bookmarked
            if interaction.is_bookmarked:
                interaction.bookmarked_at = datetime.utcnow()
            interaction.updated_at = datetime.utcnow()
            bookmarked = interaction.is_bookmarked
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'bookmarked': bookmarked,
            'message': 'Bookmark updated'
        })
        
    except Exception as e:
        logging.error(f"Error updating bookmark: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update bookmark'
        }), 500

@bp.route('/api/updates/<int:update_id>/reminder', methods=['POST'])
def set_update_reminder(update_id):
    """Set a reminder for an update"""
    try:
        data = request.get_json()
        reminder_date = datetime.strptime(data['reminder_date'], '%Y-%m-%d').date()
        reminder_type = data.get('reminder_type', 'custom')
        email = data.get('email', '')
        notes = data.get('notes', '')
        
        user_session = session.get('user_id', request.remote_addr)
        
        # Check if reminder already exists
        existing_reminder = UpdateReminder.query.filter_by(
            update_id=update_id,
            user_session=user_session,
            reminder_date=reminder_date
        ).first()
        
        if existing_reminder:
            return jsonify({
                'success': False,
                'error': 'Reminder already exists for this date'
            }), 400
        
        reminder = UpdateReminder(
            update_id=update_id,
            user_session=user_session,
            reminder_date=reminder_date,
            reminder_type=reminder_type,
            email=email,
            notes=notes
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reminder set successfully'
        })
        
    except Exception as e:
        logging.error(f"Error setting reminder: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to set reminder'
        }), 500

@bp.route('/api/updates/<int:update_id>/share', methods=['POST'])
def share_update(update_id):
    """Generate shareable content for an update"""
    try:
        update = Update.query.get_or_404(update_id)
        data = request.get_json()
        email = data.get('email', '')
        message = data.get('message', '')
        
        # Generate share content
        share_content = {
            'subject': f'STR Update: {update.title}',
            'body': f"""
Industry Update Alert

Title: {update.title}
Category: {update.category}
Impact Level: {update.impact_level}
Jurisdiction: {update.jurisdiction_affected}
Status: {update.status}

Description:
{update.description}

""",
            'url': f"{request.host_url}updates#{update.id}"
        }
        
        if update.action_required:
            share_content['body'] += f"""
ACTION REQUIRED:
{update.action_description}

"""
        
        if update.effective_date:
            share_content['body'] += f"Effective Date: {update.effective_date.strftime('%B %d, %Y')}\n"
        
        if update.deadline_date:
            share_content['body'] += f"Deadline: {update.deadline_date.strftime('%B %d, %Y')}\n"
        
        share_content['body'] += f"""
{message}

---
This update was shared from the STR Compliance Toolkit.
For more information, visit: {request.host_url}
"""
        
        # If email provided, you could send actual email here
        # For now, just return the shareable content
        
        return jsonify({
            'success': True,
            'share_content': share_content
        })
        
    except Exception as e:
        logging.error(f"Error generating share content: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate share content'
        }), 500

@bp.route('/api/updates/search')
def search_updates():
    """Advanced search within updates"""
    try:
        query_text = request.args.get('q', '')
        category = request.args.get('category', '')
        impact = request.args.get('impact', '')
        status = request.args.get('status', '')
        jurisdiction = request.args.get('jurisdiction', '')
        has_deadline = request.args.get('has_deadline', '')
        action_required = request.args.get('action_required', '')
        
        query = Update.query
        
        if query_text:
            search_terms = f'%{query_text}%'
            query = query.filter(
                db.or_(
                    Update.title.ilike(search_terms),
                    Update.description.ilike(search_terms),
                    Update.tags.ilike(search_terms),
                    Update.action_description.ilike(search_terms)
                )
            )
        
        if category:
            query = query.filter(Update.category == category)
        
        if impact:
            query = query.filter(Update.impact_level == impact)
        
        if status:
            query = query.filter(Update.status == status)
        
        if jurisdiction:
            query = query.filter(Update.jurisdiction_affected.ilike(f'%{jurisdiction}%'))
        
        if has_deadline == 'true':
            query = query.filter(Update.deadline_date.isnot(None))
        elif has_deadline == 'false':
            query = query.filter(Update.deadline_date.is_(None))
        
        if action_required == 'true':
            query = query.filter(Update.action_required == True)
        elif action_required == 'false':
            query = query.filter(Update.action_required == False)
        
        updates = query.order_by(Update.priority.asc(), Update.update_date.desc()).limit(50).all()
        
        results = []
        for update in updates:
            result = update.to_dict()
            result['related_regulations'] = [reg.to_dict() for reg in update.get_related_regulations()]
            results.append(result)
        
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

@bp.route('/api/updates/bookmarked')
def get_bookmarked_updates():
    """Get user's bookmarked updates"""
    try:
        user_session = session.get('user_id', request.remote_addr)
        
        bookmarked_interactions = UserUpdateInteraction.query.filter_by(
            user_session=user_session,
            is_bookmarked=True
        ).all()
        
        update_ids = [interaction.update_id for interaction in bookmarked_interactions]
        updates = Update.query.filter(Update.id.in_(update_ids)).order_by(Update.priority.asc()).all()
        
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

@bp.route('/api/updates/reminders')
def get_user_reminders():
    """Get user's update reminders"""
    try:
        user_session = session.get('user_id', request.remote_addr)
        
        reminders = UpdateReminder.query.filter_by(
            user_session=user_session,
            is_sent=False
        ).order_by(UpdateReminder.reminder_date.asc()).all()
        
        results = []
        for reminder in reminders:
            result = {
                'id': reminder.id,
                'update_id': reminder.update_id,
                'update_title': reminder.update.title,
                'reminder_date': reminder.reminder_date.isoformat(),
                'reminder_type': reminder.reminder_type,
                'notes': reminder.notes
            }
            results.append(result)
        
        return jsonify({
            'success': True,
            'reminders': results,
            'count': len(results)
        })
        
    except Exception as e:
        logging.error(f"Error getting reminders: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get reminders'
        }), 500

@bp.route('/api/notifications/preferences', methods=['GET', 'POST'])
def notification_preferences():
    """Get or update notification preferences"""
    try:
        user_session = session.get('user_id', request.remote_addr)
        
        if request.method == 'GET':
            prefs = NotificationPreference.query.filter_by(user_session=user_session).first()
            
            if not prefs:
                # Create default preferences
                prefs = NotificationPreference(
                    user_session=user_session,
                    notify_new_updates=True,
                    notify_deadlines=True,
                    notify_weekly_digest=False
                )
                db.session.add(prefs)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'preferences': {
                    'email': prefs.email,
                    'locations': prefs.locations.split(',') if prefs.locations else [],
                    'categories': prefs.categories.split(',') if prefs.categories else [],
                    'impact_levels': prefs.impact_levels.split(',') if prefs.impact_levels else [],
                    'notify_new_updates': prefs.notify_new_updates,
                    'notify_deadlines': prefs.notify_deadlines,
                    'notify_weekly_digest': prefs.notify_weekly_digest
                }
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            
            prefs = NotificationPreference.query.filter_by(user_session=user_session).first()
            if not prefs:
                prefs = NotificationPreference(user_session=user_session)
                db.session.add(prefs)
            
            # Update preferences
            prefs.email = data.get('email', '')
            prefs.locations = ','.join(data.get('locations', []))
            prefs.categories = ','.join(data.get('categories', []))
            prefs.impact_levels = ','.join(data.get('impact_levels', []))
            prefs.notify_new_updates = data.get('notify_new_updates', True)
            prefs.notify_deadlines = data.get('notify_deadlines', True)
            prefs.notify_weekly_digest = data.get('notify_weekly_digest', False)
            prefs.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Notification preferences updated'
            })
            
    except Exception as e:
        logging.error(f"Error managing notification preferences: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to manage notification preferences'
        }), 500

@bp.route('/api/notifications/alerts')
def get_notification_alerts():
    """Get notifications for urgent updates and deadlines"""
    try:
        user_session = session.get('user_id', request.remote_addr)
        
        # Get user preferences
        prefs = NotificationPreference.query.filter_by(user_session=user_session).first()
        
        alerts = []
        
        # Check for upcoming deadlines (within next 7 days)
        upcoming_deadline_date = datetime.now().date() + timedelta(days=7)
        deadline_updates = Update.query.filter(
            Update.deadline_date.isnot(None),
            Update.deadline_date <= upcoming_deadline_date,
            Update.deadline_date >= datetime.now().date()
        ).all()
        
        for update in deadline_updates:
            # Check if user should be notified about this update
            should_notify = True
            
            if prefs:
                # Filter by user's location preferences
                if prefs.locations:
                    user_locations = [loc.strip().lower() for loc in prefs.locations.split(',')]
                    if not any(loc in update.jurisdiction_affected.lower() for loc in user_locations):
                        should_notify = False
                
                # Filter by user's category preferences  
                if prefs.categories and should_notify:
                    user_categories = [cat.strip() for cat in prefs.categories.split(',')]
                    if update.category not in user_categories:
                        should_notify = False
                
                # Filter by user's impact level preferences
                if prefs.impact_levels and should_notify:
                    user_impacts = [imp.strip() for imp in prefs.impact_levels.split(',')]
                    if update.impact_level not in user_impacts:
                        should_notify = False
            
            if should_notify:
                days_until_deadline = (update.deadline_date - datetime.now().date()).days
                alert_type = 'urgent' if days_until_deadline <= 3 else 'warning'
                
                alerts.append({
                    'type': alert_type,
                    'title': f'Deadline Approaching: {update.title}',
                    'message': f'Deadline in {days_until_deadline} day{"s" if days_until_deadline != 1 else ""}',
                    'update_id': update.id,
                    'deadline_date': update.deadline_date.isoformat(),
                    'action_required': update.action_required
                })
        
        # Check for high priority recent updates
        recent_high_priority = Update.query.filter(
            Update.priority == 1,
            Update.update_date >= datetime.now().date() - timedelta(days=3)
        ).all()
        
        for update in recent_high_priority:
            # Apply same filtering logic
            should_notify = True
            
            if prefs:
                if prefs.locations:
                    user_locations = [loc.strip().lower() for loc in prefs.locations.split(',')]
                    if not any(loc in update.jurisdiction_affected.lower() for loc in user_locations):
                        should_notify = False
                
                if prefs.categories and should_notify:
                    user_categories = [cat.strip() for cat in prefs.categories.split(',')]
                    if update.category not in user_categories:
                        should_notify = False
            
            if should_notify:
                alerts.append({
                    'type': 'info',
                    'title': f'High Priority Update: {update.title}',
                    'message': f'New {update.impact_level.lower()} impact update in {update.jurisdiction_affected}',
                    'update_id': update.id,
                    'category': update.category,
                    'impact_level': update.impact_level
                })
        
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

@bp.route('/api/notifications/weekly-digest')
def generate_weekly_digest():
    """Generate weekly digest of updates"""
    try:
        # Get updates from the past week
        week_ago = datetime.now().date() - timedelta(days=7)
        weekly_updates = Update.query.filter(
            Update.update_date >= week_ago
        ).order_by(Update.priority.asc(), Update.update_date.desc()).all()
        
        # Group updates by category
        digest = {
            'week_start': week_ago.isoformat(),
            'week_end': datetime.now().date().isoformat(),
            'total_updates': len(weekly_updates),
            'by_category': {},
            'high_priority': [],
            'upcoming_deadlines': [],
            'summary': ''
        }
        
        for update in weekly_updates:
            category = update.category
            if category not in digest['by_category']:
                digest['by_category'][category] = []
            
            digest['by_category'][category].append({
                'id': update.id,
                'title': update.title,
                'jurisdiction': update.jurisdiction_affected,
                'impact_level': update.impact_level,
                'status': update.status,
                'action_required': update.action_required
            })
            
            # Track high priority items
            if update.priority == 1:
                digest['high_priority'].append(update.title)
        
        # Get upcoming deadlines for next 2 weeks
        two_weeks_ahead = datetime.now().date() + timedelta(days=14)
        upcoming_deadlines = Update.query.filter(
            Update.deadline_date.isnot(None),
            Update.deadline_date >= datetime.now().date(),
            Update.deadline_date <= two_weeks_ahead
        ).order_by(Update.deadline_date.asc()).all()
        
        for update in upcoming_deadlines:
            days_until = (update.deadline_date - datetime.now().date()).days
            digest['upcoming_deadlines'].append({
                'title': update.title,
                'deadline_date': update.deadline_date.isoformat(),
                'days_until': days_until,
                'jurisdiction': update.jurisdiction_affected
            })
        
        # Generate summary
        summary_parts = []
        if len(weekly_updates) > 0:
            summary_parts.append(f"{len(weekly_updates)} new updates this week")
        if len(digest['high_priority']) > 0:
            summary_parts.append(f"{len(digest['high_priority'])} high priority items")
        if len(digest['upcoming_deadlines']) > 0:
            summary_parts.append(f"{len(digest['upcoming_deadlines'])} deadlines approaching")
        
        digest['summary'] = '. '.join(summary_parts) + '.' if summary_parts else 'No significant updates this week.'
        
        return jsonify({
            'success': True,
            'digest': digest
        })
        
    except Exception as e:
        logging.error(f"Error generating weekly digest: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate weekly digest'
        }), 500

@bp.route('/notifications')
def notifications_page():
    """Notification management page"""
    return render_template('notifications.html')

# Admin Routes
@bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if is_admin_logged_in():
        return redirect(url_for('main.admin_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            session['admin_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html', form=form)

@bp.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))

@bp.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin_logged_in():
        flash('Please log in to access admin panel', 'error')
        return redirect(url_for('main.admin_login'))
    
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

@bp.route('/admin/regulations')
def admin_manage_regulations():
    if not is_admin_logged_in():
        return redirect(url_for('main.admin_login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    regulations = Regulation.query.order_by(Regulation.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/manage_regulations.html', regulations=regulations)

@bp.route('/admin/regulations/new', methods=['GET', 'POST'])
def admin_new_regulation():
    if not is_admin_logged_in():
        return redirect(url_for('main.admin_login'))
    
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
        return redirect(url_for('main.admin_manage_regulations'))
    
    return render_template('admin/edit_regulation.html', form=form, title='Add New Regulation')

@bp.route('/admin/regulations/<int:id>/edit', methods=['GET', 'POST'])
def admin_edit_regulation(id):
    if not is_admin_logged_in():
        return redirect(url_for('main.admin_login'))
    
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
        return redirect(url_for('main.admin_manage_regulations'))
    
    return render_template('admin/edit_regulation.html', form=form, regulation=regulation, title='Edit Regulation')

@bp.route('/admin/regulations/<int:id>/delete', methods=['POST'])
def admin_delete_regulation(id):
    if not is_admin_logged_in():
        return redirect(url_for('main.admin_login'))
    
    regulation = Regulation.query.get_or_404(id)
    db.session.delete(regulation)
    db.session.commit()
    flash('Regulation deleted successfully!', 'success')
    return redirect(url_for('main.admin_manage_regulations'))

@bp.route('/admin/updates')
def admin_manage_updates():
    if not is_admin_logged_in():
        return redirect(url_for('main.admin_login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    updates = Update.query.order_by(Update.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/manage_updates.html', updates=updates)

@bp.route('/admin/updates/new', methods=['GET', 'POST'])
def admin_new_update():
    if not is_admin_logged_in():
        return redirect(url_for('main.admin_login'))
    
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
        return redirect(url_for('main.admin_manage_updates'))
    
    return render_template('admin/edit_update.html', form=form, title='Add New Update')

@bp.route('/admin/updates/<int:id>/edit', methods=['GET', 'POST'])
def admin_edit_update(id):
    if not is_admin_logged_in():
        return redirect(url_for('main.admin_login'))
    
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
        return redirect(url_for('main.admin_manage_updates'))
    
    return render_template('admin/edit_update.html', form=form, update=update, title='Edit Update')

@bp.route('/admin/updates/<int:id>/delete', methods=['POST'])
def admin_delete_update(id):
    if not is_admin_logged_in():
        return redirect(url_for('main.admin_login'))
    
    update = Update.query.get_or_404(id)
    db.session.delete(update)
    db.session.commit()
    flash('Update deleted successfully!', 'success')
    return redirect(url_for('main.admin_manage_updates'))
