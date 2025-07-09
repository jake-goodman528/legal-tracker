from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

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
    submit = SubmitField('Save Regulation')

class UpdateForm(FlaskForm):
    title = StringField('Update Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    jurisdiction_affected = StringField('Jurisdiction Affected', validators=[DataRequired(), Length(max=100)])
    update_date = DateField('Update Date', validators=[DataRequired()])
    status = SelectField('Status',
                        choices=[('Recent', 'Recent'), ('Upcoming', 'Upcoming'), ('Proposed', 'Proposed')],
                        validators=[DataRequired()])
    submit = SubmitField('Save Update')
