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


def get_vins_add_query():
    query = f"""
                INSERT INTO 
                    dc_base.vins 
                VALUES ($1) 
                ON CONFLICT DO NOTHING
            """
    return query


def get_insert_query(force_rewrite):
    # query = f"""
    #             INSERT INTO
    #                 dcs
    #             VALUES (
    #                 $1,
    #                 $2,
    #                 $3::date,
    #                 $4::date,
    #                 $5::timestamp,
    #                 $6::timestamp,
    #                 $7::int4,
    #                 $8,
    #                 $9,
    #                 $10,
    #                 $11
    #             ) ON CONFLICT (dc_number) DO
    #             UPDATE SET
    #                 vin=$2,
    #                 issue_date=$3::date,
    #                 expiry_date=$4::date,
    #                 touched_at=$5::timestamp,
    #                 odometer_value=$7::int4,
    #                 model=$8,
    #                 brand=$9,
    #                 operator_name=$10,
    #                 operator_address=$11
    #         """
    query = f"""
                    INSERT INTO 
                        dc_base.diagnostic_cards 
                    VALUES (
                        $1,
                        $2,
                        $3::date,
                        $4::date,
                        $5::int4,
                        $6::int4,
                        $7::timestamp,
                        $8::timestamp
                    ) ON CONFLICT (card_number) DO 
                    UPDATE SET 
                        vin=$2, 
                        issue_date=$3::date, 
                        expiry_date=$4::date, 
                        odometer_value=$5::int4,
                        operator_number=$6::int4,
                        updated_at=$7::timestamp
                """
    if force_rewrite:
        query += ",created_at=$8::timestamp"
    return query


def get_update_vin_record_query():
    query = """
                UPDATE dc_base.vins
                SET model=$2, brand=$3
                WHERE vin=$1;
      
    """
    return query


# def get_insert_dk_prev_query():
#     query = f"""
#                 INSERT INTO
#                     dk_previous
#                 VALUES (
#                     $1,
#                     $2,
#                     $3::date,
#                     $4::date,
#                     $5::int4
#                 ) ON CONFLICT (dc_number) DO
#                 UPDATE SET
#                     odometer_value=$5::int4
#             """
#     return query


