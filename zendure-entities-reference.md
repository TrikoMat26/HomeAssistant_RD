# Référence des Entités Zendure & SolarFlow

Ce document répertorie toutes les entités liées à votre batterie Zendure SolarFlow 800 Plus et au Zendure Manager disponibles dans Home Assistant. Chaque entité est accompagnée d'une description détaillée de son utilité.

---

## 🎛️ 1. Contrôles de l'Interface Utilisateur (Helpers & Automations)
Ces entités sont configurées localement dans Home Assistant pour simplifier le pilotage et synchroniser les valeurs de consigne avec les paramètres physiques de l'appareil.

| Entity ID | État | Nom | Description / Utilité |
| --- | --- | --- | --- |
| `input_select.solarflow_limite_charge` | Varie | SolarFlow — Limite charge | Sélecteur personnalisé (menu déroulant) dans le tableau de bord pour définir la puissance de charge souhaitée (de 0 W à 1000 W). C'est la source de vérité pour l'UI. |
| `input_select.solarflow_limite_decharge` | Varie | SolarFlow — Limite décharge | Sélecteur personnalisé (menu déroulant) dans le tableau de bord pour définir la puissance de décharge (injection) souhaitée (de 0 W à 800 W). C'est la source de vérité pour l'UI. |
| `automation.solarflow_sync_limite_charge` | `on` | SolarFlow — Sync limite charge | Automatisation qui synchronise la valeur choisie dans `input_select.solarflow_limite_charge` vers l'entité de configuration physique `number.solarflow_800_plus_input_limit`. Si > 0 W, elle force le mode AC sur `"input"` et met la décharge à 0 W (exclusion mutuelle). |
| `automation.solarflow_sync_limite_decharge` | `on` | SolarFlow — Sync limite décharge | Automatisation qui synchronise la valeur choisie dans `input_select.solarflow_limite_decharge` vers l'entité de configuration physique `number.solarflow_800_plus_output_limit`. Si > 0 W, elle force le mode AC sur `"output"` et met la charge à 0 W (exclusion mutuelle). |
| `automation.solarflow_alerte_temperature_elevee` | `on` | SolarFlow — Alerte température élevée | Sécurité système : envoie une notification persistante si la température de l'appareil (`sensor.solarflow_800_plus_hyper_tmp`) dépasse 45 °C pendant 2 minutes. La notification est effacée automatiquement sous 42 °C. |
| `automation.solarflow_notification_batterie_79` | `on` | SolarFlow - Notification batterie > 70% | Automatisation de notification lorsque le niveau de charge de la batterie franchit le seuil de 70% ou 80%. |

---

## ⚙️ 2. Zendure Manager (Régulation Intelligente)
Le Zendure Manager est un module de l'intégration qui permet d'ajuster automatiquement la charge/décharge de la batterie en fonction de la consommation globale de la maison (par exemple via les données d'un téléinformation EDF ou d'un capteur de puissance générale).

