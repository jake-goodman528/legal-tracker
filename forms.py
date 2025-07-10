from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Optional


class LoginForm(FlaskForm):
    """Form for admin login"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Login')


class RegulationForm(FlaskForm):
    """Form for creating/editing regulations"""
    jurisdiction_level = SelectField('Jurisdiction Level', 
                                   choices=[('National', 'National'), 
                                          ('State', 'State'), 
                                          ('Local', 'Local')],
                                   validators=[DataRequired()])
    
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    key_requirements = TextAreaField('Key Requirements', validators=[DataRequired()])
    last_updated = DateField('Last Updated', validators=[DataRequired()])
    
    # Optional fields
    category = StringField('Category', validators=[Optional(), Length(max=100)])
    compliance_level = SelectField('Compliance Level',
                                 choices=[('Required', 'Required'),
                                        ('Recommended', 'Recommended'),
                                        ('Optional', 'Optional')],
                                 validators=[Optional()])
    property_type = StringField('Property Type', validators=[Optional(), Length(max=100)])
    effective_date = DateField('Effective Date', validators=[Optional()])
    expiry_date = DateField('Expiry Date', validators=[Optional()])
    keywords = StringField('Keywords', validators=[Optional(), Length(max=200)])
    
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
    
    submit = SubmitField('Save Update') 