import re
import os
import base64
import json

from pathlib import Path
from typing import ClassVar, BinaryIO, Union, Dict
from dataclasses import dataclass, field, asdict
from hashlib import sha3_256
from datetime import datetime

__all__ = [
    'datetime_format_str',
    'email_regex',

    'MSpecJsonEncoder',
    'to_json',

    'CID',
    'Tags',
    'Hierarchy',
    'Hierarchies',
    'Meta',
    'Context',

    'entity_types',
    'Entity',
    'ACL',
    'permission_types',
    'Permission',
]


try:
    import boto3
except ImportError:
    pass

datetime_format_str = '%Y-%m-%dT%H:%M:%S'
email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

#
# json encoder
#

class MSpecJsonEncoder(json.JSONEncoder):

    def default(self, obj):

        if isinstance(obj, datetime):
            return obj.strftime(datetime_format_str)
        elif isinstance(obj, CID):
            return str(obj)
        elif isinstance(obj, Path):
            return str(obj)
        elif getattr(obj, '__dataclass_params__', None):
            return super().default(asdict(obj))
        else:
            return super().default(obj)

def to_json(data:dict) -> str:
    return json.dumps(data, sort_keys=True, cls=MSpecJsonEncoder)

#
# content id
#

_cid_hash_pattern = r'[A-Za-z0-9-_]{43}'
_read_buffer_len = int(os.environ.get('READ_BUFFER_LEN', 1024 * 1024 * 16))

@dataclass(frozen=True)
class CID:
    hash:str
    size:int
    ext:str = ''

    cid_version: ClassVar[int] = 0

    # core methods #

    def validate(self):
        try:
            if not re.match(_cid_hash_pattern, self.hash):
                raise ValueError('Invalid content id hash')
        except TypeError:
            raise ValueError(f'Invalid content hash {self.hash}')
        
        try:
            if self.size < 0:
                raise ValueError('Invalid content id size')
        except TypeError:
            raise ValueError('Invalid content id size')
        
        if not isinstance(self.ext, str):
            raise ValueError('Invalid content id ext')

    def __str__(self) -> str:
        return self.identifier
    
    @property
    def identifier(self) -> str:
        cid = f'{self.cid_version}{self.hash}{self.size}'
        if self.ext != '':
            cid += f'.{self.ext}'
        return cid
    
    @staticmethod
    def _hash_from_digest(digest:bytes) -> str:
        return base64.urlsafe_b64encode(digest).decode('utf-8')[0:-1]   # remove final padding (=)
        
    # initilization existing CIDs #

    @classmethod
    def create(cls, content_id:Union[str, dict, 'CID']) -> 'CID':
        """initialize an existing ContentId from various input types"""
        if isinstance(content_id, str):
            return cls.parse(content_id)
        elif isinstance(content_id, dict):
            return cls(**content_id)
        elif isinstance(content_id, cls):
            return content_id
        else:
            raise ValueError(f'Invalid ContentId input type: {type(content_id)}')

    @classmethod
    def parse(cls, content_id:str) -> 'CID':
        """parse an existing ContentId string"""
        version = int(content_id[0])
        if version != 0:
            raise ValueError(f'Invalid CID version')
        
        hash = content_id[1:44]
        if not re.match(_cid_hash_pattern, hash):
            raise ValueError('Invalid content id hash')

        period_index = content_id.find('.')

        if period_index == -1:
            size = int(content_id[44:])
            ext = ''
        else:
            size = int(content_id[44:period_index])
            ext = content_id[period_index + 1:]

        return cls(hash=hash, size=size, ext=ext)
    
    # calculate new content id #

    @classmethod
    def from_string(cls:'CID', string:str, ext:str) -> 'CID':
        """calculate a return a ContentId from a string"""
        hash_obj = sha3_256(string.encode('utf-8'))
        hash = cls._hash_from_digest(hash_obj.digest())
        return cls(hash=hash, size=len(string), ext=ext)

    @classmethod
    def from_dict(cls:'CID', data:Dict) -> 'CID':
        """calculate a return a ContentId from a dictionary"""
        json_string = to_json(data)
        cid = cls.from_string(json_string, 'json')
        # print(f'{cid.hash} {json_string}')
        return cid

    @classmethod
    def from_io(cls:'CID', stream:BinaryIO, size:int, ext:str) -> 'CID':
        """calculate a return a ContentId from a file-like object"""
        hash_obj = sha3_256()
        while True:
                buffer = stream.read(_read_buffer_len)
                if not buffer:
                    break
                hash_obj.update(buffer)

        hash = cls._hash_from_digest(hash_obj.digest())

        return cls(hash=hash, size=size, ext=ext)

    @classmethod
    def from_filepath(cls:'CID', filepath:Union[str, Path]) -> 'CID':
        """calculate a return a ContentId from a file path"""
        path:Path = Path(filepath)
        ext = ''.join(path.suffixes)[1:]

        stat = path.stat()
        size = stat.st_size

        with path.open('rb') as stream:
            return cls.from_io(stream, size, ext)
    
    @classmethod
    def from_s3(cls:'CID', bucket:str, key:str) -> 'CID':
        """calculate a return a ContentId from an S3 object"""
        ext = os.path.splitext(key)[1][1:]

         # stat file for size #
        try:
            s3_client = boto3.client('s3')
        except NameError:
            raise NameError('boto3 is not installed. Please install it to use S3 functionality.')
        
        stat = s3_client.head_object(Bucket=bucket, Key=key)
        size = stat['ContentLength']

        # calculate hash #

        hash_obj = sha3_256()
        start = 0
        end = _read_buffer_len

        while True:
            if start >= size:
                break

            response = s3_client.get_object(
                Bucket=bucket, 
                Key=key, 
                Range=f'bytes {start}-{min(size, end)}/{size}'
            )
            hash_obj.update(response['Body'].read())

            start += _read_buffer_len
            end += _read_buffer_len
        
        hash = cls._hash_from_digest(hash_obj.digest())

        return cls(hash=hash, size=size, ext=ext)

