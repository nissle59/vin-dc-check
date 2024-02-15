from itertools import cycle

import config
import parser
import sql_adapter


async def find_dc(vin_code, noproxy):
    v = parser.VinDcCheck()
    c = 0
    vin = None
    if noproxy:
        vin = v.get_vin_code(vin_code)
    else:
        while c <= config.tries:
            try:
                prx = next(config.r_proxies)
                vin = v.get_vin_code(vin_code, prx)
                break
            except StopIteration:
                config.r_proxies = cycle(config.proxies)
                prx = next(config.r_proxies)
            except Exception as e:
                print(e)
                prx = next(config.r_proxies)

    result = []
    if vin:
        if len(vin) == 1:
            vin = vin[0]
            resp = await sql_adapter.create_vin_act_dk(vin)
            result.append(await sql_adapter.find_vin_act_dk(vin_code))
            return result[0]
        elif len(vin) > 1:
            for item in vin:
                resp = await sql_adapter.create_vin_act_dk(item)
                if resp:
                    result.append(await sql_adapter.find_vin_act_dk(vin_code))
            return result
        else:
            return None
    else:
        print(f'Cant parse vin_code {vin_code}')
        return None


async def dc(vin_code):
    return await sql_adapter.find_vin_act_dk(vin_code)


async def dk_previous(vin_code):
    return await sql_adapter.find_vin_prev_dk(vin_code)


async def update_proxies():
    proxies = parser.get_proxies_from_url()
    config.proxies = [{'http': f'http://{proxy["username"]}:{proxy["password"]}@{proxy["ip"]}:{proxy["port"]}',
                       'https': f'http://{proxy["username"]}:{proxy["password"]}@{proxy["ip"]}:{str(proxy["port"])}'}
                      for proxy in
                      await sql_adapter.get_active_proxies('HTTPS')]
    return await sql_adapter.update_proxies(proxies)