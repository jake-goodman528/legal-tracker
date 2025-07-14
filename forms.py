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
    """Enhanced form for creating/editing regulations with new template structure"""
    
    # Core Information
    jurisdiction = SelectField(
        'Jurisdiction', 
        choices=[('National', 'National'), ('State', 'State'), ('Local', 'Local')],
        validators=[DataRequired()],
        description="The level of government jurisdiction"
    )
    
    jurisdiction_level = SelectField(
        'Jurisdiction Level',
        choices=[('National', 'National'), ('State', 'State'), ('Local', 'Local')],
        validators=[DataRequired()],
        description="Level of government jurisdiction"
    )
    
    location = SelectField(
        'Location', 
        choices=[],  # Will be populated dynamically based on jurisdiction_level
        validators=[DataRequired()],
        description="Geographic area where this regulation applies"
    )
    
    title = StringField(
        'Regulation Title', 
        validators=[DataRequired(), Length(min=5, max=200)],
        render_kw={"placeholder": "Enter a descriptive regulation title"},
        description="Clear, concise title describing the regulation"
    )
    
    last_updated = DateField(
        'Last Updated',
        validators=[Optional()],
        default=datetime.today,
        description="Date when this regulation information was last verified or updated"
    )
    
    # Rich Text Content Fields - Support formatting (bold, indent, numbering, bullet points, etc.)
    overview = TextAreaField(
        'Overview',
        validators=[Optional()],
        render_kw={
            "placeholder": "Provide a comprehensive overview of this regulation...",
            "rows": 6,
            "class": "rich-text-editor"
        },
        description="High-level overview and summary of the regulation"
    )
    
    detailed_requirements = TextAreaField(
        'Detailed Requirements',
        validators=[Optional()],
        render_kw={
            "placeholder": "List the detailed compliance requirements...",
            "rows": 8,
            "class": "rich-text-editor"
        },
        description="Comprehensive breakdown of all requirements and obligations"
    )
    
    compliance_steps = TextAreaField(
        'Compliance Steps',
        validators=[Optional()],
        render_kw={
            "placeholder": "Outline the specific steps for compliance...",
            "rows": 6,
            "class": "rich-text-editor"
        },
        description="Step-by-step process for achieving compliance"
    )
    
    required_forms = TextAreaField(
        'Required Forms',
        validators=[Optional()],
        render_kw={
            "placeholder": "List all forms, documents, and submissions required...",
            "rows": 4,
            "class": "rich-text-editor"
        },
        description="All forms, documents, and official submissions required"
    )
    
    penalties_non_compliance = TextAreaField(
        'Penalties for Non Compliance',
        validators=[Optional()],
        render_kw={
            "placeholder": "Describe penalties, fines, and consequences for non-compliance...",
            "rows": 4,
            "class": "rich-text-editor"
        },
        description="Penalties, fines, and consequences for failing to comply"
    )
    
    recent_changes = TextAreaField(
        'Recent Changes',
        validators=[Optional()],
        render_kw={
            "placeholder": "Document any recent changes or updates to this regulation...",
            "rows": 4,
            "class": "rich-text-editor"
        },
        description="Recent modifications, amendments, or updates to the regulation"
    )
    
    submit = SubmitField('Save Regulation')
    
    def populate_location_choices(self):
        """Populate location choices based on the selected jurisdiction_level"""
        from models import get_location_options_by_jurisdiction
        
        if self.jurisdiction_level.data:
            locations = get_location_options_by_jurisdiction(self.jurisdiction_level.data)
            self.location.choices = [('', 'Select Location')] + [(loc, loc) for loc in locations]
        else:
            self.location.choices = [('', 'Select Jurisdiction Level First')]


