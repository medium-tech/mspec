import os

from hashlib import sha3_256
from mimetypes import guess_type

from mapp.auth import current_user
from mapp.context import MappContext
from mapp.errors import  MappValidationError, MappUserError
from mapp.types import ModelListResult, File, FilePart, datetime_now_utc, datetime_for_db, datetime_from_db

__all__ = [
	'ingest_start',
	'ingest_part',
	'ingest_finish',
	'verify_file',
	'delete_file',
	'list_files',
	'list_parts'
]

MAPP_APP_PATH = os.getenv('MAPP_APP_PATH', '')

"""

./run.sh --log -fi ./app/file_system/splash.png file-system ingest-start run '{"name": "splash.png", "size": 4007485, "parts": 1, "finish": true}'

./run.sh file-system list-files run

./run.sh file-system list-parts run '{"file_id": "3"}'

./run.sh -fo splash_copy.png file-system get-part-content run '{"file_id": "3", "part_number": 1}'

"""

def _file_part_dir(file_id: str) -> str:
	if MAPP_APP_PATH == '':
		raise ValueError('MAPP_APP_PATH environment variable not set')
	return os.path.join(MAPP_APP_PATH, 'file_system/file_parts', file_id)

def _file_part_path(file_id: str, part_number: int) -> str:
	return os.path.join(_file_part_dir(file_id), f'{part_number:08}.part')

#
# low level ops
#

def _ingest_part(ctx: MappContext, part_number:int, file_input: bytes, file_record: File, user: dict):
	
	part_size = len(file_input)
	part_sha3_256 = sha3_256(file_input).hexdigest()

	ctx.log(f'_ingest_part - begin - {file_record.id=} {part_number=} {part_size=} {part_sha3_256=}')

	part_path = _file_part_path(str(file_record.id), part_number)
	os.makedirs(os.path.dirname(part_path), exist_ok=True)

	with open(part_path, 'wb') as f:
		f.write(file_input)

	file_part = FilePart(
		id=None,
		file_id=file_record.id,
		size=part_size,
		part_number=part_number,
		sha3_256=part_sha3_256,
		user_id=user['id'],
		uploaded_at=datetime_for_db(datetime_now_utc())
	)

	ctx.db.cursor.execute(
		"""
		INSERT INTO file_part (file_id, size, part_number, sha3_256, user_id, uploaded_at)
		VALUES (?, ?, ?, ?, ?, ?)
		""",
		(
			file_part.file_id,
			file_part.size,
			file_part.part_number,
			file_part.sha3_256,
			file_part.user_id,
			file_part.uploaded_at
		)
	)

	ctx.db.commit()

	ctx.log(f'_ingest_part - complete - {file_record.id=}')

def _list_parts(ctx: MappContext, file_id:str) -> list[FilePart]:
	ctx.db.cursor.execute(
		"""
		SELECT id, file_id, size, part_number, sha3_256, user_id, uploaded_at
		FROM file_part
		WHERE file_id = ?
		ORDER BY part_number ASC
		""",
		(file_id,)
	)

	return [
		FilePart(
			id=str(row[0]),
			file_id=str(row[1]),
			size=row[2],
			part_number=row[3],
			sha3_256=row[4],
			user_id=row[5],
			uploaded_at=datetime_from_db(row[6])
		) for row in ctx.db.cursor.fetchall()
	]

