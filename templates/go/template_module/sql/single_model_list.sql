-- mtemplate :: {"module": "template module", "model": "single model"}
SELECT 
    id,
    -- macro :: go_sql_list_field :: {"single_bool": "field.name.snake_case"}
    single_bool,
    -- end macro ::
    -- ignore ::
    single_int,
    single_float,
    single_string,
    single_enum,
    single_datetime
    -- end ignore ::
    -- for :: {% for field in model.non_list_fields %} :: {}
    -- insert :: macro.go_sql_list_field(field=field)
    -- end for :: clip_trailing_comma
FROM single_model
ORDER BY id
LIMIT ? OFFSET ?
