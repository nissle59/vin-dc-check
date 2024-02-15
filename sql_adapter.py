import datetime
import re
from itertools import cycle
from pathlib import Path

import config
from database import AsyncDatabase


def del_tz(dt: datetime.datetime):
    dt = dt.replace(tzinfo=None)
    return dt


def convert_to_ts(s: str):
    # dt = datetime.datetime.strptime(s,'%Y-%m-%d')
    # dt = del_tz(dt)
    dt = s
    return dt


camel_pat = re.compile(r'([A-Z])')
under_pat = re.compile(r'_([a-z])')


def camel_to_underscore(name):
    return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)


def underscore_to_camel(name):
    return under_pat.sub(lambda x: x.group(1).upper(), name)


conf = config.DATABASE


def list_detector(input):
    new_data = {}
    if isinstance(input, list):
        data = [dict(record) for record in input][0]
    else:
        data = dict(input)
    for key, value in data.items():
        new_data[underscore_to_camel(key)] = data.get(key)
    return new_data


def list_detector_to_list(input):
    if isinstance(input, list):
        new_data = []
        # data = [dict(record) for record in input]
        for record in input:
            new_d = {}
            record = dict(record)
            for key, value in record.items():
                new_d[underscore_to_camel(key)] = record.get(key)
            new_data.append(new_d)
    else:
        new_data = {}
        data = dict(input)
        for key, value in data.items():
            new_data[underscore_to_camel(key)] = data.get(key)
    return new_data


async def get_setting(setting_name: str):
    query = f"SELECT value FROM settings WHERE setting_name = '{setting_name}'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return {}

    data = list_detector(data)

    return data[setting_name]


async def get_active_proxies(proxy_type: str):
    if proxy_type == "HTTPS":
        t_name = 'https_active_proxies'
    elif proxy_type == 'SOCKS5':
        t_name = 'socks_active_proxies'
    else:
        t_name = 'active_proxies'

    query = f"SELECT * FROM {t_name}"
    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return []

    data = list_detector_to_list(data)

    return data


async def find_vin_act_dk(vin):
    query = f"SELECT * FROM dcs WHERE vin = '{vin}'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return {}

    data = list_detector(data)

    return data


async def scan_vins_to_update():
    query = "select vin from dcs where dc_number is null or expiry_date < now() "

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return []

    data = [item['vin'] for item in list_detector_to_list(data)]

    return data


async def find_vin_prev_dk(vin):
    query = f"SELECT * FROM dk_previous WHERE vin = '{vin}'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return {}

    data = list_detector_to_list(data)

    return data


async def create_vin_act_dk(vin_d):
    nowdt = del_tz(datetime.datetime.now())
    dc_num = vin_d['dcNumber']
    vin_code = vin_d['body']
    issue_date = convert_to_ts(vin_d["dcDate"])
    expiry_date = convert_to_ts(vin_d["dcExpirationDate"])
    items_tuple = (dc_num, vin_code, issue_date, expiry_date, 'now()', 'now()')
    # query = f"INSERT INTO dcs VALUES {items_tuple} ON CONFLICT (vin) DO UPDATE SET dc_number='{dc_num}', issue_date='{issue_date}', expiry_date='{expiry_date}', touched_at=now()"
    query = f"INSERT INTO dcs VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (vin) DO UPDATE SET dc_number=$1, issue_date=$3, expiry_date=$4, touched_at=$5"
    async with AsyncDatabase(**conf) as db:
        data = await db.execute(query, dc_num, vin_code, issue_date, expiry_date, 'now()', 'now()')
        if data is not None:
            for prev_dk in vin_d["previousDcs"]:
                items_tuple = (prev_dk["dcNumber"], vin_d["body"], convert_to_ts(prev_dk["dcDate"]),
                               convert_to_ts(prev_dk["dcExpirationDate"]))
                query = f"INSERT INTO dk_previous VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING"
                prev_data = await db.execute(query, prev_dk["dcNumber"], vin_d["body"],
                                             convert_to_ts(prev_dk["dcDate"]),
                                             convert_to_ts(prev_dk["dcExpirationDate"]))
            return True
        else:
            return None


async def load_vins(fname: Path):
    with open(fname, "r") as f:
        vins = f.read().split('\n')
    items_arr = []
    for vin in vins:
        vin = vin.strip()
        if vin != '':
            items_tuple = (vin,)
            items_arr.append(items_tuple)
    query = f"INSERT INTO dcs(vin) VALUES ($1) ON CONFLICT (vin) DO NOTHING"
    async with AsyncDatabase(**conf) as db:
        data = await db.executemany(query, items_arr)
        if data is not None:
            return True
        else:
            return None


async def update_proxies(plist):
    count = 0
    values = []
    for item in plist:
        proxy_id = item['proxyId']
        ip = item['ip']
        username = item['username']
        password = item['password']
        pr_type = item['type']
        enabled = item['enabled']
        port = int(item["port"])
        items_tuple = (proxy_id, ip, username, password, pr_type, enabled, port)
        values.append(items_tuple)
        count += 1
    async with AsyncDatabase(**conf) as db:
        query = f'INSERT INTO proxies VALUES ($1, $2, $3, $4, $5, $6, $7) ON CONFLICT (proxy_id) DO UPDATE SET ip=$2, username=$3, "password"=$4, "type"=$5, enabled=$6, port=$7'
        data = await db.executemany(query, values)
    config.r_proxies = cycle(config.proxies)
    return {
        "count": count,
        "result": data
    }
