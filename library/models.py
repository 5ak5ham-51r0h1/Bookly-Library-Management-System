from datetime import datetime
from library import db,login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    author_request = db.Column(db.Boolean, default=False)
    author_approval = db.Column(db.Boolean, default=False)
    user_tier = db.Column(db.String(20), default='standard')

    requests = db.relationship("Request", backref="user")
    feedbacks = db.relationship("Feedback", backref="user")


class Section(db.Model):
    SectionID = db.Column(db.Integer, primary_key=True)
    SectionName = db.Column(db.String,unique=True)
    SectionDescription = db.Column(db.String)


class Book(db.Model):
    BookID = db.Column(db.Integer, primary_key=True)
    BookName = db.Column(db.String)
    BookContent = db.Column(db.LargeBinary)
    BookThumbnail = db.Column(db.LargeBinary)
    Authors = db.Column(db.String)
    DateCreated = db.Column(db.DateTime, default=datetime.utcnow)
    SectionID = db.Column(db.Integer, db.ForeignKey('section.SectionID'))
    book_price = db.Column(db.Float)
    
    requests = db.relationship("Request", backref="book", cascade="all, delete-orphan")
    feedbacks = db.relationship("Feedback", backref="book", cascade="all, delete-orphan")

class Request(db.Model):
    RequestID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    BookID = db.Column(db.Integer, db.ForeignKey('book.BookID'), nullable=False)
    RequestDate = db.Column(db.DateTime)
    ReturnDate = db.Column(db.DateTime)
    Status = db.Column(db.String)
    book_bought = db.Column(db.Boolean, default=False)

class Feedback(db.Model):
    FeedbackID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    BookID = db.Column(db.Integer, db.ForeignKey('book.BookID'), nullable=False)
    FeedbackText = db.Column(db.String)
    FeedbackDate = db.Column(db.DateTime)