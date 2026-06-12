Résumé de session — Micro-onduleur HMS-1600 / OpenDTU / Home Assistant
Date : 16-17 mai 2026 | Lieu : Beauvallon, Auvergne-Rhône-Alpes, FR

Contexte matériel
Micro-onduleur : Hoymiles HMS-1600-4T (4 strings DC, monophasé AC)

Numéro de série : 116495202971

Firmware onduleur : v1.0.27 (2023-06-05)

Puissance nominale : 1 600 W (puissance maximale détectée : 1 600 W)

Gateway : OpenDTU (firmware v26.3.30, connecté via OpenDTU-4C9028)

IP OpenDTU : 192.168.1.137

Intégration HA : via MQTT (broker 192.168.1.79, port 1883, user mqtt_user, topic de base solar/, intervalle de publication : 5 secondes)

HA Discovery MQTT : activé, topic homeassistant/

Problème investigué : décrochages répétés de la production
Symptômes observés (16 mai 2026)
Décrochages de production observés dans Home Assistant à : 12:13 – 13:02 – 13:28 – 14:15 – 14:52

Recherche dans les logs OpenDTU
La console OpenDTU (Informations → Console) est un flux temps réel en RAM uniquement — elle ne conserve pas les événements passés après redémarrage.

Le Journal des événements de l'onduleur (icône log, badge "2") est la seule source fiable pour les événements passés.

Le journal du 16 mai ne contenait que les entrées postérieures à 15h31 (redémarrage OpenDTU à 15:31:59) → les décrochages de la matinée étaient perdus.

Cause identifiée — décrochage du 17 mai à ~11h48
Le journal des événements a clairement loggé :

Départ	Arrêt	ID	Message
11:48:03	11:49:02	141	Réseau : Surtension du réseau
Cause confirmée : surtension du réseau EDF, code événement Hoymiles ID 141 = Grid Overvoltage.

Pourquoi Home Assistant n'a pas vu la surtension
L'intervalle MQTT est de 5 secondes. Le pic de tension a duré moins de 5 secondes — assez pour déclencher le trip de l'onduleur (seuil HV1 = 253 V pendant 3 s), mais trop court pour être capturé entre deux publications MQTT. La surtension est passée entre deux mesures → invisible dans HA.

Grid Profile analysé
Nom : XX - NF_EN_50549-1:2019 | Version : 2.0.0

Profil basé sur la norme française/européenne pour micro-générateurs ≤ 16A (NF EN 50549-1:2019). Le préfixe "XX" = profil générique universel.

Seuils de tension (section Voltage H/LVRT)
Paramètre	Valeur	Délai de trip
Nominale (NV)	230 V	—
Low Voltage 1 (LV1)	195,5 V	1,5 s
Low Voltage 2 (LV2)	161 V	0,2 s
High Voltage 1 (HV1)	253 V	3 s
High Voltage 2 (HV2)	264,5 V	0,2 s
High Voltage 3 (HV3)	276 V	0,1 s
AHV (moyenne 10 min)	253 V	décrochage
Paramètres de reconnexion (section Reconnection RT)
Paramètre	Valeur
Reconnect Time (RT)	60 secondes
Reconnect High Voltage (RHV)	253 V
Reconnect Low Voltage (RLV)	195,5 V
Reconnect High Frequency (RHF)	50,2 Hz
Reconnect Low Frequency (RLF)	49,5 Hz
Ramp Rates (RR)
Paramètre	Valeur
Normal Ramp up Rate	20 Rated%/s
Soft Start Ramp up Rate	0,16 Rated%/s
Le délai de 30 minutes de redémarrage
Constat : après un décrochage, l'onduleur reste inactif ~30 minutes avant de reprendre.

Explication : Ce délai n'est pas configurable depuis OpenDTU. Il est probablement dû à :

La condition AHV : si la tension moyenne sur 10 min reste ≥ 253 V, l'onduleur reporte la reconnexion → plusieurs cycles de 10 min s'enchaînent

Un comportement interne du firmware Hoymiles qui allonge progressivement le délai après tentatives ratées

Un paramètre accessible uniquement via l'outil DTU-Pro Hoymiles (logiciel propriétaire, inaccessible depuis OpenDTU)

Note : Le Reconnect Time du Grid Profile est bien 60 s, pas 30 min.

Redémarrage manuel de la production
Trois méthodes disponibles depuis OpenDTU (boutons dans la barre du HMS-1600) :

Bouton ON/OFF (bouton rouge power) → éteindre puis rallumer → réinitialise le compteur d'attente, reconnexion en 60 s

Coupure DC physique (sectionneur DC) → attendre 30 s → redémarrage complet

Limite à 0 W puis retour → forcer recalcul des conditions de connexion

Comportement de la limite de puissance absolue
Question : Est-ce un écrêtage ou une réduction proportionnelle ?

