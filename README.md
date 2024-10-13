# Mental health WebUI

## Requirements
1. Docker
2. Docker compose

## Running
1. Download the database at: https://github.com/JPEspinoza/mental-health/releases: `wget https://github.com/JPEspinoza/mental-health/releases/download/dataset-r3/db.sqlite3.xz src/db.sqlite3.xz`
2. `docker compose up`
3. Access site at `http://localhost:9000`

## Running locally
Don't want to run on docker for development?

`python3.13 -m venv venv`
`source venv/bin/activate.fish`
`pip install -r requirements.txt`
`gunicorn app:app --chdir src --bind localhost:9000 --log-level debug --reload`