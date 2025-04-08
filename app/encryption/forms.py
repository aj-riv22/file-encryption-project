from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length

class EncryptForm(FlaskForm):
    file = FileField('File to Encrypt', validators=[FileRequired()])
    password = PasswordField('Encryption Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Encrypt')

class DecryptForm(FlaskForm):
    password = PasswordField('Decryption Password', validators=[DataRequired()])
    submit = SubmitField('Decrypt')

class ShareFileForm(FlaskForm):
    user = SelectField('Share with User', coerce=int, validators=[DataRequired()])
    access_level = SelectField('Access Level', 
                              choices=[('read', 'Read Only'), ('write', 'Read and Write')],
                              default='read')
    submit = SubmitField('Share File')