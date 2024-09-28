#!/bin/bash
uwsgi --http :9009 --wsgi-file src/msample/server.py --static-map /=srv/ --static-index index.html --workers 4