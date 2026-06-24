import unittest
from app.services.field_patterns import (
    validate_date, validate_pan, validate_aadhaar, validate_mobile, validate_pincode, validate_survey_no
)

class TestValidators(unittest.TestCase):
    def test_validate_date(self):
        self.assertTrue(validate_date("17-02-2026"))
        self.assertTrue(validate_date("17/02/2026"))
        self.assertTrue(validate_date("2026-02-17"))
        self.assertFalse(validate_date("not a date"))

    def test_validate_pan(self):
        self.assertTrue(validate_pan("ABCDE1234F"))
        self.assertTrue(validate_pan("abcde1234f"))
        self.assertFalse(validate_pan("ABC1234"))

    def test_validate_aadhaar(self):
        self.assertTrue(validate_aadhaar("1234 5678 9012"))
        self.assertTrue(validate_aadhaar("123456789012"))
        self.assertFalse(validate_aadhaar("12345"))

    def test_validate_mobile(self):
        self.assertTrue(validate_mobile("9876543210"))
        self.assertTrue(validate_mobile("+91 8765432109"))
        self.assertFalse(validate_mobile("12345"))

    def test_validate_pincode(self):
        self.assertTrue(validate_pincode("500089"))
        self.assertFalse(validate_pincode("50008"))

    def test_validate_survey_no(self):
        self.assertTrue(validate_survey_no("90/A"))
        self.assertFalse(validate_survey_no("1"))

if __name__ == "__main__":
    unittest.main()
