import tempfile
import unittest
from pathlib import Path
import importlib.util

MODULE_PATH = Path(__file__).resolve().parents[1] / "password_security.py"
spec = importlib.util.spec_from_file_location("scrum243_password_security", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PasswordService = module.PasswordService
AuthenticationError = module.AuthenticationError
ChangeRequiredError = module.ChangeRequiredError
PasswordPolicyError = module.PasswordPolicyError



class PasswordSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.service = PasswordService(Path(self.temp.name) / 'auth.db')
        self.service.create_user('store_admin', 'Temporary-S3cret-4821')

    def tearDown(self):
        self.temp.cleanup()

    def test_first_login_requires_change(self):
        login = self.service.login('store_admin', 'Temporary-S3cret-4821')
        self.assertTrue(login['must_change_password'])
        with self.assertRaises(ChangeRequiredError):
            self.service.authenticate(login['token'])
        self.assertTrue(self.service.authenticate(login['token'], allow_password_change_only=True))

    def test_change_password_revokes_other_sessions(self):
        a = self.service.login('store_admin', 'Temporary-S3cret-4821')
        b = self.service.login('store_admin', 'Temporary-S3cret-4821')
        new_token = self.service.change_password(a['token'], 'Temporary-S3cret-4821', 'New-Store-Pass-934!')
        for old in (a['token'], b['token']):
            with self.assertRaises(AuthenticationError):
                self.service.authenticate(old, allow_password_change_only=True)
        self.assertFalse(self.service.authenticate(new_token)['must_change_password'])
        with self.assertRaises(AuthenticationError):
            self.service.login('store_admin', 'Temporary-S3cret-4821')
        self.assertFalse(self.service.login('store_admin', 'New-Store-Pass-934!')['must_change_password'])

    def test_menu_change_after_first_login(self):
        first = self.service.login('store_admin', 'Temporary-S3cret-4821')
        current = self.service.change_password(first['token'], 'Temporary-S3cret-4821', 'New-Store-Pass-934!')
        newer = self.service.change_password(current, 'New-Store-Pass-934!', 'Another-Store-Pass-782!')
        self.assertEqual(self.service.authenticate(newer)['username'], 'store_admin')

    def test_wrong_password_and_weak_new_password(self):
        token = self.service.login('store_admin', 'Temporary-S3cret-4821')['token']
        with self.assertRaises(AuthenticationError):
            self.service.change_password(token, 'wrong', 'New-Store-Pass-934!')
        with self.assertRaises(PasswordPolicyError):
            self.service.change_password(token, 'Temporary-S3cret-4821', 'short')
        self.service.authenticate(token, allow_password_change_only=True)

    def test_logout_invalidates_token(self):
        token = self.service.login('store_admin', 'Temporary-S3cret-4821')['token']
        self.service.logout(token)
        with self.assertRaises(AuthenticationError):
            self.service.authenticate(token)


if __name__ == '__main__':
    unittest.main()
