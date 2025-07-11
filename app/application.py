import os
import logging
import logging.handlers
from flask import Flask, request, g
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
import traceback
import sys
import time
from datetime import datetime

# Add the parent directory to Python path to ensure imports work (models.py is in parent dir)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def configure_logging(app):
    """Configure comprehensive logging for the application"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Set log level from environment
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level_value = getattr(logging, log_level, logging.INFO)
    
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # File handler for all logs (rotating)
    app_log_file = os.path.join(log_dir, 'app.log')
    file_handler = logging.handlers.RotatingFileHandler(
        app_log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level_value)
    file_handler.setFormatter(detailed_formatter)
    
    # Error file handler for errors only
    error_log_file = os.path.join(log_dir, 'errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_value)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Configure Flask app logger
    app.logger.setLevel(log_level_value)
    
    # Disable default Flask logging to avoid duplicates
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Create application-specific logger
    app_logger = logging.getLogger('str_tracker')
    app_logger.info(f"Logging configured successfully - Level: {log_level}")
    app_logger.info(f"Log files: {app_log_file}, {error_log_file}")
    
    return app_logger

def setup_request_logging(app):
    """Set up request-level logging and monitoring"""
    
    @app.before_request
    def before_request():
        """Log request start and set up timing"""
        g.start_time = time.time()
        g.request_id = f"{int(time.time())}-{id(request)}"
        
        # Log request details
        logger = logging.getLogger('str_tracker.requests')
        logger.info(
            f"Request started - ID: {g.request_id} | Method: {request.method} | "
            f"URL: {request.url} | Remote: {request.remote_addr} | "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')[:100]}"
        )
        
        # Log form data for POST requests (excluding sensitive fields)
        if request.method == 'POST' and request.form:
            safe_form_data = {}
            sensitive_fields = {'password', 'csrf_token', 'session_secret'}
            for key, value in request.form.items():
                if key.lower() not in sensitive_fields:
                    safe_form_data[key] = value[:100] if len(str(value)) > 100 else value
                else:
                    safe_form_data[key] = '[REDACTED]'
            logger.debug(f"Request form data - ID: {g.request_id} | Data: {safe_form_data}")
    
    @app.after_request
    def after_request(response):
        """Log request completion and performance metrics"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            logger = logging.getLogger('str_tracker.requests')
            
            # Determine log level based on response status and duration
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING
            elif duration > 2.0:  # Slow request
                log_level = logging.WARNING
            else:
                log_level = logging.INFO
            
            logger.log(
                log_level,
                f"Request completed - ID: {getattr(g, 'request_id', 'unknown')} | "
                f"Status: {response.status_code} | Duration: {duration:.3f}s | "
                f"Size: {response.content_length or 0} bytes"
            )
            
            # Log slow requests separately
            if duration > 1.0:
                slow_logger = logging.getLogger('str_tracker.performance')
                slow_logger.warning(
                    f"Slow request detected - ID: {getattr(g, 'request_id', 'unknown')} | "
                    f"URL: {request.url} | Duration: {duration:.3f}s"
                )
        
        return response
    
    @app.errorhandler(404)
    def handle_404(error):
        """Log 404 errors with context"""
        logger = logging.getLogger('str_tracker.errors')
        logger.warning(
            f"404 Not Found - URL: {request.url} | "
            f"Referrer: {request.referrer} | Remote: {request.remote_addr}"
        )
        return error
    
    @app.errorhandler(500)
    def handle_500(error):
        """Log 500 errors with full context"""
        logger = logging.getLogger('str_tracker.errors')
        logger.error(
            f"500 Internal Server Error - URL: {request.url} | "
            f"Error: {str(error)} | Request ID: {getattr(g, 'request_id', 'unknown')}",
            exc_info=True
        )
        return error

