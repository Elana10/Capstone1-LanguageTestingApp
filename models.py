"""SQLAlchemy models for Language Games."""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from random import choice
 
bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    """Connect this database to provided Flask app.
    You should call this in your Flask app.
    """
    db.app = app
    db.init_app(app)

class Scores(db.Model):
    """Record of scores by each user for each story-attempt."""
    __tablename__ = 'scores'

    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="cascade"))
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id', ondelete="cascade"))
    score = db.Column(db.Float, nullable = False)
    created_at = db.Column(db.DateTime, nullable = False)
    story = db.relationship('Story')

    def __repr__(self):
        return f"User: {self.user_id} Score:{self.score} Story:{self.story_id} "


class Story(db.Model):
    """Translated text models for users to attempt/play."""
    __tablename__ = 'stories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="cascade"))
    base_language = db.Column(db.String, nullable = False)
    foreign_language = db.Column(db.String, nullable = False)
    title = db.Column(db.String, nullable = False)
    sentences = db.relationship('StorySentence')
    scores = db.relationship('Scores')

    def __repr__(self):
        return f"<ID {self.id} {self.title} from {self.base_language} to {self.foreign_language}>"

class StorySentence(db.Model):
    """A translated sentence for each line in the story."""
    __tablename__ = 'sentences'

    id = db.Column(db.Integer, primary_key = True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id', ondelete="cascade"), nullable = False)
    base_language = db.Column(db.String, nullable = False)
    foreign_language = db.Column(db.String, nullable = False)
    base_sentence = db.Column(db.String, nullable = False)
    translated_sentence = db.Column(db.String, nullable = False)
    # base_tuple = db.Column(db.String, nullable = False)
    # foreign_tuple = db.Column(db.String, nullable = False)
    tokens = db.Column(db.Integer, nullable = False)

class User(db.Model):
    """User information."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key= True)
    email = db.Column(db.Text, nullable = False, unique = True)
    username = db.Column(db.Text, nullable = False, unique = True)
    password = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"
    
    @classmethod
    def signup(cls, username, email, password):
        """ Create a new user. 
        Hashes tje password and adds to the database."""

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username = username,
            email = email, 
            password = hashed_pwd
        )
        db.session.add(user)
        return user
    
    @classmethod
    def authenticate(cls, username, password):
        """ Find user with 'username' and check hashed_ 'password' to database. 
        Return user if matched, return False if incorrect. """

        user = cls.query.filter_by(username = username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user
        
        return False
    