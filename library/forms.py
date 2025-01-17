from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, FileField, SelectField, TextAreaField,DecimalField
from library.models import User,Book,Section
from wtforms.validators import DataRequired,Length,Email,EqualTo,ValidationError,NumberRange,Regexp

        
class RegistrationForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddSectionForm(FlaskForm):
    name = StringField('Section Name', validators=[DataRequired(), Length(min=3, max=50), Regexp(r'^[^0-9]*$', message="Name field should not contain numbers.")])
    description = TextAreaField('Section Description', validators=[DataRequired(), Length(min=10, max=200)])
    submit = SubmitField('Add Section')

class AddBookForm(FlaskForm):
    book_name = StringField('Book Name', validators=[DataRequired(), Length(min=3, max=100)])
    book_content = FileField('Book Content', validators=[FileRequired(), FileAllowed(['pdf'], 'PDF files only')])
    book_thumbnail = FileField('Book Thumbnail', validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Image files only')])
    authors = StringField('Authors', validators=[DataRequired(), Length(min=3, max=100), Regexp(r'^[^0-9]*$', message="Authors field should not contain numbers.")])
    section = SelectField('Section', validators=[DataRequired()])
    book_price = DecimalField('Book Price', validators=[DataRequired(), NumberRange(min=0, max=9999.99)])
    submit = SubmitField('Add Book')

class EditBookForm(FlaskForm):
    book_select = SelectField('Book to Edit', validators=[DataRequired()])
    book_name = StringField('Book Name', validators=[Length(min=3, max=100)])
    book_content = FileField('Book Content', validators=[FileAllowed(['pdf'], 'PDF files only')])
    book_thumbnail = FileField('Book Thumbnail', validators=[FileAllowed(['jpg', 'png'], 'Image files only')])
    authors = StringField('Authors', validators=[Length(min=3, max=100), Regexp(r'^[^0-9]*$', message="Authors field should not contain numbers.")])
    section = SelectField('Section')
    book_price = DecimalField('Book Price', validators=[NumberRange(min=0, max=9999.99)])
    submit = SubmitField('Update Book')

    def __init__(self, *args, **kwargs):
        super(EditBookForm, self).__init__(*args, **kwargs)
        self.book_select.choices = [(book.BookID, book.BookName) for book in Book.query.all()]
        self.section.choices = [(section.SectionID, section.SectionName) for section in Section.query.all()]

class RemoveForm(FlaskForm):
    book_select = SelectField('Book to Edit')
    section = SelectField('Section', validators=[DataRequired()])
    submit = SubmitField('Remove')


    def __init__(self, *args, **kwargs):
        super(RemoveForm, self).__init__(*args, **kwargs)
        self.populate_book_choices()
        self.populate_section_choices()

    def populate_book_choices(self):
        self.book_select.choices = [(book.BookID, book.BookName) for book in Book.query.all()]

    def populate_section_choices(self):
        self.section.choices = [(section.SectionID, section.SectionName) for section in Section.query.all()]

    @property
    def book_choices(self):
        section_id = self.section.data
        if section_id:
            return [(book.BookID, book.BookName) for book in Book.query.filter_by(SectionID=section_id)]
        else:
            return self.book_select.choices