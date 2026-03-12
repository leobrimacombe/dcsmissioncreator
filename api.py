from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from generateur import generer_mission # On importe la fonction du fichier d'à côté

app = FastAPI(title="Générateur DCS Iron Storm")

# Configuration CORS pour que React puisse parler à Python
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

@app.post("/generer-mission")
async def creer_mission_endpoint(config: MissionConfig):
    # Appelle la fonction dans generateur.py
    chemin_fichier = generer_mission(config)
    return FileResponse(
        path=chemin_fichier,
        filename=chemin_fichier,
        media_type='application/octet-stream'
    )