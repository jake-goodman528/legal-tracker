# STR Compliance Toolkit - Architecture Overview

## Overview

This is a Flask-based web application that serves as a Short-Term Rental (STR) Legal and Compliance toolkit. The application helps users track regulatory requirements across different jurisdictions (National, State, Local) and stay updated with industry changes. It provides both public access to view regulations and updates, plus an admin interface for content management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with SQLite (configurable via DATABASE_URL environment variable)
- **Session Management**: Flask's built-in session handling with secure secret key
- **Forms**: Flask-WTF for form handling and CSRF protection
- **Authentication**: Simple password hash-based admin authentication using Werkzeug

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default)
- **CSS Framework**: Bootstrap 5 with dark theme
- **Icons**: Font Awesome 6.0
- **JavaScript**: Vanilla JavaScript with Bootstrap components
- **Responsive Design**: Mobile-first Bootstrap grid system

### Database Schema
Three main models:
1. **Regulation**: Stores regulatory requirements with jurisdiction level, location, title, requirements, and dates
2. **Update**: Tracks industry updates with status (Recent/Upcoming/Proposed) and jurisdiction affected
3. **AdminUser**: Simple admin authentication with username and password hash

## Key Components

### Public Interface
- **Home Page**: Landing page with hero section and feature overview
- **Regulations Page**: Filterable/searchable list of regulations by jurisdiction and location
- **Updates Page**: Timeline view of regulatory changes and updates

### Admin Interface
- **Login System**: Simple username/password authentication
- **Dashboard**: Statistics overview of regulations and updates
- **Content Management**: CRUD operations for regulations and updates
- **Form Validation**: Server-side validation using WTForms

### Core Features
- **Multi-level Jurisdiction Support**: National, State, and Local regulations
- **Advanced Filtering**: Filter by jurisdiction level, location, and search terms
- **Status Tracking**: Updates categorized as Recent, Upcoming, or Proposed
- **Responsive Design**: Works on desktop and mobile devices

## Data Flow

1. **Public Access**: Users browse regulations and updates without authentication
2. **Admin Access**: Admins log in to manage content through dedicated interfaces
3. **Database Operations**: All data stored in SQLite with SQLAlchemy ORM handling queries
4. **Form Processing**: Flask-WTF handles form validation and CSRF protection
5. **Session Management**: Admin authentication state maintained via Flask sessions

## External Dependencies

### Python Packages
- Flask: Web framework
- Flask-SQLAlchemy: Database ORM
- Flask-WTF: Form handling
- WTForms: Form validation
- Werkzeug: WSGI utilities and password hashing

### Frontend Dependencies (CDN)
- Bootstrap 5: CSS framework
- Font Awesome 6: Icon library
- Custom CSS: Application-specific styling

### Environment Variables
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `SESSION_SECRET`: Secret key for session encryption

## Deployment Strategy

### Development Setup
- SQLite database for local development
- Flask development server with debug mode
- Automatic table creation on startup
- Default admin user (admin/admin123) created automatically

### Production Considerations
- Database URL configurable via environment variable
- Session secret should be set via environment variable
- ProxyFix middleware included for deployment behind reverse proxy
- Connection pooling configured for database reliability

### Key Files
- `app.py`: Application factory and configuration
- `main.py`: Application entry point
- `models.py`: Database models
- `routes.py`: URL routing and view logic
- `forms.py`: Form definitions and validation
- `templates/`: Jinja2 templates for all pages
- `static/`: CSS, JavaScript, and other static assets

The application follows Flask best practices with a clear separation of concerns between models, views, and templates. The architecture is designed to be simple yet extensible, making it easy to add new features or modify existing functionality.