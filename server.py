import json
import random

from fastapi import FastAPI, responses
from fastapi.middleware.cors import CORSMiddleware

import config
import service

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
    await mdc(True)


@app.get("/mFindDc")
async def mdc(use_proxy=True):
    # config.threads = threads
    res = json.dumps(
        await service.multithreaded_find_dcs(use_proxy),
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
        await service.dk_previous(vin),
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
