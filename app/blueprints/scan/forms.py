from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

class ScanUploadForm(FlaskForm):
    mri_image = FileField('MRI Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'JPG and PNG only.')
    ])
    submit = SubmitField('Analyse')