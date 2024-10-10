from pathlib import Path
import yaml

__all__ = ['spec', 'spec_dir', 'dist_dir']

spec_dir = Path(__file__).parent.parent.parent / 'spec'
dist_dir = Path(__file__).parent.parent.parent / 'dist'

def load_spec(pattern:str='*.yaml') -> dict:
    """
    load all yaml files in the spec directory and return them as a dictionary,
    each top level key is the name of the file without extension 
    and its value is the parsed yaml as a dictionary
    """
    spec = {}
    for spec_path in spec_dir.glob(pattern):
        with open(spec_path) as f:
            spec[spec_path.stem] = yaml.load(f, Loader=yaml.FullLoader)
    return spec
