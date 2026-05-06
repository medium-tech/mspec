import sqlite3
import unittest

from collections import namedtuple

from mapp.context import MappContext, ClientContext, DBContext
from mapp.errors import MappValidationError
from mapp.module.model.db import db_model_create_table
from mapp.types import (
    MAX_LIST_FIELD_ITEMS,
    MAX_LIST_STR_TOTAL_LENGTH,
    MAX_RICH_TEXT_JSON_LENGTH,
    MAX_STR_FIELD_LENGTH,
    _validate_obj,
)


class _FakeModel:
    _model_spec = {
        'name': {'snake_case': 'fake_model'},
        'non_list_fields': [
            {'name': {'snake_case': 'title'}, 'type': 'str'},
            {'name': {'snake_case': 'body'}, 'type': 'str', 'rich_text': True},
        ],
        'list_fields': [],
    }


class TestMappFieldLimits(unittest.TestCase):

    def test_validate_obj_str_max_len(self):
        spec = {
            'title': {'name': {'snake_case': 'title'}, 'type': 'str'},
        }
        Obj = namedtuple('Obj', ['title'])
        with self.assertRaises(MappValidationError):
            _validate_obj(spec, Obj(title='a' * (MAX_STR_FIELD_LENGTH + 1)), 'error')

    def test_validate_obj_rich_text_str_max_len(self):
        spec = {
            'body': {'name': {'snake_case': 'body'}, 'type': 'str', 'rich_text': True},
        }
        Obj = namedtuple('Obj', ['body'])
        with self.assertRaises(MappValidationError):
            _validate_obj(spec, Obj(body='a' * (MAX_RICH_TEXT_JSON_LENGTH + 1)), 'error')

    def test_validate_obj_list_item_count_limit(self):
        spec = {
            'tags': {'name': {'snake_case': 'tags'}, 'type': 'list', 'element_type': 'int'},
        }
        Obj = namedtuple('Obj', ['tags'])
        with self.assertRaises(MappValidationError):
            _validate_obj(spec, Obj(tags=list(range(MAX_LIST_FIELD_ITEMS + 1))), 'error')

    def test_validate_obj_list_str_total_len_limit(self):
        spec = {
            'tags': {'name': {'snake_case': 'tags'}, 'type': 'list', 'element_type': 'str'},
        }
        Obj = namedtuple('Obj', ['tags'])
        with self.assertRaises(MappValidationError):
            _validate_obj(
                spec,
                Obj(tags=['a' * 400, 'a' * 400, 'a' * (MAX_LIST_STR_TOTAL_LENGTH - 800 + 1)]),
                'error'
            )

    def test_db_model_create_table_includes_str_length_checks(self):
        conn = sqlite3.connect(':memory:')
        ctx = MappContext(
            server_port=0,
            client=ClientContext(host='http://localhost', headers={}),
            db=DBContext(
                db_url=':memory:',
                connection=conn,
                cursor=conn.cursor(),
                commit=conn.commit,
            ),
            log=lambda _: None,
        )

        db_model_create_table(ctx, _FakeModel)
        create_sql = ctx.db.cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'fake_model'"
        ).fetchone()[0]

        self.assertIn(f'CHECK (LENGTH("title") <= {MAX_STR_FIELD_LENGTH})', create_sql)
        self.assertIn(f'CHECK (LENGTH("body") <= {MAX_RICH_TEXT_JSON_LENGTH})', create_sql)


if __name__ == '__main__':
    unittest.main()