| Entity ID | État | Nom | Description / Utilité |
| --- | --- | --- | --- |
| `select.zendure_manager_operation` | `store_solar` | Zendure Manager Mode de fonctionnement | Définit le mode de régulation globale. Les valeurs courantes sont `store_solar` (stocker en priorité l'énergie solaire dans la batterie) ou `manual` (puissance fixe). |
| `number.zendure_manager_manual_power` | `1000` | Zendure Manager Puissance manuelle | Puissance cible (en W) à injecter ou charger lorsque le manager est configuré en mode manuel. |
| `sensor.zendure_manager_power` | `0` | Zendure Manager Puissance | Affiche la puissance de régulation en temps réel actuellement calculée ou demandée par le gestionnaire Zendure. |
| `sensor.zendure_manager_operation_state` | `0` | Zendure Manager State | Code d'état interne représentant la phase opérationnelle actuelle du régulateur (ex: 0 = Idle/Repos). |
| `sensor.zendure_manager_available_kwh` | `0` | Zendure Manager Énergie disponible | Estimation de l'énergie stockée utilisable calculée par le gestionnaire (en kWh). |
| `sensor.zendure_manager_total_kwh` | `1.92` | Zendure Manager Total Battery Capacity | Capacité totale configurée des batteries connectées au manager (1.92 kWh correspond à une batterie AB2000). |

---

## 🔋 3. SolarFlow 800 Plus — Paramètres & Seuils Physiques
Ces entités représentent les configurations matérielles écrites directement dans la mémoire de l'appareil (via Cloud ou local MQTT).

| Entity ID | État | Nom | Description / Utilité |
| --- | --- | --- | --- |
| `select.solarflow_800_plus_ac_mode` | `output` | SolarFlow 800 Plus Mode de fonctionnement AC | Bascule le mode de fonctionnement physique du convertisseur AC : `"input"` (la batterie absorbe l'énergie du secteur/HMS) ou `"output"` (la batterie injecte vers la maison). Géré automatiquement par vos automatisations de synchronisation. |
| `number.solarflow_800_plus_input_limit` | `0.0` | SolarFlow 800 Plus Limite d'entrée | Consigne physique de la puissance maximale de charge autorisée (en W, de 0 à 1000 W). |
| `number.solarflow_800_plus_output_limit` | `800.0` | SolarFlow 800 Plus Limite de sortie | Consigne physique de la puissance maximale injectée vers le micro-onduleur (en W, de 0 à 800 W). |
| `number.solarflow_800_plus_min_soc` | `20.0` | SolarFlow 800 Plus SOC minimum | Seuil de décharge minimum (%) en dessous duquel la décharge se coupe pour protéger la batterie d'une décharge profonde. |
| `number.solarflow_800_plus_soc_set` | `80.0` | SolarFlow 800 Plus SOC maximum | Seuil de charge maximum (%) à partir duquel la charge s'arrête (utile pour prolonger la durée de vie des cellules lithium). |
| `select.solarflow_800_plus_connection` | `cloud` | SolarFlow 800 Plus Mode de connexion | Permet de choisir le canal de communication privilégié (`cloud` via serveurs Zendure ou `local` MQTT). |
| `select.solarflow_800_plus_grid_reverse` | `forbidden` | SolarFlow 800 Plus Exportation d'énergie | Option de configuration déterminant si l'injection réseau inverse est autorisée ou interdite (souvent configuré sur `forbidden` en France si pas de convention spécifique). |
| `select.solarflow_800_plus_fuse_group` | `unused` | SolarFlow 800 Plus groupe de fusible | Paramètre avancé pour associer le SolarFlow à un groupe de protection/fusible électrique. |
| `switch.solarflow_800_plus_lamp_switch` | `on` | SolarFlow 800 Plus LED | Interrupteur permettant d'allumer ou d'éteindre le voyant LED physique présent sur le boîtier du SolarFlow. |

---

## 📊 4. SolarFlow 800 Plus — Mesures & Télémesures Temps Réel
Ces capteurs remontent les flux d'énergie et les états physiques de l'installation.

| Entity ID | État | Nom | Description / Utilité |
| --- | --- | --- | --- |
| `sensor.solarflow_800_plus_electric_level` | `20` | SolarFlow 800 Plus Niveau de batterie | Le State of Charge (SOC) actuel en pourcentage. |
| `sensor.solarflow_800_plus_bat_in_out` | `0` | SolarFlow 800 Plus Puissance de la batterie | Flux net de puissance de la batterie (en W). Une valeur négative indique que la batterie charge, une valeur positive indique qu'elle décharge. |
| `sensor.solarflow_800_plus_bat_volt` | `49.19` | SolarFlow 800 Plus Tension de batterie | Tension électrique mesurée aux bornes du pack de batterie (en V). |
| `sensor.solarflow_800_plus_hyper_tmp` | `34.0` | SolarFlow 800 Plus Température de l'appareil | Température interne du processeur/châssis (en °C). Utilisée pour l'alerte surchauffe. |
| `sensor.solarflow_800_plus_solar_input_power` | `0` | SolarFlow 800 Plus Puissance d'entrée solaire | Puissance instantanée totale produite par les panneaux solaires branchés sur le SolarFlow (Somme PV1 + PV2 en W). |
| `sensor.solarflow_800_plus_solar_power1` | `0` | SolarFlow 800 Plus Puissance solaire PV1 | Puissance instantanée reçue sur l'entrée MPPT 1 (en W). |
| `sensor.solarflow_800_plus_solar_power2` | `0` | SolarFlow 800 Plus Puissance solaire PV2 | Puissance instantanée reçue sur l'entrée MPPT 2 (en W). |
| `sensor.solarflow_800_plus_output_home_power` | `0` | SolarFlow 800 Plus Puissance de sortie | Puissance électrique actuellement injectée vers le micro-onduleur domestique (en W). |
| `sensor.solarflow_800_plus_output_pack_power` | `0` | SolarFlow 800 Plus Puissance d'entrée de la batterie | Puissance brute de charge entrante mesurée à l'entrée de la batterie (en W). |
| `sensor.solarflow_800_plus_pack_input_power` | `0` | SolarFlow 800 Plus Puissance de sortie de la batterie | Puissance brute de décharge sortante mesurée à la sortie de la batterie (en W). |
| `sensor.solarflow_800_plus_grid_input_power` | `0` | SolarFlow 800 Plus Grid Input Power | Puissance consommée depuis le réseau AC pour charger la batterie (si le chargeur AC optionnel ou le mode AC Input est actif). |
| `sensor.solarflow_800_plus_remaining_time` | `0` | SolarFlow 800 Plus Temps de restant | Temps restant estimé (en minutes) avant que la batterie ne soit vide (en décharge) ou pleine (en charge). |
| `sensor.solarflow_800_plus_available_kwh` | `0.0` | SolarFlow 800 Plus Énergie disponible | Quantité d'énergie stockée réellement exploitable (en kWh), calculée selon le SOC actuel et la capacité totale. |
| `sensor.solarflow_800_plus_total_kwh` | `1.92` | SolarFlow 800 Plus Total Battery Capacity | Capacité énergétique nominale totale de la batterie connectée (1.92 kWh pour un pack AB2000). |
| `binary_sensor.solarflow_800_plus_heat_state` | `off` | SolarFlow 800 Plus chauffage de batterie | Indique si le film chauffant interne de la batterie est actif (utile en hiver pour permettre la charge lorsque la température ambiante est inférieure à 0 °C). |
| `binary_sensor.solarflow_800_plus_hems_state` | `on` | SolarFlow 800 Plus HEMS Active | Indique si le système de gestion d'énergie HEMS Zendure est actif. |
| `binary_sensor.solarflow_800_plus_reverse_state` | `off` | SolarFlow 800 Plus Reverse Flow State | Indique s'il y a un retour anormal de courant détecté (flux inverse). |

---

## 📈 5. Capteurs d'Énergie Cumulée (Statistiques d'Intégration)
Ces index cumulent la production et la consommation d'énergie au fil du temps (en kWh), idéaux pour un ajout dans le **Dashboard Énergie** de Home Assistant.

| Entity ID | État | Nom | Description / Utilité |
| --- | --- | --- | --- |
| `sensor.solarflow_800_plus_aggr_charge` | `21.38` | SolarFlow 800 Plus Total charges | Index cumulatif de l'énergie totale envoyée dans la batterie pour la recharger (en kWh). |
| `sensor.solarflow_800_plus_aggr_discharge` | `19.02` | SolarFlow 800 Plus Total décharges | Index cumulatif de l'énergie totale soutirée de la batterie (en kWh). |
| `sensor.solarflow_800_plus_aggr_solar` | `0.0` | SolarFlow 800 Plus Total solaire | Index cumulatif de l'énergie totale générée par les panneaux solaires (en kWh). |
| `sensor.solarflow_800_plus_aggr_output_home` | `19.08` | SolarFlow 800 Plus introduit dans la maison | Index cumulatif de l'énergie totale fournie au micro-onduleur domestique (en kWh). |
| `sensor.solarflow_800_plus_aggr_grid_input_power` | `21.38` | SolarFlow 800 Plus Total Grid Energy | Index cumulatif de l'énergie réseau utilisée pour la charge (en kWh). |

---

## 💻 6. Entités Techniques & Diagnostic Système
Ces capteurs sont principalement destinés au débogage, à la surveillance réseau et au suivi du firmware de l'appareil.

| Entity ID | État | Nom | Description / Utilité |
| --- | --- | --- | --- |
| `sensor.solarflow_800_plus_connection_status` | `2` | SolarFlow 800 Plus État de la connexion | État de la connectivité réseau du Hub (ex: 2 = Connecté au cloud). |
| `sensor.solarflow_800_plus_rssi` | `-62` | SolarFlow 800 Plus rssi | Puissance du signal Wi-Fi reçu par l'appareil (en dBm). |
| `sensor.solarflow_800_plus_pack_num` | `1` | SolarFlow 800 Plus Nombre de batteries | Nombre de modules de batterie physiques détectés (AB2000/AB1000). |
| `sensor.solarflow_800_plus_pack_state` | `0` | SolarFlow 800 Plus État de la batterie | Code d'état des cellules et du BMS de la batterie. |
| `sensor.solarflow_800_plus_next_calibration` | `2026...` | SolarFlow 800 Plus Next Calibration | Horodatage prévu pour la prochaine calibration automatique du SOC par décharge/charge complète. |
| `sensor.solarflow_800_plus_switch_count` | `690.0` | SolarFlow 800 Plus Switch Count | Compteur du nombre de commutations des relais internes (indicateur d'usure matérielle). |
| `sensor.solarflow_800_plus_iotstate` | `2` | SolarFlow 800 Plus IOTState | Code de statut de la connexion au broker IoT de Zendure. |
| `sensor.solarflow_800_plus_ai_state` | `2` | SolarFlow 800 Plus aiState | Code d'état de l'algorithme d'optimisation IA Zendure. |
| `sensor.solarflow_800_plus_is_error` | `0` | SolarFlow 800 Plus is_error | Indicateur de défaut matériel. `0` = aucun problème, `1` = alarme active. |
| `sensor.solarflow_800_plus_dc_status` | `0` | SolarFlow 800 Plus dcStatus | Code d'état du module de conversion de tension continue (DC-DC). |
| `sensor.solarflow_800_plus_pv_status` | `0` | SolarFlow 800 Plus pvStatus | Code d'état du contrôleur de charge solaire MPPT. |
| `sensor.solarflow_800_plus_ac_status` | `0` | SolarFlow 800 Plus acStatus | Code d'état de l'étage de conversion alternative (AC). |
| `sensor.solarflow_800_plus_grid_state` | `1` | SolarFlow 800 Plus gridState | Statut de synchronisation avec la fréquence du réseau électrique. |
| `sensor.solarflow_800_plus_grid_standard` | `1` | SolarFlow 800 Plus gridStandard | Norme réseau enregistrée (ex: DIN VDE 0126, EN 50549). |
| `sensor.solarflow_800_plus_inverse_max_power` | `800` | SolarFlow 800 Plus Puissance limite de sortie AC | Limite physique maximale absolue supportée pour l'injection (800 W). |
| `sensor.solarflow_800_plus_charge_max_limit` | `1000` | SolarFlow 800 Plus chargeMaxLimit | Puissance physique maximale absolue supportée pour la charge (1000 W). |
| `sensor.solarflow_800_plus_smart_mode` | `0` | SolarFlow 800 Plus smartMode | Flag de statut pour le mode de puissance dynamique. |
| `sensor.solarflow_800_plus_phase_switch` | `1` | SolarFlow 800 Plus phaseSwitch | Indique la configuration de phase sélectionnée pour le chargeur/onduleur. |
| `sensor.solarflow_800_plus_volt_wakeup` | `0` | SolarFlow 800 Plus VoltWakeup | Indicateur lié au réveil automatique par tension solaire. |
| `sensor.solarflow_800_plus_bindstate` | `0` | SolarFlow 800 Plus bindstate | Statut d'association/liaison de l'appareil au compte utilisateur Zendure. |
| `sensor.solarflow_800_plus_factory_mode_state` | `0` | SolarFlow 800 Plus factoryModeState | Indique si l'appareil est en mode test d'usine (`0` = non). |
| `sensor.solarflow_800_plus_otastate` | `0` | SolarFlow 800 Plus OTAState | Statut de téléchargement ou d'installation d'une mise à jour de firmware. |
| `sensor.solarflow_800_plus_lcnstate` | `0` | SolarFlow 800 Plus LCNState | État de la boucle de contrôle locale (Local Control Network). |
| `sensor.solarflow_800_plus_write_rsp` | `0` | SolarFlow 800 Plus writeRsp | Code de réponse de la dernière écriture MQTT (sert à confirmer la bonne réception d'une consigne). |
| `update.zendure_home_assistant_integration_update` | `off` | Zendure Home Assistant Integration Update | Indique si une nouvelle version de l'intégration HACS de FireSon est disponible au téléchargement. |
