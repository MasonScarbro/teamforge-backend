import unittest
import json
from app import app

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        # Set up the test client
        self.app = app.test_client()
        self.app.testing = True

    def test_current_user_no_session(self):
        # Test the /current_user route when no user is logged in
        response = self.app.get('/current_user')
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"No user logged in", response.data)

    def test_add_user_missing_fields(self):
        # Test the /add_user route with missing fields
        response = self.app.post('/add_user', json={
            "username": "testuser",
            "password": "password123"
            # Missing email
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing fields", response.data)

    def test_validate_user_invalid_credentials(self):
        # Test the /validate_user route with invalid credentials
        response = self.app.post('/validate_user', json={
            "username_or_email": "nonexistentuser",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"Invalid username or password", response.data)

    def test_get_user_data_no_username(self):
        # Test the /get_user_data route with no username provided
        response = self.app.post('/get_user_data', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Username is required", response.data)

    def test_upload_file_no_file(self):
        # Test the /upload route with no file part
        response = self.app.post('/upload', data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"No file part", response.data)

if __name__ == '__main__':
    unittest.main()