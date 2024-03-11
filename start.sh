pip install -r /var/www/html/requirements.txt
sh -c 'echo "" > $(docker inspect --format="{{.LogPath}}" parser_vin_dc_gibdd)'
uvicorn server:app --host 0.0.0.0 --port 5000 --workers 15
tail -f /dev/null