import unittest
from app.services.documents import extract_boundaries

class TestBoundaries(unittest.TestCase):
    def test_basic_boundaries(self):
        lines = [
            "North: Corridor.",
            "Bounded on South by: Open to sky",
            "East: 30 Feet Wide Road",
            "West: Plot 10"
        ]
        required_fields = ["boundaries_north", "boundaries_south", "boundaries_east", "boundaries_west"]
        res = extract_boundaries(lines, required_fields)
        
        self.assertIn("boundaries_north", res)
        self.assertEqual(res["boundaries_north"]["value"], "Corridor.")
        self.assertIn("boundaries_south", res)
        self.assertEqual(res["boundaries_south"]["value"], "Open to sky")
        self.assertIn("boundaries_east", res)
        self.assertEqual(res["boundaries_east"]["value"], "30 Feet Wide Road")
        self.assertIn("boundaries_west", res)
        self.assertEqual(res["boundaries_west"]["value"], "Plot 10")

if __name__ == "__main__":
    unittest.main()
