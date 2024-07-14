import datetime
import json
import logging
import random

import requests
from fastapi import FastAPI, responses, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

import config
import service
import sql_adapter

LOGGER = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
async def startup():
    LOGGER = logging.getLogger(__name__ + ".startup")
    await service.update_proxies()
    for i in range(random.randint(0, len(config.proxies))):
        next(config.r_proxies)
    LOGGER.info('Updating started')
    # await mdc()


@app.get("/updateVins")
async def updateVins():
    LOGGER = logging.getLogger(__name__ + ".updateVins")
    res = json.dumps(
        await service.update_vins(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str
    )
    err = {"status": "error"}
    err = json.dumps(err, indent=4, sort_keys=True, default=str)

    if res:
        return responses.Response(
            content=res,
            status_code=200,
            media_type='application/json'
        )

    else:
        return responses.Response(
            content=err,
            status_code=500,
            media_type='application/json'
        )


@app.get("/bDc")
async def bdc(vin, background_tasks: BackgroundTasks):
    LOGGER = logging.getLogger(__name__ + ".bDc")
    background_tasks.add_task(service.find_dc, vin)

    res = json.dumps(
        {"status": "success"},
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str
    )
    err = {"status": "error"}
    err = json.dumps(err, indent=4, sort_keys=True, default=str)

    if res:
        return responses.Response(
            content=res,
            status_code=200,
            media_type='application/json'
        )

    else:
        return responses.Response(
            content=err,
            status_code=500,
            media_type='application/json'
        )

@app.get("/mFindDc")
async def mdc(background_tasks: BackgroundTasks, use_proxy=True):
    LOGGER = logging.getLogger(__name__ + ".mFindDc")
    # config.threads = threads
    bg_tasks = await sql_adapter.check_bg_tasks()
    if len(bg_tasks) > 0:
        res = {"status": "in process"}
        d = {'bg_tasks': []}
        for bg_task in bg_tasks:
            t_diff = (datetime.datetime.now() - bg_task['startAt']).total_seconds() - 10800
            print(f'Total bg_task t_diff seconds: {t_diff}')
            if t_diff > 28800:
                LOGGER.error('Парсер VIN обрабатывает задачу уже 8 часов!! Сброс задачи')
                await sql_adapter.done_bg_task(bg_task['id'])
                requests.post(
                    url="http://10.8.0.5:2375/v1.24/containers/parser_vin_dc_gibdd/restart"
                )
            d['bg_tasks'].append(
                {
                    'id': bg_task['id'],
                    'startAt': bg_task['startAt'].strftime('%Y-%m-%d %H:%M:%S')
                }
            )
        res.update(d)
    else:
        task = await sql_adapter.add_bg_task()
        background_tasks.add_task(
            service.multithreaded_find_dcs, use_proxy, task
        )
        res = {"status": "task started", 'task_id': task['id']}
    # background_tasks.add_task(
    #     service.multithreaded_find_dcs, use_proxy
    # )
    res = json.dumps(
        res,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str
    )
    err = {"status": "error"}
    err = json.dumps(err, indent=4, sort_keys=True, default=str)

    if res:
        return responses.Response(
            content=res,
            status_code=200,
            media_type='application/json'
        )

    else:
        return responses.Response(
            content=err,
            status_code=500,
            media_type='application/json'
        )


@app.get("/findDc")
async def getdc(vin, noproxy=False):
    LOGGER = logging.getLogger(__name__ + ".findDc")
    res = json.dumps(
        await service.find_dc(vin),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str
    )
    err = {"status": "error"}
    err = json.dumps(err, indent=4, sort_keys=True, default=str)

    if res:
        return responses.Response(
            content=res,
            status_code=200,
            media_type='application/json'
        )

    else:
        return responses.Response(
            content=err,
            status_code=500,
            media_type='application/json'
        )


@app.get("/dc")
async def dc(vin):
    LOGGER = logging.getLogger(__name__ + ".dc")
    res = json.dumps(
        await service.dc(vin),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str
    )
    err = {"status": "error"}
    err = json.dumps(err, indent=4, sort_keys=True, default=str)

    if res:
        return responses.Response(
            content=res,
            status_code=200,
            media_type='application/json'
        )

    else:
        return responses.Response(
            content=err,
            status_code=500,
            media_type='application/json'
        )


@app.get("/dk_previous")
async def dk_previous(vin):
    LOGGER = logging.getLogger(__name__ + ".dk_previous")
    res = json.dumps(
        await service.dcs_ended(vin),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str
    )
    err = {"status": "error"}
    err = json.dumps(err, indent=4, sort_keys=True, default=str)

    if res:
        return responses.Response(
            content=res,
            status_code=200,
            media_type='application/json'
        )

    else:
        return responses.Response(
            content=err,
            status_code=500,
            media_type='application/json'
        )


@app.get("/load_vins")
async def load_vins():
    LOGGER = logging.getLogger(__name__ + ".load_vins")
    res = json.dumps(
        await service.load_vins(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str
    )
    err = {"status": "error"}
    err = json.dumps(err, indent=4, sort_keys=True, default=str)

    if res:
        return responses.Response(
            content=res,
            status_code=200,
            media_type='application/json'
        )

    else:
        return responses.Response(
            content=err,
            status_code=500,
            media_type='application/json'
        )


@app.get('/scan_vins')
async def scan_vins(touched_at=7):
    LOGGER = logging.getLogger(__name__ + ".scan_vins")
    config.touched_at = touched_at
    res = json.dumps(
        await service.scan_vins(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str
    )
    err = {"status": "error"}
    err = json.dumps(err, indent=4, sort_keys=True, default=str)

    if res:
        return responses.Response(
            content=res,
            status_code=200,
            media_type='application/json'
        )

    else:
        return responses.Response(
            content=err,
            status_code=500,
            media_type='application/json'
        )


@app.get("/update_proxy_list")
async def upd_prx():
    LOGGER = logging.getLogger(__name__ + ".update_proxy_list")
    res = json.dumps(
        await service.update_proxies(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str
    )
    err = {"status": "error"}
    err = json.dumps(err, indent=4, sort_keys=True, default=str)

    if res:
        return responses.Response(
            content=res,
            status_code=200,
            media_type='application/json'
        )

    else:
        return responses.Response(
            content=err,
            status_code=500,
            media_type='application/json'
        )

# @app.get("/qDc")
# async def qdc(vin):
#     LOGGER = logging.getLogger(__name__ + ".qDc")
#     job = config.queue.enqueue(service.queue_dc, vin, timeout=3600)
#     # print(job.__dict__)
#
#     res = json.dumps(
#         {"status": "success", "job": job.id, "jobCreatedAt": job.created_at},
#         ensure_ascii=False,
#         indent=2,
#         sort_keys=True,
#         default=str
#     )
#     err = {"status": "error"}
#     err = json.dumps(err, indent=4, sort_keys=True, default=str)
#
#     if res:
#         return responses.Response(
#             content=res,
#             status_code=200,
#             media_type='application/json'
#         )
#
#     else:
#         return responses.Response(
#             content=err,
#             status_code=500,
#             media_type='application/json'
#         )

# @app.get("/qFindDc")
# async def qdc_all():
#     jobs = [{"id": job.id, "jobCreatedAt": job.created_at} for job in await service.queue_dc_all()]
#
#     res = json.dumps(
#         {"status": "success", "jobs": jobs},
#         ensure_ascii=False,
#         indent=2,
#         sort_keys=True,
#         default=str
#     )
#     err = {"status": "error"}
#     err = json.dumps(err, indent=4, sort_keys=True, default=str)
#
#     if res:
#         return responses.Response(
#             content=res,
#             status_code=200,
#             media_type='application/json'
#         )
#
#     else:
#         return responses.Response(
#             content=err,
#             status_code=500,
#             media_type='application/json'
#         )
