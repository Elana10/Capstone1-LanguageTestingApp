import os
from unittest import TestCase
from models import db, User, Story, StorySentence, Scores

os.environ['DATABASE_URL'] = 'postgresql:///translate-test'

from app import app

db.create_all()

class UserModelTestCase(TestCase):
    """Tests User Model"""

    def setUp(self):
        """Create test"""
        self.client = app.test_client()
        User.query.delete()
        Story.query.delete()
        StorySentence.query.delete()
        Scores.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Create new user."""
        u = User(
            email = 'test@test.com',
            username = 'Test',
            password = 'secretkey'
        )
        db.session.add(u)
        db.session.commit()

        self.assertIn(f"<User #{u.id}: {u.username}, {u.email}>", repr(u))
        self.assertTrue(u.id)

    def test_user_signup_fx(self):
        """Test the User.signup function"""
        u = User.signup(
            email = 'test2@test2.com',
            username = 'Test2',
            password = 'secretkey'            
        )
        db.session.commit()
        
        self.assertIn(f"<User #{u.id}: {u.username}, {u.email}>", repr(u))
        self.assertTrue(u.id)        