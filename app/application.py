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
                        jurisdiction_level='National',
                        location='USA',
                        title='Fair Housing Act Compliance',
                        key_requirements='All short-term rental operators must comply with Fair Housing Act provisions, including non-discrimination in advertising, booking, and guest services based on protected characteristics.',
                        last_updated=date(2024, 1, 15)
                    ),
                    Regulation(
                        jurisdiction_level='National',
                        location='USA',
                        title='ADA Accessibility Requirements',
                        key_requirements='Properties must meet ADA accessibility standards where applicable. Online booking platforms must provide accurate accessibility information.',
                        last_updated=date(2024, 2, 1)
                    ),
                    Regulation(
                        jurisdiction_level='State',
                        location='Florida',
                        title='State Licensing Requirements',
                        key_requirements='Short-term rental operators must obtain appropriate business licenses and register with the Florida Department of Revenue for tax collection purposes.',
                        last_updated=date(2024, 3, 10)
                    ),
                    Regulation(
                        jurisdiction_level='State',
                        location='Florida',
                        title='Tax Collection Obligations',
                        key_requirements='Operators must collect and remit state sales tax and tourist development tax. Monthly reporting required for properties generating over $1,000 in monthly revenue.',
                        last_updated=date(2024, 3, 15)
                    ),
                    Regulation(
                        jurisdiction_level='Local',
                        location='Tampa',
                        title='Business Tax Receipt',
                        key_requirements='All short-term rental operators must obtain a business tax receipt from the City of Tampa. Annual renewal required with proof of insurance and property compliance.',
                        last_updated=date(2024, 4, 1)
                    ),
                    Regulation(
                        jurisdiction_level='Local',
                        location='Tampa',
                        title='Zoning Restrictions',
                        key_requirements='Short-term rentals are permitted in specific zoning districts only. Properties in residential zones may have additional restrictions on rental duration and guest capacity.',
                        last_updated=date(2024, 4, 5)
                    ),
                    Regulation(
                        jurisdiction_level='Local',
                        location='St. Petersburg',
                        title='Minimum 7-Day Stay Requirement',
                        key_requirements='All short-term rentals must have a minimum stay of 7 consecutive days. No exceptions for holidays or special events.',
                        last_updated=date(2024, 5, 1)
                    ),
                    Regulation(
                        jurisdiction_level='Local',
                        location='St. Petersburg',
                        title='Registration Requirements',
                        key_requirements='Properties must be registered with the city and display registration numbers in all advertising. Annual inspections required for compliance verification.',
                        last_updated=date(2024, 5, 10)
                    ),
                    Regulation(
                        jurisdiction_level='Local',
                        location='Clearwater',
                        title='31-Day Minimum in Residential Areas',
                        key_requirements='Short-term rentals in residential zoning districts must have a minimum rental period of 31 days. Commercial districts may allow shorter stays with proper permits.',
                        last_updated=date(2024, 6, 1)
                    ),
                    Regulation(
                        jurisdiction_level='Local',
                        location='Sarasota',
                        title='Minimum 7-Day Stay and Registration',
                        key_requirements='Properties must maintain 7-day minimum stays and complete city registration process. Operators must provide emergency contact information available 24/7.',
                        last_updated=date(2024, 6, 15)
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
                        update_date=date(2024, 7, 1),
                        status='Recent'
                    ),
                    Update(
                        title='Florida State Tax Collection Changes',
                        description='New legislation proposed to modify tourist development tax rates and collection procedures. Would affect all short-term rental operators statewide.',
                        jurisdiction_affected='Florida',
                        update_date=date(2024, 8, 15),
                        status='Upcoming'
                    ),
                    Update(
                        title='Federal Fair Housing Enforcement Guidelines',
                        description='Department of Housing and Urban Development released updated enforcement guidelines for short-term rental platforms and operators regarding fair housing compliance.',
                        jurisdiction_affected='USA',
                        update_date=date(2024, 6, 20),
                        status='Recent'
                    ),
                    Update(
                        title='St. Petersburg Registration Fee Increase',
                        description='Proposed increase in annual registration fees for short-term rental properties from $150 to $300. Public hearing scheduled for next month.',
                        jurisdiction_affected='St. Petersburg',
                        update_date=date(2024, 9, 1),
                        status='Proposed'
                    ),
                    Update(
                        title='Sarasota Noise Ordinance Review',
                        description='City commission considering stricter noise regulations for short-term rentals following increased complaints from residents.',
                        jurisdiction_affected='Sarasota',
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