def _ingest_finish(ctx: MappContext, file_record: File) -> File:

	ctx.log(f'_ingest_finish - begin - {file_record.id=}')

	calculated_size = 0
	counted_parts = 0
	part_numbers_seen = set()
	
	for part in _list_parts(ctx, file_record.id):
		calculated_size += part.size
		counted_parts += 1
		part_numbers_seen.add(part.part_number)

	if counted_parts != file_record.parts:
		new_staus = 'failed'
		new_message = f'File ingest failed: expected {file_record.parts} parts but found {counted_parts} parts'
	elif calculated_size != file_record.size:
		new_staus = 'failed'
		new_message = f'File ingest failed: expected file size {file_record.size} bytes but calculated file size is {calculated_size} bytes'
	elif part_numbers_seen != set(range(1, file_record.parts + 1)):
		new_staus = 'failed'
		new_message = f'File ingest failed: invalid part number sequence'
	else:
		new_staus = 'completed'
		new_message = 'File ingest completed successfully'

	file_record = file_record._replace(
		status=new_staus,
		message=new_message,
		updated_at=datetime_for_db(datetime_now_utc())
	)

	ctx.db.cursor.execute(
		"""
		UPDATE file
		SET status = ?, message = ?, updated_at = ?
		WHERE id = ?
		""",
		(
			file_record.status,
			file_record.message,
			datetime_for_db(datetime_now_utc()),
			file_record.id
		)
	)

	ctx.db.commit()

	ctx.log(f'_ingest_finish - complete - {file_record.id=} {file_record.status=} {file_record.message=}')

	return file_record

#
# commands
#

def ingest_start(ctx: MappContext, name: str, size: int, parts: int, content_type: str = '', finish: bool = False) -> dict:
	"""Placeholder for ingest_start operation."""

	file_input = ctx.self.get('file_input', None)

	user = current_user(ctx)['value']

	#
	# validate input
	#

	field_errors = {}

	if finish and file_input is None:
		field_errors['finish'] = 'User must supply a file_input if finish is true'
	elif finish and parts != 1:
		field_errors['finish'] = f'Cannot finish ingest in ingest_start call if multiple parts are specified; got: {parts}'
	
	if parts < 0:
		field_errors['parts'] = 'Parts must be a non-negative integer'

	if field_errors:
		raise MappValidationError('Error starting file ingest', field_errors)
	
	#
	# create file record
	#

	ingest_timestamp = datetime_for_db(datetime_now_utc())

	file_record = File(
		id=None,
		name=name,
		status='ingesting',
		message='File ingest started',
		extension=os.path.splitext(name)[1][1:],
		size=size,
		parts=parts,
		content_type=content_type if content_type else guess_type(name)[0] or 'application/octet-stream',
		user_id=user['id'],
		created_at=ingest_timestamp,
		updated_at=ingest_timestamp,
		sha3_256=''
	)

	ctx.db.cursor.execute("""
		INSERT INTO file (name, status, message, extension, size, parts, content_type, user_id, created_at, updated_at, sha3_256)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		""",
		(
			file_record.name,
			file_record.status,
			file_record.message,
			file_record.extension,
			file_record.size,
			file_record.parts,
			file_record.content_type,
			file_record.user_id,
			file_record.created_at,
			file_record.updated_at,
			file_record.sha3_256
		)
	)

	ctx.db.commit()

	file_record = file_record._replace(id=ctx.db.cursor.lastrowid)

	# 
	# upload part and/or finish if requested
	#

	if file_input is not None:
		_ingest_part(ctx, 1, file_input, file_record, user)
		if finish:
			file_record = _ingest_finish(ctx, file_record)
		
	msg = f'File id {file_record.id} created with status: {file_record.status}'
	ctx.log(f'ingest_start - complete - {file_record.id=} {file_record.status=} {file_record.message=}')

	if file_record.message:
		msg += f': {file_record.message}'
	
	return {'file_id': file_record.id, 'message': msg}

def ingest_part(ctx: MappContext, file_id: str, part_number: int) -> dict:
	"""Placeholder for ingest_part operation."""
	return {'acknowledged': True, 'message': 'File part uploaded'}

def ingest_finish(ctx: MappContext, file_id: str) -> dict:
	"""Placeholder for ingest_finish operation."""
	return {'acknowledged': True, 'message': 'File upload finished'}

