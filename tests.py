"""Tests for Rich City Stops."""


import os

os.environ["DATABASE_URL"] = "postgresql:///rich_city_test"
os.environ["FLASK_DEBUG"] = "0"

import re
from unittest import TestCase

from flask import session
from app import app, CURR_USER_KEY
from models import db, Stop, Neighborhood, User

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

# Don't req CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False

db.drop_all()
db.create_all()

#######################################
# helper functions for tests


def debug_html(response, label="DEBUGGING"):  # pragma: no cover
    """Prints HTML response; useful for debugging tests."""

    print("\n\n\n", "*********", label, "\n")
    print(response.data.decode('utf8'))
    print("\n\n")


def login_for_test(client, user_id):
    """Log in this user."""

    with client.session_transaction() as sess:
        sess[CURR_USER_KEY] = user_id


#######################################
# data to use for test objects / testing forms


NEIGHBORHOOD_DATA = dict(
    code="point",
    name="Point Richmond"
)

STOP_DATA = dict(
    name="Test Stop",
    description="Test description",
    url="http://teststop.com/",
    address="500 Andrade Ave",
    hood_code="point",
    image_url="http://teststopimg.com/"
)

STOP_DATA_EDIT = dict(
    name="new-name",
    description="new-description",
    url="http://new-image.com/",
    address="500 Humboldt St",
    hood_code="point",
    image_url="http://new-image.com/"
)

TEST_USER_DATA = dict(
    username="test",
    first_name="Testy",
    last_name="MacTest",
    description="Test Description.",
    email="test@test.com",
    password="secret",
)

TEST_USER_DATA_EDIT = dict(
    first_name="new-fn",
    last_name="new-ln",
    description="new-description",
    email="new-email@test.com",
    image_url="http://new-image.com",
)

TEST_USER_DATA_NEW = dict(
    username="new-username",
    first_name="new-fn",
    last_name="new-ln",
    description="new-description",
    password="secret",
    email="new-email@test.com",
    image_url="http://new-image.com",
)

ADMIN_USER_DATA = dict(
    username="admin",
    first_name="Addie",
    last_name="MacAdmin",
    description="Admin Description.",
    email="admin@test.com",
    password="secret",
    admin=True,
)


#######################################
# homepage


class HomepageViewsTestCase(TestCase):
    """Tests about homepage."""

    def test_homepage(self):
        with app.test_client() as client:
            resp = client.get("/")
            self.assertIn(b'RICHCITYSTOPS', resp.data)


#######################################
# neighborhoods


class NeighborhoodModelTestCase(TestCase):
    """Tests for Neighborhood Model."""

    def setUp(self):
        """Before all tests, add sample hood & users"""

        Stop.query.delete()
        Neighborhood.query.delete()

        point = Neighborhood(**NEIGHBORHOOD_DATA)
        db.session.add(point)

        stop = Stop(**STOP_DATA)
        db.session.add(stop)

        db.session.commit()

        self.stop = stop

    def tearDown(self):
        """After each test, remove all stops."""

        Stop.query.delete()
        Neighborhood.query.delete()
        db.session.commit()

    # depending on how you solve exercise, you may have things to test on
    # the Neighborhood model, so here's a good place to put that stuff.


#######################################
# stops


class StopModelTestCase(TestCase):
    """Tests for Stop Model."""

    def setUp(self):
        """Before all tests, add sample hood & users"""

        Stop.query.delete()
        Neighborhood.query.delete()

        point = Neighborhood(**NEIGHBORHOOD_DATA)
        db.session.add(point)

        stop = Stop(**STOP_DATA)
        db.session.add(stop)

        db.session.commit()

        self.stop = stop

    def tearDown(self):
        """After each test, remove all stops."""

        Stop.query.delete()
        Neighborhood.query.delete()
        db.session.commit()


