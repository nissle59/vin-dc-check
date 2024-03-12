import asyncio
import random
import threading
from pathlib import Path

import config
import parser
import sql_adapter


async def multithreaded_find_dcs(use_proxy=True):
    vins = await sql_adapter.get_vins_to_update()
    parser.mulithreaded_processor(vins)


async def queue_dc(vin_code):
    await update_proxies()
    find_dc(vin_code)


def q_dc(vin_code):
    asyncio.run(update_proxies())
    find_dc(vin_code)


async def queue_dc_all():
    # await update_proxies()
    vins = await sql_adapter.get_vins_to_update()
    jobs = []
    for vin in vins:
        jobs.append(config.queue.enqueue(queue_dc, vin))
    return jobs


def find_dc(vin_code):
    config.logger.info(f'Started parsing of [{vin_code}]')
    t1 = threading.Thread(target=parser.process_thread, args=([vin_code],), daemon=True)
    t1.start()
    t1.join()


async def dc(vin_code):
    return await sql_adapter.find_vin_actual_dc(vin_code)


async def dcs_ended(vin_code):
    return await sql_adapter.find_vin_ended_dcs(vin_code)


async def update_proxies():
    #proxies = parser.get_proxies_from_url()
    config.proxies = [{'http': f'http://{proxy["username"]}:{proxy["password"]}@{proxy["ip"]}:{proxy["port"]}',
                       'https': f'http://{proxy["username"]}:{proxy["password"]}@{proxy["ip"]}:{str(proxy["port"])}'}
                      for proxy in
                      await sql_adapter.get_active_proxies('HTTPS')]
    for i in range(random.randint(0, len(config.proxies))):
        next(config.r_proxies)
    return config.proxies
    #return await sql_adapter.update_proxies(proxies)


async def update_vins():
    vins = parser.get_vins_from_url()
    return await sql_adapter.create_vins(vins)


async def load_vins():
    fname = Path("VIN.txt")
    return await sql_adapter.load_vins(fname)


async def scan_vins():
    vins = await sql_adapter.get_vins_to_update()
    return vins
