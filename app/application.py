import os
import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
import traceback
import sys

# Add the parent directory to Python path to ensure imports work (models.py is in parent dir)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging - configurable via environment
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app():
    # create the app with correct template and static directories
    # Since we're in app/ subdirectory, templates and static are in parent directory
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Require secure session secret - no insecure fallback
    session_secret = os.environ.get("SESSION_SECRET")
    if not session_secret:
        raise ValueError("SESSION_SECRET environment variable is required for security")
    app.secret_key = session_secret
    
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///str_compliance.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

    try:
        # Import db from models and initialize the app
        from models import db
        db.init_app(app)

        # Initialize CSRF protection
        csrf = CSRFProtect(app)

        with app.app_context():
            # Import models after app context is created
            from models import AdminUser, Regulation, Update
            from werkzeug.security import generate_password_hash
            from datetime import datetime, date
            
            # Create all tables
            db.create_all()
            
            # Create default admin user if none exists
            if not AdminUser.query.first():
                admin_username = os.environ.get("ADMIN_USERNAME", "admin")
                admin_password = os.environ.get("ADMIN_PASSWORD")
                if not admin_password:
                    raise ValueError("ADMIN_PASSWORD environment variable is required for initial admin setup")
                
                admin = AdminUser(
                    username=admin_username,
                    password_hash=generate_password_hash(admin_password, method='pbkdf2:sha256')
                )
                db.session.add(admin)
                db.session.commit()
                logging.info(f"Default admin user created: {admin_username}")
            
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
                logging.info("Sample regulations added")
            
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
                logging.info("Sample updates added")
        
        # Import and register blueprints
        from app.blueprints.main import main_bp
        from app.blueprints.api import api_bp
        from app.blueprints.admin import admin_bp
        
        app.register_blueprint(main_bp)
        app.register_blueprint(api_bp)
        app.register_blueprint(admin_bp)
        
        logging.info("Flask app created successfully")
        return app
        
    except Exception as e:
        logging.error(f"Error creating Flask app: {str(e)}")
        logging.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    application = create_app()
    # Only enable debug mode if explicitly set via environment variable
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    application.run(host='0.0.0.0', port=9000, debug=debug_mode)
