import unittest
from speedview.models.settings import Settings

class TestSettings(unittest.TestCase):
    def test_default_settings(self):
        settings = Settings()
        self.assertEqual(settings.max_speed, 100)
        self.assertEqual(settings.update_interval, 1.0)

if __name__ == '__main__':
    unittest.main()