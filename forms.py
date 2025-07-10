from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Optional
from datetime import datetime


class LoginForm(FlaskForm):
    """Form for admin login"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Login')


class RegulationForm(FlaskForm):
    """Enhanced form for creating/editing regulations with comprehensive fields"""
    
    # Core Information
    jurisdiction_level = SelectField(
        'Jurisdiction Level', 
        choices=[
            ('National', 'National'),
            ('State', 'State'), 
            ('Local', 'Local')
        ],
        validators=[DataRequired()],
        default='Local',
        description="Select the governmental level for this regulation"
    )
    
    location = StringField(
        'Location', 
        validators=[DataRequired(), Length(min=2, max=100)],
        render_kw={"placeholder": "e.g., USA, Florida, Tampa"},
        description="Geographic area where this regulation applies"
    )
    
    title = StringField(
        'Regulation Title', 
        validators=[DataRequired(), Length(min=5, max=200)],
        render_kw={"placeholder": "Enter a descriptive regulation title"},
        description="Clear, concise title describing the regulation"
    )
    
    key_requirements = TextAreaField(
        'Key Requirements', 
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Describe the key requirements and compliance obligations in detail...",
            "rows": 6
        },
        description="Detailed description of what property owners must do to comply"
    )
    
    # Compliance Details
    compliance_level = SelectField(
        'Compliance Level',
        choices=[
            ('Mandatory', 'Mandatory - Required by law'),
            ('Recommended', 'Recommended - Best practice'),
            ('Optional', 'Optional - Additional guidance')
        ],
        validators=[DataRequired()],
        default='Mandatory',
        description="How critical is compliance with this regulation?"
    )
    
    property_types = StringField(
        'Property Types',
        validators=[Optional()],
        render_kw={"placeholder": "Residential, Commercial, Mixed-use (comma-separated)"},
        description="Types of properties this regulation applies to (separate multiple with commas)"
    )
    
    status = SelectField(
        'Regulation Status',
        choices=[
            ('Current & Active', 'Current & Active'),
            ('Upcoming', 'Upcoming - Not yet effective'),
            ('Expired', 'Expired - No longer active')
        ],
        validators=[DataRequired()],
        default='Current & Active',
        description="Current enforcement status of this regulation"
    )
    
    # Metadata & Classification
    category = SelectField(
        'Regulation Category',
        choices=[
            ('Zoning', 'Zoning - Land use restrictions'),
            ('Registration', 'Registration - Property/business registration'),
            ('Tax', 'Tax - Tax obligations and collection'),
            ('Licensing', 'Licensing - Required permits and licenses'),
            ('Safety', 'Safety - Safety requirements and inspections'),
            ('Environmental', 'Environmental - Environmental compliance'),
            ('General', 'General - Other regulations')
        ],
        validators=[DataRequired()],
        default='General',
        description="Primary category that best describes this regulation"
    )
    
    priority = SelectField(
        'Priority Level',
        choices=[
            ('High', 'High - Critical compliance'),
            ('Medium', 'Medium - Important compliance'),
            ('Low', 'Low - Standard compliance')
        ],
        validators=[DataRequired()],
        default='Medium',
        description="Importance level for property owners and operators"
    )
    
    related_keywords = StringField(
        'Related Keywords',
        validators=[Optional()],
        render_kw={"placeholder": "short-term rental, vacation rental, licensing, permits (comma-separated)"},
        description="Keywords and tags to improve searchability (separate with commas)"
    )
    
    compliance_checklist = TextAreaField(
        'Compliance Checklist',
        validators=[Optional()],
        render_kw={
            "placeholder": "• Obtain business license\n• Register property with city\n• Install safety equipment\n• Maintain insurance coverage",
            "rows": 6
        },
        description="Specific actionable items property owners must complete"
    )
    
    # Contact Information
    local_authority_contact = TextAreaField(
        'Local Authority Contact Information',
        validators=[Optional()],
        render_kw={
            "placeholder": "Department: City Planning Office\nPhone: (555) 123-4567\nEmail: planning@city.gov\nAddress: 123 City Hall Dr",
            "rows": 4
        },
        description="Contact details for relevant local government offices or departments"
    )
    
    # Date Information
    last_updated = DateField(
        'Last Updated',
        validators=[Optional()],
        default=datetime.today,
        description="Date when this regulation information was last verified or updated"
    )
    
    effective_date = DateField(
        'Effective Date',
        validators=[Optional()],
        description="Date when this regulation becomes/became effective"
    )
    
    expiry_date = DateField(
        'Expiry Date',
        validators=[Optional()],
        description="Date when this regulation expires (leave blank if permanent)"
    )
    
    # Legacy fields for backward compatibility (collapsed by default in UI)
    property_type = StringField(
        'Property Type (Legacy)', 
        validators=[Optional(), Length(max=100)],
        description="Legacy single property type field - use 'Property Types' instead"
    )
    
    keywords = StringField(
        'Keywords (Legacy)', 
        validators=[Optional(), Length(max=200)],
        description="Legacy keywords field - use 'Related Keywords' instead"
    )
    
    submit = SubmitField('Save Regulation')


class UpdateForm(FlaskForm):
    """Form for creating/editing updates"""
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    jurisdiction_affected = StringField('Jurisdiction Affected', validators=[DataRequired(), Length(max=100)])
    update_date = DateField('Update Date', validators=[DataRequired()])
    status = SelectField('Status',
                        choices=[('Recent', 'Recent'),
                               ('Upcoming', 'Upcoming'),
                               ('Proposed', 'Proposed')],
                        validators=[DataRequired()])
    
    # Add missing required fields
    category = SelectField('Category',
                          choices=[('Regulatory Changes', 'Regulatory Changes'),
                                 ('Tax Updates', 'Tax Updates'),
                                 ('Licensing Changes', 'Licensing Changes'),
                                 ('Court Decisions', 'Court Decisions'),
                                 ('Industry News', 'Industry News')],
                          validators=[DataRequired()],
                          default='Regulatory Changes')
    
    impact_level = SelectField('Impact Level',
                              choices=[('High', 'High'),
                                     ('Medium', 'Medium'),
                                     ('Low', 'Low')],
                              validators=[DataRequired()],
                              default='Medium')
    
    effective_date = DateField('Effective Date', validators=[Optional()])
    deadline_date = DateField('Deadline Date', validators=[Optional()])
    
    action_required = SelectField('Action Required',
                                 choices=[('True', 'Yes'),
                                        ('False', 'No')],
                                 validators=[DataRequired()],
                                 default='False')
    
    action_description = TextAreaField('Action Description', validators=[Optional()])
    
    property_types = SelectField('Property Types',
                                choices=[('Residential', 'Residential'),
                                       ('Commercial', 'Commercial'),
                                       ('Both', 'Both')],
                                validators=[DataRequired()],
                                default='Both')
    
    related_regulation_ids = StringField('Related Regulation IDs (comma-separated)', validators=[Optional()])
    tags = StringField('Tags (comma-separated)', validators=[Optional()])
    source_url = StringField('Source URL', validators=[Optional(), Length(max=500)])
    
    priority = SelectField('Priority',
                          choices=[('1', 'High'),
                                 ('2', 'Medium'),
                                 ('3', 'Low')],
                          validators=[DataRequired()],
                          default='3')
    
    # New fields for expanded functionality
    expected_decision_date = DateField(
        'Expected Decision Date',
        validators=[Optional()],
        description="Expected date when a decision will be made on this proposed change"
    )
    
    potential_impact = TextAreaField(
        'Potential Impact',
        validators=[Optional()],
        render_kw={
            "placeholder": "Describe the potential impact on property owners and operators...",
            "rows": 4
        },
        description="Assessment of how this change might affect short-term rental operators"
    )
    
    decision_status = SelectField(
        'Decision Status',
        choices=[
            ('', 'Not Applicable'),
            ('Under Review', 'Under Review'),
            ('Public Hearings', 'Public Hearings'),
            ('Proposed', 'Proposed'),
            ('Approved', 'Approved'),
            ('Rejected', 'Rejected')
        ],
        validators=[Optional()],
        description="Current status of the decision-making process for proposed changes"
    )
    
    change_type = SelectField(
        'Change Type',
        choices=[
            ('Recent', 'Recent - Already implemented'),
            ('Upcoming', 'Upcoming - Will be implemented'),
            ('Proposed', 'Proposed - Under consideration')
        ],
        validators=[DataRequired()],
        default='Recent',
        description="Type of change based on implementation timeline"
    )
    
    compliance_deadline = DateField(
        'Compliance Deadline',
        validators=[Optional()],
        description="Deadline by which operators must comply with this change"
    )
    
    affected_operators = TextAreaField(
        'Affected Operators',
        validators=[Optional()],
        render_kw={
            "placeholder": "Describe which types of operators are affected (e.g., all STR operators, only commercial operators, etc.)...",
            "rows": 3
        },
        description="Description of which operators or property types are affected by this change"
    )
    
    submit = SubmitField('Save Update') 