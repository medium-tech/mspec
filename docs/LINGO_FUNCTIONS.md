# Lingo Expressions

- [Data Types](#data-types)
- [Built-in Functions](#functions)
  - [Comparison](#comparison-functions)
  - [Bool](#bool-functions)
  - [Int](#int-functions)
  - [Float](#float-functions)
  - [Str](#str-functions)
  - [Math](#math-functions)
  - [Sequence](#sequence-functions)
  - [Sequence Ops](#sequence-ops-functions)
  - [Date and Time](#date-and-time-functions)
  - [Random](#random-functions)
  - [Auth](#auth-functions)
  - [Client](#client-functions)
  - [Com](#com-functions)
  - [File System](#file-system-functions)
  - [Media](#media-functions)
  - [Database](#database-functions)
- [Control Flow](#control-flow)
- [UI Elements](#ui-elements)
- [Expressions](#expressions)

## Data Types

### Primitives

- **bool**: Boolean true/false values
- **int**: Integer numbers
- **float**: Floating-point numbers
- **str**: String values
- **datetime**: datetime objects

### collections

- **list** - A list of elements, all elements must be the same type. All primitives are supported.

## Functions

### Comparison Functions
`eq` - return true if `a` equals `b`
  - **args:**
    - **a** `int|float|str`
    - **b** `int|float|str`
  - **return:** `bool`

`ne` - return true if `a` does not equal `b`
  - **args:**
    - **a** `int|float|str`
    - **b** `int|float|str`
  - **return:** `bool`

`lt` - return true if `a` is less than `b`
  - **args:**
    - **a** `int|float|str`
    - **b** `int|float|str`
  - **return:** `bool`

`le` - return true if `a` is less than or equal to `b`
  - **args:**
    - **a** `int|float|str`
    - **b** `int|float|str`
  - **return:** `bool`

`gt` - return true if `a` is greater than `b`
  - **args:**
    - **a** `int|float|str`
    - **b** `int|float|str`
  - **return:** `bool`

`ge` - return true if `a` is greater than or equal to `b`
  - **args:**
    - **a** `int|float|str`
    - **b** `int|float|str`
  - **return:** `bool`
  
### Bool Functions
`bool` - convert value to boolean
  - **args:**
    - **object** `any`
  - **return:** `bool`

`not` - logical NOT operation
  - **args:**
    - **object** `any`
  - **return:** `bool`

`and` - bitwise AND
  - **args:**
    - **a** `any`
    - **b** `any`
  - **return:** `any`

`or` - bitwise OR
  - **args:**
    - **a** `any`
    - **b** `any`
  - **return:** `any`

### Int Functions
`int` - convert to integer
  - **args:**
    - **number** `any` (optional)
    - **string** `str` (optional)
    - **base** `int` (default: 10)
  - **return:** `int`

`neg` - arithmetic negation
  - **args:**
    - **object** `any`
  - **return:** `int|float`

### Float Functions
`float` - convert to float
  - **args:**
    - **number** `any`
  - **return:** `float`

`round` - round a float to the nearest integer or to a given number of digits
  - **args:**
    - **number** `float`
    - **ndigits** `int` (optional)
  - **return:** `float`

### Str Functions
`str` - convert to string
  - **args:**
    - **object** `any`
  - **return:** `str`
  
`join` - join a list of items with a separator
  - **args:**
    - **separator** `str`
    - **items** `list`
  - **return:** `str`

### Math Functions
`add` - perform addition on `a` and `b` and return the result
  - **args:**
    - **a** `int|float`
    - **b** `int|float`
  - **return:** `int|float`

`sub` - perform subtraction on `a` and `b` and return the result
  - **args:**
    - **a** `int|float`
    - **b** `int|float`
  - **return:** `int|float`

`mul` - perform multiplication on `a` and `b` and return the result
  - **args:**
    - **a** `int|float`
    - **b** `int|float`
  - **return:** `int|float`

`div` - perform division on `a` and `b` and return the result
  - **args:**
    - **a** `int|float`
    - **b** `int|float`
  - **return:** `float`

`floordiv` - perform floor division on `a` and `b` and return the result
  - **args:**
    - **a** `int|float`
    - **b** `int|float`
  - **return:** `int`

`mod` - perform modulo on `a` and `b` and return the result
  - **args:**
    - **a** `int|float`
    - **b** `int|float`
  - **return:** `int|float`

`pow` - raise `a` to the power of `b` and return the result
  - **args:**
    - **a** `int|float`
    - **b** `int|float`
  - **return:** `int|float`

`min` - return the minimum of `a` and `b`
  - **args:**
    - **a** `int|float`
    - **b** `int|float`
  - **return:** `int|float`

`max` - return the maximum of `a` and `b`
  - **args:**
    - **a** `int|float`
    - **b** `int|float`
  - **return:** `int|float`

`abs` - return the absolute value of `number`
  - **args:**
    - **number** `int|float`
  - **return:** `int|float`

### Sequence Functions
`len` - return the length of a string or list
  - **args:**
    - **object** `str|list`
  - **return:** `int`

`range` - create a range of integers
  - **args:**
    - **start** `int` (default: 0)
    - **stop** `int`
    - **step** `int` (default: 1)
  - **return:** `list`

`slice` - slice a list
  - **args:**
    - **iterator** `list`
    - **start** `int` (optional)
    - **stop** `int`
    - **step** `int` (optional)
  - **return:** `list`

`any` - return true if any element is true
  - **args:**
    - **iterable** `list`
  - **return:** `bool`

`all` - return true if all elements are true
  - **args:**
    - **iterable** `list`
  - **return:** `bool`

`sum` - return the sum of elements in a list
  - **args:**
    - **iterable** `list`
    - **start** `int|float` (default: 0)
  - **return:** `int|float`

`sorted` - return a sorted list
  - **args:**
    - **iterable** `list`
  - **return:** `list`

### Sequence Ops Functions
`map` - apply a function to each item in a list and return a new list
  - **args:**
    - **iterable** `list`
    - **function** `expression`
  - **return:** `list`

`filter` - filter a list by a function, returning items where the function is true
  - **args:**
    - **iterable** `list`
    - **function** `expression`
  - **return:** `list`

`dropwhile` - drop items from a list while the function is true, then return the rest
  - **args:**
    - **iterable** `list`
    - **function** `expression`
  - **return:** `list`

`takewhile` - take items from a list while the function is true, then stop
  - **args:**
    - **iterable** `list`
    - **function** `expression`
  - **return:** `list`

`reversed` - return a reversed copy of a list
  - **args:**
    - **sequence** `list`
  - **return:** `list`

`accumulate` - accumulate results of applying a function to items in a list (like running total)
  - **args:**
    - **iterable** `list`
    - **function** `expression`
    - **initial** `any` (optional)
  - **return:** `list`

`reduce` - reduce a list to a single value by applying a function
  - **args:**
    - **iterable** `list`
    - **function** `expression`
    - **initial** `any` (optional)
  - **return:** `any`


### Date and Time Functions
`datetime.now` - return the current date and time
  - **args:**
    - *(none)*
  - **return:** `datetime`

`current.weekday` - return the current weekday as an integer (0=Monday, 6=Sunday)
  - **args:**
    - *(none)*
  - **return:** `int`

### Random Functions

`random.randint` - return a random integer between `a` and `b` (inclusive)
  - **args:**
    - **a** `int`
    - **b** `int`
  - **return:** `int`

### Auth Functions
`auth.create_user` - Create a new user with name, email, password, and password confirmation
  - **args:**
    - **name** `str` - Name of the user
    - **email** `str` - Email of the user
    - **password** `str` - Password for the user
    - **password_confirm** `str` - Password confirmation
  - **return:** struct with `id`, `name`, `email`

`auth.login_user` - Login a user with email and password
  - **args:**
    - **email** `str` - Email of the user
    - **password** `str` - Password for the user
  - **return:** struct with `access_token`, `token_type`

`auth.current_user` - Get the current logged in user
  - **args:** *(none)*
  - **return:** struct with `id`, `name`, `email`, `number_of_sessions`

`auth.logout_user` - Logout the current user
  - **args:**
    - **mode** `str` - Logout mode (`all`, `current`, `others`)
  - **return:** struct with `acknowledged`, `message`

`auth.delete_user` - Delete currently logged in user
  - **args:** *(none)*
  - **return:** struct with `acknowledged`, `message`

`auth.drop_sessions` - Drop all sessions (requires root password)
  - **args:**
    - **root_password** `str` - Root password to authorize dropping all sessions
  - **return:** struct with `acknowledged`, `message`

### Client Functions
`client.reload` - Reload the client, currently only availble in the js browser interpreter which calls `window.location.reload`
  - **args:** *(none)*
  - **return:** struct with `acknowledged`, `message`

### Com Functions
`com.send_email` - Send an email to the specified address. Set env variable `MAPP_SMTP_MOCK` to `true` to log the email instead of sending via SMTP, useful for dev testing
  - **args:**
    - **email** `str` - Recipient email address
    - **subject** `str` - Email subject line
    - **body** `str` - Email body text
  - **return:** struct with `acknowledged`, `message`

`com.start_email_verification` - Starts an email verification for currently logged in user. Emails a code to the user which is then supplied to the `com.verify_email_address` op to finish verifying the email address.
  - **args:** *(none)*
  - **return:** struct with `acknowledged`, `message`

`com.verify_email_address` - Verify the email address of the currently logged-in user. Checks an email code generated by the `com.start_email_verification` op; on success, sets `email_verified=true` on the user and deletes the verification record. Returns `AUTHENTICATION_ERROR` if no valid match is found. Must be verified within timeframe configurated by env variable `MAPP_EMAIL_VERIFICATION_EXPIRATION`, default 600 seconds.
  - **args:**
    - **code** `str` - Verification code sent to the user's email address
  - **return:** struct with `acknowledged`, `message`

### File System Functions
`file_system.ingest_start` - Start ingesting a file
  - **args:**
    - **name** `str` - Name of the file
    - **size** `int` - Size in bytes
    - **parts** `int` - Number of parts
    - **content_type** `str` (optional) - MIME type
    - **finish** `bool` (optional) - Mark as finished if single part
  - **return:** struct with `file_id`, `message`

`file_system.list_files` - List files with pagination and filters
  - **args:**
    - **offset** `int` (default: 0)
    - **size** `int` (default: 50)
    - **user_id** `str` (optional)
    - **file_id** `str` (optional)
    - **status** `str` (optional)
  - **return:** struct with `items`, `total`

`file_system.list_parts` - List file parts for a file
  - **args:**
    - **file_id** `str`
    - **offset** `int` (default: 0)
    - **size** `int` (default: 50)
    - **user_id** `str` (optional)
  - **return:** struct with `items`, `total`

`file_system.get_part_content` - Get the content of a file part
  - **args:**
    - **file_id** `str`
    - **part_number** `int`
  - **return:** struct with `acknowledged`, `message`

`file_system.get_file_content` - Get the content of a file
  - **args:**
    - **file_id** `str`
  - **return:** struct with `acknowledged`, `message`

`file_system.process_file` - Assemble file parts to create final file
  - **args:**
    - **file_id** `str`
  - **return:** struct with `acknowledged`, `message`

### Media Functions
`media.create_image` - Create an image record for a file
  - **args:**
    - **name** `str` - Name of the image
    - **content_type** `str` (optional) - MIME type
  - **return:** struct with `image_id`, `file_id`, `message`

`media.get_image` - Get an image record by ID
  - **args:**
    - **image_id** `str`
  - **return:** struct with image metadata fields

`media.get_media_file_content` - Get the file content of a media file (image)
  - **args:**
    - **image_id** `str`
  - **return:** struct with `acknowledged`, `message`

`media.list_images` - List image records with pagination and filtering
  - **args:**
    - **offset** `int` (default: 0)
    - **size** `int` (default: 50)
    - **image_id** `str` (optional)
    - **file_id** `str` (optional)
    - **user_id** `str` (optional)
  - **return:** struct with `items`, `total`

### Database Functions
`db.create` - Create a model instance and return the new ID
  - **args:**
    - **model_type** `str` - dot-notation module.model (e.g. `sosh_net.thread`)
    - **data** `struct` - model field values
  - **return:** `str` model ID

`db.read` - Read a single model instance by ID
  - **args:**
    - **model_type** `str` - dot-notation module.model (e.g. `sosh_net.post`)
    - **model_id** `str` - the record ID
  - **return:** struct with all model fields

`db.unique_counts` - Return counts of unique values for a model field
  - **args:**
    - **model_type** `str` - dot-notation module.model
    - **group_by** `str` - field name to group by
    - **filters** `struct` (optional) - `{field_name: value}` pairs for WHERE clause
  - **return:** list of structs `[{<group_by_field>: value, count: int}, ...]`

`db.query` - Return all rows matching a set of field equality filters
  - **args:**
    - **model_type** `str` - dot-notation module.model (e.g. `sosh_net.profile`)
    - **fields** `struct` - `{field_name: value}` equality filters; only `str` and `foreign_key` field types are supported
  - **return:** list of matching model structs (same format as `db.read`)
  - **errors:** Raises a `ValueError` if a filter key is an unsupported field type (e.g. `int`, `bool`)

## Control Flow

### Branch (if/elif/else)
```json
{
  "branch": [
    {"if": condition, "then": result},
    {"elif": condition, "then": result},
    {"else": result}
  ]
}
```

### Switch Statement
```json
{
  "switch": {
    "expression": value_expression,
    "cases": [
      {"case": value1, "then": result1},
      {"case": value2, "then": result2}
    ],
    "default": default_result
  }
}
```

## UI Elements

### Heading
```json
{"heading": {"text": "Heading Text"}, "level": 1}
```
- **level**: Integer from 1-6 (like HTML h1-h6)

### Text
```json
{"text": "Plain text content"}
```

### Line Break
```json
{"break": 1}
```
- **break**: Number of line breaks to insert

### Button
```json
{"button": {"op": {"operation_name": {"arg": "value"}}}, "text": "Button Text"}
```

### Input Field
```json
{"input": {"type": "text"}, "bind": {"state": {"field_name": {}}}}
```
- **type**: Input type (currently "text")
- **bind**: Must bind to a state variable

### Link
```json
{"link": "https://example.com", "text": "Link Text"}
```
- **text**: Optional display text (defaults to URL)

### Block Container
```json
{"block": [
  {"text": "First element"},
  {"text": "Second element"}
]}
```

### Dynamic Expression (Lingo)
```json
{"lingo": expression}
```
Renders the result of any expression as text.

## Expressions

### State Access
```json
{"state": {"field_name": {}}}
```

### Parameter Access  
```json
{"params": {"param_name": {}}}
```

### Function Call
```json
{"call": "function_name", "args": {"a": value1, "b": value2}}
```

### Operation Call
```json
{"op": {"operation_name": {"arg": "value"}}}
```

### State Setting
```json
{
  "set": {"state": {"field_name": {}}},
  "to": expression
}
```

### Argument Access (within ops)
```json
{"args": "argument_name"}
```
