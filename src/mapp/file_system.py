import os

from mapp.context import MappContext
from mapp.types import ModelListResult

MAPP_APP_PATH = os.getenv('MAPP_APP_PATH', '')

"""

./run.sh file-system ingest-start run '{"name": "document.txt", "size": 1024, "parts": 1}'


"""

def _file_part_dir(file_id: str) -> str:
	if MAPP_APP_PATH == '':
		raise ValueError('MAPP_APP_PATH environment variable not set')
	return os.path.join(MAPP_APP_PATH, 'file_parts', file_id)

def ingest_start(ctx: MappContext, name: str, size: int, parts: int, content_type: str = '', finish: bool = False) -> dict:
	"""Placeholder for ingest_start operation."""
	
	return {'file_id': '1'}

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
