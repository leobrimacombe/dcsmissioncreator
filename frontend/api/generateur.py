import logging
logging.getLogger().setLevel(logging.CRITICAL)
import dcs
from dcs.planes import F_15C, Su_27, E_3A, A_50
from dcs.vehicles import AirDefence
from dcs.weather import Weather

THEATRES = {
    "caucase": {
        "terrain": None,
        "blue_airport": "Kutaisi",
        "red_airport": "Gudauta",
    },
    "golfe_persique": {
        "terrain": "PersianGulf",
        "blue_airport": "Al Dhafra AFB",
        "red_airport": "Bandar Abbas Intl",
    },
}

HEURES = {
    "aube": 6,
    "jour": 12,
    "crepuscule": 18,
    "nuit": 2,
}

def appliquer_meteo(m, meteo):
    if meteo == "nuageux":
        m.weather.clouds_base = 1500
        m.weather.clouds_density = 6
        m.weather.clouds_thickness = 200
    elif meteo == "orage":
        m.weather.clouds_base = 1000
        m.weather.clouds_density = 9
        m.weather.clouds_thickness = 400
        m.weather.clouds_iprecptns = Weather.Preceptions.Rain
        m.weather.wind_at_ground.speed = 8

def generer_mission(config):
    theatre = THEATRES.get(config.theatre, THEATRES["caucase"])

    if theatre["terrain"]:
        from dcs.terrain import PersianGulf
        m = dcs.Mission(terrain=PersianGulf())
    else:
        m = dcs.Mission()

    # Heure de départ
    hour = HEURES.get(config.heure, 12)
    m.start_time = m.start_time.replace(hour=hour, minute=0, second=0)

    # Météo
    appliquer_meteo(m, config.meteo)

    usa = m.coalition["blue"].countries["USA"]
    russie = m.coalition["red"].countries["Russia"]

    base_otan = m.terrain.airports[theatre["blue_airport"]]
    base_russie = m.terrain.airports[theatre["red_airport"]]

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

    if config.activer_sam:
        m.vehicle_group(usa, "SAM_Blue", AirDefence.M1097_Avenger, base_otan.position)
        m.vehicle_group(russie, "SAM_Red", AirDefence.ZSU_23_4_Shilka, base_russie.position)

    chemin_complet = "/tmp/mission.miz"
    m.save(chemin_complet)
    return chemin_complet
