import json

from fastapi import FastAPI, responses
from fastapi.middleware.cors import CORSMiddleware

import service

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# @app.on_event("startup")
# async def startup():
#     Instrumentator().instrument(app).expose(app)


@app.get("/findDc")
async def getdc(vin):
    res = await service.find_dc(vin)
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
    res = await service.dc(vin)
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
    res = await service.dk_previous(vin)
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