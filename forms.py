from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, URL

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegulationForm(FlaskForm):
    jurisdiction_level = SelectField('Jurisdiction Level', 
                                   choices=[('National', 'National'), ('State', 'State'), ('Local', 'Local')],
                                   validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    title = StringField('Regulation Title', validators=[DataRequired(), Length(max=200)])
    key_requirements = TextAreaField('Key Requirements', validators=[DataRequired()])
    last_updated = DateField('Last Updated', validators=[DataRequired()])
    category = SelectField('Category', 
                          choices=[('Legal', 'Legal'), ('Licensing', 'Licensing'), ('Taxes', 'Taxes'), 
                                  ('Zoning', 'Zoning'), ('Occupancy', 'Occupancy'), ('Registration', 'Registration'), 
                                  ('Discrimination', 'Discrimination')],
                          validators=[DataRequired()])
    submit = SubmitField('Save Regulation')

class UpdateForm(FlaskForm):
    title = StringField('Update Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    jurisdiction_affected = StringField('Jurisdiction Affected', validators=[DataRequired(), Length(max=100)])
    update_date = DateField('Update Date', validators=[DataRequired()])
    status = SelectField('Status',
                        choices=[('Recent', 'Recent'), ('Upcoming', 'Upcoming'), ('Proposed', 'Proposed')],
                        validators=[DataRequired()])
    
    # Enhanced fields
    category = SelectField('Category',
                          choices=[
                              ('Regulatory Changes', 'Regulatory Changes'),
                              ('Tax Updates', 'Tax Updates'),
                              ('Licensing Changes', 'Licensing Changes'),
                              ('Court Decisions', 'Court Decisions'),
                              ('Industry News', 'Industry News')
                          ],
                          default='Regulatory Changes',
                          validators=[DataRequired()])
    
    impact_level = SelectField('Impact Level',
                              choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')],
                              default='Medium',
                              validators=[DataRequired()])
    
    effective_date = DateField('Effective Date', validators=[Optional()])
    deadline_date = DateField('Deadline Date', validators=[Optional()])
    
    action_required = BooleanField('Action Required')
    action_description = TextAreaField('Action Description', validators=[Optional()])
    
    property_types = SelectField('Property Types Affected',
                                choices=[('Residential', 'Residential'), ('Commercial', 'Commercial'), ('Both', 'Both')],
                                default='Both',
                                validators=[DataRequired()])
    
    related_regulation_ids = StringField('Related Regulation IDs (comma-separated)', validators=[Optional()])
    tags = StringField('Tags (comma-separated)', validators=[Optional()])
    source_url = StringField('Official Source URL', validators=[Optional(), URL()])
    
    priority = SelectField('Priority',
                          choices=[('1', 'High Priority'), ('2', 'Medium Priority'), ('3', 'Low Priority')],
                          default='2',
                          validators=[DataRequired()])
    
    submit = SubmitField('Save Update')
