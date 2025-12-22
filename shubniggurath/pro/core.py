"""
Inicialización central de Shub Pro. Este archivo puede ser usado para montar subapps.
"""
from fastapi import FastAPI
from .interface_api import app as api_app


def create_app() -> FastAPI:
    return api_app
