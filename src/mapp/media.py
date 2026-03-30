import json
import os
import subprocess
import tempfile

from mapp.auth import current_user
from mapp.context import MappContext
from mapp.errors import MappUserError, MappError
from mapp.file_system import _file_path, ingest_start, _get_file_record, get_file_content
from mapp.types import Image, MasterImage, datetime_from_db, datetime_now_utc

__all__ = [
	'create_image',
	'get_image',
	'get_master_image',
	'get_media_file_content',
	'ingest_master_image',
	'list_images',
	'list_master_images'
]

MAPP_MEDIA_INFO_PATH = os.getenv('MAPP_MEDIA_INFO_PATH', 'mediainfo')
MAPP_FFMPEG_PATH = os.getenv('MAPP_FFMPEG_PATH', 'ffmpeg')

# ffmpeg -q:v scale: 1 (best) to 31 (worst); 5 gives roughly 85% JPEG quality #
FFMPEG_JPEG_QUALITY = '5'

"""

./run.sh --log -fi ./tests/samples/splash-orig.png media create-image run '{"name": "splash.png"}'
./run.sh --log -fi ./tests/samples/splash-low.jpg media create-image run '{"name": "splash-low.jpg"}'

./run.sh media list-images run

./run.sh media get-image run '{"image_id": "1"}'

./run.sh -fo splash-media-id-1.png media get-media-file-content run '{"image_id": "1"}'

curl -X GET -o image-8.jpg  "http://localhost:3003/api/media/get-media-file-content?image_id=8" \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer xyz"

"""

#
# low level ops
#

