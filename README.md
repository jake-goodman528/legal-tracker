# STR Compliance Toolkit

A comprehensive web application for tracking and managing Short-Term Rental (STR) compliance requirements across multiple jurisdictions. This toolkit helps property managers, owners, and compliance professionals stay up-to-date with evolving regulations, deadlines, and requirements.

## 🏢 About Kaystreet Management

This application was developed for Kaystreet Management, a leading property management company specializing in short-term rental compliance and operations.

## ✨ Features

### 🔍 **Regulation Management**
- **Comprehensive Database**: Access to detailed regulations across multiple jurisdictions and compliance areas
- **Detailed Requirements**: Comprehensive regulation details with compliance information, effective dates, and keywords
- **Related Regulations**: Automatic discovery of related regulations by location and category
- **Export Capabilities**: CSV export functionality for compliance reporting

### 📈 **Update Tracking**
- **Real-time Updates**: Track regulatory changes, court decisions, and industry news
- **Priority Management**: High, medium, and low priority classification system
- **Bookmark System**: Save important updates for easy reference



### 👥 **Administrative Interface**
- **Secure Admin Panel**: Role-based access control for content management
- **CRUD Operations**: Complete management of regulations and updates
- **Dashboard Analytics**: Statistics and insights on regulatory activity
- **Bulk Import/Export**: Efficient data management capabilities

### 🔒 **Security Features**
- **Environment-based Configuration**: Secure credential management
- **Session Security**: Encrypted session management
- **CSRF Protection**: Cross-site request forgery protection
- **Input Validation**: Comprehensive input sanitization
- **Secure Defaults**: Production-ready security configuration

## 🛠 Technology Stack

- **Backend**: Python 3.9+, Flask 3.1+
- **Database**: SQLAlchemy with SQLite (configurable for PostgreSQL/MySQL)
- **Forms**: Flask-WTF with CSRF protection
- **Frontend**: Bootstrap 5, JavaScript ES6+
- **Architecture**: Modular blueprint structure with service layer pattern

## 📋 Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ShortTermRentalTracker
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```bash
# Required Security Settings
SESSION_SECRET=your-super-secret-session-key-here
ADMIN_PASSWORD=your-secure-admin-password

# Optional Configuration
ADMIN_USERNAME=admin
DATABASE_URL=sqlite:///instance/str_compliance.db
FLASK_DEBUG=false
LOG_LEVEL=INFO
```

**⚠️ Security Note**: Never commit the `.env` file to version control. Use strong, unique passwords for production deployments.

### 5. Initialize the Database
```bash
python3 -c "from app.application import create_app; app = create_app(); app.app_context().push()"
```

### 6. Run the Application
```bash
python3 main.py
```

The application will be available at `http://localhost:5000`

## 📖 Usage Guide

### Public Interface

#### **Browsing Regulations**
1. Navigate to `/regulations` to view all regulations
2. Browse regulations by:
   - Jurisdiction level (National, State, Local)
   - Location (specific cities/states)
   - Category (Legal, Licensing, Taxes, etc.)
   - Detailed requirements and compliance information

#### **Tracking Updates**
1. Visit `/updates` to see regulatory changes
2. View by status (Recent, Upcoming, Proposed)
3. Bookmark important updates for quick access



### Administrative Interface

#### **Accessing Admin Panel**
1. Navigate to `/admin/login`
2. Login with admin credentials
3. Access dashboard at `/admin/dashboard`

#### **Managing Content**
- **Regulations**: Add, edit, delete regulation entries
- **Updates**: Manage regulatory updates and announcements
- **Statistics**: View usage analytics and compliance metrics

## 🏗 Architecture Overview

### Directory Structure
```
ShortTermRentalTracker/
├── app/                      # Application package
│   ├── __init__.py
│   ├── application.py        # Flask app factory
│   ├── blueprints/          # Route blueprints
│   │   ├── main.py          # Public routes
│   │   ├── api.py           # REST API endpoints
│   │   └── admin.py         # Admin interface
│   └── services/            # Business logic layer
│       ├── regulation_service.py
│       ├── update_service.py
│       └── user_interaction_service.py
├── templates/               # Jinja2 templates
├── static/                  # CSS, JS, images
├── instance/               # Database files
├── models.py              # SQLAlchemy models
├── forms.py               # WTForms definitions
├── main.py                # Application entry point
└── requirements.txt       # Python dependencies
```

### Service Layer Pattern
The application uses a service layer architecture to separate business logic from route handlers:

- **RegulationService**: Regulation management and content organization
- **UpdateService**: Update management and categorization
- **UserInteractionService**: Bookmarks and user sessions

### Database Models
- **Regulation**: Core regulation data with compliance information
- **Update**: Regulatory updates and announcements
- **AdminUser**: Administrative user accounts

- **UserUpdateInteraction**: User bookmarks and interactions

## 🔧 Development

### Setting Up Development Environment
```bash
# Install development dependencies
pip install -r requirements.txt

# Set debug mode
export FLASK_DEBUG=true

# Run with auto-reload
python3 main.py
```

### Code Quality
The project follows Python best practices:
- **PEP 8**: Code style compliance
- **Type Hints**: Comprehensive type annotations
- **Docstrings**: Detailed function and class documentation
- **Error Handling**: Consistent exception handling patterns
- **Logging**: Comprehensive logging for debugging and monitoring

### Adding New Features
1. **Models**: Define database models in `models.py`
2. **Services**: Add business logic to appropriate service classes
3. **Routes**: Create blueprint routes with minimal logic
4. **Templates**: Build responsive HTML templates
5. **Tests**: Add unit tests for new functionality

## 🔌 API Documentation

### Update Endpoints
- `GET /api/updates/bookmarked` - Get user bookmarks
- `POST /api/updates/{id}/bookmark` - Toggle bookmark




### Export Endpoints
- `GET /api/export/csv` - Export regulations to CSV

## 🚀 Deployment

### Production Configuration
1. **Environment Variables**: Set all required environment variables
2. **Database**: Configure production database (PostgreSQL recommended)
3. **Security**: Use strong secrets and enable HTTPS
4. **Logging**: Configure appropriate log levels
5. **Performance**: Consider using Gunicorn or uWSGI

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python3", "main.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to all new functions
- Include comprehensive docstrings
- Write unit tests for new features
- Update documentation for API changes

## 📄 License

This project is proprietary software developed for Kaystreet Management. All rights reserved.

## 📞 Support

For support and questions:
- **Email**: support@kaystreetmanagement.com
- **Documentation**: Check this README and inline code documentation
- **Issues**: Use the GitHub issue tracker for bug reports

## 🔄 Changelog

### Version 2.0.0 (Current)
- ✅ Complete security overhaul with environment-based configuration
- ✅ Modular blueprint architecture implementation
- ✅ Service layer pattern for business logic separation
- ✅ Comprehensive documentation and type hints

- ✅ Comprehensive regulation database access
- ✅ Responsive UI with Bootstrap 5

### Version 1.0.0 (Legacy)
- Basic regulation tracking functionality
- Simple admin interface
- SQLite database integration

---

**Built with ❤️ for the Short-Term Rental Industry** 