def get_insert_proxy_query():
    query = f'''
                INSERT INTO 
                    dc_base.proxies 
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


def set_items_tuple_create_vin_record(vins):
    items = []
    for vin in vins:
        items_tuple = (vin,)
        items.append(items_tuple)
    return items


def set_items_tuple_create_dc_record(dict_of_vin, execute_many_flag=False):
    dt_now_timestamp = del_tz(datetime.datetime.now())
    if execute_many_flag is True:
        items_tuple = (
            dict_of_vin['dcNumber'],
            dict_of_vin['vin'],
            convert_to_ts(dict_of_vin["dcDate"]),
            convert_to_ts(dict_of_vin["dcExpirationDate"]),
            int(dict_of_vin['odometerValue']),
            int(dict_of_vin['operatorName']),
            dt_now_timestamp,
            dt_now_timestamp
        )
    else:
        items_tuple = [
            dict_of_vin['dcNumber'],
            dict_of_vin['vin'],
            convert_to_ts(dict_of_vin["dcDate"]),
            convert_to_ts(dict_of_vin["dcExpirationDate"]),
            int(dict_of_vin['odometerValue']),
            int(dict_of_vin['operatorName']),
            dt_now_timestamp,
            dt_now_timestamp
        ]
    return items_tuple


def set_items_arr_for_prev_dks(dict_of_vin):
    items = []
    dt_now_timestamp = del_tz(datetime.datetime.now())
    for dc in dict_of_vin["previousDcs"]:
        if len(dc["dcNumber"]) == 15:
            op_num = int(dc["dcNumber"][:5])
        else:
            op_num = 0
        item_tuple = (
            dc["dcNumber"],
            dict_of_vin["vin"],
            convert_to_ts(dc["dcDate"]),
            convert_to_ts(dc["dcExpirationDate"]),
            int(dc['odometerValue']),
            op_num,
            dt_now_timestamp,
            dt_now_timestamp
        )
        items.append(item_tuple)
    return items


def camel_to_underscore(name):
    return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)


def underscore_to_camel(name):
    return under_pat.sub(lambda x: x.group(1).upper(), name)


conf = config.DATABASE


def list_detector(input_data):
    new_data = {}
    if isinstance(input_data, list):
        try:
            data = [dict(record) for record in input_data][0]
        except:
            data = {}
    else:
        data = dict(input_data)
    for key, value in data.items():
        new_data[underscore_to_camel(key)] = data.get(key)
    return new_data


def list_detector_to_list(input_data):
    if isinstance(input_data, list):
        new_data = []
        # data = [dict(record) for record in input_data]
        for record in input_data:
            new_d = {}
            record = dict(record)
            for key, value in record.items():
                new_d[underscore_to_camel(key)] = record.get(key)
            new_data.append(new_d)
    else:
        new_data = {}
        data = dict(input_data)
        for key, value in data.items():
            new_data[underscore_to_camel(key)] = data.get(key)
    return new_data


async def get_setting(setting_name: str):
    query = f"SELECT value FROM dc_base.settings WHERE setting_name = '{setting_name}'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return {}

    data = list_detector(data)

    return data[setting_name]


async def get_active_proxies(proxy_type: str):
    if proxy_type == "HTTPS":
        view_name = 'dc_base.https_active_proxies'
    elif proxy_type == 'SOCKS5':
        view_name = 'dc_base.socks_active_proxies'
    else:
        view_name = 'dc_base.active_proxies'

    query = f"SELECT * FROM {view_name}"
    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return []

    data = list_detector_to_list(data)

    return data


async def find_vin_actual_dc(vin):
    query = f"SELECT * FROM dc_base.dcs_actual WHERE vin = '{vin}'"
    # query = f"SELECT * FROM dcs WHERE vin = '{vin}'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return []

    data = list_detector(data)

    return data


async def find_vin_canceled_dk(vin):
    query = f"SELECT * FROM dc_base.dcs_canceled WHERE vin = '{vin}'"
    # query = f"SELECT * FROM dcs WHERE vin = '{vin}'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return []

    data = list_detector(data)

    return data


async def find_vin_ended_dcs(vin):
    query = f"SELECT * FROM dc_base.dcs_ended WHERE vin = '{vin}'"
    # query = f"SELECT * FROM dcs WHERE vin = '{vin}'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)

    if data is None:
        return []

    data = list_detector(data)

    return data


async def get_vins_to_update():
    # touched_at = config.touched_at
    query = "SELECT * FROM dc_base.vins_to_update"
    # query = f"select vin, created_at from dcs
    # where dc_number is null or expiry_date < now() or created_at is null or (now()-touched_at) >= '{touched_at} days'"

    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(query)
        # config.logger.info(data)
        if data is None:
            return []
        # config.logger.info(data)
        data = [{'vin': item['vin'], 'createdAt': item['createdAt']} for item in list_detector_to_list(data)]
        # config.logger.info(data)
        return data


async def update_vin(dict_of_vin):
    items_tuple = (
        dict_of_vin["vin"],
        dict_of_vin.get("model", ''),
        dict_of_vin.get("brand", '')
    )
    query = get_update_vin_record_query()
    async with AsyncDatabase(**conf) as db:
        data = await db.execute(query, items_tuple)
        if data is not None:
            return True
        else:
            return False


async def create_dc_for_vin(dict_of_vin, force_rewrite=False):
    # config.logger.info(f'{dict_of_vin["vin"]} SQL Insert...')
    await update_vin(dict_of_vin)
    items_tuple = set_items_tuple_create_dc_record(dict_of_vin, execute_many_flag=False)
    query = get_insert_query(force_rewrite)
    # await touch_vin_at(dict_of_vin["vin"])
    async with AsyncDatabase(**conf) as db:
        data = await db.execute(query, items_tuple)
        # if data is not None:
        previous_dc_list = set_items_arr_for_prev_dks(dict_of_vin)
        query = get_insert_query(False)
        await db.executemany(query, previous_dc_list)
    await update_vin_at(dict_of_vin["vin"])
    return True
    # else:
    #     return False


async def create_dc_for_vin_bulk(list_of_vins):
    items = []
    previous_dc_list = []
    for dict_of_vin in list_of_vins:
        items_tuple = set_items_tuple_create_dc_record(dict_of_vin, execute_many_flag=True)
        items.append(items_tuple)
        previous_dc_list.extend(set_items_arr_for_prev_dks(dict_of_vin))
    query = get_insert_query(False)
    async with AsyncDatabase(**conf) as db:
        data = await db.executemany(query, items)
        query = get_insert_query(False)
        await db.executemany(query, previous_dc_list)
        if data is not None:
            return True
        else:
            return False


async def create_vins(vins):
    async with AsyncDatabase(**conf) as db:
        query = get_vins_add_query()
        data = await db.executemany(
            query,
            set_items_tuple_create_vin_record(vins)
        )
        if data is not None:
            return True
        else:
            return False


async def touch_vin_at(vin_number: str):
    async with AsyncDatabase(**conf) as db:
        query = f"""
        UPDATE dc_base.vins
        SET touched_at=CURRENT_TIMESTAMP
        WHERE vin='{vin_number}';
        """
        data = await db.fetch(
            query
        )
        if data is not None:
            # config.logger.info(f'{vin_number} touch updated')
            return True
        else:
            #config.logger.error(f'{vin_number} touch NOT updated')
            return False


async def update_vin_at(vin_number: str):
    async with AsyncDatabase(**conf) as db:
        query = f"""
        UPDATE dc_base.vins
        SET updated_at=CURRENT_TIMESTAMP
        WHERE vin=$1;
        """
        data = await db.execute(
            query,
            (vin_number,)
        )
        if data is not None:
            config.logger.debug(f'{vin_number} UPD updated')
            return True
        else:
            config.logger.error(f'{vin_number} UPD NOT updated')
            return False


async def load_vins(filename: Path):
    with open(filename, "r") as f:
        vins = f.read().split('\n')
    items_arr = []
    for vin in vins:
        vin = vin.strip()
        if vin != '':
            items_tuple = (vin,)
            items_arr.append(items_tuple)
    query = f"""
        INSERT INTO 
            dc_base.vins(vin) 
        VALUES (
            $1
        ) ON CONFLICT (vin) DO NOTHING
    """
    async with AsyncDatabase(**conf) as db:
        data = await db.executemany(query, items_arr)
        if data is not None:
            return True
        else:
            return False


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


async def check_bg_tasks():
    q = f"""select * from dc_base.bg_tasks where done is false"""
    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(q)

    if data is None:
        return []

    data = list_detector_to_list(data)

    return data


async def add_bg_task():
    q = f"""insert into dc_base.bg_tasks (done) VALUES (false) returning *"""
    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(q)

    if data is None:
        return []

    data = list_detector_to_list(data)

    return data[0]


async def done_bg_task(id):
    q = f"""update dc_base.bg_tasks SET done=true where id = {id} returning *"""
    async with AsyncDatabase(**conf) as db:
        data = await db.fetch(q)

    if data is None:
        return []

    data = list_detector_to_list(data)

    return data[0]