class UpdateForm(FlaskForm):
    """Form for creating/editing updates"""
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()], render_kw={"rows": 4})
    jurisdiction = SelectField(
        'Jurisdiction',
        choices=[('National', 'National'), ('State', 'State'), ('Local', 'Local')],
        validators=[DataRequired()],
        description="Level of government jurisdiction"
    )
    jurisdiction_affected = SelectField(
        'Location',
        choices=[],  # Will be populated dynamically
        validators=[DataRequired()],
        description="Geographic area where this update applies"
    )
    jurisdiction_level = SelectField(
        'Jurisdiction Level',
        choices=[('National', 'National'), ('State', 'State'), ('Local', 'Local')],
        validators=[DataRequired()],
        description="Level of government jurisdiction"
    )
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
    
    source_url = StringField('Source URL', validators=[Optional(), Length(max=500)])
    
    priority = SelectField('Priority',
                          choices=[('1', 'High'),
                                 ('2', 'Medium'),
                                 ('3', 'Low')],
                          validators=[DataRequired()],
                          default='3')
    
    tags = StringField('Tags', validators=[Optional(), Length(max=200)], 
                      description="Comma-separated tags for categorization")
    
    potential_impact = TextAreaField(
        'Potential Impact',
        validators=[Optional()],
        render_kw={
            "placeholder": "Describe the potential impact of this change...",
            "rows": 4
        },
        description="Description of the potential impact on property operators"
    )
    
    affected_operators = TextAreaField(
        'Affected Operators',
        validators=[Optional()],
        render_kw={
            "placeholder": "Describe which operators are affected by this change...",
            "rows": 3
        },
        description="Description of which types of operators are affected"
    )
    
    # New fields for expanded functionality
    expected_decision_date = DateField(
        'Expected Decision Date',
        validators=[Optional()],
        description="Expected date when a decision will be made on this proposed change"
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
    
    related_regulation_ids = StringField(
        'Related Regulation IDs',
        validators=[Optional(), Length(max=200)],
        description="Comma-separated IDs of related regulations"
    )
    
    # New template fields for structured public-facing display
    summary = TextAreaField(
        'Summary',
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Enter a brief summary of the update...",
            "rows": 4,
            "class": "rich-text-editor"
        },
        description="Brief summary of the update for the Summary section"
    )
    
    full_text = TextAreaField(
        'Full Text',
        validators=[Optional()],
        render_kw={
            "placeholder": "Enter the complete detailed text of the update...",
            "rows": 8,
            "class": "rich-text-editor"
        },
        description="Complete detailed text of the update with full context and information"
    )
    
    compliance_requirements = TextAreaField(
        'Compliance Requirements',
        validators=[Optional()],
        render_kw={
            "placeholder": "List specific compliance requirements that operators must meet...",
            "rows": 6,
            "class": "rich-text-editor"
        },
        description="Specific compliance requirements and obligations for property operators"
    )
    
    implementation_timeline = TextAreaField(
        'Implementation Timeline',
        validators=[Optional()],
        render_kw={
            "placeholder": "Describe the timeline for implementing these changes...",
            "rows": 4,
            "class": "rich-text-editor"
        },
        description="Timeline and phases for implementing the regulatory changes"
    )
    
    official_sources = TextAreaField(
        'Official Sources',
        validators=[Optional()],
        render_kw={
            "placeholder": "List official sources, documents, and references...",
            "rows": 4,
            "class": "rich-text-editor"
        },
        description="Official sources, documents, and authoritative references"
    )
    
    expert_analysis = TextAreaField(
        'Expert Analysis: Kaystreet Management\'s Interpretation',
        validators=[Optional()],
        render_kw={
            "placeholder": "Provide Kaystreet Management's expert interpretation and analysis...",
            "rows": 6,
            "class": "rich-text-editor"
        },
        description="Kaystreet Management's expert interpretation and analysis of the regulatory change"
    )
    
    kaystreet_commitment = TextAreaField(
        'Kaystreet Management\'s Commitment',
        validators=[Optional()],
        render_kw={
            "placeholder": "Describe Kaystreet Management's commitment to helping clients...",
            "rows": 4,
            "class": "rich-text-editor"
        },
        description="Kaystreet Management's commitment statement regarding client support and guidance"
    )
    
    submit = SubmitField('Save Update')
    
    def populate_location_choices(self):
        """Populate location choices based on the selected jurisdiction"""
        from models import get_location_options_by_jurisdiction
        
        # Use jurisdiction field for Updates (it's called jurisdiction, not jurisdiction_level)
        jurisdiction_level = self.jurisdiction.data
        
        if jurisdiction_level:
            locations = get_location_options_by_jurisdiction(jurisdiction_level)
            self.jurisdiction_affected.choices = [('', 'Select Location')] + [(loc, loc) for loc in locations]
        else:
            self.jurisdiction_affected.choices = [('', 'Select Jurisdiction First')] 