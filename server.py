import json
import random

from fastapi import FastAPI, responses, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

import config
import service
import sql_adapter

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
    await service.update_proxies()
    for i in range(random.randint(0, len(config.proxies))):
        next(config.r_proxies)
    config.logger.info('Updating started')
    # await mdc()


@app.get("/updateVins")
async def updateVins():
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
    # config.threads = threads
    bg_tasks = await sql_adapter.check_bg_tasks()
    if len(bg_tasks) > 0:
        res = {"status": "in process"}
        d = {'bg_tasks': []}
        for bg_task in bg_tasks:
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


@app.get("/findDc")
async def getdc(vin, noproxy=False):
    res = json.dumps(
        await service.find_dc(vin, noproxy),
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


@app.get("/qDc")
async def qdc(vin):
    job = config.queue.enqueue(service.queue_dc, vin, timeout=3600)
    # print(job.__dict__)

    res = json.dumps(
        {"status": "success", "job": job.id, "jobCreatedAt": job.created_at},
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
