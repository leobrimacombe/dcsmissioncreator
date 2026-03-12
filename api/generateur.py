import logging
logging.getLogger().setLevel(logging.CRITICAL)
import dcs
from dcs.planes import F_15C, Su_27, E_3A, A_50
from dcs.vehicles import AirDefence

def generer_mission(config):
    m = dcs.Mission()
    usa = m.coalition["blue"].countries["USA"]
    russie = m.coalition["red"].countries["Russia"]
    
    base_otan = m.terrain.airports["Kutaisi"]
    base_russie = m.terrain.airports["Gudauta"]

    # 1. CHASSEURS
    fg_joueurs = m.flight_group_from_airport(
        country=usa, 
        name="Joueurs_F15C", 
        aircraft_type=F_15C,
        airport=base_otan, 
        group_size=int(config.nb_joueurs)
    )
    fg_joueurs.set_client()

    if config.presence_ennemis and config.nb_ennemis > 0:
        m.flight_group_from_airport(
            country=russie, 
            name="IA_Su27", 
            aircraft_type=Su_27,
            airport=base_russie, 
            group_size=int(config.nb_ennemis)
        )

    # 2. AWACS
    if config.activer_awacs:
        m.flight_group_from_airport(
            country=usa, 
            name="AWACS_OTAN", 
            aircraft_type=E_3A, 
            airport=base_otan, 
            group_size=1
        )
        m.flight_group_from_airport(
            country=russie, 
            name="AWACS_RUSSIE", 
            aircraft_type=A_50, 
            airport=base_russie, 
            group_size=1
        )

    # --- 3. LES DÉFENSES SAM (UNITÉS AU SOL) ---
    if config.activer_sam:
        # On passe : Pays, Nom, Type, Position (SANS mettre les noms des variables)
        m.vehicle_group(usa, "SAM_Kutaisi", AirDefence.M1097_Avenger, base_otan.position)
        m.vehicle_group(russie, "SAM_Gudauta", AirDefence.ZSU_23_4_Shilka, base_russie.position)

    nom_fichier = "Black_Sea_Iron_Storm.miz"
    chemin_complet = f"/tmp/{nom_fichier}" 
    m.save(chemin_complet)
    return chemin_complet