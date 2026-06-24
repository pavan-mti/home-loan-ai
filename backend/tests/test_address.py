import unittest
from app.services.documents import extract_address

class TestAddress(unittest.TestCase):
    def test_address_normalization(self):
        raw = "h no. 12-3,   flat no. 502,, road 12,, village, mandal"
        expected = "H.No. 12-3, Flat No. 502, road 12, village, mandal"
        self.assertEqual(extract_address(raw), expected)

    def test_door_plot_normalization(self):
        raw = "d no 5-10, plot no 12"
        expected = "Door No. 5-10, Plot No. 12"
        self.assertEqual(extract_address(raw), expected)

if __name__ == "__main__":
    unittest.main()
