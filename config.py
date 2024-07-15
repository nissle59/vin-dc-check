import json
import logging.config
from itertools import cycle

name = "VIN DC Parser"

logging.config.dictConfig(json.load(open('logging.json', 'r')))
LOGGER = logging.getLogger(__name__)

# from redis import Redis
# from rq import Queue, Worker

DATABASE = {
    'host': 'pg.db.services.local',
    'port': 5432,
    'user': 'postgres',
    'pswd': 'psqlpass',
    'database': 'vindcgibdd'
}

tries = 5
proxies = []
r_proxies = cycle(proxies)
threads = 40
touched_at = 7

# rc = Redis(host='redis.local', username='default', password='redispwd')
# queue = Queue(connection=rc, name='vin-queue')

# workers = Worker.all(queue=queue)


# logging.basicConfig(level=logging.INFO)
#
# handler = logging.FileHandler('app.log')
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# s_handler = logging.StreamHandler(sys.stdout)
# logger = logging.getLogger(__name__)
# logger.addHandler(handler)
# logger.addHandler(s_handler)
# logger.setLevel(logging.INFO)
# logger.propagate = False

# logger.info(f'RQ({queue.get_redis_server_version()}) Workers:')
# for w in workers:
#     logger.info(f'\t{w.name} - {w.get_state()} - S {w.successful_job_count} - F {w.failed_job_count}')
# logger.info(f'Total workers: {len(workers)}')
# bot_token = '7194357846:AAGfBntMhRcfEpoHPJ0JiVMdXN12FYQUQ4g'
# chat_id = '288772431'
# tg_sendmessage_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
#
#
# def error(message):
#     logger.error(message)
#     requests.post(tg_sendmessage_url, data={'chat_id': chat_id, 'text': f'VIN-DC: {message}'})
