import unittest
from app import app
import json

class TestCropRecommendation(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_home_page(self):
        """Test home page loads with new tabs."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('Leaf Disease', content)
        self.assertIn('Crop Recommender', content)

    def test_recommendation_flow_city(self):
        """Test recommendation with City input."""
        # Mocking external requests would be better, but for integration test 
        # let's see if it actually hits the public APIs (user has internet).
        response = self.client.post('/recommend', data={
            'city': 'London',
            'lat': '',
            'lon': ''
        })
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('Recommended Crop:', content)
        self.assertIn('London', content)

    def test_recommendation_flow_coords(self):
        """Test recommendation with Lat/Lon input."""
        response = self.client.post('/recommend', data={
            'city': '',
            'lat': '51.51',
            'lon': '-0.13'
        })
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('Recommended Crop:', content)
        self.assertIn('51.51, -0.13', content)

if __name__ == '__main__':
    unittest.main()
