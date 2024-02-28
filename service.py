from itertools import cycle
from pathlib import Path

import config
import parser
import sql_adapter


async def multithreaded_find_dcs(use_proxy=True):
    vins = await sql_adapter.get_vins_to_update()
    config.logger.info(vins)
    # v = parser.VinDcCheck()
    # v.multithreading_get_vins(vins, use_proxy)
    parser.mulithreaded_processor(vins)
    # print(v.results)
    # result = None
    # if v.results:
    #     if len(v.results) > 0:
    #         result = await sql_adapter.create_dc_for_vin_bulk(v.results)
    #
    # return result



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
                config.logger.info(f'Trying proxy {prx["http"]}')
                vin = v.get_vin_code(vin_code, prx)
                break
            except StopIteration:
                config.r_proxies = cycle(config.proxies)
                prx = next(config.r_proxies)
            except Exception as e:
                config.logger.info(e)
                prx = next(config.r_proxies)

    result = []
    if vin:
        if len(vin) == 1:
            vin = vin[0]
            resp = await sql_adapter.create_dc_for_vin(vin)
            result.append(await sql_adapter.find_vin_actual_dc(vin_code))
            return result[0]
        elif len(vin) > 1:
            for item in vin:
                resp = await sql_adapter.create_dc_for_vin(item)
                if resp:
                    result.append(await sql_adapter.find_vin_actual_dc(vin_code))
            return result
        else:
            return None
    else:
        config.logger.info(f'Cant parse vin_code {vin_code}')
        return None


async def dc(vin_code):
    return await sql_adapter.find_vin_actual_dc(vin_code)


async def dcs_ended(vin_code):
    return await sql_adapter.find_vin_ended_dcs(vin_code)


async def update_proxies():
    proxies = parser.get_proxies_from_url()
    config.proxies = [{'http': f'http://{proxy["username"]}:{proxy["password"]}@{proxy["ip"]}:{proxy["port"]}',
                       'https': f'http://{proxy["username"]}:{proxy["password"]}@{proxy["ip"]}:{str(proxy["port"])}'}
                      for proxy in
                      await sql_adapter.get_active_proxies('HTTPS')]
    return await sql_adapter.update_proxies(proxies)


async def update_vins():
    vins = parser.get_vins_from_url()
    return await sql_adapter.create_vins(vins)


async def load_vins():
    fname = Path("VIN.txt")
    return await sql_adapter.load_vins(fname)


async def scan_vins():
    vins = await sql_adapter.get_vins_to_update()
    return vins