Réponse : réduction proportionnelle sur tous les strings DC.

La limite absolue est convertie en pourcentage de la puissance nominale (ex : 1 300 W / 1 600 W = 81,25%) et appliquée uniformément sur le courant de chaque string DC. L'onduleur recule son point de travail MPPT — les panneaux ne dissipent pas d'énergie en chaleur. C'est confirmé par l'affichage OpenDTU qui montre toujours les deux valeurs en parallèle (ex : "Limite de courant : 1 299 W | 81,2%").

Automation Home Assistant — Throttling dynamique anti-surtension
Principe
HA lit sensor.hms_1600_voltage (mis à jour toutes les 5 s via MQTT) et envoie des commandes de limite via le topic MQTT :

text
solar/116495202971/cmd/limit_nonpersistent_absolute
(nonpersistent = limite perdue au redémarrage, plus sûr pour une commande dynamique)

Code YAML complet
text
automation:
  - alias: "HMS-1600 Throttling tension réseau"
    description: "Réduit la puissance quand la tension approche 253V"
    mode: single
    max_exceeded: silent
    trigger:
      - platform: state
        entity_id: sensor.hms_1600_voltage
    action:
      - variables:
          tension: "{{ states('sensor.hms_1600_voltage') | float(0) }}"
      - choose:
          # Surtension critique : arrêt préventif
          - conditions:
              - condition: template
                value_template: "{{ tension >= 252 }}"
            sequence:
              - service: mqtt.publish
                data:
                  topic: "solar/116495202971/cmd/limit_nonpersistent_absolute"
                  payload: "0"
              - service: notify.mobile_app_ton_telephone
                data:
                  title: "⚡ HMS-1600 ARRÊT PRÉVENTIF"
                  message: "Tension {{ tension }}V ≥ 252V — production coupée"

          # Zone rouge : throttling fort (50%)
          - conditions:
              - condition: template
                value_template: "{{ tension >= 250 and tension < 252 }}"
            sequence:
              - service: mqtt.publish
                data:
                  topic: "solar/116495202971/cmd/limit_nonpersistent_absolute"
                  payload: "700"
              - service: notify.mobile_app_ton_telephone
                data:
                  title: "⚠️ HMS-1600 Throttling fort"
                  message: "Tension {{ tension }}V — limite 700W"

          # Zone orange : throttling modéré (75%)
          - conditions:
              - condition: template
                value_template: "{{ tension >= 248 and tension < 250 }}"
            sequence:
              - service: mqtt.publish
                data:
                  topic: "solar/116495202971/cmd/limit_nonpersistent_absolute"
                  payload: "1000"

          # Zone normale : retour à pleine puissance
          - conditions:
              - condition: template
                value_template: "{{ tension < 248 }}"
            sequence:
              - service: mqtt.publish
                data:
                  topic: "solar/116495202971/cmd/limit_nonpersistent_absolute"
                  payload: "1400"
Paliers de throttling
Tension réseau	Limite	% puissance max
< 248 V	1 400 W	100% (normal)
248 – 249 V	1 000 W	~71%
250 – 251 V	700 W	50%
≥ 252 V	0 W	Arrêt préventif + notification
Points à adapter
Nom exact du capteur : vérifier dans HA (peut être sensor.hms_1600_phase_1_voltage)

Entité de notification : remplacer notify.mobile_app_ton_telephone

Anti-rebond : ajouter for: "00:00:10" sur le trigger pour n'agir qu'après 10 s de stabilité

Limitation connue
Les pics de tension qui déclenchent réellement le trip durent < 5 secondes (inférieur à l'intervalle MQTT). L'automation réduit le risque (moins d'injection → tension qui monte moins) mais ne capturera pas tous les pics instantanés. C'est la meilleure protection disponible depuis HA.

État actuel du système (17 mai 2026, 17h)
Production en cours : 511,7 W | Tension : 241,8 V

Limite : 1 600 W | 100% (pleine puissance)

Rendement du jour : 7 472 Wh

Rendement total : 3 194,812 kWh

Température onduleur : 42,1 °C

Pistes pour la suite
Implémenter l'automation de throttling dans HA avec le code YAML ci-dessus

Réduire l'intervalle MQTT à 1 s (Paramètres → MQTT dans OpenDTU) pour améliorer la détection des pics de tension

Créer une automation de notification dans HA basée sur Producing = Off pour être alerté immédiatement lors des décrochages

Contacter Enedis pour signaler une tension réseau anormalement élevée (des pics > 253 V en France sont hors tolérance de la norme EN 50160 qui fixe la limite à +10% de 230 V = 253 V)

Explorer le topic MQTT solar/116495202971/ pour identifier s'il existe un topic d'événement (alarm/event) publié directement par OpenDTU lors d'un décrochage