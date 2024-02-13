from fastapi import FastAPI, responses
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import json

import parser
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


@app.get("/getdc")
async def getdc(vin):
    VDCP = parser.VinDcCheck()
    res = await VDCP.process_vin(vin)
    err = {
        "status": "error"
    }

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