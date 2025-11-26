from datetime import datetime

from mapp.context import MappContext
from mapp.errors import NotFoundError, MappError
from mapp.types import DATETIME_FORMAT_STR, ModelListResult, validate_model, Acknowledgment


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

    validate_model(model_class, obj)
    
    if obj.id is not None:
        raise ValueError('id must be null to create a new item')

    model_spec = model_class._model_spec
    model_snake_case = model_class._model_spec['name']['snake_case']

    # non list sql #
    
    fields = []
    values = []
    placeholders = []
    has_non_list_fields = False

    for field in model_spec['non_list_fields']:
        has_non_list_fields = True
        field_name = field['name']['snake_case']

        fields.append(field_name)
        value = getattr(obj, field_name)
        
        if field['type'] == 'datetime':
            value = value.isoformat()

        values.append(value)
        placeholders.append('?')

    if has_non_list_fields:
        fields_str = ', '.join(f"'{f}'" for f in fields)
        placeholder_str = ', '.join(placeholders)
        non_list_sql = f'INSERT INTO {model_snake_case} (' + fields_str + ') VALUES (' + placeholder_str + ')'
    else:
        non_list_sql = f'INSERT INTO {model_snake_case} DEFAULT VALUES'

    # call db #

    result = ctx.db.cursor.execute(non_list_sql, values)
    assert result.rowcount == 1
    assert result.lastrowid is not None
    obj = obj._replace(id=str(result.lastrowid))

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

    sql = f'SELECT * FROM {model_snake_case} WHERE id=?'

    row = ctx.db.cursor.execute(sql, (model_id,)).fetchone()
    if row is None:
        raise NotFoundError(f'{model_snake_case} {model_id} not found')

    # convert non list fields #

    data = {'id': model_id}
    for idx, field in enumerate(model_spec['non_list_fields'], start=1):
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
            f'SELECT value FROM {list_table_name} WHERE {model_snake_case}_id = ? ORDER BY position ASC',
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

def db_model_update(ctx:MappContext, model_class: type, obj: object):

    if obj.id is None:
        raise MappError('MODEL_ID_NOT_PROVIDED', 'id must be provided to update an item')

    validate_model(model_class, obj)

    model_spec = model_class._model_spec
    model_snake_case = model_spec['name']['snake_case']

    #
    # non list fields
    #

    # prepare sql #

    fields = []
    values = []

    for field in model_spec['non_list_fields']:
        field_name = field['name']['snake_case']
        value = getattr(obj, field_name)

        if field['type'] == 'datetime':
            value = value.isoformat()

        fields.append(f"'{field_name}' = ?")
        values.append(value)

    values.append(obj.id)
    set_clause = ', '.join(fields)
    sql = f'UPDATE {model_snake_case} SET {set_clause} WHERE id = ?'

    # execute sql #

    result = ctx.db.cursor.execute(sql, values)
    if result.rowcount == 0:
        raise NotFoundError(f'{model_snake_case} {obj.id} not found')

    #
    # list fields
    #

    for field in model_spec['list_fields']:
        field_name = field['name']['snake_case']
        list_table_name = f'{model_snake_case}_{field_name}'

        # clear existing values #

        ctx.db.cursor.execute(f'DELETE FROM {list_table_name} WHERE {model_snake_case}_id = ?', (obj.id,))

        # insert new values #
        
        for pos, value in enumerate(getattr(obj, field_name)):
            ctx.db.cursor.execute(
                f'INSERT INTO {list_table_name} (value, position, {model_snake_case}_id) VALUES (?, ?, ?)',
                (value, pos, obj.id)
            )

    # finish #

    ctx.db.commit()
    
    return obj

def db_model_delete(ctx:MappContext, model_class: type, model_id: str) -> Acknowledgment:
    model_spec = model_class._model_spec
    model_snake_case = model_spec['name']['snake_case']

    # list tables #

    for field in model_spec['list_fields']:
        field_name = field['name']['snake_case']
        list_table_name = f'{model_snake_case}_{field_name}'
        ctx.db.cursor.execute(f'DELETE FROM {list_table_name} WHERE {model_snake_case}_id = ?', (model_id,))

    # main table #

    ctx.db.cursor.execute(f'DELETE FROM {model_snake_case} WHERE id = ?', (model_id,))
    ctx.db.commit()
    return Acknowledgment()

def db_model_list(ctx:MappContext, model_class: type, offset: int = 0, size: int = 50) -> ModelListResult:
    model_spec = model_class._model_spec
    model_snake_case = model_spec['name']['snake_case']

    # query #

    sql = f'SELECT * FROM {model_snake_case} ORDER BY id LIMIT ? OFFSET ?'
    rows = ctx.db.cursor.execute(sql, (size, offset)).fetchall()
    
    # convert results #

    models = []

    for row in rows:
        data = {'id': str(row[0])}

        # convert non list fields #

        for index, field in enumerate(model_spec['non_list_fields'], start=1):
            field_name = field['name']['snake_case']
            match field['type']:
                case 'bool':
                    value = bool(row[index])
                case 'datetime' if row[index] is not None:
                    value = datetime.strptime(row[index], DATETIME_FORMAT_STR).replace(microsecond=0)
                case _:
                    value = row[index]

            data[field_name] = value

        # query for and convert list fields #

        for field in model_spec['list_fields']:

            field_name = field['name']['snake_case']
            list_table_name = f'{model_snake_case}_{field_name}'

            cursor = ctx.db.cursor.execute(
                f'SELECT value FROM {list_table_name} WHERE {model_snake_case}_id = ? ORDER BY position ASC',
                (data['id'],)
            )

            match field['element_type']:
                case 'bool':
                    convert_element = bool
                case 'datetime' if row[index] is not None:
                    convert_element = lambda x: datetime.strptime(x, DATETIME_FORMAT_STR).replace(microsecond=0)
                case _:
                    convert_element = lambda x: x

            data[field_name] = [convert_element(row[0]) for row in cursor.fetchall()]

        models.append(model_class(**data))

    # result #
        
    total_items = ctx.db.cursor.execute(f'SELECT COUNT(*) FROM {model_snake_case}').fetchone()[0]

    return ModelListResult(
        items=models, 
        total=total_items
    )
