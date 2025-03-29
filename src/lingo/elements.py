from enum import Enum
from dataclasses import dataclass, field, asdict, fields
from typing import Annotated, Union, Optional, Any
from pathlib import Path
from datetime import datetime, date
from random import randint

# from mistletoe import Document as MistletoeDocument
# from mistletoe import block_token, span_token
# from mistletoe.base_renderer import BaseRenderer as BaseMistletoeRenderer

"""
self:
  - input
  - state
  - output
  - client
    - if we're a client this is info about the local machine
    - if we're a server this is info about the remote client
  - server
    - if we're a client this is info about the remote server
    - if we're a server this is info about the local machine

control flow:
  branch (if/elif/else)
  switch

comparison:
  eq, ne, lt, le, gt, ge

logical:
  and, or, not

convert:
  to_bool, to_int, to_float, to_str, to_list, invert

math functions:
  nums:  add, subtract, multiply, divide, power, modulo
  lists: sum, mean, median, mode, range, variance, standard_deviation

temporal:
  now, today, duration, timedelta, time, date, datetime

list ops:
  sort, reverse
  enumerate, count
  concat, append, extend, insert
  any, all, none, map, reduce
  filter, drop, dropwhile, take, takewhile

device:
  screen(s), resolution, dpi
  camera, location, orientation

document:
  heading, text
"""

__all__ = [
    'TextOptions',
    'Text',
    'Link',
    'Heading',
    'TextListType',
    'TextList',
    'TextBlockElements',
    'TextBlock',
    'CodeBlock',
    'Footer',

    'ModelOp',
    'ModelField',
    'ModelFields',
    'ModelView',
    'MenuSeparator',
    'Menu',
    'MarkdownContent',
    'PageElements',
    'Page',
    'Route',

    'UserInterfaceId',
    'UserInterfaceCid',
    'UserInterface',
    'UserInterfaceCreator',

    'TextDocumentId',
    'TextDocumentCid',
    'TextDocument',
    'TextDocumentCreator'
]

#
# text components
#

@dataclass
class TextComponent:
    """base class for text components"""

