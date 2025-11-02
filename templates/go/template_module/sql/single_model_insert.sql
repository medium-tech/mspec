-- mtemplate :: {"module": "template module", "model": "single model"}
INSERT INTO single_model (
    -- macro :: go_sql_insert_field :: {"single_bool": "field.name.snake_case"}
    single_bool, 
    -- end macro ::
    single_int, 
    single_float, 
    single_string, 
    single_enum, 
    single_datetime
    -- for :: {% for field in model.non_list_fields %} :: {}
    -- insert :: macro.go_sql_insert_field(field=field)
    -- end for :: clip_trailing_comma
)
VALUES (
    -- macro :: go_sql_insert_field_value
    ?, 
    -- end macro ::
    ?, 
    ?, 
    ?, 
    ?, 
    ?
    -- for :: {% for field in model.non_list_fields %} :: {}
    -- insert :: macro.go_sql_insert_field_value(field=field)
    -- end for :: clip_trailing_comma
)
