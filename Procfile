web: cd Frontend && PORT=${PORT:-3000} npm start
api: gunicorn --bind 0.0.0.0:${BACKEND_PORT:-5000} src.api:app
