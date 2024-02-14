import datetime
from database import AsyncDatabase
import config
import re


def del_tz(dt: datetime.datetime):
    dt = dt.replace(tzinfo=None)
    return dt

def convert_to_ts(s:str):
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
    if isinstance(input, list):
        data = [dict(record) for record in input][0]
    else:
        data = dict(input)
    for key, value in data.items():
        data[underscore_to_camel(key)] = data.pop(key)
    return data


async def get_setting(setting_name:str):
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


async def create_vin_act_dk(vin_d):
    nowdt = del_tz(datetime.datetime.now())
    items_tuple = (vin_d["dcNumber"],vin_d["body"],convert_to_ts(vin_d["dcDate"]),convert_to_ts(vin_d["dcExpirationDate"]),'now()','now()')
    query = f"INSERT INTO dcs VALUES {items_tuple} ON CONFLICT DO NOTHING"
    async with AsyncDatabase(**conf) as db:
        data = await db.execute(query)
        if data is not None:
            return await find_vin_act_dk(vin_d["body"])
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