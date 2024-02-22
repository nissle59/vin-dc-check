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
    dt = datetime.datetime.strptime(s, '%Y-%m-%d')
    dt = del_tz(dt)
    # dt = s
    return dt


camel_pat = re.compile(r'([A-Z])')
under_pat = re.compile(r'_([a-z])')


def get_insert_query(force_rewrite):
    query = f"""
                INSERT INTO 
                    dcs 
                VALUES (
                    $1,
                    $2,
                    $3::date,
                    $4::date,
                    $5::timestamp,
                    $6::timestamp,
                    $7::int4,
                    $8,
                    $9,
                    $10,
                    $11
                ) ON CONFLICT (vin) DO 
                UPDATE SET 
                    dc_number=$1, 
                    issue_date=$3::date, 
                    expiry_date=$4::date, 
                    touched_at=$5::timestamp,
                    odometer_value=$7::int4,
                    model=$8,
                    brand=$9,
                    operator_name=$10,
                    operator_address=$11
            """
    if force_rewrite == True:
        query += ",created_at=$6::timestamp"
    return query


def get_insert_dk_prev_query():
    query = f"""
                INSERT INTO 
                    dk_previous 
                VALUES (
                    $1, 
                    $2, 
                    $3::date, 
                    $4::date,
                    $5::int4
                ) ON CONFLICT (dc_number) DO 
                UPDATE SET 
                    odometer_value=$5::int4
            """
    return query


def get_insert_proxy_query():
    query = f'''
                INSERT INTO 
                    proxies 
                VALUES (
                    $1, 
                    $2, 
                    $3, 
                    $4, 
                    $5, 
                    $6, 
                    $7
                ) ON CONFLICT (proxy_id) DO 
                UPDATE SET 
                    ip=$2, 
                    username=$3, 
                    "password"=$4, 
                    "type"=$5, 
                    enabled=$6, 
                    port=$7
            '''
    return query


def set_items_tuple_create_vin_record(vin_d, multi=False):
    nowdt = del_tz(datetime.datetime.now())
    if multi is True:
        items_tuple = (
            vin_d['dcNumber'],
            vin_d['vin'],
            convert_to_ts(vin_d["dcDate"]),
            convert_to_ts(vin_d["dcExpirationDate"]),
            nowdt,
            nowdt,
            int(vin_d['odometerValue']),
            vin_d['model'],
            vin_d['brand'],
            vin_d['operatorName'],
            vin_d['pointAddress']
        )
    else:
        items_tuple = [
            vin_d['dcNumber'],
            vin_d['vin'],
            convert_to_ts(vin_d["dcDate"]),
            convert_to_ts(vin_d["dcExpirationDate"]),
            nowdt,
            nowdt,
            int(vin_d['odometerValue']),
            vin_d['model'],
            vin_d['brand'],
            vin_d['operatorName'],
            vin_d['pointAddress']
        ]
    return items_tuple


def set_items_arr_for_prev_dks(vin_d):
    prev_arr = []
    for prev_dk in vin_d["previousDcs"]:
        prev_tuple = (
            prev_dk["dcNumber"],
            vin_d["vin"],
            convert_to_ts(prev_dk["dcDate"]),
            convert_to_ts(prev_dk["dcExpirationDate"]),
            int(prev_dk['odometerValue'])
        )
        prev_arr.append(prev_tuple)
    return prev_arr


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
    touched_at = config.touched_at
    query = f"select vin, created_at from dcs where dc_number is null or expiry_date < now() or created_at is null or (now()-touched_at) >= '{touched_at} days'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return []
    # config.logger.info(data)
    data = [{'vin': item['vin'], 'createdAt': item['createdAt']} for item in list_detector_to_list(data)]
    config.logger.info(data)
    return data


async def find_vin_prev_dk(vin):
    query = f"SELECT * FROM dk_previous WHERE vin = '{vin}'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return {}

    data = list_detector_to_list(data)

    return data


async def create_vin_act_dk(vin_d, force_rewrite=False):
    config.logger.debug(f'{vin_d["vin"]} SQL Insert...')
    items_tuple = set_items_tuple_create_vin_record(vin_d, multi=False)
    query = get_insert_query(force_rewrite)
    async with AsyncDatabase(**conf) as db:
        data = await db.execute(query, items_tuple)
        if data is not None:
            prev_arr = set_items_arr_for_prev_dks(vin_d)
            query = get_insert_dk_prev_query()
            prev_data = await db.executemany(query, prev_arr)
            return True
        else:
            return None


async def create_vins_act_dk(vins_l):
    items_arr = []
    prev_arr = []
    for vin_d in vins_l:
        items_tuple = set_items_tuple_create_vin_record(vin_d, multi=True)
        items_arr.append(items_tuple)
        prev_arr.extend(set_items_arr_for_prev_dks(vin_d))
    query = get_insert_query(False)
    async with AsyncDatabase(**conf) as db:
        data = await db.executemany(query, items_arr)
        query = get_insert_dk_prev_query()
        prev_data = await db.executemany(query, prev_arr)
        if data is not None:
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
    query = f"""
        INSERT INTO 
            dcs(vin) 
        VALUES (
            $1
        ) ON CONFLICT (vin) DO NOTHING
    """
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
        items_tuple = (
            proxy_id,
            ip,
            username,
            password,
            pr_type,
            enabled,
            port
        )
        values.append(items_tuple)
        count += 1
    async with AsyncDatabase(**conf) as db:
        query = get_insert_proxy_query()
        data = await db.executemany(query, values)
    config.r_proxies = cycle(config.proxies)
    return {
        "count": count,
        "result": data
    }
