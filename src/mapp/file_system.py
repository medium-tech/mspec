import os

from hashlib import sha3_256
from mimetypes import guess_type

from mapp.auth import current_user
from mapp.context import MappContext
from mapp.errors import  MappValidationError, MappUserError, NotFoundError, MappError
from mapp.types import File, FilePart, datetime_now_utc, datetime_for_db, datetime_from_db

__all__ = [
	'ingest_start',
	'ingest_part',
	'ingest_finish',
	'verify_file',
	'delete_file',
	'list_files',
	'list_parts',
	'get_part_content',
	'get_file_content',
	'process_file'
]

MAPP_FILE_SYSTEM_REPO = os.getenv('MAPP_FILE_SYSTEM_REPO', '')
FILE_SIZE_LIMIT = 50 * 1024 * 1024
OS_HANDLE_BUFFER_SIZE = 8192

"""

./run.sh --log -fi ./tests/samples/splash.png file-system ingest-start run '{"name": "splash.png", "size": 4007485, "parts": 1, "finish": true}'

./run.sh file-system list-files run

./run.sh file-system list-parts run '{"file_id": ""}'

./run.sh -fo splash-part.png file-system get-part-content run '{"file_id": "", "part_number": 1}'

./run.sh -fo splash-file.png file-system get-file-content run '{"file_id": ""}'

"""

#
# path helpers
#

def _file_dir(file_id: str) -> str:
	"""get the directory where full file content is stored"""
	if MAPP_FILE_SYSTEM_REPO == '':
		raise ValueError('MAPP_FILE_SYSTEM_REPO environment variable not set')
	return os.path.join(MAPP_FILE_SYSTEM_REPO, 'file_system/files', str(file_id))

def _file_path(file_record: File) -> str:
	"""get the path where full file content for file_record is stored"""
	return os.path.join(_file_dir(file_record.id), f'content.{file_record.extension}')

def _file_part_dir(file_id: str) -> str:
	"""get the directory where file parts are stored"""
	if MAPP_FILE_SYSTEM_REPO == '':
		raise ValueError('MAPP_FILE_SYSTEM_REPO environment variable not set')
	return os.path.join(MAPP_FILE_SYSTEM_REPO, 'file_system/file_parts', str(file_id))

def _file_part_path(file_id: str, part_number: int) -> str:
	"""get the path where a file part should be stored"""
	return os.path.join(_file_part_dir(file_id), f'{part_number:08}.part')

#
# low level ops
#