def _call_mediainfo(file_path: str) -> dict:
	"""Get media info for a file using the mediainfo command line tool. Returns a dict with raw media info output."""
	
	if not os.path.exists(file_path):
		raise MappUserError(f'File not found at path: {file_path}')
	
	try:
		result = subprocess.run([MAPP_MEDIA_INFO_PATH, '--Full', '--Output=JSON', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
		return json.loads(result.stdout)
	
	except subprocess.CalledProcessError as e:
		if not os.path.exists(MAPP_MEDIA_INFO_PATH):
			raise MappError(f'Mediainfo tool not found at path: {MAPP_MEDIA_INFO_PATH}')
		else:
			raise MappUserError(f'Error getting media info: {e.stderr.decode()}')

def _call_ffmpeg(args: list[str]) -> None:
	"""Call ffmpeg with the given arguments. Raises an error if ffmpeg is not found or returns a non-zero exit code."""
	try:
		subprocess.run([MAPP_FFMPEG_PATH] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
	except subprocess.CalledProcessError as e:
		raise MappUserError('FFMPEG_ERROR', f'Error calling ffmpeg: {e.stderr.decode()}')
	except FileNotFoundError:
		raise MappError('FFMPEG_NOT_FOUND', f'ffmpeg tool not found at path: {MAPP_FFMPEG_PATH}, set path via env MAPP_FFMPEG_PATH')

def _get_image_record(ctx: MappContext, image_id: str) -> Image:
	"""Fetch an image record by ID and return it as an Image namedtuple. Raises an error if the record is not found, or user doesn't have access to it."""

	user = current_user(ctx)['value']

	ctx.db.cursor.execute("""
	SELECT id, file_id, user_id, format, width, height, aspect_ratio, file_size, compression_mode, bit_depth, color_space, chroma_subsampling, created_at
	FROM image
	WHERE id = ?
	""", (image_id,))

	row = ctx.db.cursor.fetchone()
	if row is None:
		raise MappUserError('IMAGE_NOT_FOUND', f'No image found with ID: {image_id}')
	
	return Image(
		id=str(row[0]),
		file_id=str(row[1]),
		user_id=str(row[2]),
		format=row[3],
		width=row[4],
		height=row[5],
		aspect_ratio=row[6],
		file_size=row[7],
		compression_mode=row[8],
		bit_depth=row[9],
		color_space=row[10],
		chroma_subsampling=row[11],
		created_at=datetime_from_db(row[12])
	)

def _get_master_image_record(ctx: MappContext, master_image_id: str) -> MasterImage:
	"""Fetch a master image record by ID and return it as a MasterImage namedtuple. Raises an error if the record is not found, or user doesn't have access to it."""

	user = current_user(ctx)['value']

	ctx.db.cursor.execute("""
	SELECT id, original_image_id, web_image_id, thumbnail_image_id, user_id, created_at
	FROM master_image
	WHERE id = ?
	""", (master_image_id,))

	row = ctx.db.cursor.fetchone()
	if row is None:
		raise MappUserError('MASTER_IMAGE_NOT_FOUND', f'No master image found with ID: {master_image_id}')

	return MasterImage(
		id=str(row[0]),
		original_image_id=str(row[1]),
		web_image_id=str(row[2]),
		thumbnail_image_id=str(row[3]),
		user_id=str(row[4]),
		created_at=datetime_from_db(row[5])
	)

#
# commands
#

def create_image(ctx: MappContext, name:str, content_type: str) -> dict:
	f"""Ingest a file, create a file record, and create an image record linked to it. 
		Returns an error if the file is not a valid image.

		Must provide ctx.self.file_input as bytes for the file content to ingest.

	Args: 
		name: str - the name of the file to ingest (e.g. "splash.png")
		content_type: str - the content type of the file to ingest, if not provided
							it will be inferred from the file name extension (e.g. "image/png")
							this will be stored on the file record that is created
	Returns: a dict with
		image_id:str - the ID of the created image record
		file_id:str - the ID of the ingested file
		message:str - a message indicating success or failure
	"""

	user = current_user(ctx)['value']

	#
	# ingest file
	#

	try:
		file_input = ctx.self['file_input']
	except KeyError:
		raise MappUserError('MISSING_FILE_INPUT', 'Missing required input: self.file_input')

	ingest_result = ingest_start(
		ctx=ctx,
		name=name,
		size=len(file_input),
		parts=1,
		content_type=content_type,
		finish=True,
	)

	file_record = _get_file_record(ctx, ingest_result['file_id'])			# hack solution bc ingest_start doesn't return the record,
																			# could be made more efficient by returning the record directly from ingest_start
	
	#
	# call mediainfo and parse output
	#

	full_file_path = _file_path(file_record)

	info = _call_mediainfo(full_file_path)
	try:
		tracks = info['media']['track']
	except KeyError as e:
		raise MappError('MALFORMED_MEDIA_INFO', f'Missing key: {e}')
	
	try:
		image_track = list(filter(lambda t: t['@type'] == 'Image', tracks))[0]
	except IndexError:
		raise MappUserError('INVALID_IMAGE', 'File is missing an image track')
	
	try:
		format = image_track['Format']
	except KeyError:
		raise MappUserError('MISSING_IMAGE_FORMAT', 'Image track is missing format information')
	
	try:
		width = int(image_track['Width'])
		height = int(image_track['Height'])
	except KeyError:
		raise MappUserError('MISSING_IMAGE_DIMENSIONS', 'Image track is missing width and height information')
	
	#
	# create image record
	#
	
	image_record = Image(
		id='',
		file_id=file_record.id,
		user_id=user['id'],
		format=format,
		width=width,
		height=height,
		aspect_ratio=width / height,
		file_size=file_record.size,
		compression_mode=image_track.get('Compression_Mode', '-'),
		bit_depth=int(image_track.get('BitDepth', -1)),
		color_space=image_track.get('ColorSpace', '-'),
		chroma_subsampling=image_track.get('ChromaSubsampling', '-'),
		created_at=datetime_now_utc()
	)

	ctx.db.cursor.execute("""
		INSERT INTO image (file_id, user_id, format, width, height, aspect_ratio, file_size, compression_mode, bit_depth, color_space, chroma_subsampling, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	""", (
		image_record.file_id,
		image_record.user_id,
		image_record.format,
		image_record.width,
		image_record.height,
		image_record.aspect_ratio,
		image_record.file_size,
		image_record.compression_mode,
		image_record.bit_depth,
		image_record.color_space,
		image_record.chroma_subsampling,
		image_record.created_at,
	))

	ctx.db.commit()

	image_record = image_record._replace(id=str(ctx.db.cursor.lastrowid))

	return {
		'image_id': image_record.id,
		'file_id': file_record.id,
		'message': 'Image created successfully'
	}

def ingest_master_image(ctx: MappContext, name: str, content_type: str, thumbnail_max_size: int = 300) -> dict:
	"""Ingest an image and create alternate versions (web and thumbnail) via ffmpeg. 
		Creates an image record for each version and links them via a master image record.

		Must provide ctx.self.file_input as bytes for the original file content to ingest.

	Args:
		name: str - the name of the original image file (e.g. "photo.png")
		content_type: str - the content type of the original image file (e.g. "image/png")
		thumbnail_max_size: int - the maximum width or height of the thumbnail in pixels (default: 300)
	Returns: a dict with
		master_image_id:str - the ID of the created master image record
		original_image_id:str - the ID of the original image record
		web_image_id:str - the ID of the web version image record
		thumbnail_image_id:str - the ID of the thumbnail image record
		message:str - a message indicating success
	"""

	user = current_user(ctx)['value']

	#
	# step 1: ingest original image
	#

	original_result = create_image(ctx, name, content_type)
	original_image_id = original_result['image_id']
	original_file_record = _get_file_record(ctx, original_result['file_id'])
	original_file_path = _file_path(original_file_record)

	with tempfile.TemporaryDirectory() as tmp_dir:

		#
		# step 2: create web version via ffmpeg (full resolution, JPEG, quality ~85)
		#

		web_path = os.path.join(tmp_dir, 'web.jpg')
		_call_ffmpeg(['-y', '-i', original_file_path, '-q:v', FFMPEG_JPEG_QUALITY, web_path])

		with open(web_path, 'rb') as f:
			web_bytes = f.read()

		#
		# step 3: ingest web version
		#

		web_name = os.path.splitext(name)[0] + '.web.jpg'
		ctx.self['file_input'] = web_bytes
		web_result = create_image(ctx, web_name, 'image/jpeg')
		web_image_id = web_result['image_id']

		#
		# step 4: create thumbnail via ffmpeg (constrained size, maintaining aspect ratio)
		#

		thumb_path = os.path.join(tmp_dir, 'thumb.jpg')
		n = thumbnail_max_size
		_call_ffmpeg(['-y', '-i', original_file_path, '-vf', f'scale={n}:{n}:force_original_aspect_ratio=decrease', '-q:v', FFMPEG_JPEG_QUALITY, thumb_path])

		with open(thumb_path, 'rb') as f:
			thumb_bytes = f.read()

		#
		# step 5: ingest thumbnail
		#

		thumb_name = os.path.splitext(name)[0] + '.thumb.jpg'
		ctx.self['file_input'] = thumb_bytes
		thumb_result = create_image(ctx, thumb_name, 'image/jpeg')
		thumbnail_image_id = thumb_result['image_id']

	#
	# step 6: create master image record
	#

	master_image_record = MasterImage(
		id='',
		original_image_id=original_image_id,
		web_image_id=web_image_id,
		thumbnail_image_id=thumbnail_image_id,
		user_id=user['id'],
		created_at=datetime_now_utc()
	)

	ctx.db.cursor.execute("""
		INSERT INTO master_image (original_image_id, web_image_id, thumbnail_image_id, user_id, created_at)
		VALUES (?, ?, ?, ?, ?)
	""", (
		master_image_record.original_image_id,
		master_image_record.web_image_id,
		master_image_record.thumbnail_image_id,
		master_image_record.user_id,
		master_image_record.created_at,
	))

	ctx.db.commit()

	master_image_id = str(ctx.db.cursor.lastrowid)

	return {
		'master_image_id': master_image_id,
		'original_image_id': original_image_id,
		'web_image_id': web_image_id,
		'thumbnail_image_id': thumbnail_image_id,
		'message': 'Master image created successfully'
	}

def get_image(ctx: MappContext, image_id: str) -> dict:
	"""Get an image record by ID. Returns an error if the record is not found, or user doesn't have access to it.

	Args:
		image_id: str - the ID of the image record to fetch
	Returns: a dict with
		image_id:str - the ID of the image record
		file_id:str - the ID of the associated file record
		user_id:str - the ID of the user who created the image record
		format:str - the image format (e.g. JPEG, PNG)
		width:int - the image width in pixels
		height:int - the image height in pixels
		aspect_ratio:float - the image aspect ratio (width / height)
		file_size:int - the size of the image file in bytes
		compression_mode:str - the compression mode used for the image (e.g. Lossy, Lossless)
		bit_depth:int - the bit depth of the image (e.g. 8, 16)
		color_space:str - the color space of the image (e.g. RGB, YUV)
		chroma_subsampling:str - the chroma subsampling used for the image (e.g. 4:4:4, 4:2:0)
		created_at:str - the ISO format timestamp when the image record was created
	"""

	image_record = _get_image_record(ctx, image_id)

	return {
		'id': image_record.id,
		'file_id': image_record.file_id,
		'user_id': image_record.user_id,
		'format': image_record.format,
		'width': image_record.width,
		'height': image_record.height,
		'aspect_ratio': image_record.aspect_ratio,
		'file_size': image_record.file_size,
		'compression_mode': image_record.compression_mode,
		'bit_depth': image_record.bit_depth,
		'color_space': image_record.color_space,
		'chroma_subsampling': image_record.chroma_subsampling,
		'created_at': image_record.created_at.isoformat()
	}

def get_media_file_content(ctx: MappContext, image_id: str = '-1', master_image_id: str = '-1') -> bytes:

	# check to see if we're logged in, any user can read any file
	current_user(ctx)['value']

	if image_id == '-1' and master_image_id == '-1':
		raise MappUserError('MISSING_ARG', 'get_media_file_content requires either image_id or master_image_id')

	if image_id != '-1' and master_image_id != '-1':
		raise MappUserError('AMBIGUOUS_ARG', 'get_media_file_content requires either image_id or master_image_id, not both')

	if image_id != '-1':
		image_record = _get_image_record(ctx, image_id)
		return get_file_content(ctx, image_record.file_id)
	else:
		master_image_record = _get_master_image_record(ctx, master_image_id)
		image_record = _get_image_record(ctx, master_image_record.original_image_id)
		return get_file_content(ctx, image_record.file_id)

def list_images(ctx: MappContext, offset: int = 0, size: int = 50, image_id: str = '-1', file_id: str = '-1', user_id: str = '-1') -> dict:
	"""List images that the current user has access to. Supports pagination and filtering by image ID and file ID.

	Args:
		offset: int - the number of records to skip for pagination
		size: int - the maximum number of records to return
		image_id: str - filter by image ID
		file_id: str - filter by file ID
		user_id: str - filter by user ID (i.e. list only images associated with files owned by this user ID)
	Returns: a dict with
		images: a list of image records matching the filters and pagination
		total: the total number of images matching the filters (ignoring pagination)
	"""

	user = current_user(ctx)['value']

	# fetch images #

	ctx.db.cursor.execute(f"""
	SELECT id, file_id, user_id, format, width, height, aspect_ratio, file_size, compression_mode, bit_depth, color_space, chroma_subsampling, created_at
	FROM image
	WHERE (? = '-1' OR id = ?) AND (? = '-1' OR file_id = ?) AND (? = '-1' OR user_id = ?)
	ORDER BY created_at DESC
	LIMIT ? OFFSET ?
	""", (image_id, image_id, file_id, file_id, user_id, user_id, size, offset))

	items = [
		{
			'id': str(row[0]),
			'file_id': str(row[1]),
			'user_id': str(row[2]),
			'format': row[3],
			'width': row[4],
			'height': row[5],
			'aspect_ratio': row[6],
			'file_size': row[7],
			'compression_mode': row[8],
			'bit_depth': row[9],
			'color_space': row[10],
			'chroma_subsampling': row[11],
			'created_at': datetime_from_db(row[12]).isoformat()
		}
		for row in ctx.db.cursor.fetchall()
	]

	# fetch total count #

	ctx.db.cursor.execute(f"""
	SELECT COUNT(*)
	FROM image
	WHERE (? = '-1' OR id = ?) AND (? = '-1' OR file_id = ?) AND (? = '-1' OR user_id = ?)
	""", (image_id, image_id, file_id, file_id, user_id, user_id))

	total = ctx.db.cursor.fetchone()[0]

	# return result #

	return {
		'items': items,
		'total': total
	}

def get_master_image(ctx: MappContext, master_image_id: str) -> dict:
	"""Get a master image record by ID. Returns an error if the record is not found, or user doesn't have access to it.

	Args:
		master_image_id: str - the ID of the master image record to fetch
	Returns: a dict with
		id:str - the ID of the master image record
		original_image_id:str - the ID of the original image record
		web_image_id:str - the ID of the web version image record
		thumbnail_image_id:str - the ID of the thumbnail image record
		user_id:str - the ID of the user who created the master image record
		created_at:str - the ISO format timestamp when the master image record was created
	"""

	master_image_record = _get_master_image_record(ctx, master_image_id)

	return {
		'id': master_image_record.id,
		'original_image_id': master_image_record.original_image_id,
		'web_image_id': master_image_record.web_image_id,
		'thumbnail_image_id': master_image_record.thumbnail_image_id,
		'user_id': master_image_record.user_id,
		'created_at': master_image_record.created_at.isoformat()
	}

def list_master_images(ctx: MappContext, offset: int = 0, size: int = 50, master_image_id: str = '-1', user_id: str = '-1') -> dict:
	"""List master images that the current user has access to. Supports pagination and filtering by master image ID and user ID.

	Args:
		offset: int - the number of records to skip for pagination
		size: int - the maximum number of records to return
		master_image_id: str - filter by master image ID
		user_id: str - filter by user ID
	Returns: a dict with
		items: a list of master image records matching the filters and pagination
		total: the total number of master images matching the filters (ignoring pagination)
	"""

	user = current_user(ctx)['value']

	# fetch master images #

	ctx.db.cursor.execute("""
	SELECT id, original_image_id, web_image_id, thumbnail_image_id, user_id, created_at
	FROM master_image
	WHERE (? = '-1' OR id = ?) AND (? = '-1' OR user_id = ?)
	ORDER BY created_at DESC
	LIMIT ? OFFSET ?
	""", (master_image_id, master_image_id, user_id, user_id, size, offset))

	items = [
		{
			'id': str(row[0]),
			'original_image_id': str(row[1]),
			'web_image_id': str(row[2]),
			'thumbnail_image_id': str(row[3]),
			'user_id': str(row[4]),
			'created_at': datetime_from_db(row[5]).isoformat()
		}
		for row in ctx.db.cursor.fetchall()
	]

	# fetch total count #

	ctx.db.cursor.execute("""
	SELECT COUNT(*)
	FROM master_image
	WHERE (? = '-1' OR id = ?) AND (? = '-1' OR user_id = ?)
	""", (master_image_id, master_image_id, user_id, user_id))

	total = ctx.db.cursor.fetchone()[0]

	# return result #

	return {
		'items': items,
		'total': total
	}
