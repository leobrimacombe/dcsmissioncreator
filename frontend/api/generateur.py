import logging
logging.getLogger().setLevel(logging.CRITICAL)
import math
import dcs
from dcs.planes import F_15C, Su_27, E_3A, A_50
from dcs.vehicles import AirDefence
from dcs.weather import Weather
from dcs.task import OrbitAction, EngageTargets
from dcs.unit import Skill
from dcs.weapons_data import Weapons
from dcs.goals import Goal
from dcs.condition import GroupDead
from dcs.triggers import TriggerOnce, Event
from dcs.action import MessageToAll

THEATRES = {
    "caucase": {
        "terrain": None,
        "blue_airport": "Kutaisi",
        "red_airport": "Gudauta",
        "red_awacs_airport": None,
        "nom": "Caucase",
    },
    "golfe_persique": {
        "terrain": "PersianGulf",
        "blue_airport": "Al Dhafra AFB",
        "red_airport": "Bandar Abbas Intl",
        "red_awacs_airport": "Shiraz Intl",
        "nom": "Golfe Persique",
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

def _charger_armement_su27(fg):
    """Charge R-77 (radar) et R-73 (infrarouge) sur chaque Su-27 du groupe."""
    for unit in fg.units:
        unit.load_pylon((3, Weapons.R_77__AA_12_Adder____Active_Rdr))
        unit.load_pylon((4, Weapons.R_77__AA_12_Adder____Active_Rdr))
        unit.load_pylon((7, Weapons.R_77__AA_12_Adder____Active_Rdr))
        unit.load_pylon((8, Weapons.R_77__AA_12_Adder____Active_Rdr))
        unit.load_pylon((1, Weapons.R_73__AA_11_Archer____Infra_Red))
        unit.load_pylon((10, Weapons.R_73__AA_11_Archer____Infra_Red))

def _charger_armement_f15c(fg):
    """Charge AIM-120C (radar) et AIM-9M (infrarouge) sur chaque F-15C du groupe."""
    for unit in fg.units:
        unit.load_pylon((1, Weapons.AIM_120C_5_AMRAAM___Active_Rdr_AAM))
        unit.load_pylon((2, Weapons.AIM_120C_5_AMRAAM___Active_Rdr_AAM))
        unit.load_pylon((8, Weapons.AIM_120C_5_AMRAAM___Active_Rdr_AAM))
        unit.load_pylon((9, Weapons.AIM_120C_5_AMRAAM___Active_Rdr_AAM))
        unit.load_pylon((3, Weapons.AIM_9M_Sidewinder_IR_AAM))
        unit.load_pylon((7, Weapons.AIM_9M_Sidewinder_IR_AAM))

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

    # Zone de CAP Su-27 : 40% du chemin depuis la base rouge
    cap_center = base_russie.position.point_from_heading(hdg_red_to_blue, dist_totale * 0.4)
    cap_p1 = cap_center.point_from_heading((hdg_red_to_blue + 90) % 360, 25000)
    cap_p2 = cap_center.point_from_heading((hdg_red_to_blue - 90) % 360, 25000)

    # Zone orbite AWACS : 60 km derrière les lignes de chaque camp
    awacs_blue_pos = base_otan.position.point_from_heading(hdg_red_to_blue, 60000)
    awacs_red_pos = base_russie_awacs.position.point_from_heading(hdg_blue_to_red, 60000)

    # --- Joueurs (F-15C) ---
    fg_joueurs = m.flight_group_from_airport(
        country=usa,
        name="Joueurs_F15C",
        aircraft_type=F_15C,
        airport=base_otan,
        group_size=int(config.nb_joueurs)
    )
    fg_joueurs.set_client()
    _charger_armement_f15c(fg_joueurs)

    # --- IA ennemie (Su-27) ---
    fg_ennemis = None
    if config.presence_ennemis and config.nb_ennemis > 0:
        fg_ennemis = m.flight_group_from_airport(
            country=russie,
            name="IA_Su27",
            aircraft_type=Su_27,
            airport=base_russie,
            group_size=int(config.nb_ennemis)
        )
        # Tâche principale : CAP (interception aérienne)
        fg_ennemis.task = "CAP"
        # Niveau IA : réaliste et redoutable
        fg_ennemis.set_skill(Skill.High)
        # Tâche en-route : engager tout aéronef ennemi dans un rayon de 160 km
        et = EngageTargets(max_distance=160000)
        et.auto = True
        fg_ennemis.tasks.append(et)
        # Armement : R-77 (BVR) + R-73 (courte portée)
        _charger_armement_su27(fg_ennemis)
        # Route de patrouille : orbite racetrack dans la zone CAP
        wp1 = fg_ennemis.add_waypoint(cap_p1, 6000)
        wp1.add_task(OrbitAction(altitude=6000, speed=700, pattern=OrbitAction.OrbitPattern.RaceTrack))
        fg_ennemis.add_waypoint(cap_p2, 6000)

    # --- AWACS ---
    if config.activer_awacs:
        fg_awacs_blue = m.flight_group_from_airport(
            country=usa,
            name="AWACS_OTAN",
            aircraft_type=E_3A,
            airport=base_otan,
            group_size=1
        )
        fg_awacs_blue.task = "AWACS"
        fg_awacs_blue.set_frequency(251.0)
        wp_b = fg_awacs_blue.add_waypoint(awacs_blue_pos, 9000)
        wp_b.add_task(OrbitAction(altitude=9000, speed=500, pattern=OrbitAction.OrbitPattern.RaceTrack))

        fg_awacs_red = m.flight_group_from_airport(
            country=russie,
            name="AWACS_RUSSIE",
            aircraft_type=A_50,
            airport=base_russie_awacs,
            group_size=1
        )
        fg_awacs_red.task = "AWACS"
        fg_awacs_red.set_frequency(264.0)
        wp_r = fg_awacs_red.add_waypoint(awacs_red_pos, 9000)
        wp_r.add_task(OrbitAction(altitude=9000, speed=500, pattern=OrbitAction.OrbitPattern.RaceTrack))

    # --- Défenses SAM ---
    if config.activer_sam:
        m.vehicle_group(usa, "SAM_Blue", AirDefence.M1097_Avenger, base_otan.position)
        m.vehicle_group(russie, "SAM_Red", AirDefence.ZSU_23_4_Shilka, base_russie.position)

    # --- Briefing ---
    theatre_nom = theatre["nom"]
    awacs_info = "\n- AWACS OTAN sur 251.0 MHz (Eagle)" if config.activer_awacs else ""
    sam_info = "\n- SAM défensif M1097 Avenger sur la base OTAN" if config.activer_sam else ""

    m.set_sortie_text("Iron Storm - Interception")

    m.set_description_text(
        f"MISSION : IRON STORM — INTERCEPTION\n"
        f"Théâtre : {theatre_nom}\n\n"
        f"SITUATION :\n"
        f"Des Su-27 russes ont établi une zone de patrouille avancée (CAP) entre les deux bases. "
        f"Ils sont armés de missiles R-77 à guidage radar et R-73 infrarouge. "
        f"Votre mission est de les intercepter et de les détruire avant qu'ils ne franchissent "
        f"nos lignes et n'attaquent notre base.\n\n"
        f"OBJECTIF PRINCIPAL :\n"
        f"→ Détruire tous les Su-27 ennemis\n\n"
        f"APPUIS DISPONIBLES :{awacs_info}{sam_info}\n\n"
        f"RÈGLES D'ENGAGEMENT :\n"
        f"- Tirs au-delà de la vue (BVR) autorisés\n"
        f"- Ne pas attaquer les aéronefs non identifiés\n\n"
        f"Bonne chasse !"
    )

    m.set_description_bluetask_text(
        "1. Décoller de la base OTAN\n"
        "2. Monter en altitude de croisière (25 000 ft)\n"
        + (f"3. Contacter l'AWACS Eagle sur 251.0 MHz pour le tableau de situation\n"
           f"4. Intercepter les Su-27 ennemis en CAP\n"
           f"5. Détruire tous les appareils ennemis\n"
           f"6. Retourner à la base" if config.activer_awacs else
           f"3. Intercepter les Su-27 ennemis en CAP\n"
           f"4. Détruire tous les appareils ennemis\n"
           f"5. Retourner à la base")
    )

    m.set_description_redtask_text(
        "1. Maintenir la zone de CAP avancée\n"
        "2. Intercepter et détruire tout aéronef OTAN\n"
        "3. Protéger la base rouge"
    )

    # --- Objectifs de victoire et triggers ---
    if fg_ennemis is not None:
        # Condition de victoire : tous les Su-27 détruits
        goal_victoire = Goal(comment="Tous les Su-27 détruits - Victoire OTAN", score=100)
        goal_victoire.rules.append(GroupDead(fg_ennemis))
        m.goals.add_blue(goal_victoire)

        # Message de victoire
        trig_victoire = TriggerOnce(Event.NoEvent, "Victoire OTAN")
        trig_victoire.add_condition(GroupDead(fg_ennemis))
        trig_victoire.add_action(MessageToAll(
            text=m.string(
                "✈ MISSION ACCOMPLIE !\n\n"
                "Tous les Su-27 ennemis ont été éliminés.\n"
                "La supériorité aérienne est établie.\n"
                "Retournez à la base."
            ),
            seconds=30
        ))
        m.triggerrules.triggers.append(trig_victoire)

    # Message d'échec si tous les joueurs sont détruits
    trig_echec = TriggerOnce(Event.NoEvent, "Echec Mission")
    trig_echec.add_condition(GroupDead(fg_joueurs))
    trig_echec.add_action(MessageToAll(
        text=m.string(
            "✈ MISSION ÉCHOUÉE.\n\n"
            "Tous les pilotes ont été abattus.\n"
            "La zone aérienne est perdue."
        ),
        seconds=30
    ))
    m.triggerrules.triggers.append(trig_echec)

    chemin_complet = "/tmp/mission.miz"
    m.save(chemin_complet)
    return chemin_complet
