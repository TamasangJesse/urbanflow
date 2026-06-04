# middleware.py — registers all middleware on the app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def register_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://194.163.153.164:5173", "http://194.163.153.164"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )