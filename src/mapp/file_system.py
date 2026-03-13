import os
import datetime

from hashlib import sha3_256
from mimetypes import guess_type

from mapp.auth import current_user
from mapp.context import MappContext
from mapp.errors import  MappValidationError
from mapp.types import ModelListResult, File, FilePart, datetime_now_utc, datetime_for_db

MAPP_APP_PATH = os.getenv('MAPP_APP_PATH', '')

"""

./run.sh file-system ingest-start run '{"name": "document.txt", "size": 1024, "parts": 1}'


"""

def _file_part_dir(file_id: str) -> str:
	if MAPP_APP_PATH == '':
		raise ValueError('MAPP_APP_PATH environment variable not set')
	return os.path.join(MAPP_APP_PATH, 'file_parts', file_id)

#
# low level ops
#

def _ingest_part(ctx: MappContext, file_input: bytes, file_record: File, user: dict):
	part_size = len(file_input)
	part_sha3_256 = sha3_256(file_input).hexdigest()
	part_number = 1

	part_dir = _file_part_dir(str(file_record.id))
	os.makedirs(part_dir, exist_ok=True)

	part_path = os.path.join(part_dir, f'{part_number:08}.part')
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
		'''
		INSERT INTO file_part (file_id, size, part_number, sha3_256, user_id, uploaded_at)
		VALUES (%s, %s, %s, %s, %s, %s)
		''',
		(
			file_part.file_id,
			file_part.size,
			file_part.part_number,
			file_part.sha3_256,
			file_part.user_id,
			file_part.uploaded_at
		)
	)

def _list_parts(ctx: MappContext, file_id:str) -> list[dict]:
	ctx.db.cursor.execute(
		'''
		SELECT file_id, size, part_number, sha3_256, user_id, uploaded_at
		FROM file_part
		WHERE file_id = %s
		ORDER BY part_number ASC
		''',
		(file_id,)
	)

	return [dict(row) for row in ctx.db.cursor.fetchall()]


def _ingest_finish(ctx: MappContext, file_record: File) -> File:

	calculated_size = 0
	counted_parts = 0
	part_numbers_seen = set()
	
	for part in _list_parts(ctx, file_record.id):
		calculated_size += part['size']
		counted_parts += 1
		part_numbers_seen.add(part['part_number'])

	if counted_parts != file_record.parts:
		file_record.status = 'failed'
		file_record.message = f'File ingest failed: expected {file_record.parts} parts but found {counted_parts} parts'
	elif calculated_size != file_record.size:
		file_record.status = 'failed'
		file_record.message = f'File ingest failed: expected file size {file_record.size} bytes but calculated file size is {calculated_size} bytes'
	elif part_numbers_seen != set(range(1, file_record.parts + 1)):
		file_record.status = 'failed'
		file_record.message = f'File ingest failed: invalid part number sequence'
	else:
		file_record.status = 'completed'
		file_record.message = 'File ingest completed successfully'

	ctx.db.cursor.execute(
		'''
		UPDATE file
		SET status = %s, message = %s, updated_at = %s
		WHERE id = %s
		''',
		(
			file_record.status,
			file_record.message,
			datetime_for_db(datetime_now_utc()),
			file_record.id
		)
	)


#
# commands
#

def ingest_start(ctx: MappContext, name: str, size: int, parts: int, content_type: str = '', finish: bool = False) -> dict:
	"""Placeholder for ingest_start operation."""

	file_input = ctx.self.get('file_input', None)

	user = current_user(ctx)

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
		updated_at=ingest_timestamp
	)

	insert_file_record = ctx.db.cursor.execute(
		'''
		INSERT INTO file (name, status, message, extension, size, parts, content_type, user_id, created_at, updated_at)
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		''',
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
			file_record.updated_at
		)
	)

	file_record.id = insert_file_record.lastrowid

	# 
	# upload part and/or finish if requested
	#

	if file_input is not None:
		_ingest_part(ctx, file_input, file_record, user)
		if finish:
			_ingest_finish(ctx, file_record)
		
	
	return {'file_id': file_record.id, 'message': f'{file_record.status}: {file_record.message}'}

def ingest_part(ctx: MappContext, file_id: str, part_number: int) -> dict:
	"""Placeholder for ingest_part operation."""
	return {'acknowledged': True, 'message': 'File part uploaded'}

def ingest_finish(ctx: MappContext, file_id: str) -> dict:
	"""Placeholder for ingest_finish operation."""
	return {'acknowledged': True, 'message': 'File upload finished'}

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

def list_files(ctx: MappContext, offset: int = 0, size: int = 50, user_id: str = '-1') -> ModelListResult:
	"""Placeholder for list_files operation."""
	return ModelListResult(items=[{'name': 'document.txt'}], total=1)

def list_parts(ctx: MappContext, file_id: str = '-1', offset: int = 0, size: int = 50, user_id: str = '-1') -> ModelListResult:
	"""Placeholder for list_parts operation."""
	return ModelListResult(items=[{'file_id': '1', 'part_number': 1}], total=1)
