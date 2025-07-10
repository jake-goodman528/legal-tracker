from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, PasswordField, SubmitField
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
    
    submit = SubmitField('Save Update') 