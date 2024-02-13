import psycopg2
import datetime

DATABASE = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'psqlpass',
    'database': 'vindcgibdd'
}

def connect_to_db():
    conn = psycopg2.connect(
        user=DATABASE['user'],
        password=DATABASE['password'],
        host=DATABASE['host'],
        port=DATABASE['port'],
        database=DATABASE['database']
    )
    return conn


def find_vin(vin: str):
    conn = connect_to_db()
    cursor = conn.cursor()
    q = "SELECT * FROM vin_cache WHERE vin = %s"
    item_tuple = (vin,)
    cursor.execute(q, item_tuple)
    res = cursor.fetchall()
    if len(res) > 0:
        conn.close()
        return res[0]
    else:
        conn.close()
        return None


def check_vin(vin: str):
    v = find_vin(vin)
    if v:
        dc = find_dc(v['actual_dc'])
        if dc['dc_expiration'] > datetime.datetime.timestamp(datetime.datetime.now()):
            result = {
                'source': 'cache',
                'vin': v['vin'],
                'actual_dc': dc['dc_number'],
                'dc_date': dc['dc_date'],
                'dc_expiration': dc['dc_expiration'],
                'dc_history': v['dc_history']
            }
            return result
        else:
            return None
    else:
        return None



def update_vin(vin: dict):
    conn = connect_to_db()
    cursor = conn.cursor()
    q = "UPDATE vin_cache SET actual_dc = %s, dc_history = %s WHERE vin = %s"
    item_tuple = (vin['dcNumber'],[dc['dcNumber'] for dc in vin['previousDcs']],vin['body'])
    cursor.execute(q, item_tuple)
    conn.commit()
    conn.close()


def insert_dc(dc: dict):
    conn = connect_to_db()
    _insert_dc_no_commit(conn, dc)
    conn.commit()
    conn.close()


def insert_dcs(dcs: list):
    conn = connect_to_db()
    for dc in dcs:
        _insert_dc_no_commit(conn, dc)
    conn.commit()
    conn.close()


def _insert_dc_no_commit(conn, dc: dict):
    cursor = conn.cursor()
    q = "INSERT INTO dcs (dc_number, odo_value, dc_date, dc_expiration) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING"
    dc['dcDate'] = datetime.datetime.timestamp(datetime.datetime.strptime( dc['dcDate'],'%Y-%m-%d'))
    dc['dcExpirationDate'] = datetime.datetime.timestamp(datetime.datetime.strptime(dc['dcExpirationDate'], '%Y-%m-%d'))
    item_tuple = (dc['dcNumber'], dc['odometerValue'], dc['dcDate'], dc['dcExpirationDate'])
    cursor.execute(q, item_tuple)


def find_dc(dcNumber: str):
    conn = connect_to_db()
    cursor = conn.cursor()
    q = "SELECT * FROM dcs WHERE dc_number = %s"
    item_tuple = (dcNumber,)
    cursor.execute(q, item_tuple)
    res = cursor.fetchall()
    if len(res) > 0:
        conn.close()
        return res[0]
    else:
        conn.close()
        return None


def insert_vin(vin: dict):
    print(vin['body'])
    fv = find_vin(vin['body'])
    if fv:
        ad = find_dc(fv['actual_dc'])
        if ad:
            if ad['dcExpirationDate'] > datetime.datetime.timestamp(datetime.datetime.now()):
                result = {
                    'source':'cache',
                    'vin':fv['vin'],
                    'actual_dc':ad['dc_number'],
                    'dc_date':ad['dc_date'],
                    'dc_expiration':ad['dc_expiration'],
                    'dc_history':fv['dc_history']
                }
                return result
            else:
                dcs = vin['previousDcs']
                dc_act = {
                    "odometerValue": vin.get('odometerValue',''),
                    "dcExpirationDate": vin['dcExpirationDate'],
                    "dcNumber": vin.get('dcNumber',''),
                    "dcDate": vin['dcDate']
                }
                insert_dcs(dcs)
                insert_dc(dc_act)
                update_vin(vin)
                result = {
                    'source': 'api:new-dcs',
                    'vin': fv['vin'],
                    'actual_dc': vin['dcNumber'],
                    'dc_date': datetime.datetime.timestamp(datetime.datetime.strptime(vin['dcDate'], '%Y-%m-%d')),
                    'dc_expiration': datetime.datetime.timestamp(datetime.datetime.strptime(vin['dcExpirationDate'], '%Y-%m-%d')),
                    'dc_history': [dc['dcNumber'] for dc in vin['previousDcs']]
                }
                return result
    else:
        dcs = vin['previousDcs']
        dc_act = {
            "odometerValue": vin.get('odometerValue', ''),
            "dcExpirationDate": vin['dcExpirationDate'],
            "dcNumber": vin.get('dcNumber', ''),
            "dcDate": vin['dcDate']
        }
        insert_dcs(dcs)
        insert_dc(dc_act)

        conn = connect_to_db()
        cursor = conn.cursor()
        q = "INSERT INTO vin_cache (vin, actual_dc, dc_history) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING"
        dc_act['dcDate'] = datetime.datetime.timestamp(datetime.datetime.strptime(dc_act['dcDate'], '%Y-%m-%d'))
        dc_act['dcExpirationDate'] = datetime.datetime.timestamp(
            datetime.datetime.strptime(dc_act['dcExpirationDate'], '%Y-%m-%d'))
        item_tuple = (vin['body'], dc_act['dcNumber'],[dc['dcNumber'] for dc in vin['previousDcs']])
        cursor.execute(q, item_tuple)
        conn.commit()
        cursor.close()

        result = {
            'source': 'api:new-all',
            'vin': vin['body'],
            'actual_dc': vin['dcNumber'],
            'dc_date': datetime.datetime.timestamp(datetime.datetime.strptime(vin['dcDate'], '%Y-%m-%d')),
            'dc_expiration': datetime.datetime.timestamp(datetime.datetime.strptime(vin['dcExpirationDate'], '%Y-%m-%d')),
            'dc_history': [dc['dcNumber'] for dc in vin['previousDcs']]
        }

        return result


def insert_vins(vins: list):
    results = []
    for vin in vins:
        results.append(insert_vin(vin))