def _ingest_part(ctx: MappContext, part_number:int, file_input: bytes, file_record: File, user: dict) -> FilePart:
	
	part_size = len(file_input)
	part_sha3_256 = sha3_256(file_input).hexdigest()

	if part_size > FILE_SIZE_LIMIT:
		raise MappUserError('FILE_PART_TOO_LARGE', f'File part size {part_size} exceeds limit of {FILE_SIZE_LIMIT} bytes')

	ctx.log(f'_ingest_part - begin - {file_record.id=} {part_number=} {part_size=} {part_sha3_256=}')

	part_path = _file_part_path(str(file_record.id), part_number)
	os.makedirs(os.path.dirname(part_path), exist_ok=True)

	if os.path.exists(part_path):
		raise MappUserError('FILE_PART_ALREADY_EXISTS', f'File part exists for file_id: {file_record.id} part_number: {part_number}')

	with open(part_path, 'wb+') as f:
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

	return file_part._replace(id=str(ctx.db.cursor.lastrowid))

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
			user_id=str(row[5]),
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
		new_status = 'error'
		new_message = f'File ingest failed: expected {file_record.parts} parts but found {counted_parts} parts'
	elif calculated_size != file_record.size:
		new_status = 'error'
		new_message = f'File ingest failed: expected file size {file_record.size} bytes but calculated file size is {calculated_size} bytes'
	elif part_numbers_seen != set(range(1, file_record.parts + 1)):
		new_status = 'error'
		new_message = f'File ingest failed: invalid part number sequence'
	else:
		new_status = 'processing_queue'
		new_message = f'Ingested file {file_record.name} with {counted_parts} parts and total size {calculated_size} bytes'

	file_record = file_record._replace(
		status=new_status,
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

def _process_file(ctx: MappContext, file_record: File) -> File:
	"""
	Assemble file from parts, compute sha3_256, update file_record, handle errors.
	"""
	ctx.log(f'_process_file - begin - {file_record.id=}')
	#
	# initialize
	#

	file_path = _file_path(file_record)
	parts = _list_parts(ctx, file_record.id)
	checksum = sha3_256()

	#
	# copy data to single file and compute checksum
	#

	try:

		# actual process #

		os.makedirs(os.path.dirname(file_path), exist_ok=True)
		with open(file_path, 'wb') as full_file_handle:
			for part in parts:
				part_path = _file_part_path(file_record.id, part.part_number)
				with open(part_path, 'rb') as part_handle:
					while True:
						chunk = part_handle.read(OS_HANDLE_BUFFER_SIZE)
						if not chunk:
							break
						full_file_handle.write(chunk)
						checksum.update(chunk)
	
	except Exception as e:

		# handle error in process #

		err_msg = f'Error processing file: {str(e)}'
		file_record = file_record._replace(
			status='error',
			message=err_msg,
			updated_at=datetime_for_db(datetime_now_utc())
		)
	
	else:

		# handle successful process #

		file_record = file_record._replace(
			status='good',
			sha3_256=checksum.hexdigest(),
			updated_at=datetime_for_db(datetime_now_utc()),
			message='File processed successfully'
		)
		
	#
	# update file record with status
	#

	ctx.db.cursor.execute(
		"""
		UPDATE file
		SET status = ?, sha3_256 = ?, message = ?, updated_at = ?
		WHERE id = ?
		""",
		(
			file_record.status,
			file_record.sha3_256,
			file_record.message,
			file_record.updated_at,
			file_record.id
		)
	)
	ctx.db.commit()

	#
	# return
	#

	return file_record

def _get_file_record(ctx: MappContext, file_id: str) -> File:
	files = list_files(ctx, 0, 1, user_id='-1', file_id=file_id)
	try:
		file_record_dict = files['items'][0]
		return File(**file_record_dict)
	except IndexError:
		raise NotFoundError('FILE_NOT_FOUND', f'File not found for id: {file_id}')

#
# commands
#

def ingest_start(ctx: MappContext, name: str, size: int, parts: int, content_type: str = '', finish: bool = False) -> dict: 
	f"""Ingest a file

	name: file name with extension
	size: total size of the file in bytes
	parts: total number of parts the file is split into; must be 1 for now
	content_type: optional content type of the file; will be guessed from name if not provided
	finish: if true, will attempt to finish ingest and process file after ingesting part(s); must provide part content in file_input

	CURRENT LIMITATIONS:
	- Only single part files are supported (parts must be 1)
	- must provide finish=true
	- file must be less than {FILE_SIZE_LIMIT} bytes in size

	"""

	user = current_user(ctx)['value']

	file_input = ctx.self.get('file_input', None)

	#
	# validate input
	#

	field_errors = {}

	if finish and file_input is None:
		field_errors['finish'] = 'User must supply a file_input if finish is true'
	elif finish and parts != 1:
		field_errors['finish'] = f'Cannot finish ingest in ingest_start call if multiple parts are specified; got: {parts}'
	elif not finish:
		field_errors['finish'] = 'Currently only auto-finish of single part files is supported'
	
	if parts < 0:
		field_errors['parts'] = 'Parts must be a non-negative integer'
	elif parts > 1:
		field_errors['parts'] = 'Ingest of multipart files is not supported yet'

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

	file_record = file_record._replace(id=str(ctx.db.cursor.lastrowid))

	# 
	# upload part and/or finish if requested
	#

	if file_input is not None:
		_ingest_part(ctx, 1, file_input, file_record, user)
		if finish:
			file_record = _ingest_finish(ctx, file_record)
			if file_record.status == 'processing_queue':
				file_record = _process_file(ctx, file_record)
		
	msg = f'file id {file_record.id} created with status: {file_record.status}'
	if file_record.message:
		msg += f' - {file_record.message}'

	ctx.log(f'ingest_start - {msg}')
	
	return {'file_id': file_record.id, 'message': msg}

def ingest_part(ctx: MappContext, file_id: str, part_number: int) -> dict:

	return {'acknowledged': False, 'message': 'ingest_part is not implemented yet'}

	file_input = ctx.self.get('file_input', None)
	user = current_user(ctx)['value']

	files = list_files(ctx, 0, 1, user.id, file_id)
	try:
		file_record = files['items'][0]
	except IndexError:
		raise NotFoundError('FILE_NOT_FOUND', f'File not found for id: {file_id}')

	#
	# validate input
	#

	field_errors = {}

	if file_input is None:
		raise MappUserError('NO_FILE_INPUT', 'User must supply a file_input for ingest_part')
	
	if not 0 < part_number <= file_record['parts']:
		field_errors['part_number'] = f'Part number must be between 1 and {file_record["parts"]} for file_id {file_id}'

	if field_errors:
		raise MappValidationError('Error uploading file part', field_errors)
	
	#
	# write part
	#

	_ingest_part(ctx, part_number, file_input, File(**file_record), user)

	return {'acknowledged': True, 'message': 'File part uploaded'}

def ingest_finish(ctx: MappContext, file_id: str) -> dict:
	return {'acknowledged': False, 'message': 'ingest_finish is not implemented yet'}

def get_part_content(ctx: MappContext, file_id: str, part_number: int) -> dict:

	#
	# validate input
	#

	# check to see if we're logged in, any user can ready any file
	current_user(ctx)['value']

	# user provided file_output #

	file_output = ctx.self.get('file_output', None)

	if file_output is None:
		raise MappUserError('NO_FILE_OUTPUT', 'User must supply a file_output to write file part content to')

	#
	# copy contents to file_output
	#

	part_path = _file_part_path(file_id, part_number)

	try:
		with open(part_path, 'rb') as f:
			while True:
				chunk = f.read(OS_HANDLE_BUFFER_SIZE)
				if not chunk:
					break
				file_output.write(chunk)
				file_output.flush()
	except FileNotFoundError:
		raise MappUserError('FILE_PART_NOT_FOUND', f'File part not found for file_id: {file_id} part_number: {part_number}')
	
	#
	# return
	#

	return {
		'acknowledged': True,
		'message': 'File part content written to self.file_output',
	}

def get_file_content(ctx: MappContext, file_id: str) -> dict:

	#
	# validate input
	#

	# check to see if we're logged in, any user can ready any file
	current_user(ctx)['value']

	# user provided file_output #

	file_output = ctx.self.get('file_output', None)

	if file_output is None:
		raise MappUserError('NO_FILE_OUTPUT', 'User must supply a file_output to write file content to')
	
	# file record #

	files = list_files(ctx, 0, 1, user_id='-1', file_id=file_id)
	try:
		file_record_dict = files['items'][0]
	except IndexError:
		raise NotFoundError('FILE_NOT_FOUND', f'File not found for id: {file_id}')
	
	if file_record_dict['parts'] > 1:
		raise MappUserError('MULTIPART_FILE', 'get_file_content does not support multipart files yet')
	
	file_record = File(**file_record_dict)
	full_file_path = _file_path(file_record)

	#
	# copy contents to file_output
	#

	ctx.self['file_output_name'] = file_record.name

	try:
		with open(full_file_path, 'rb') as f:
			while True:
				chunk = f.read(OS_HANDLE_BUFFER_SIZE)
				if not chunk:
					break
				file_output.write(chunk)
				file_output.flush()
	except FileNotFoundError:
		raise MappUserError('FILE_CONTENT_NOT_FOUND', f'File content not found for file_id: {file_id}')
	
	#
	# return
	#
	
	return {
		'acknowledged': True,
		'message': 'Feature only implemented for single part files'
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
	return {'acknowledged': False, 'message': 'delete_file is not implemented yet'}

def list_files(ctx: MappContext, offset: int = 0, size: int = 50, user_id: str = '-1', file_id: str = '-1', status: str = 'all') -> dict:
	
	# fetch files #

	ctx.log(f'list_files - {user_id=} {file_id=} {status=} {offset=} {size=}')

	ctx.db.cursor.execute(
		"""
		SELECT id, name, status, message, extension, size, parts, content_type, user_id, created_at, updated_at, sha3_256
		FROM file
		WHERE (? = '-1' OR user_id = ?) AND (? = '-1' OR id = ?) AND (? = 'all' OR status = ?)
		ORDER BY updated_at ASC
		LIMIT ? OFFSET ?
		""",
		(user_id, user_id, file_id, file_id, status, status, size, offset)
	)

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
			'user_id': str(row[8]),
			'created_at': datetime_from_db(row[9]).isoformat(),
			'updated_at': datetime_from_db(row[10]).isoformat(),
			'sha3_256': row[11]
		} 
		for row in ctx.db.cursor.fetchall()
	]

	# fetch total count #

	ctx.db.cursor.execute(
		"SELECT COUNT(*) FROM file WHERE (? = '-1' OR user_id = ?) AND (? = '-1' OR id = ?) AND (? = 'all' OR status = ?)",
		(user_id, user_id, file_id, file_id, status, status)
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
			'user_id': str(row[5]),
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

def process_file(ctx: MappContext, file_id: str) -> dict:
	"""
	Assemble file from parts, compute sha3_256, update file_record, handle errors.
	"""

	user = current_user(ctx)['value']
	files = list_files(ctx, 0, 1, user.id, file_id)
	try:
		file_record_dict = files['items'][0]
	except IndexError:
		raise NotFoundError('FILE_NOT_FOUND', f'File not found for id: {file_id}')

	file_record = File(**file_record_dict)
	file_path = _file_path(file_record)
	parts = _list_parts(ctx, file_id)
	checksum = sha3_256()

	try:
		os.makedirs(os.path.dirname(file_path), exist_ok=True)
		with open(file_path, 'wb') as full_file_handle:
			for part in parts:
				part_path = _file_part_path(file_id, part.part_number)
				with open(part_path, 'rb') as part_handle:
					while True:
						chunk = part_handle.read(OS_HANDLE_BUFFER_SIZE)
						if not chunk:
							break
						full_file_handle.write(chunk)
						checksum.update(chunk)

		file_record = file_record._replace(
			status='good',
			sha3_256=checksum.hexdigest(),
			updated_at=datetime_for_db(datetime_now_utc()),
			message='File processed successfully'
		)
		ctx.db.cursor.execute(
			"""
			UPDATE file
			SET status = ?, sha3_256 = ?, message = ?, updated_at = ?
			WHERE id = ?
			""",
			(
				file_record.status,
				file_record.sha3_256,
				file_record.message,
				file_record.updated_at,
				file_record.id
			)
		)
		ctx.db.commit()
		return {'acknowledged': True, 'message': f'File processed successfully for file_id: {file_id} w/ sha3_256: {file_record.sha3_256}'}
	
	except Exception as e:
		err_msg = f'Error processing file: {str(e)}'
		file_record = file_record._replace(
			status='error',
			message=err_msg,
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
				file_record.updated_at,
				file_record.id
			)
		)
		ctx.db.commit()
		return {'acknowledged': False, 'message': err_msg}
