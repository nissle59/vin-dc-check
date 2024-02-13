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


def convert_to_ts(s:str):
    dt = datetime.datetime.strptime(s,'%Y-%m-%d')
    return psycopg2.Date(dt.year, dt.month, dt.day)
    #return datetime.datetime.timestamp(datetime.datetime.strptime(s,'%Y-%m-%d'))*1000

def find_vin(vin: str):
    conn = connect_to_db()
    cursor = conn.cursor()
    q = "SELECT * FROM vin_cache WHERE vin = %s"
    item_tuple = (vin,)
    cursor.execute(q, item_tuple)
    res = cursor.fetchall()
    cursor.close()
    if len(res) > 0:
        conn.close()
        return res[0]
    else:
        conn.close()
        return None


def check_vin(vin: str):
    v = find_vin(vin)
    if v:
        #print(v)
        dc = find_dc(v[1])
        if dc[3] > datetime.datetime.now():
            result = {
                'source': 'cache',
                'vin': v[0],
                'actual_dc': dc[0],
                'dc_date': dc[2],
                'dc_expiration': dc[3],
                'dc_history': v[2]
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
    cursor.close()
    conn.close()


def insert_dc(dc: dict):
    conn = connect_to_db()
    _insert_dc_no_commit(conn, dc)
    conn.commit()
    conn.close()


def insert_dcs(dcs: list):
    #print('Try to connect to DB')
    conn = connect_to_db()
    #print('Connected to DB')
    for dc in dcs:
        #print('Try to insert')
        _insert_dc_no_commit(conn, dc)
    #print('Commiting..')
    conn.commit()
    #print('Committed.. Close connection')
    conn.close()


def _insert_dc_no_commit(conn, dc: dict):
    print('Creating cursor')
    cursor = conn.cursor()
    q = "INSERT INTO dcs VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING"
    item_tuple = (dc['dcNumber'], dc['odometerValue'],convert_to_ts(dc['dcDate']),convert_to_ts(dc['dcExpirationDate']))
    print('Execute insertion')
    cursor.execute(q, item_tuple)
    cursor.close()


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
    #print(vin['body'])
    fv = find_vin(vin['body'])
    #print(fv)
    if fv:
        ad = find_dc(fv[1])
        print(ad)
        if ad:
            if ad[3] > datetime.datetime.now():
                result = {
                    'source':'cache',
                    'vin':fv[0],
                    'actual_dc':ad[0],
                    'dc_date':ad[2],
                    'dc_expiration':ad[3],
                    'dc_history':fv[2]
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
                    'vin': fv[0],
                    'actual_dc': vin['dcNumber'],
                    'dc_date': vin['dcDate'],
                    'dc_expiration': vin['dcExpirationDate'],
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
        #print('dc_act')
        #print(dc_act)
        insert_dcs(dcs)
        insert_dc(dc_act)

        #print('Try to connect to DB')
        conn = connect_to_db()
        #print('Connected to DB')
        cursor = conn.cursor()
        q = "INSERT INTO vin_cache (vin, actual_dc, dc_history) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING"
        # print('Converting dt...')
        # dc_act['dcDate'] = convert_to_ts(dc_act['dcDate'])
        # dc_act['dcExpirationDate'] = convert_to_ts(dc_act['dcExpirationDate'])
        item_tuple = (vin['body'], dc_act['dcNumber'],[dc['dcNumber'] for dc in vin['previousDcs']])
        #print('Execute vin_cache upd...')
        cursor.execute(q, item_tuple)
        #print('Commiting...')
        conn.commit()
        #print('Done')
        cursor.close()

        result = {
            'source': 'api:new-all',
            'vin': vin['body'],
            'actual_dc': vin['dcNumber'],
            'dc_date': vin['dcDate'],
            'dc_expiration': vin['dcExpirationDate'],
            'dc_history': [dc['dcNumber'] for dc in vin['previousDcs']]
        }
        print('Result done')
        return result


def insert_vins(vins: list):
    results = []
    for vin in vins:
        results.append(insert_vin(vin))
