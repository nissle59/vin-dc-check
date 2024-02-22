import logging

import sys
from itertools import cycle

DATABASE = {
    'host': 'db.local',
    'port': 5432,
    'user': 'postgres',
    'pswd': 'psqlpass',
    'database': 'vindcgibdd'
}

tries = 5
proxies = []
r_proxies = cycle(proxies)
threads = 20
touched_at = 7

logging.basicConfig(level=logging.INFO)

handler = logging.FileHandler('app.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
s_handler = logging.StreamHandler(sys.stdout)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(s_handler)
logger.setLevel(logging.INFO)
logger.propagate = False
