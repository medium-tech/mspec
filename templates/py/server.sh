#!/bin/bash

# env vars from .env
export $(grep -v '^#' .env | xargs)

uwsgi --yaml ./dev.yaml