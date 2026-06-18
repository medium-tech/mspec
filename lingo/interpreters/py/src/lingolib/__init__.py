import yaml


def parse_file(path):
    with open(path) as f:
        doc = yaml.safe_load(f)
    spec = (doc.get('lingo') or {}).get('spec')
    if not spec:
        raise ValueError(f'missing lingo.spec in {path}')
    return doc


def _eval(expr):
    if isinstance(expr, dict):
        if 'str' in expr:
            return str(expr['str'])
    raise ValueError(f'unsupported expression: {expr!r}')


def execute_exe(doc):
    main = doc.get('main')
    if main is None:
        raise ValueError('exe spec missing main')
    return _eval(main)


def execute_file(path):
    doc = parse_file(path)
    spec = doc['lingo']['spec']
    if spec == 'exe':
        return execute_exe(doc)
    raise ValueError(f'unsupported spec: {spec!r}')
