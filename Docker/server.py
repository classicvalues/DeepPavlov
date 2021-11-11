import asyncio
import json
from typing import Dict, List
from logging import getLogger

import aiohttp
import requests
import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from deeppavlov.core.commands.utils import parse_config
from deeppavlov import configs, build_model, train_model, evaluate_model

logger = getLogger(__file__)
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

ner_config = parse_config("ner_rus_distilbert_torch.json")
entity_detection_config = parse_config("ner_rus_vx_distil.json")
entity_detection = build_model(entity_detection_config, download=False)

@app.post("/model")
async def model(request: Request):
    while True:
        try:
            inp = await request.json()
            texts = inp["x"]
            entity_substr, entity_lemm_substr, entity_offsets, entity_init_offsets, tags, sentences_offsets, \
                sentences, probas = ner(texts)
            res = {"entity_substr": entity_substr, "entity_lemm_substr": entity_lemm_substr,
                   "entity_offsets": entity_offsets, "entity_init_offsets": entity_init_offsets, "tags": tags,
                   "sentences_offsets": sentences_offsets, "sentences": sentences, "probas": probas}
            return res
            
        except aiohttp.client_exceptions.ClientConnectorError:
            logger.warning(f'{host} is unavailable, restarting worker container')
            loop = asyncio.get_event_loop()
            loop.create_task(porter.update_container(host))

@app.post("/train")
async def model(request: Request):
    while True:
        try:
            inp = await request.json()
            train_filename = inp["train_filename"]
            with open(train_filename, 'r') as fl:
                total_data = json.load(fl)
            train_data = total_data[:int(len(train_filename) * 0.9)]
            test_data = total_data[int(len(train_filename) * 0.9):]
            new_filename = f"{train_filename.strip('.json')}_train.json"
            with open(new_filename, 'w', encoding="utf8") as out:
                json.dump({"train": train_data, "valid": test_data, "test": test_data},
                          out, indent=2, ensure_ascii=False)
            
            ner_config["dataset_reader"] = {
                "class_name": "sq_reader",
                "data_path": new_filename
            }
            ner_config["metadata"]["MODEL_PATH"] = f"{ner_config['metadata']['MODEL_PATH']}_new"
            train_model(new_config)
            
            return {"trained": True}
            
        except aiohttp.client_exceptions.ClientConnectorError:
            logger.warning(f'{host} is unavailable, restarting worker container')
            loop = asyncio.get_event_loop()
            loop.create_task(porter.update_container(host))

@app.post("/test")
async def model(request: Request):
    while True:
        try:
            inp = await request.json()
            test_filename = inp["test_filename"]
            with open(test_filename, 'r') as fl:
                test_data = json.load(fl)
            new_filename = f"{test_filename.strip('.json')}_test.json"
            with open(new_filename, 'w', encoding="utf8") as out:
                json.dump({"train": [], "valid": [], "test": test_data},
                          out, indent=2, ensure_ascii=False)
            
            ner_config["dataset_reader"] = {
                "class_name": "sq_reader",
                "data_path": new_filename
            }
            res = evaluate_model(ner_config)
            metrics = dict(res["test"])
            
            return {"metrics": metrics}
            
        except aiohttp.client_exceptions.ClientConnectorError:
            logger.warning(f'{host} is unavailable, restarting worker container')
            loop = asyncio.get_event_loop()
            loop.create_task(porter.update_container(host))

uvicorn.run(app, host='0.0.0.0', port=8000)