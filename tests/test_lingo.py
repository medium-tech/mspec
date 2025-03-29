from lingo.expressions import *
from pprint import pprint

app = LingoApp.init(example_spec, first_visit=False)

rendered_doc = render_document(app)
pprint(rendered_doc)

# breakpoint()