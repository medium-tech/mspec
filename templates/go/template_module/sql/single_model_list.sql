SELECT
    id,
    single_bool,
    single_int,
    single_float,
    single_string,
    single_enum,
    single_datetime,
FROM single_model
ORDER BY id
LIMIT ? OFFSET ?
