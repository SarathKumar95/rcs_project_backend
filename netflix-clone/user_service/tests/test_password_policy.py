import unittest

from pydantic import ValidationError

from app.schemas.user import UserCreate


class UserCreatePasswordPolicyTests(unittest.TestCase):
    def test_accepts_password_with_minimum_length_uppercase_and_symbol(self):
        user = UserCreate(email="user@example.com", password="Abcdefghij1!")
        self.assertEqual(user.password, "Abcdefghij1!")

    def test_rejects_password_shorter_than_twelve_characters(self):
        with self.assertRaises(ValidationError):
            UserCreate(email="user@example.com", password="Abcdefghi1!")

    def test_rejects_password_without_uppercase_letter(self):
        with self.assertRaises(ValidationError):
            UserCreate(email="user@example.com", password="abcdefghijkl1!")

    def test_rejects_password_without_symbol(self):
        with self.assertRaises(ValidationError):
            UserCreate(email="user@example.com", password="Abcdefghijkl1")


if __name__ == "__main__":
    unittest.main()
