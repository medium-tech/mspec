#!/bin/bash
uwsgi --http :9009 --wsgi-file src/msample/server.py --static-map /=../html/ --static-index index.html --workers 4