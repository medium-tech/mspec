import sqlite3

from datetime import datetime

from mapp.context import MappContext
from mapp.errors import NotFoundError
from mapp.module.model.type import DATETIME_FORMAT_STR

__all__ = [
    'db_model_create_table',
    'db_model_create',
    'db_model_read',
    'db_model_update',
    'db_model_delete',
    'db_model_list'
]


def db_model_create_table(ctx:MappContext, model_class: type):
    model_spec = model_class._model_spec
    model_snake_case = model_spec['name']['snake_case']

    # non list fields #
    
    columns = ['id INTEGER PRIMARY KEY']
    for field in model_spec['non_list_fields']:
        field_name = field['name']['snake_case']
        field_type = field['type']
        
        match field_type:
            case 'bool':
                sql_type = 'INTEGER'
            case 'int':
                sql_type = 'INTEGER'
            case 'float':
                sql_type = 'REAL'
            case 'str' | 'enum':
                sql_type = 'TEXT'
            case 'datetime':
                sql_type = 'TEXT'
            case _:
                raise ValueError(f'Unsupported field type: {field_type}')
            
        columns.append(f"'{field_name}' {sql_type}")

    columns_str = ', '.join(columns)
    main_sql_table = f"CREATE TABLE IF NOT EXISTS {model_snake_case}({columns_str})"
    ctx.db.cursor.execute(main_sql_table)

    # list fields #

    for field in model_spec['list_fields']:
        field_name = field['name']['snake_case']
        list_table_name = f'{model_snake_case}_{field_name}'
        
        list_sql_table = f"""CREATE TABLE IF NOT EXISTS {list_table_name}(
            id INTEGER PRIMARY KEY,
            value,
            position INTEGER,
            {model_snake_case}_id INTEGER REFERENCES {model_snake_case}(id)
        )"""
        ctx.db.cursor.execute(list_sql_table)

        index_sql = f"CREATE INDEX IF NOT EXISTS {list_table_name}_index ON {list_table_name}({model_snake_case}_id)"
        ctx.db.cursor.execute(index_sql)

    ctx.db.commit()


def db_model_create(ctx:MappContext, model_class: type, obj: object) -> object:

    # init #
    
    if obj.id is not None:
        raise ValueError('id must be null to create a new item')

    model_spec = model_class._model_spec
    model_snake_case = model_class._model_spec['name']['snake_case']

    # non list sql #
    
    fields = []
    values = []
    placeholders = []

    for field in model_spec['non_list_fields']:
        field_name = field['name']['snake_case']

        fields.append(field_name)
        value = getattr(obj, field_name)
        
        if field['type'] == 'datetime':
            value = value.isoformat()

        values.append(value)
        placeholders.append('?')

    fields_str = ', '.join(f"'{f}'" for f in fields)
    placeholder_str = ', '.join(placeholders)

    # call db #

    sql = f'INSERT INTO {model_snake_case} (' + fields_str + ') VALUES (' + placeholder_str + ')'
    result = ctx.db.cursor.execute(sql, values)
    assert result.rowcount == 1
    assert result.lastrowid is not None
    obj.id = str(result.lastrowid)

    # list fields sql #

    for field in model_spec['list_fields']:
        field_name = field['name']['snake_case']
        list_table_name = f'{model_snake_case}_{field_name}'
        values_list = getattr(obj, field_name, [])
        for pos, value in enumerate(values_list):
            ctx.db.cursor.execute(
                f"INSERT INTO {list_table_name} (value, position, {model_snake_case}_id) VALUES (?, ?, ?)",
                (value, pos, obj.id)
            )

    ctx.db.commit()
    return obj

def db_model_read(ctx:MappContext, model_class: type, model_id: str):
    model_spec = model_class._model_spec
    model_snake_case = model_spec['name']['snake_case']

    # read non list fields #

    field_names = ['id'] + [field['name']['snake_case'] for field in model_spec['non_list_fields']]
    select_fields = ', '.join(f"'{f}'" for f in field_names)
    sql = f'SELECT {select_fields} FROM {model_snake_case} WHERE id = ?'

    row = ctx.db.cursor.execute(sql, (model_id,)).fetchone()
    if row is None:
        raise NotFoundError(f'{model_snake_case} {model_id} not found')

    # convert non list fields #

    data = {}
    for idx, field in enumerate(model_spec['non_list_fields']):
        field_name = field['name']['snake_case']
        match field['type']:
            case 'bool':
                value = bool(row[idx])
            case 'datetime' if row[idx] is not None:
                value = datetime.strptime(row[idx], DATETIME_FORMAT_STR).replace(microsecond=0)
            case _:
                value = row[idx]
        data[field_name] = value

    # read list fields #

    for field in model_spec['list_fields']:

        field_name = field['name']['snake_case']
        list_table_name = f'{model_snake_case}_{field_name}'

        cursor = ctx.db.cursor.execute(
            f"SELECT value FROM {list_table_name} WHERE {model_snake_case}_id = ? ORDER BY position ASC",
            (model_id,)
        )

        match field['element_type']:
            case 'bool':
                convert_element = bool
            case 'datetime' if row[idx] is not None:
                convert_element = lambda x: datetime.strptime(x, DATETIME_FORMAT_STR).replace(microsecond=0)
            case _:
                convert_element = lambda x: x

        data[field_name] = [convert_element(row[0]) for row in cursor.fetchall()]

    return model_class(**data)

def db_model_update(ctx:MappContext, model_class: type, model_id: str, data: dict):
    print(f'[PLACEHOLDER] Would update model with id={model_id} in the local SQLite database.')

def db_model_delete(ctx:MappContext, model_class: type, model_id: str):
    print(f'[PLACEHOLDER] Would delete model with id={model_id} from the local SQLite database.')

def db_model_list(ctx:MappContext, model_class: type, offset: int = 0, limit: int = 50):
    print(f'[PLACEHOLDER] Would list models from the local SQLite database with offset={offset} and limit={limit}.')