class StopViewsTestCase(TestCase):
    """Tests for views on stops."""

    def setUp(self):
        """Before all tests, add sample city & users"""

        Stop.query.delete()
        Neighborhood.query.delete()
        User.query.delete()

        point = Neighborhood(**NEIGHBORHOOD_DATA)
        db.session.add(point)

        stop = Stop(**STOP_DATA)
        db.session.add(stop)

        user = User.register(**TEST_USER_DATA)
        db.session.add(user)

        db.session.commit()

        self.stop_id = stop.id
        self.user_id = user.id

    def tearDown(self):
        """After each test, remove all stops."""

        Stop.query.delete()
        Neighborhood.query.delete()
        User.query.delete()
        db.session.commit()

    def test_list(self):
        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get("/stops")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Test Stop", resp.data)

    def test_detail(self):
        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get(f"/stops/{self.stop_id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Test Stop", resp.data)
            self.assertIn(b'teststop.com', resp.data)


class StopAdminViewsTestCase(TestCase):
    """Tests for add/edit views on stops."""

    def setUp(self):
        """Before each test, add sample hood, users, and stops"""

        Neighborhood.query.delete()
        Stop.query.delete()
        User.query.delete()

        point = Neighborhood(**NEIGHBORHOOD_DATA)
        db.session.add(point)

        stop = Stop(**STOP_DATA)
        db.session.add(stop)

        user = User.register(**ADMIN_USER_DATA)
        db.session.add(user)

        db.session.commit()

        self.stop_id = stop.id
        self.user_id = user.id

    def tearDown(self):
        """After each test, delete the cities."""

        Stop.query.delete()
        Neighborhood.query.delete()
        User.query.delete()
        db.session.commit()

    def test_add(self):
        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get(f"/stops/add")
            self.assertIn(b'Add Stop', resp.data)

            resp = client.post(
                f"/stops/add",
                data=STOP_DATA_EDIT,
                follow_redirects=True)
            self.assertIn(b'added', resp.data)

    def test_dynamic_cities_vocab(self):
        id = self.stop_id

        # the following is a regular expression for the HTML for the drop-down
        # menu pattern we want to check for
        choices_pattern = re.compile(
            r'<select [^>]*name="hood_code"[^>]*><option [^>]*value="point">' +
            r'Point Richmond</option></select>')

        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get(f"/stops/add")
            self.assertRegex(resp.data.decode('utf8'), choices_pattern)

            resp = client.get(f"/stops/{id}/edit")
            self.assertRegex(resp.data.decode('utf8'), choices_pattern)

    def test_edit(self):
        id = self.stop_id

        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get(f"/stops/{id}/edit", follow_redirects=True)
            self.assertIn(b'Edit StopName', resp.data)

            resp = client.post(
                f"/stops/{id}/edit",
                data=STOP_DATA_EDIT,
                follow_redirects=True)
            self.assertIn(b'edited', resp.data)

    def test_edit_form_shows_curr_data(self):
        id = self.stop_id

        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get(f"/stops/{id}/edit", follow_redirects=True)
            self.assertIn(b'Test description', resp.data)


#######################################
# users


class UserModelTestCase(TestCase):
    """Tests for the user model."""

    def setUp(self):
        """Before each test, add sample users."""

        User.query.delete()
        user = User.register(**TEST_USER_DATA)
        db.session.add(user)

        db.session.commit()

        self.user = user

    def tearDown(self):
        """After each test, remove all users."""
        db.session.rollback()
        User.query.delete()
        db.session.flush()

    def test_authenticate(self):
        rez = User.authenticate("test", "secret")
        self.assertEqual(rez, self.user)

    def test_authenticate_fail(self):
        rez = User.authenticate("no-such-user", "secret")
        self.assertFalse(rez)

        rez = User.authenticate("test", "password")
        self.assertFalse(rez)

    def test_full_name(self):
        self.assertEqual(self.user.get_full_name(), "Testy MacTest")

    def test_register(self):
        u = User.register(**TEST_USER_DATA)
        # test that password gets bcrypt-hashed (all start w/$2b$)
        self.assertEqual(u.hashed_password[:4], "$2b$")
        db.session.rollback()


