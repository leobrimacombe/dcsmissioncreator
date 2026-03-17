import logging
logging.getLogger().setLevel(logging.CRITICAL)
import math
import dcs
from dcs.planes import F_15C, Su_27, E_3A, A_50
from dcs.vehicles import AirDefence
from dcs.weather import Weather
from dcs.task import OrbitAction

THEATRES = {
    "caucase": {
        "terrain": None,
        "blue_airport": "Kutaisi",
        "red_airport": "Gudauta",
        "red_awacs_airport": None,
    },
    "golfe_persique": {
        "terrain": "PersianGulf",
        "blue_airport": "Al Dhafra AFB",
        "red_airport": "Bandar Abbas Intl",
        "red_awacs_airport": "Shiraz Intl",
    },
}

HEURES = {
    "aube": 6,
    "jour": 12,
    "crepuscule": 18,
    "nuit": 2,
}

def _heading(from_pos, to_pos):
    dx = to_pos.x - from_pos.x
    dy = to_pos.y - from_pos.y
    return math.degrees(math.atan2(dy, dx)) % 360

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
    red_awacs_name = theatre.get("red_awacs_airport") or theatre["red_airport"]
    base_russie_awacs = m.terrain.airports[red_awacs_name]

    # Calcul des positions tactiques
    hdg_blue_to_red = _heading(base_otan.position, base_russie.position)
    hdg_red_to_blue = (hdg_blue_to_red + 180) % 360
    dx = base_russie.position.x - base_otan.position.x
    dy = base_russie.position.y - base_otan.position.y
    dist_totale = math.sqrt(dx*dx + dy*dy)

    # Zone de CAP Su-27 : 40% du chemin depuis la base rouge vers le bleu
    cap_center = base_russie.position.point_from_heading(hdg_red_to_blue, dist_totale * 0.4)
    cap_p1 = cap_center.point_from_heading((hdg_red_to_blue + 90) % 360, 25000)
    cap_p2 = cap_center.point_from_heading((hdg_red_to_blue - 90) % 360, 25000)

    # Zone orbite AWACS bleu : 60km derrière les lignes bleues
    awacs_blue_pos = base_otan.position.point_from_heading(hdg_red_to_blue, 60000)
    # Zone orbite AWACS rouge : 60km derrière les lignes rouges
    awacs_red_pos = base_russie_awacs.position.point_from_heading(hdg_blue_to_red, 60000)

    fg_joueurs = m.flight_group_from_airport(
        country=usa,
        name="Joueurs_F15C",
        aircraft_type=F_15C,
        airport=base_otan,
        group_size=int(config.nb_joueurs)
    )
    fg_joueurs.set_client()

    if config.presence_ennemis and config.nb_ennemis > 0:
        fg_ennemis = m.flight_group_from_airport(
            country=russie,
            name="IA_Su27",
            aircraft_type=Su_27,
            airport=base_russie,
            group_size=int(config.nb_ennemis)
        )
        wp1 = fg_ennemis.add_waypoint(cap_p1, 6000)
        wp1.add_task(OrbitAction(altitude=6000, speed=700, pattern=OrbitAction.OrbitPattern.RaceTrack))
        fg_ennemis.add_waypoint(cap_p2, 6000)

    if config.activer_awacs:
        fg_awacs_blue = m.flight_group_from_airport(
            country=usa,
            name="AWACS_OTAN",
            aircraft_type=E_3A,
            airport=base_otan,
            group_size=1
        )
        wp_b = fg_awacs_blue.add_waypoint(awacs_blue_pos, 9000)
        wp_b.add_task(OrbitAction(altitude=9000, speed=500, pattern=OrbitAction.OrbitPattern.RaceTrack))

        fg_awacs_red = m.flight_group_from_airport(
            country=russie,
            name="AWACS_RUSSIE",
            aircraft_type=A_50,
            airport=base_russie_awacs,
            group_size=1
        )
        wp_r = fg_awacs_red.add_waypoint(awacs_red_pos, 9000)
        wp_r.add_task(OrbitAction(altitude=9000, speed=500, pattern=OrbitAction.OrbitPattern.RaceTrack))

    if config.activer_sam:
        m.vehicle_group(usa, "SAM_Blue", AirDefence.M1097_Avenger, base_otan.position)
        m.vehicle_group(russie, "SAM_Red", AirDefence.ZSU_23_4_Shilka, base_russie.position)

    chemin_complet = "/tmp/mission.miz"
    m.save(chemin_complet)
    return chemin_complet