class TextOptions(TextComponent):
    bold: Optional[bool] = None
    code: Optional[bool] = None
    italic: Optional[bool] = None
    strikethrough: Optional[bool] = None
    underline: Optional[bool] = None

    def validate(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if value is not None and not isinstance(value, bool):
                raise ValueError(f'{field.name} must be a boolean or null, got {type(value)}')

    def render_dict(self, **context) -> dict:
        data = {}
        for field in fields(self):
            value = getattr(self, field.name)
            if value is not None:
                data[field.name] = value
        return data

    def render_str(self, **context) -> str:
        
        options = []
        for key, value in self.model_dump().items():
            if value is True:
                options.append(key)

        out = 'TextOptions: '
        out += ', '.join(options)
        return out

class Text(TextComponent):
    text: str
    options: Optional[TextOptions] = None

    def validate(self):
        if not isinstance(self.text, str):
            raise ValueError(f'Text must be a string, got {type(self.text)}')
        
        if self.options is not None and not isinstance(self.options, TextOptions):
            raise ValueError(f'Options must be a TextOptions instance or null, got {type(self.options)}')
        
        try:
            self.options.validate()
        except AttributeError:
            pass

    def render_dict(self, **context) -> dict:
        out = {'text': self.text}
        if self.options:
            out['options'] = self.options.render_dict(**context)
        return out

    def render_str(self, **context) -> str:
        out = f'Text: {self.text}'
        try:
            out += f' ({self.options.render_str(**context)})'
        except AttributeError:
            pass

        return out

class Link(TextComponent):
    link: str   # the url
    text: Optional[str] = None
    options: Optional[TextOptions] = None

    def validate(self):
        if not isinstance(self.link, str):
            raise ValueError(f'Link must be a string, got {type(self.link)}')
        
        if self.text is not None and not isinstance(self.text, str):
            raise ValueError(f'Text must be a string or null, got {type(self.text)}')

        if self.options is not None and not isinstance(self.options, TextOptions):
            raise ValueError(f'Options must be a TextOptions instance or null, got {type(self.options)}')
        
        try:
            self.options.validate()
        except AttributeError:
            pass
        
    def render_dict(self, **context) -> dict:
        out = {'link': self.link}
        if self.text:
            out['text'] = self.text
        if self.options:
            out['options'] = self.options.render_dict(**context)
        return out

    def render_str(self, **context) -> str:
        out = f'Link: {self.link}'
        if self.text:
            out += f' | {self.text}'

        return out
    
class Location(TextComponent):
    model: str
    cid: str
    text: Optional[str] = None
    options: Optional[TextOptions] = None

    def validate(self):
        if not isinstance(self.model, str):
            raise ValueError(f'Model must be a string, got {type(self.model)}')
        
        if not isinstance(self.cid, str):
            raise ValueError(f'CID must be a string, got {type(self.cid)}')

        if self.text is not None and not isinstance(self.text, str):
            raise ValueError(f'Text must be a string or null, got {type(self.text)}')

        if self.options is not None and not isinstance(self.options, TextOptions):
            raise ValueError(f'Options must be a TextOptions instance or null, got {type(self.options)}')
        
        try:
            self.options.validate()
        except AttributeError:
            pass

    def render_dict(self, **context) -> dict:
        out = {'model': self.model, 'cid': self.cid}
        if self.text:
            out['text'] = self.text
        if self.options:
            out['options'] = self.options.render_dict(**context)
        return out
    
    def render_str(self, **context) -> str:
        out = f'Location: {self.model} {self.cid}'
        if self.text:
            out += f' | {self.text}'

        return out

class Heading(TextComponent):
    heading: str
    level: int = field(default=1)

    def validate(self):
        if not isinstance(self.heading, str):
            raise ValueError(f'Heading must be a string, got {type(self.heading)}')
        if not isinstance(self.level, int):
            raise ValueError(f'Heading level must be an integer, got {type(self.level)}')
        if not (1 <= self.level <= 3):
            raise ValueError(f'Heading level must be between 1 and 3, got {self.level}')

    def render_dict(self, **context) -> dict:
        return asdict(self)

    def render_str(self, **context) -> str:
        return f'Heading {self.level}: {self.heading}\n'

class TextListType(str, Enum):
    bulleted = 'bulleted'
    numbered = 'numbered'

class TextList(TextComponent):
    list: list[Text]
    type: TextListType = TextListType.bulleted
    options: Optional[TextOptions] = None
    start: Optional[int] = None

    def validate(self):
        if not isinstance(self.list, list):
            raise ValueError(f'List must be a list, got {type(self.list)}')
        
        for item in self.list:
            if not isinstance(item, Text):
                raise ValueError(f'List items must be Text instances, got {type(item)}')

        if self.options is not None and not isinstance(self.options, TextOptions):
            raise ValueError(f'Options must be a TextOptions instance or null, got {type(self.options)}')
        
        try:
            self.options.validate()
        except AttributeError:
            pass

    def render_dict(self, **context) -> dict:
        out = {
            'list': [item.render_dict(**context) for item in self.list],
            'type': self.type,
        }
        
        if self.options:
            out['options'] = self.options.render_dict(**context)
        if self.start:
            out['start'] = self.start
        return out

    def render_str(self, **context) -> str:
        out = f'TextList\n'

        start_index = 1 if self.start is None else self.start

        for n, item in enumerate(self.list, start=start_index):
            if self.type == TextListType.numbered:
                bullet = f'{n})'
            else:
                bullet = f'*'

            out += f'\t{bullet} {item.render_str(**context)}\n'

        return out

TextBlockElements = Union[Link|Location|Text|TextList]
class TextBlock(TextComponent):
    block: list[TextBlockElements]

    def validate(self):
        if not isinstance(self.block, list):
            raise ValueError(f'Block must be a list, got {type(self.block)}')
        
        for item in self.block:
            if not isinstance(item, TextBlockElements):
                raise ValueError(f'Block items must be TextBlockElements instances, got {type(item)}')

    def render_dict(self, **context) -> dict:
        return {'block': [element.render_dict(**context) for element in self.block]}

    def render_str(self, **context) -> str:
        out = 'TextBlock:\n'

        for element in self.block:
            out += '\t' + element.render_str(**context) + '\n'
            # out += f'\t{type(element)} {element}\n'

        return out

class CodeBlock(TextComponent):
    code: str

    def validate(self):
        if not isinstance(self.code, str):
            raise ValueError(f'Code must be a string, got {type(self.code)}')

    def render_dict(self, **context) -> dict:
        return {'code': self.code}

    def render_str(self, **context) -> str:
        out = f'CodeBlock:\n'
        for line in self.code.split('\n'):
            out += f' >>> {line}\n'
        return out

class Footer(TextComponent):
    footer: TextBlock

    def render_dict(self, **context) -> dict:
        return {'footer': self.footer.render_dict(**context)}
    
    def render_str(self, **context) -> str:
        return f'Footer:\n{self.footer.render_str()}\n'

#
# ui components
#

class ModelOp(str, Enum):
    create = 'create'
    read = 'read'
    update = 'update'
    delete = 'delete'
    list = 'list'

ModelField = Annotated[str, 'a string representing a model field']
ModelFields = Annotated[list[ModelField], 'a list of ModelField instances (strings)']

class ModelView(TextComponent):
    model: str
    op: ModelOp
    id: Optional[str] = None
    fields: Optional[ModelFields] = None

MenuSeparator = Annotated[str, 'a string with text for a menu separator']

class Menu(TextComponent):
    menu: list[Link|MenuSeparator] = field(default_factory=list)
    heading: Optional[str] = None

    def render_dict(self, **context) -> dict:
        render_item = lambda item: item if isinstance(item, str) else item.render_dict(**context)
        out = {'menu': [render_item(item) for item in self.menu]}
        if self.heading:
            out['heading'] = self.heading
        return out

class MarkdownContent(TextComponent):
    md_path: Annotated[Path, 'path to a markdown file']
    pack: bool = False

    def _get_text_doc(self, **context) -> 'TextDocumentCreator':
        try:
            file_root = context['file_root']
        except KeyError:
            raise ValueError(f'No file_root in context, cannot load md_path: {self.md_path}')
        
        server_path = file_root / self.md_path
        
        return text_document_from_markdown(server_path)

    def render_dict(self, **context) -> list:
        if self.pack:
            text_doc = self._get_text_doc(**context)
            text_doc_rendered = text_doc.render_dict(**context)
            return text_doc_rendered['children']
        else:
            out = {'md_path': str(self.md_path)}
            if self.pack:
                out['pack'] = self.pack
            return [out]

    def render_str(self, **context) -> str:
        out = f'MarkdownContent: {self.md_path}\n'
        text_doc = self._get_text_doc(**context)
        out += text_doc.render_str(**context)
        return out
    
PageElements = Union[Heading, TextBlock, TextList, CodeBlock, ModelView, MarkdownContent]

class Page(TextComponent):
    page: list[PageElements] = field(default_factory=list)
    title: Optional[str] = None
    menu: Optional[Menu] = None
    footer: Optional[Footer] = None

    def render_dict(self, **context) -> dict:
        out = {'page': []}
        for element in self.page:
            if isinstance(element, MarkdownContent):
                out['page'].extend(element.render_dict(**context))
            else:   
                out['page'].append(element.render_dict(**context))

        if self.title:
            out['title'] = self.title
        if self.menu:
            out['menu'] = self.menu.render_dict(**context)
        if self.footer:
            out['footer'] = self.footer.render_dict(**context)
        return out

    def render_str(self, **context) -> str:
        out = 'Page:\n'
        if self.title:
            out += f'\tTitle: {self.title}\n'
        if self.menu:
            out += f'\tMenu: \n{self.menu}\n'
        if self.footer:
            out += f'\tFooter: {self.footer}\n'

        for element in self.page:
            out += element.render_str(**context)

        return out

class Route(TextComponent):
    route: Page
    path: str

    def render_dict(self, **context) -> dict:
        return {'route': self.route.render_dict(**context), 'path': self.path}

    def render_str(self, **context) -> str:
        out = f'Route: {self.path}\n'
        out += self.route.render_str(**context)
        return out