class AuthViewsTestCase(TestCase):
    """Tests for views on logging in/logging out/registration."""

    def setUp(self):
        """Before each test, add sample users."""

        User.query.delete()

        user = User.register(**TEST_USER_DATA)
        db.session.add(user)

        db.session.commit()

        self.user_id = user.id

    def tearDown(self):
        """After each test, remove all users."""

        User.query.delete()
        db.session.commit()

    def test_signup(self):
        with app.test_client() as client:
            resp = client.get("/signup")
            self.assertIn(b'Sign Up', resp.data)

            resp = client.post(
                "/signup",
                data=TEST_USER_DATA_NEW,
                follow_redirects=True,
            )

            self.assertIn(b"Hello, new-username", resp.data)
            self.assertTrue(session.get(CURR_USER_KEY))

    def test_signup_username_taken(self):
        with app.test_client() as client:
            resp = client.get("/signup")
            self.assertIn(b'Sign Up', resp.data)

            # signup with same data as the already-added user
            resp = client.post(
                "/signup",
                data=TEST_USER_DATA,
                follow_redirects=True,
            )

            self.assertIn(b"Username already taken", resp.data)

    def test_login(self):
        with app.test_client() as client:
            resp = client.get("/login")
            self.assertIn(b'Welcome Back!', resp.data)

            resp = client.post(
                "/login",
                data={"username": "test", "password": "WRONG"},
                follow_redirects=True,
            )

            self.assertIn(b"Invalid credentials", resp.data)

            resp = client.post(
                "/login",
                data={"username": "test", "password": "secret"},
                follow_redirects=True,
            )

            self.assertIn(b"Hello, test", resp.data)
            self.assertEqual(session.get(CURR_USER_KEY), self.user_id)

    def test_logout(self):
        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.post("/logout", follow_redirects=True)

            self.assertIn(b"Successfully logged out", resp.data)
            self.assertEqual(session.get(CURR_USER_KEY), None)


class NavBarTestCase(TestCase):
    """Tests navigation bar."""

    def setUp(self):
        """Before tests, add sample user."""

        User.query.delete()

        user = User.register(**TEST_USER_DATA)

        db.session.add_all([user])
        db.session.commit()

        self.user_id = user.id

    def tearDown(self):
        """After tests, remove all users."""

        User.query.delete()
        db.session.commit()

    def test_anon_navbar(self):
        with app.test_client() as client:
            resp = client.get('/')

            self.assertIn(b"Log In", resp.data)
            self.assertEqual(resp.status_code, 200)

    def test_logged_in_navbar(self):
        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get('/')

            self.assertIn(b"Log Out", resp.data)
            self.assertEqual(resp.status_code, 200)


class ProfileViewsTestCase(TestCase):
    """Tests for views on user profiles."""

    def setUp(self):
        """Before each test, add sample user."""

        User.query.delete()

        user = User.register(**TEST_USER_DATA)
        db.session.add(user)

        db.session.commit()

        self.user_id = user.id

    def tearDown(self):
        """After each test, remove all users."""

        User.query.delete()
        db.session.commit()

    def test_anon_profile(self):
        with app.test_client() as client:
            resp = client.get(f'/users/{self.user_id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized", resp.data)

    def test_logged_in_profile(self):
        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get(f'/users/{self.user_id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Testy MacTest', resp.data)

    def test_anon_profile_edit(self):
        with app.test_client() as client:
            resp = client.get(
                f'/users/{self.user_id}/edit', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized", resp.data)

    def test_logged_in_profile_edit(self):
        with app.test_client() as client:
            login_for_test(client, self.user_id)

            resp = client.post(
                f'/users/{self.user_id}/edit',
                data=TEST_USER_DATA_EDIT,
                follow_redirects=True
            )

            self.assertIn(b'Profile edited', resp.data)
            self.assertEqual(resp.status_code, 200)


#######################################
# likes


class LikeViewsTestCase(TestCase):
    """Tests for views on cafes."""

    def setUp(self):
        """ Before each test add sample user and stop
            add stop to users liked stops
        """
        User.query.delete()
        Stop.query.delete()
        Neighborhood.query.delete()

        user = User.register(**TEST_USER_DATA)
        stop = Stop(**STOP_DATA)
        point = Neighborhood(**NEIGHBORHOOD_DATA)
        db.session.add_all([user, stop, point])

        db.session.commit()

        self.user_id = user.id
        self.stop_id = stop.id

    def tearDown(self):
        """After each test, remove all users and stops"""

        User.query.delete()
        Stop.query.delete()
        Neighborhood.query.delete()
        db.session.commit()

    def test_user_no_liked_stops(self):
        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get(f'/users/{self.user_id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'You have no liked Stops', resp.data)
