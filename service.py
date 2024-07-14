import asyncio
import logging
import random
import threading
from itertools import cycle
from pathlib import Path

import config
import parser
import sql_adapter

LOGGER = logging.getLogger(__name__)

async def multithreaded_find_dcs(use_proxy=True, task=None):
    LOGGER = logging.getLogger(__name__ + ".multithreaded_find_dcs")
    vins = await sql_adapter.get_vins_to_update()
    # print(vins)
    parser.mulithreaded_processor(vins)
    await sql_adapter.done_bg_task(task['id'])


async def queue_dc(vin_code):
    LOGGER = logging.getLogger(__name__ + ".queue_dc")
    await update_proxies()
    find_dc(vin_code)


def q_dc(vin_code):
    LOGGER = logging.getLogger(__name__ + ".q_dc")
    asyncio.run(update_proxies())
    find_dc(vin_code)


# async def queue_dc_all():
#     # await update_proxies()
#     vins = await sql_adapter.get_vins_to_update()
#     jobs = []
#     for vin in vins:
#         jobs.append(config.queue.enqueue(multi_dc, vin, timeout=3600))
#     return jobs


# def multi_dc(vins):
#     asyncio.run(update_proxies())
#     parser.mulithreaded_processor(vins)


def find_dc(vin_code):
    LOGGER = logging.getLogger(__name__ + ".find_dc")
    LOGGER.info(f'Started parsing of [{vin_code}]')
    t1 = threading.Thread(target=parser.process_thread, args=([vin_code],), daemon=True)
    t1.start()
    t1.join()


async def dc(vin_code):
    LOGGER = logging.getLogger(__name__ + ".dc")
    return await sql_adapter.find_vin_actual_dc(vin_code)


async def dcs_ended(vin_code):
    LOGGER = logging.getLogger(__name__ + ".dcs_ended")
    return await sql_adapter.find_vin_ended_dcs(vin_code)


async def update_proxies():
    LOGGER = logging.getLogger(__name__ + ".update_proxies")
    #proxies = parser.get_proxies_from_url()
    config.proxies = [{'http': f'http://{proxy["username"]}:{proxy["password"]}@{proxy["ip"]}:{proxy["port"]}',
                       'https': f'http://{proxy["username"]}:{proxy["password"]}@{proxy["ip"]}:{str(proxy["port"])}'}
                      for proxy in
                      await sql_adapter.get_active_proxies('HTTPS')]
    LOGGER.info(len(config.proxies))
    config.r_proxies = cycle(config.proxies)
    for i in range(random.randint(0, len(config.proxies))):
        next(config.r_proxies)
    return config.proxies
    #return await sql_adapter.update_proxies(proxies)


async def update_vins():
    LOGGER = logging.getLogger(__name__ + ".update_vins")
    vins = parser.get_vins_from_url()
    return await sql_adapter.create_vins(vins)


async def load_vins():
    LOGGER = logging.getLogger(__name__ + ".load_vins")
    fname = Path("VIN.txt")
    return await sql_adapter.load_vins(fname)


async def scan_vins():
    LOGGER = logging.getLogger(__name__ + ".scan_vins")
    vins = await sql_adapter.get_vins_to_update()
    return vins
