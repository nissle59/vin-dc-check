from itertools import cycle

DATABASE = {
    'host': 'db.local',
    'port': 5432,
    'user': 'postgres',
    'pswd': 'psqlpass',
    'database': 'vindcgibdd'
}

proxies = []
r_proxies = cycle(proxies)
threads = 100
