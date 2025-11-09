import unittest
from src.app import app

class TestGateway(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = app.test_client()
        cls.app.testing = True

    def test_route_service(self):
        response = self.app.get('/api/routes')
        self.assertEqual(response.status_code, 200)

    def test_stop_service(self):
        response = self.app.get('/api/stops')
        self.assertEqual(response.status_code, 200)

    def test_bus_service(self):
        response = self.app.get('/api/buses')
        self.assertEqual(response.status_code, 200)

    def test_schedule_service(self):
        response = self.app.get('/api/schedules')
        self.assertEqual(response.status_code, 200)

    def test_user_service(self):
        response = self.app.get('/api/users')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()