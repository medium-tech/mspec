

__all__ = ['router', 'app']

def routes(url):
    if url == '':
        pass
    else:
        pass

def application(env, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return [b"<html><body><h1>Hello World</h1></body></html>"]