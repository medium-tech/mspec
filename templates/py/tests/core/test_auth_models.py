import unittest

from core.models import *
from core.client import *
from core.db import *

test_ctx = create_db_context()
test_ctx.update(create_client_context())

class SingleModels(unittest.TestCase):

    def test_user_validate(self):

        user_good = User.example()
        user_validated = user_good.validate()
        self.assertEqual(user_good, user_validated)

        user_bad_type = User(
            name='Alice',
            email='alice@nice.com',
            profile=12345
        )
        self.assertRaises(ValueError, user_bad_type.validate)

        user_upper_case = User(
            name='Alice',
            email='Alice@EXAMPLE.com',
            profile='12345'
        )
        user_upper_case.validate()
        self.assertEqual(user_upper_case.email, 'alice@example.com')

    def test_profile_validate(self):

        profile_good = Profile.example()

        profile_validated = profile_good.validate()
        self.assertEqual(profile_good, profile_validated)

        profile_bad_type = Profile.example()
        profile_bad_type.bio = 12345
        
        self.assertRaises(ValueError, profile_bad_type.validate)


if __name__ == '__main__':
    unittest.main()