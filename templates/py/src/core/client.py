# for :: {% for module in modules.values() %} :: {"sample_module": "module.name.snake_case"}
from sample_module import sample_module_client
# end for ::
import os

# vars :: {"http://localhost:9009": "client.default_host"}

"""
WARNING: urlib.request module is unsafe to use with os.fork on OSX
    ref: https://docs.python.org/3/library/urllib.request.html#urllib.request.urlopen
"""

__all__ = [
    'create_client_context'
]

default_host = os.environ.get('MSPEC_CLIENT_HOST', 'http://localhost:9009')

def create_client_context(host:str=default_host) -> dict:
    """
    initialize the client with a host. if host is not provided,
    it will use the value of the `MSPEC_CLIENT_HOST` environment variable,
    if that is not set, it will use the value for environment variable `MSPEC_CLIENT_HOST`.
    
    args ::
        host :: the host to connect to.
    
    return :: None
    """.format(default_host)

    return {
        'host': host,
        'headers': {
            'Content-Type': 'application/json'
        }
    }

class MSpecClient:

    # for :: {% for module in modules.values() %} :: {"sample_module": "module.name.snake_case"}
    sample_module = sample_module_client
    # end for ::