#
# metadata
#

_max_tags_length = int(os.environ.get('MAX_TAGS_LENGTH', 32))
class Tags(list):

    def validate(self):
        total = 0
        for tag in self:
            total += 1
            if not isinstance(tag, str):
                raise ValueError('Invalid tag type')
        if total > _max_tags_length:
            raise ValueError(f'Tags length exceeds maximum of {_max_tags_length}')
        
        if len(self) != len(set(self)):
            raise ValueError('Tags must be unique')

class Hierarchy(str):

    def levels(self) -> list:
        return str.split(self, '/')
    
    def validate(self):
        if self[0] == '/' or self[-1] == '/':
            raise ValueError('Hierarchy cannot start or end with a /')
        
        for level in self.levels():
            if level == '':
                raise ValueError('Hierarchy level cannot be an empty string')

class Hierarchies(list):

    def __init__(self, iterable=None):
        if iterable is None:
            iterable = []
        super().__init__(Hierarchy(item) for item in iterable)

    def validate(self):
        for index, item in enumerate(self):
            if not isinstance(item, Hierarchy):
                raise ValueError(f'Invalid hierarchy type at index {index}')
        
            item.validate()

@dataclass
class Meta:
    data: dict[str, str|int|float|bool] = field(default_factory=dict)
    tags: Tags = field(default_factory=Tags)
    hierarchies: Hierarchies = field(default_factory=lambda: Hierarchies([]))

    def __post_init__(self):
        self.tags = Tags(self.tags)
        self.hierarchies = Hierarchies(self.hierarchies)
    
    def validate(self):
        for key, value in self.data.items():
            if not isinstance(key, str):
                raise ValueError('Meta keys must be strings')
            if not isinstance(value, (str, int, float, bool)):
                raise ValueError(f'Invalid value type for data.{key}')
        self.tags.validate()
        self.hierarchies.validate()

@dataclass
class Context:
    id: str = ''
    source: str = ''
    meta: meta = field(default_factory=Meta) # type: ignore

    def validate(self):
        if not isinstance(self.id, str):
            raise ValueError('Context id must be a string')
        
        if not isinstance(self.source, str):
            raise ValueError('Context source must be a string')
        
        self.meta.validate()

#
# permissions
#

entity_types = {'user', 'profile', 'group_profile'}

@dataclass
class Entity:
    id: CID
    type: str

    def validate(self):
        if not isinstance(self.id, CID):
            raise ValueError('Invalid entity id')
        
        self.id.validate()
        
        if self.type not in entity_types:
            raise ValueError(f'Invalid entity type: {self.type}')
           
@dataclass
class ACL:
    name: str
    admin: Entity

    def validate(self):
        if not isinstance(self.name, str):
            raise ValueError('ACL name must be a string')
        
        if not isinstance(self.admin, Entity):
            raise ValueError('ACL admin must be an entity')
        
        self.admin.validate()

permission_types = {'public', 'private', 'inherit'}

@dataclass
class Permission:
    """define permissions either by PermissionType or a ContentId of an ACL"""
    read: str | CID
    write: str | CID
    delete: str | CID

    def validate(self):
        if isinstance(self.read, CID):
            self.read.validate()
        elif self.read not in permission_types:
            raise ValueError(f'Invalid read permission type: {self.read}')
        
        if isinstance(self.write, CID):
            self.write.validate()
        elif self.write not in permission_types:
            raise ValueError(f'Invalid write permission type: {self.write}')
        
        if isinstance(self.delete, CID):
            self.delete.validate()
        elif self.delete not in permission_types:
            raise ValueError(f'Invalid delete permission type: {self.delete}')


class Fonts:
    heading1 = ('Courier', 35)
    text = ('Courier', 12)
