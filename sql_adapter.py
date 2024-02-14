import datetime
import re

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


async def get_setting(setting_name: str):
    query = f"SELECT value FROM settings WHERE setting_name = '{setting_name}'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return {}

    data = list_detector(data)

    return data[setting_name]


async def find_vin_act_dk(vin):
    query = f"SELECT * FROM dcs WHERE vin = '{vin}'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return {}

    data = list_detector(data)

    return data


async def find_vin_prev_dk(vin):
    query = f"SELECT * FROM dk_previous WHERE vin = '{vin}'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return {}

    data = list_detector(data)

    return data


async def create_vin_act_dk(vin_d):
    nowdt = del_tz(datetime.datetime.now())
    dc_num = vin_d['dcNumber']
    vin_code = vin_d['body']
    issue_date = convert_to_ts(vin_d["dcDate"])
    expiry_date = convert_to_ts(vin_d["dcExpirationDate"])
    items_tuple = (
        dc_num, vin_code, issue_date, expiry_date, 'now()', 'now()')
    query = f"INSERT INTO dcs VALUES {items_tuple} ON CONFLICT (vin) DO UPDATE SET dc_number='{dc_num}', issue_date='{issue_date}', expiry_date='{expiry_date}', touched_at=now()"
    async with AsyncDatabase(**conf) as db:
        data = await db.execute(query)
        if data is not None:
            for prev_dk in vin_d["previousDcs"]:
                items_tuple = (prev_dk["dcNumber"], vin_d["body"], convert_to_ts(prev_dk["dcDate"]),
                               convert_to_ts(prev_dk["dcExpirationDate"]))
                query = f"INSERT INTO dk_previous VALUES {items_tuple} ON CONFLICT DO NOTHING"
                prev_data = await db.execute(query)
            return True
        else:
            return None

#    q = "SELECT * FROM vin_cache WHERE vin = %s"
#
#    q = "UPDATE vin_cache SET actual_dc = %s, dc_history = %s WHERE vin = %s"
#
#    q = "INSERT INTO dcs VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING"
#
#    q = "SELECT * FROM dcs WHERE dc_number = %s"
#
#    q = "INSERT INTO vin_cache (vin, actual_dc, dc_history) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING"
#
#    q = "SELECT value FROM settings WHERE setting_name = %s"
