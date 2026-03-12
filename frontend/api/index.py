import sys
import os

# Permet d'importer generateur.py qui est dans le même dossier api/
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from generateur import generer_mission

app = FastAPI(title="Générateur DCS Iron Storm")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MissionConfig(BaseModel):
    nb_joueurs: int = Field(default=4, ge=1, le=16)
    presence_ennemis: bool = Field(default=True)
    nb_ennemis: int = Field(default=2, ge=1, le=16)
    activer_awacs: bool = Field(default=True)
    activer_sam: bool = Field(default=True)
    meteo: str = Field(default="clair", pattern="^(clair|nuageux|orage)$")
    heure: str = Field(default="jour", pattern="^(aube|jour|crepuscule|nuit)$")
    theatre: str = Field(default="caucase", pattern="^(caucase|golfe_persique)$")

# ⚠️ La route doit inclure /api/ car Vercel transmet le chemin complet à FastAPI
@app.post("/api/generer-mission")
async def creer_mission_endpoint(config: MissionConfig):
    chemin_fichier = generer_mission(config)
    return FileResponse(
        path=chemin_fichier,
        filename="Black_Sea_Iron_Storm.miz",
        media_type="application/octet-stream",
    )
