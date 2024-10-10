from sample import *

import os
import json

from urllib.request import Request, urlopen

# vars :: {"http://localhost:9009": "project.default_client_host"}

"""
WARNING: urlib.request module is unsafe to use with os.fork on OSX
    ref: https://docs.python.org/3/library/urllib.request.html#urllib.request.urlopen
"""

__all__ = [
    'client_init'
]

client_host = None
default_client_host = 'http://localhost:9009'
headers = {'Content-Type': 'application/json'}

def client_init(host:str=None) -> str:
    """
    initialize the client with a host. if host is not provided,
    it will use the value of the MSPEC_CLIENT_HOST environment variable,
    if that is not set, it will use '{}'.
    
    args ::
        host :: the host to connect to.
    
    return :: None
    """.format(default_client_host)
    global client_host
    if host is None:
        client_host = os.environ.get('MSPEC_CLIENT_HOST', default_client_host)
    else:
        client_host = host
    return client_host