def get_part_content(ctx: MappContext, file_id: str, part_number: int) -> dict:

	# check to see if we're logged in, any user can ready any file
	current_user(ctx)['value']

	file_output = ctx.self.get('file_output', None)

	if file_output is None:
		MappUserError('NO_FILE_OUTPUT', 'User must supply a file_output to write file part content to')

	part_path = _file_part_path(file_id, part_number)

	try:
		with open(part_path, 'rb') as f:
			while True:
				chunk = f.read(8192)
				if not chunk:
					break
				file_output.write(chunk)
				file_output.flush()
	except FileNotFoundError:
		raise MappUserError('FILE_PART_NOT_FOUND', f'File part not found for file_id: {file_id} part_number: {part_number}')

	return {
		'acknowledged': True,
		'message': 'File part content written to self.file_output',
	}

def get_file_content(ctx: MappContext, file_id: str) -> dict:
	return {
		'acknowledged': True,
		'message': 'File content written to self.file_output',
	} 

def verify_file(ctx: MappContext, file_id: str) -> dict:
	"""Placeholder for verify_file operation."""
	return {
		'verified': True,
		'message': 'File verified',
		'size': 1024,
		'parts': 1
	}

def delete_file(ctx: MappContext, file_id: str) -> dict:
	"""Placeholder for delete_file operation."""
	return {'acknowledged': True, 'message': 'File deleted'}

def list_files(ctx: MappContext, offset: int = 0, size: int = 50, user_id: str = '-1', file_id: str = '-1') -> dict:
	
	# fetch files #

	ctx.db.cursor.execute(
		"""
		SELECT id, name, status, message, extension, size, parts, content_type, user_id, created_at, updated_at, sha3_256
		FROM file
		WHERE (? = '-1' OR user_id = ?) AND (? = '-1' OR id = ?)
		ORDER BY created_at DESC
		LIMIT ? OFFSET ?
		""",
		(user_id, user_id, file_id, file_id, size, offset)
	)

	rows = ctx.db.cursor.fetchall()
	items = [
		{
			'id': str(row[0]),
			'name': row[1],
			'status': row[2],
			'message': row[3],
			'extension': row[4],
			'size': row[5],
			'parts': row[6],
			'content_type': row[7],
			'user_id': row[8],
			'created_at': datetime_from_db(row[9]).isoformat(),
			'updated_at': datetime_from_db(row[10]).isoformat(),
			'sha3_256': row[11]
		} 
		for row in rows
	]

	# fetch total count #

	ctx.db.cursor.execute(
		"SELECT COUNT(*) FROM file WHERE (? = '-1' OR user_id = ?) AND (? = '-1' OR id = ?)",
		(user_id, user_id, file_id, file_id)
	)
	total = ctx.db.cursor.fetchone()[0]

	# return result #

	return {
		'items': items,
		'total': total
	}

def list_parts(ctx: MappContext, file_id: str = '-1', offset: int = 0, size: int = 50, user_id: str = '-1') -> dict:
	
	# fetch file parts #

	ctx.db.cursor.execute(
		"""
		SELECT id, file_id, size, part_number, sha3_256, user_id, uploaded_at
		FROM file_part
		WHERE (? = '-1' OR user_id = ?) AND (? = '-1' OR file_id = ?)
		ORDER BY part_number ASC
		LIMIT ? OFFSET ?
		""",
		(user_id, user_id, file_id, file_id, size, offset)
	)

	rows = ctx.db.cursor.fetchall()
	items = [
		{
			'id': str(row[0]),
			'file_id': str(row[1]),
			'size': row[2],
			'part_number': row[3],
			'sha3_256': row[4],
			'user_id': row[5],
			'uploaded_at': datetime_from_db(row[6]).isoformat()
		} for row in rows
	]

	# fetch total count #

	ctx.db.cursor.execute(
		"SELECT COUNT(*) FROM file_part WHERE (? = '-1' OR user_id = ?) AND (? = '-1' OR file_id = ?)",
		(user_id, user_id, file_id, file_id)
	)
	total = ctx.db.cursor.fetchone()[0]

	return {
		'items': items,
		'total': total
	}