def create_app():
    # create the app with correct template and static directories
    # Since we're in app/ subdirectory, templates and static are in parent directory
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Configure logging first
    app_logger = configure_logging(app)
    
    # Set up request logging
    setup_request_logging(app)
    
    # Require secure session secret - no insecure fallback
    session_secret = os.environ.get("SESSION_SECRET")
    if not session_secret:
        app_logger.error("SESSION_SECRET environment variable is required for security")
        raise ValueError("SESSION_SECRET environment variable is required for security")
    app.secret_key = session_secret
    
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///str_compliance.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Configure server settings for URL generation (only set SERVER_NAME if explicitly provided)
    if os.environ.get('SERVER_NAME'):
        app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
    app.config['APPLICATION_ROOT'] = '/'
    app.config['PREFERRED_URL_SCHEME'] = 'http'
    
    # DISABLE TEMPLATE CACHING TO FIX STALE TEMPLATE ISSUES
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.jinja_env.auto_reload = True
    app.jinja_env.cache = None
    
    # Force template recompilation
    if hasattr(app.jinja_env, 'bytecode_cache'):
        app.jinja_env.bytecode_cache = None
    
    # Clear any compiled templates
    if hasattr(app.jinja_env, '_module_loader'):
        app.jinja_env._module_loader = None
    
    # Configure CSRF exemptions for specific endpoints
    app.config['WTF_CSRF_EXEMPT_LIST'] = ['/api/client-errors']

    try:
        # Import db from models and initialize the app
        from models import db
        db.init_app(app)

        # Initialize CSRF protection
        csrf = CSRFProtect(app)
        app_logger.info("CSRF protection initialized")

        with app.app_context():
            # Import models after app context is created
            from models import AdminUser, Regulation, Update
            from werkzeug.security import generate_password_hash
            from datetime import datetime, date
            
            # Create all tables
            db.create_all()
            app_logger.info("Database tables created/verified")
            
            # Create default admin user if none exists
            if not AdminUser.query.first():
                admin_username = os.environ.get("ADMIN_USERNAME", "admin")
                admin_password = os.environ.get("ADMIN_PASSWORD")
                if not admin_password:
                    app_logger.error("ADMIN_PASSWORD environment variable is required for initial admin setup")
                    raise ValueError("ADMIN_PASSWORD environment variable is required for initial admin setup")
                
                admin = AdminUser(
                    username=admin_username,
                    password_hash=generate_password_hash(admin_password, method='pbkdf2:sha256')
                )
                db.session.add(admin)
                db.session.commit()
                app_logger.info(f"Default admin user created: {admin_username}")
            
            # Add sample data if tables are empty (unless skipped for testing)
            if not Regulation.query.first() and not os.environ.get("SKIP_SAMPLE_DATA"):
                sample_regulations = [
                    Regulation(
                        jurisdiction='National',
                        jurisdiction_level='National',
                        location='USA',
                        title='Fair Housing Act Compliance',
                        last_updated=date(2024, 1, 15),
                        overview='<p>The Fair Housing Act prohibits discrimination in housing based on protected characteristics including race, color, religion, sex, familial status, national origin, and disability.</p>',
                        detailed_requirements='<p><strong>All short-term rental operators must comply with Fair Housing Act provisions:</strong></p><ul><li>Non-discrimination in advertising, booking, and guest services</li><li>Equal treatment regardless of protected characteristics</li><li>Accessible accommodations for guests with disabilities</li><li>Compliance with all federal fair housing regulations</li></ul>',
                        compliance_steps='<p><strong>Follow these steps to ensure compliance:</strong></p><ol><li>Review and update all advertising materials to remove discriminatory language</li><li>Train staff on fair housing requirements</li><li>Implement non-discriminatory booking policies</li><li>Ensure accessibility compliance where required</li></ol>',
                        required_forms='<p><strong>No specific forms required, but maintain:</strong></p><ul><li>Documentation of non-discriminatory policies</li><li>Staff training records</li><li>Guest accommodation records</li></ul>',
                        penalties_non_compliance='<p><strong>Violations may result in:</strong></p><ul><li>Federal civil rights investigations</li><li>Monetary damages and civil penalties</li><li>Injunctive relief</li><li>Attorney fees and court costs</li></ul>',
                        recent_changes='<p>No recent changes to federal fair housing requirements. Continue monitoring HUD guidance and updates.</p>'
                    ),
                    Regulation(
                        jurisdiction='National',
                        jurisdiction_level='National',
                        location='USA',
                        title='ADA Accessibility Requirements',
                        last_updated=date(2024, 2, 1),
                        overview='<p>The Americans with Disabilities Act (ADA) requires places of public accommodation to be accessible to individuals with disabilities.</p>',
                        detailed_requirements='<p><strong>ADA compliance requirements for short-term rentals:</strong></p><ul><li>Physical accessibility where applicable</li><li>Effective communication accommodations</li><li>Reasonable modifications to policies</li><li>Accurate accessibility information in listings</li></ul>',
                        compliance_steps='<p><strong>Steps to ensure ADA compliance:</strong></p><ol><li>Assess property for accessibility features</li><li>Provide accurate accessibility descriptions</li><li>Offer reasonable accommodations</li><li>Train staff on ADA requirements</li></ol>',
                        required_forms='<p><strong>Maintain documentation of:</strong></p><ul><li>Accessibility assessments</li><li>Guest accommodation requests and responses</li><li>Staff training on ADA compliance</li></ul>',
                        penalties_non_compliance='<p><strong>Non-compliance may result in:</strong></p><ul><li>Federal ADA investigations</li><li>Civil penalties up to $75,000 for first violations</li><li>Injunctive relief requiring modifications</li><li>Private lawsuits for damages</li></ul>',
                        recent_changes='<p>Recent DOJ guidance emphasizes digital accessibility for booking platforms and clear communication of accessibility features.</p>'
                    ),
                    Regulation(
                        jurisdiction='Florida State',
                        jurisdiction_level='State',
                        location='Florida',
                        title='State Licensing Requirements',
                        last_updated=date(2024, 3, 10),
                        overview='<p>Florida requires short-term rental operators to obtain appropriate business licenses and register with the Florida Department of Revenue for tax collection purposes.</p>',
                        detailed_requirements='<p><strong>Florida state requirements include:</strong></p><ul><li>Business registration with Florida Department of State</li><li>Sales tax registration with Department of Revenue</li><li>Tourist development tax compliance</li><li>Local licensing where required</li></ul>',
                        compliance_steps='<p><strong>Complete these steps:</strong></p><ol><li>Register business with Florida Department of State</li><li>Obtain sales tax permit from Department of Revenue</li><li>Register for tourist development tax collection</li><li>Check local licensing requirements</li><li>Submit required tax returns</li></ol>',
                        required_forms='<p><strong>Required state forms:</strong></p><ul><li>Florida Business Registration (Form DR-1)</li><li>Sales Tax Application (Form DR-1)</li><li>Tourist Development Tax Registration</li><li>Monthly/quarterly tax returns</li></ul>',
                        penalties_non_compliance='<p><strong>Penalties for non-compliance:</strong></p><ul><li>Business license violations: Up to $1,000 per violation</li><li>Tax violations: Interest and penalties on unpaid taxes</li><li>Criminal penalties for willful tax evasion</li><li>Business closure orders</li></ul>',
                        recent_changes='<p>Recent updates include enhanced enforcement of tourist development tax collection and new online registration requirements effective January 2024.</p>'
                    ),
                    Regulation(
                        jurisdiction='Tampa City',
                        jurisdiction_level='Local',
                        location='Tampa',
                        title='Registration and Safety Requirements',
                        last_updated=date(2024, 4, 15),
                        overview='<p>Tampa requires all short-term rental properties to be registered with the city and meet specific safety and operational standards.</p>',
                        detailed_requirements='<p><strong>Tampa city requirements:</strong></p><ul><li>Annual registration with the city</li><li>Safety inspections every two years</li><li>Smoke and carbon monoxide detectors</li><li>Fire extinguishers and emergency information</li><li>Parking compliance</li><li>Noise ordinance compliance</li></ul>',
                        compliance_steps='<p><strong>Registration process:</strong></p><ol><li>Complete online registration application</li><li>Schedule safety inspection</li><li>Install required safety equipment</li><li>Pay registration fees</li><li>Display registration certificate</li><li>Renew annually</li></ol>',
                        required_forms='<p><strong>Required Tampa forms:</strong></p><ul><li>Short-Term Rental Registration Application</li><li>Property Safety Inspection Checklist</li><li>Annual Renewal Application</li><li>Incident Report Forms (when applicable)</li></ul>',
                        penalties_non_compliance='<p><strong>Tampa penalties:</strong></p><ul><li>Operating without registration: $500 per day</li><li>Safety violations: $250-$1,000 per violation</li><li>Repeat violations: Permit revocation</li><li>Code enforcement action</li></ul>',
                        recent_changes='<p>New requirements effective April 2024 include enhanced parking regulations and stricter noise ordinance enforcement during peak tourist seasons.</p>'
                    ),
                    Regulation(
                        jurisdiction='St. Petersburg City',
                        jurisdiction_level='Local',
                        location='St. Petersburg',
                        title='Registration Requirements',
                        last_updated=date(2024, 5, 10),
                        overview='<p>St. Petersburg requires all short-term rental properties to be registered with the city and display registration numbers in all advertising.</p>',
                        detailed_requirements='<p><strong>St. Petersburg requirements:</strong></p><ul><li>City registration and permit</li><li>Annual inspections for compliance</li><li>Registration number display in all advertising</li><li>Local contact person requirement</li><li>Guest limit compliance</li></ul>',
                        compliance_steps='<p><strong>Registration steps:</strong></p><ol><li>Submit registration application to city</li><li>Schedule inspection appointment</li><li>Install required safety features</li><li>Obtain registration certificate</li><li>Display registration number in all listings</li><li>Designate local contact person</li></ol>',
                        required_forms='<p><strong>Required St. Petersburg forms:</strong></p><ul><li>Short-Term Rental Registration Form</li><li>Inspection Report</li><li>Local Contact Designation Form</li><li>Annual Compliance Certification</li></ul>',
                        penalties_non_compliance='<p><strong>St. Petersburg penalties:</strong></p><ul><li>Unregistered operation: $1,000 per violation</li><li>Advertising without registration number: $500 per listing</li><li>Inspection violations: $250-$750 per violation</li><li>Permit suspension or revocation</li></ul>',
                        recent_changes='<p>Recent updates include mandatory local contact person requirements and enhanced inspection protocols effective May 2024.</p>'
                    ),
                    Regulation(
                        jurisdiction='Clearwater City',
                        jurisdiction_level='Local',
                        location='Clearwater',
                        title='31-Day Minimum in Residential Areas',
                        last_updated=date(2024, 6, 1),
                        overview='<p>Clearwater requires short-term rentals in residential zoning districts to maintain a minimum rental period of 31 days, while commercial districts may allow shorter stays with proper permits.</p>',
                        detailed_requirements='<p><strong>Clearwater zoning requirements:</strong></p><ul><li>31-day minimum stays in residential zones</li><li>Special permits required for shorter stays in commercial zones</li><li>Compliance with zoning regulations</li><li>Business license requirements</li></ul>',
                        compliance_steps='<p><strong>Compliance process:</strong></p><ol><li>Verify property zoning designation</li><li>Apply for appropriate permits based on zone</li><li>Adjust rental terms to meet minimum stay requirements</li><li>Update advertising to reflect minimum stays</li><li>Obtain required business licenses</li></ol>',
                        required_forms='<p><strong>Required Clearwater forms:</strong></p><ul><li>Zoning Compliance Application</li><li>Business License Application</li><li>Special Use Permit (for commercial zones)</li><li>Rental Agreement Templates</li></ul>',
                        penalties_non_compliance='<p><strong>Clearwater penalties:</strong></p><ul><li>Zoning violations: $250-$500 per day</li><li>Unlicensed operation: $100-$500 per violation</li><li>Cease and desist orders</li><li>Legal action for continued violations</li></ul>',
                        recent_changes='<p>New enforcement protocols implemented June 2024 include automated monitoring of rental listings and enhanced penalty structure for repeat violations.</p>'
                    ),
                    Regulation(
                        jurisdiction='Sarasota City',
                        jurisdiction_level='Local',
                        location='Sarasota',
                        title='Minimum 7-Day Stay and Registration',
                        last_updated=date(2024, 6, 15),
                        overview='<p>Sarasota requires short-term rental properties to maintain 7-day minimum stays, complete city registration, and provide 24/7 emergency contact information.</p>',
                        detailed_requirements='<p><strong>Sarasota requirements:</strong></p><ul><li>7-day minimum rental period</li><li>City registration and annual renewal</li><li>24/7 emergency contact availability</li><li>Property safety inspections</li><li>Guest registration requirements</li></ul>',
                        compliance_steps='<p><strong>Registration and compliance:</strong></p><ol><li>Complete city registration application</li><li>Schedule property safety inspection</li><li>Designate 24/7 emergency contact</li><li>Implement 7-day minimum stay policy</li><li>Update all advertising platforms</li><li>Submit annual renewal</li></ol>',
                        required_forms='<p><strong>Required Sarasota forms:</strong></p><ul><li>Short-Term Rental Registration Application</li><li>Emergency Contact Designation Form</li><li>Property Inspection Report</li><li>Guest Registration Log</li><li>Annual Renewal Application</li></ul>',
                        penalties_non_compliance='<p><strong>Sarasota penalties:</strong></p><ul><li>Unregistered operation: $1,000 per violation</li><li>Minimum stay violations: $500 per booking</li><li>Missing emergency contact: $250 per day</li><li>Registration revocation for repeat violations</li></ul>',
                        recent_changes='<p>Enhanced monitoring system launched June 2024 with real-time tracking of rental durations and automated violation detection.</p>'
                    )
                ]
                
                for regulation in sample_regulations:
                    db.session.add(regulation)
                
                db.session.commit()
                app_logger.info("Sample regulations added")
            
            if not Update.query.first() and not os.environ.get("SKIP_SAMPLE_DATA"):
                sample_updates = [
                    Update(
                        title='Tampa Zoning Ordinance Amendment',
                        description='City Council approved amendments to zoning ordinances affecting short-term rentals in downtown districts. New regulations will require additional permits for properties in historic zones.',
                        jurisdiction_affected='Tampa',
                        jurisdiction_level='Local',
                        update_date=date(2024, 7, 1),
                        status='Recent'
                    ),
                    Update(
                        title='Florida State Tax Collection Changes',
                        description='New legislation proposed to modify tourist development tax rates and collection procedures. Would affect all short-term rental operators statewide.',
                        jurisdiction_affected='Florida',
                        jurisdiction_level='State',
                        update_date=date(2024, 8, 15),
                        status='Upcoming'
                    ),
                    Update(
                        title='Federal Fair Housing Enforcement Guidelines',
                        description='Department of Housing and Urban Development released updated enforcement guidelines for short-term rental platforms and operators regarding fair housing compliance.',
                        jurisdiction_affected='USA',
                        jurisdiction_level='National',
                        update_date=date(2024, 6, 20),
                        status='Recent'
                    ),
                    Update(
                        title='St. Petersburg Registration Fee Increase',
                        description='Proposed increase in annual registration fees for short-term rental properties from $150 to $300. Public hearing scheduled for next month.',
                        jurisdiction_affected='St. Petersburg',
                        jurisdiction_level='Local',
                        update_date=date(2024, 9, 1),
                        status='Proposed'
                    ),
                    Update(
                        title='Sarasota Noise Ordinance Review',
                        description='City commission considering stricter noise regulations for short-term rentals following increased complaints from residents.',
                        jurisdiction_affected='Sarasota',
                        jurisdiction_level='Local',
                        update_date=date(2024, 8, 30),
                        status='Proposed'
                    )
                ]
                
                for update in sample_updates:
                    db.session.add(update)
                
                db.session.commit()
                app_logger.info("Sample updates added")
        
        # Import and register blueprints
        from app.blueprints.main import main_bp
        from app.blueprints.api import api_bp
        from app.blueprints.admin import admin_bp
        
        app.register_blueprint(main_bp)
        app.register_blueprint(api_bp)
        app.register_blueprint(admin_bp)
        
        # Add custom template filters
        @app.template_filter('nl2br')
        def nl2br_filter(text):
            """Convert newlines to HTML line breaks"""
            if not text:
                return text
            return text.replace('\n', '<br>\n')
        
        app_logger.info("Custom template filters registered")
        
        app_logger.info("Flask app created successfully")
        return app
        
    except Exception as e:
        app_logger.error(f"Error creating Flask app: {str(e)}")
        app_logger.error(traceback.format_exc())
        raise


