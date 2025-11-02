-- test comment: This SQL file creates the table for the single_model data model.
CREATE TABLE IF NOT EXISTS single_model (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	single_bool INTEGER NOT NULL,
	-- macro :: test_macro
	single_int INTEGER NOT NULL,
	-- macro :: test_macro_2
	single_float REAL NOT NULL,
	-- end macro ::
	single_string TEXT NOT NULL,
	single_enum TEXT NOT NULL CHECK(single_enum IN ('red', 'green', 'blue')),
	single_datetime TEXT NOT NULL,
);

CREATE INDEX IF NOT EXISTS idx_single_model_enum ON single_model(single_enum);
