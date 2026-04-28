-- mtemplate :: {"module": "template module", "model": "single model"}
CREATE TABLE IF NOT EXISTS single_model (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	-- macro :: go_sql_create_field_bool :: {"single_bool": "field.name.snake_case"}
	single_bool INTEGER NOT NULL,
	-- macro :: go_sql_create_field_int :: {"single_int": "field.name.snake_case"}
	single_int INTEGER NOT NULL,
	-- macro :: go_sql_create_field_float :: {"single_float": "field.name.snake_case"}
	single_float REAL NOT NULL,
	-- macro :: go_sql_create_field_string :: {"single_string": "field.name.snake_case"}
	single_string TEXT NOT NULL,
	-- macro :: go_sql_create_field_enum :: {"single_enum": "field.name.snake_case"}
	single_enum TEXT NOT NULL CHECK(single_enum IN (
		-- macro :: go_sql_create_field_enum_entry :: {"value": "red"}
		'red',
		-- end macro ::
		'green', 
		'blue'
	)),
	-- macro :: go_sql_create_field_datetime :: {"single_datetime": "field.name.snake_case"}
	single_datetime TEXT NOT NULL
	-- end macro ::
	-- for :: {% for field in model.non_list_fields %} :: {}
	-- insert :: macro_by_type('go_sql_create_field', field.type_id, model=model, field=field)
	-- end for :: clip_trailing_comma
);

-- macro :: go_sql_create_index_enum
CREATE INDEX IF NOT EXISTS idx_single_model_enum ON single_model(single_enum);
