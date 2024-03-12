pip install -r /var/www/html/requirements.txt > /dev/null 2>&1
rm $(docker inspect --format="{{.LogPath}}" parser_vin_dc_gibdd)
chmod +x ./run_workers.sh
./run_workers.sh &
uvicorn server:app --host 0.0.0.0 --port 5000 --workers 15
tail -f /dev/null