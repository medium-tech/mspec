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
            name=False,
            email='alice@nice.com'
        )
        self.assertRaises(ValueError, user_bad_type.validate)

        user_upper_case = User(
            name='Alice',
            email='Alice@EXAMPLE.com'
        )
        user_upper_case.validate()
        self.assertEqual(user_upper_case.email, 'alice@example.com')


if __name__ == '__main__':
    unittest.main()