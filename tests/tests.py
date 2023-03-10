import os
from datetime import datetime, timedelta
import unittest

from app import app
from app import db
from app.models import User
from app.models import Post

os.environ["DATABASE_URL"] = "sqlite://"


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username="admin")
        u.set_password("admin")
        self.assertFalse(u.check_password("password"))
        self.assertTrue(u.check_password("admin"))

    def test_avatar(self):
        u = User(username="admin", email="admin@example.com")
        self.assertEqual(u.avatar(128), ("https://www.gravatar.com/avatar/"
                                         "e64c7d89f26bd1972efa854d13d7dd61"
                                         "?d=identicon&s=128"))

    def test_follow(self):
        u1 = User(username="admin", email="admin@example.com")
        u2 = User(username="user", email="user@gmail.com")
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, "user")
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, "admin")

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        # Create 4 users
        u1 = User(username="admin", email="admin@example.com")
        u2 = User(username="user", email="user@gmail.com")
        u3 = User(username="john", email="john@example.com")
        u4 = User(username="susan", email="susan@example.com")
        db.session.add_all([u1, u2, u3, u4])

        # Create 4 posts
        now = datetime.utcnow()
        p1 = Post(body="Post from admin", author=u1, timestamp=now+timedelta(seconds=1))
        p2 = Post(body="Post from user", author=u2, timestamp=now+timedelta(seconds=4))
        p3 = Post(body="Post from john", author=u3, timestamp=now+timedelta(seconds=3))
        p4 = Post(body="Post from susan", author=u4, timestamp=now+timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # Setup the followers
        u1.follow(u2)  # admin follows user
        u1.follow(u4)  # admin follows susan
        u2.follow(u3)  # user follows john
        u3.follow(u4)  # john follows susan
        db.session.commit()

        # Check the followed posts of each user
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()

        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])


if __name__ == '__main__':
    unittest.main(verbosity=2)
