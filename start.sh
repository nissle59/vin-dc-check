pip install -r /var/www/html/requirements.txt
uvicorn server:app --host 0.0.0.0 --port 5000
tail -f /dev/null