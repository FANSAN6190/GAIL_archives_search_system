#!/bin/bash
echo "running in production mode"
source .venv/bin/activate
python3 manage.py runserver 9000 &
ngrok http --domain=pleasantly-winning-bluebird.ngrok-free.app 9000