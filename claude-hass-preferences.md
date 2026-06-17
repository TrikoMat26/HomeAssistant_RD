# Contexte Home Assistant — Claude (Krikor)

<!--
  Fichier de contexte persistant. Version stockée sur HA : /config/claude-hass-preferences.md
  Dernière mise à jour : 2026-05-28 v10 (voir Changelog en bas pour détails)
  Optimisé pour Claude Cowork (desktop/mobile/web) ET Claude Code.
-->

## 🚀 Bootstrap — à lire en premier

**Prompt à utiliser en début de session** (copier-coller) :

> "Lis le fichier de contexte Home Assistant et applique ses règles."

**Règles de chargement par environnement :**

| Environnement | Comment Claude charge ce fichier |
|---|---|
| Claude Cowork / Desktop / Web / Mobile | Connecteur HA actif → utiliser `ha-mcp` pour `/config/claude-hass-preferences.md`. Si le connecteur n'est pas activé dans la conversation, demander à Krikor de l'activer (bouton `+` → Connecteurs → Home Assistant) avant tout. |
| Claude Code | Deux options : (1) si la MCP HA est configurée côté Code, pareil que Cowork ; (2) sinon, Krikor peut copier-coller le contenu du fichier en début de session, ou faire `scp hass:/config/claude-hass-preferences.md .` dans le repo de travail puis `Read` local. |

**Priorité des outils (règle d'or, toujours dans cet ordre) :**

1. **MCP `ha-mcp` d'abord** pour tout ce qui concerne HA : automations, scripts, dashboards, helpers, zones, étages, pièces, groupes, labels, catégories, templates, états, services, logs, traces, HACS, intégrations, appareils, blueprints, validation, redémarrage, fichiers de `/config`, add-ons.
2. **SSH de Krikor en fallback** (pour écritures fichiers hors `/config` et manip hardware) : Claude donne les commandes exactes, Krikor les exécute depuis PowerShell avec `ssh hass`.
3. **Chrome/Comet en dernier recours** uniquement (lent, coûteux en tokens).
4. **Pour écrire dans `/config`** : ha-mcp n'a pas de `write_file` générique. Claude sauvegarde en outputs, Krikor copie via Samba ou SSH.

**Trigger phrases utiles :**

- `"mets à jour le fichier de contexte"` → Claude produit une nouvelle version dans outputs + commandes SSH de copie + mise à jour du changelog (voir §7.3).
- `"charge les données solaires du [date]"` → Claude lit le CSV correspondant dans `/config/claude_data/`.
- `"snapshot HA"` → Claude appelle `ha_get_overview` et met à jour mentalement les stats sans modifier le fichier (les stats sont volatiles).

---

## 🧭 Index

1. [Système & connexion](#1-système--connexion)
2. [Projet solaire & chauffe-eau](#2-projet-solaire--chauffe-eau)
2bis. [Projet Emporia — Export hebdo + Drive](#2bis-projet-emporia--export-hebdo--drive)
2ter. [HMS-1600 — Micro-onduleur OpenDTU](#2ter-hms-1600--micro-onduleur-opendtu)
2quater. [SolarFlow 800 Plus — Batterie Zendure](#2quater-solarflow-800-plus--batterie-zendure)
3. [Automations clés](#3-automations-clés)
3quater. [Cast vers Nest Hub Cuisine](#3quater-cast-vers-nest-hub-cuisine)
4. [Intégrations & add-ons](#4-intégrations--add-ons)
5. [Santé système — ouverts / connus / résolus](#5-santé-système)
6. [Bibliothèque de données solaires](#6-bibliothèque-de-données-solaires)
7. [Workflow & commandes utiles](#7-workflow--commandes-utiles)
8. [Snapshot HA (volatile — à rafraîchir à la demande)](#8-snapshot-ha-volatile)
9. [Changelog](#9-changelog)

---

## 1. Système & connexion

- **Home Assistant** : HAOS 17.2, core `2026.4.3` *(volatile — voir §8)*
- **URL publique** : `https://triko26.duckdns.org` (DuckDNS + NGINX SSL proxy, pas besoin du port 8123)
- **LAN** : `192.168.1.79:8123`
- **Localisation** : "Maison" / Beauvallon (Auvergne-Rhône-Alpes), timezone `Europe/Paris`, langue `fr`
- **Nommage** : principalement français, parfois mixte

### MCP `ha-mcp`

- Dépôt communauté : `homeassistant-ai/ha-mcp`
- Installation : `uvx ha-mcp@latest` (pas d'install permanente, auto-update)
- Runtime : `uv` / `uvx` (Astral)
- Couverture : 86 outils / 23 catégories
- Configuration Claude Desktop : `%APPDATA%\Claude\claude_desktop_config.json`, section `mcpServers`
- Auth : token longue durée HA avec **droits admin complets** → prudence sur les actions destructives, **toujours confirmer avant de modifier/supprimer** des automations ou intégrations existantes

### Accès utilisateur (pas pour Claude)

- SSH par clé publique depuis PowerShell Windows : `ssh hass` (clé `~/.ssh/hass_ed25519`)
- Samba share et Studio Code Server disponibles en alternative
- ⚠️ Le sandbox Claude (Cowork/Code) n'a **pas** d'accès réseau direct vers HA : il passe uniquement par la MCP

---

## 2. Projet solaire & chauffe-eau

> Objectif : décider d'allumer/éteindre un chauffe-eau en fonction de la production solaire.
> Aujourd'hui en **mode simulation** — aucune action physique, juste des notifications persistantes pour valider la logique avant passage en prod.

### 2.1 Matériel — 3 smart switches de production

| Nom affiché | entity_id power | Pic théorique |
|---|---|---|
| `Power_1400W` | `sensor.smart_switch_2312075875450151080948e1e9e5a5e0_power` | ~1400 W |
| `Power_800W` | `sensor.smart_switch_2312074614100551080148e1e9e52089_power` | ~800 W |
| `Power_300W` | `sensor.smart_switch_2312070251113551080948e1e9e5b52f_power` | ~300 W |

Total théorique cumulé : ~2500 W. Observé le 20/04/2026 (nuageux éclaircies) : pic 3073 W.

### 2.2 Entités dérivées

| Entité | entity_id | Rôle |
|---|---|---|
| Production Solaire Total | `sensor.total_solaire` | Somme W des 3 switches (unit W, state_class measurement) |
| Solaire stabilité stats | `sensor.solaire_stabilite_stats` | Écart-type σ de production (capteur `statistics`) |
| **Opportunité stats** | **`sensor.chauffe_eau_opportunite_stats`** | **Moyenne (0–1) de `binary_sensor.lancement_chauffe_eau_opportun` sur 30 min — critère d'arrêt** |
| Lancement chauffe-eau opportun | `binary_sensor.lancement_chauffe_eau_opportun` | Décision ON/OFF calculée en amont |
| Simulation chauffe-eau solaire | `input_boolean.simulation_chauffe_eau_solaire` | Flag simulation ON/OFF |
| Seuil production chauffe-eau | `input_number.seuil_production_chauffe_eau` | Seuil configurable (500→3000 W) — **n'est plus utilisé dans SIMU_OFF depuis 2026-04-22** |

**`sensor.chauffe_eau_opportunite_stats` — configuration YAML (`configuration.yaml`) :**

```yaml
- platform: statistics
  name: "chauffe_eau_opportunite_stats"
  entity_id: binary_sensor.lancement_chauffe_eau_opportun
  state_characteristic: mean
  max_age:
    minutes: 30
  sampling_size: 60
```

- Retourne la fraction du temps où `binary_sensor` = ON sur 30 min glissantes (0.0 = jamais ON, 1.0 = toujours ON)
- `unit_of_measurement: "%"` affiché par HA — **⚠️ vérifier si la valeur réelle est en 0–1 ou 0–100** : si 0–100, le seuil du trigger SIMU_OFF doit être corrigé de `0.40` à `40` via `ha_config_set_automation`.

**`sensor.solaire_stabilite_stats` — attributs utiles :**

- `age_coverage_ratio` : fraction de la fenêtre temporelle couverte. **Plage observée : 0.31 à 0.39** (médiane 0.33-0.34). Fix long terme : augmenter `sampling_size`.
- `buffer_usage_ratio` : toujours 1.0 (buffer plein structurellement).

**`binary_sensor.lancement_chauffe_eau_opportun` — attributs utiles :**

- `production_actuelle`, `stabilite`, `motif_blocage`
- Motifs observés : `"Production insuffisante (XXXW < 1500W)"`, `"Production instable - nuages (σ=XXXW)"`

### 2.3 ⚠️ Logique de seuil — mise à jour 2026-04-22

Depuis la refonte de l'automation SIMU_OFF (2026-04-22), **un seul seuil actif** pilote réellement l'arrêt :

1. **Seuil interne du `binary_sensor.lancement_chauffe_eau_opportun` = 1500 W** (codé en dur).
2. **Seuil de fiabilité = 40%** : si le taux d'opp=1 sur 30 min glissantes est < 40% pendant 10 min consécutives → SIMU_OFF.
3. **`input_number.seuil_production_chauffe_eau`** (500 W actuel) : **n'est plus utilisé dans SIMU_OFF**. Conservé mais inactif.

### 2.4 Automations SIMU

| Automation | entity_id | unique_id | État |
|---|---|---|---|
| 🌞 SIMU — Allumer | `automation.simu_allumer_chauffe_eau_si_solaire_favorable` | `simu_chauffe_eau_on` | actif |
| ⛅ SIMU — Éteindre | `automation.simu_eteindre_chauffe_eau_si_solaire_insuffisant` | `simu_chauffe_eau_off` | actif |

#### 🌞 SIMU — Allumer (`simu_chauffe_eau_on`)

- **Trigger** : `binary_sensor.lancement_chauffe_eau_opportun` → ON depuis **10 min**
- **Conditions** : Entre sunrise/sunset, `age_coverage_ratio ≥ 0.25`, capteurs dispos
- **Actions** : `input_boolean.simulation_chauffe_eau_solaire` → ON + notification persistante

#### ⛅ SIMU — Éteindre (`simu_chauffe_eau_off`) — refonte 2026-04-22

- **Trigger** : `numeric_state` sur `sensor.chauffe_eau_opportunite_stats` **< 0.40** depuis **10 min**
- **Conditions** : Entre sunrise/sunset, capteurs dispos, `input_boolean.simulation_chauffe_eau_solaire` = on
- **Actions** : `input_boolean.simulation_chauffe_eau_solaire` → OFF + notification persistante
- **config_hash actuel** : `7f4bcfef3029a7b4`

### 2.5 Dashboard — carte Chauffe-eau solaire

- **Type** : `custom:button-card` sur `input_boolean.simulation_chauffe_eau_solaire`
- **Label affiché** : `{prod} W · σ={sigma} W · fiab. {taux}%` + motif_blocage
- `fiab.` affiche `--` si le sensor est unavailable/unknown (normal la nuit ou après restart)

### 2.6 Export CSV hebdomadaire → Google Drive

| Champ | Valeur |
|---|---|
| Automation | `automation.export_csv_solaire_hebdomadaire_google_drive` |
| unique_id | `export_csv_solaire_hebdo_v2` |
| Trigger | Tous les jours à 00:05 |
| Condition | `now().weekday() == 0` (= lundi uniquement) |
| Actions | 1. `shell_command.export_solaire_csv` → 15s delay → 2. `shell_command.upload_solaire_gdrive` → 10s delay → 3. notification persistante |

**Format CSV (depuis 2026-05-10)** :
- Colonnes : `datetime;production_W` séparateur `;`
- `datetime` au format `YYYY-MM-DD HH:MM:SS` en **heure locale Europe/Paris**
- Les valeurs `unavailable`/`unknown` sont filtrées.

---

## 2bis. Projet Emporia — Export hebdo + Drive

> Objectif : déclencher chaque lundi l'export Emporia (mail avec lien ZIP) puis récupérer ce ZIP automatiquement et l'archiver sur Google Drive.
> **Statut** : ✅ déployé et validé end-to-end le 02/05/2026.

### 2bis.1 Architecture

```
Lundi 00:10 — automation #1 (export trigger)
  → script Python (auth Cognito + GET /devices/usage/export)
  → Emporia envoie un mail à compte-A avec lien Mandrill→S3 (ZIP)

Lundi 00:30 — automation #2 (fetch + upload)
  → script Python (Gmail API + Drive API)
  → cherche le mail no-reply@notification.emporiaenergy.com
  → suit le lien Mandrill, télécharge le ZIP
  → upload sur Drive folder Solaire
```

**Important** : 2 comptes Google distincts.
- **Compte A** = celui qui reçoit le mail Emporia (scope Gmail readonly)
- **Compte B** = celui qui possède le Drive cible (scope drive.file)
- Même `client_id` / `client_secret` OAuth pour les deux (un seul projet Google Cloud)

### 2bis.2 Fichiers Python

Tous dans `/config/python_scripts/emporia/` :

| Fichier | Rôle |
|---|---|
| `emporia_lib.py` | Auth AWS Cognito + appel `/devices/usage/export`. Stdlib only. |
| `google_lib.py` | Helpers OAuth Google + Gmail + Drive. Stdlib only. |
| `export_emporia_weekly.py` | Script Phase 2 — appelé par `shell_command.emporia_weekly_export`. |
| `fetch_emporia_to_drive.py` | Script Phase 3 — appelé par `shell_command.emporia_fetch_to_drive`. |
| `secrets_emporia.json` | Email/password Emporia + device_gid + drive_folder_id + tokens Cognito persistés. `chmod 600`. |

**Stdlib only** = pas de venv, pas de pip, pas de `docker exec`.

### 2bis.3 Secrets côté HA

| Fichier | Compte | Scope |
|---|---|---|
| `/config/secrets_gdrive_client_id` | (app OAuth) | — |
| `/config/secrets_gdrive_client_secret` | (app OAuth) | — |
| `/config/secrets_gdrive_refresh_token` | Compte B | `drive.file` |
| `/config/secrets_gmail_emporia_refresh_token` | Compte A | `gmail.readonly` |

**OAuth app status** : "In production" depuis 02/05/2026 → tokens permanents.

### 2bis.4 Automations

| Automation | entity_id | Trigger |
|---|---|---|
| 🔌 Emporia — Export hebdomadaire | `automation.emporia_export_hebdomadaire_par_e_mail` | Lundi 00:10 |
| 📥 Emporia — Récup mail + Upload Drive | `automation.emporia_recup_mail_upload_drive` | Lundi 00:30 |

### 2bis.5 Endpoint Emporia confirmé

```
GET https://api.emporiaenergy.com/devices/usage/export?deviceGid=328568&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD
Header: authtoken: <id_token Cognito>
→ 200 OK, body: {"result": "success"}
```

### 2bis.6 Cognito

- Region : `us-east-2` | Client ID : `4qte47jbstod8apnfic0bunmrq`
- Le `refresh_token` Cognito est persisté dans `secrets_emporia.json`.

### 2bis.7 Maintenance

- **Si `refresh_token` Gmail révoqué** → procédure dans `Emporia_csv/emporia/deploy/deploy_phase3.md` §2.
- **Si Cognito refresh_token révoqué** → script bascule auto sur login complet.
- **OAuth Google "invalid_grant"** → régénérer le refresh_token via la procédure deploy_phase3.md §2.

---

## 2ter. HMS-1600 — Micro-onduleur OpenDTU

> Micro-onduleur Hoymiles HMS-1600-4T installé à Beauvallon. Connecté à HA via OpenDTU + MQTT.

### 2ter.1 Matériel

| Paramètre | Valeur |
|---|---|
| Modèle | Hoymiles HMS-1600-4T (4 strings DC, monophasé AC) |
| Numéro de série | `116495202971` |
| Firmware onduleur | v1.0.27 (2023-06-05) |
| Puissance nominale | 1 600 W |
| Gateway | OpenDTU (firmware v26.3.30, ID `OpenDTU-4C9028`) |
| IP OpenDTU | `192.168.1.137` |
| Intégration HA | MQTT Discovery (broker `192.168.1.79:1883`, user `mqtt_user`, topic base `solar/`, intervalle 5 s) |

### 2ter.2 Entités clés

Deux familles d'entités coexistent : `opendtu_4c9028_*` (gateway OpenDTU) et `hms_1600_*` (onduleur via MQTT Discovery).

**Gateway OpenDTU (`opendtu_4c9028_*`) :**

| Entité | entity_id | Notes |
|---|---|---|
| Puissance AC | `sensor.opendtu_4c9028_ac_power` | W — utilisée par l'écrêteur (trigger puissance) |
| Puissance DC | `sensor.opendtu_4c9028_dc_power` | W |
| Énergie du jour | `sensor.opendtu_4c9028_yield_day` | Wh |
| Énergie totale | `sensor.opendtu_4c9028_yield_total` | kWh |
| Statut gateway | `binary_sensor.opendtu_4c9028_status` | on = connecté |

**Onduleur HMS-1600 (`hms_1600_*`) :**

| Entité | entity_id | Notes |
|---|---|---|
| **Tension AC réseau** | **`sensor.hms_1600_voltage`** | **V — utilisée par l'écrêteur (trigger tension > 250V)** |
| Puissance AC | `sensor.hms_1600_power` | W |
| Courant AC | `sensor.hms_1600_current` | A |
| Fréquence | `sensor.hms_1600_frequency` | Hz |
| Température | `sensor.hms_1600_temperature` | °C |
| En production | `binary_sensor.hms_1600_producing` | on = produit |
| Joignable | `binary_sensor.hms_1600_reachable` | on = connecté |
| **Limite non-persistante** | **`number.hms_1600_limit_nonpersistent_absolute`** | **W — entité HA native, utilisée par l'écrêteur via `number.set_value`** |
| Limite persistante | `number.hms_1600_limit_persistent_absolute` | W |
| Restart inverter | `button.hms_1600_restart_inverter` | Redémarre l'onduleur (reset compteur d'attente post-trip) |
| Turn off/on | `button.hms_1600_turn_inverter_off/on` | Coupure/allumage manuel |

### 2ter.3 Grid Profile & seuils de trip

- **Profil** : `XX - NF_EN_50549-1:2019` (norme française/européenne, micro-générateurs ≤ 16A)
- **HV1** : 253 V pendant 3 s → trip (code événement Hoymiles ID 141 = Grid Overvoltage)
- **Reconnect Time** : 60 s (paramètre profil) — mais délai observé ~30 min (condition AHV 10 min + comportement firmware)
- **Redémarrage manuel** : bouton ON/OFF dans OpenDTU, ou `button.hms_1600_restart_inverter` depuis HA

### 2ter.4 Problème surtension — diagnostic

- Cause : injection élevée dans un réseau rural à haute impédance → tension locale monte au-dessus de 253 V
- Décrochages observés les 16-17/05/2026 : ID 141 confirmé dans le journal des événements OpenDTU
- **Seuil empirique sûr : 1 000 W** — au-delà, la tension dépasse 253 V → trip
- La limite MQTT est `nonpersistent` → perdue au redémarrage de l'onduleur/HA (géré par le trigger `homeassistant.start` de l'automation)
- **Long terme** : contacter Enedis (pics > 253 V hors tolérance EN 50160)

### 2ter.5 Automation écrêteur

| Champ | Valeur |
|---|---|
| entity_id | `automation.hms_1600_ecreteur_1100w_anti_surtension` *(slug figé — alias mis à jour)* |
| alias | "HMS-1600 — Écrêteur anti-surtension" |
| unique_id | `1779033898281` |
| config_hash | `9ee97c47804acd63` |
| Mode | `restart` |

**Logique (refonte 2026-05-31 - Option A) :**

| Déclencheur | Condition runtime | Séquence |
|---|---|---|
| `voltage > 250V` | voltage > 250V | → 800W → notif (10 min) → 1000W (10 min) → 1200W (10 min) → 1600W → dismiss notif |
| Démarrage HA | voltage > 250V | idem (rétablit la limite d'écrêtage si HA démarre pendant une surtension) |
| Démarrage HA | voltage <= 250V | Réinitialise la limite à 1600W (par défaut) et ferme la notification d'écrêtage |

**Points clés :**
- **Trigger tension uniquement** : seul `sensor.hms_1600_voltage > 250V` déclenche l'écrêteur.
- **Remontée progressive par paliers (Option A)** : après un écrêtage initial à 800 W pendant 10 min, la limite remonte par étapes (1000 W puis 1200 W toutes les 10 min de stabilité) avant de retrouver sa capacité nominale de 1600 W.
- **Mode `restart`** : si la tension repasse > 250 V pendant n'importe quelle phase du cycle, l'automation redémarre instantanément la séquence à 800 W et réinitialise les minuteries.
- **Reset automatique au boot** : si HA redémarre et que la tension est basse, la limite est restaurée à 1600 W (évite de rester bloqué sur un écrêtage précédent).
- **Risque résiduel accepté** : après un trip de l'onduleur + reconnexion, l'onduleur repart librement jusqu'à ce que la tension atteigne 250V (quelques secondes à 5s d'intervalle MQTT). Le HV1 à 253V reste le filet ultime.

**Historique des incidents et évolution :**
- 2026-05-19 : trips surtension répétés → écrêteur initial créé (power-based, 1000W)
- 2026-05-22 : fix gap 800-850W (trigger above:799W sans debounce)
- 2026-05-24 : trip à 835W malgré limite 900W + tension 250.6V non détectée → refonte voltage+power, limite 800W, fix bug trip vs nuage
- 2026-05-25 : trop restrictif (écrêtage à 799W avec tension à 247V) → refonte finale : tension seule, 800W/10min/900W, mode restart

### 2ter.6 Dashboard 1.Mobile

- Bouton `button.hms_1600_restart_inverter` ajouté en bas de la section principale
- Positionné après les cartes "HMS-1600 Voltage" et "HMS-1600 Temperature"

### 2ter.7 Amélioration future — coordination avec SolarFlow (§2quater)

**Piste ouverte** : au lieu de simplement limiter le HMS à 1000 W, laisser le HMS produire à pleine puissance et utiliser le SolarFlow en mode entrée AC pour absorber l'excédent. L'injection nette (HMS − SolarFlow) resterait ≤ 1000 W sans gaspiller la production. À tester manuellement avant d'automatiser.

### 2ter.8 Dashboard 1.Mobile — carte Écrêteur

- **Type** : `custom:button-card` associée à `automation.hms_1600_ecreteur_1100w_anti_surtension`
- **Mise en page** : Insérée dans le dashboard **1.Mobile** (`dashboard-mobile`), juste après la carte "Restart Inverter".
- **Nom dynamique** : Affiche `Écrêteur ⚠️ ACTIF` uniquement si la limite actuelle est inférieure à 1600 W, `Écrêteur (Surveillance)` si l'automatisation est active mais qu'aucun bridage n'est en cours, ou `Écrêteur ❌ ÉTEINT` si l'automatisation est désactivée.
- **Informations affichées** : Tension AC réseau (`sensor.hms_1600_voltage`), production instantanée (`sensor.hms_1600_power`), et statut exact de la limite (ex: `⚠️ LIMITE : 800 W` ou `✅ Inactif`).
- **Couleurs dynamiques** : Fond orange/rouge et bordure rouge épaisse si le bridage est actif. Fond vert et bordure fine verte en veille (surveillance). Fond gris si l'automatisation est désactivée.
- **Contrôle en 1 clic** : Le clic (tap action) ouvre les détails de l'automatisation, permettant de l'activer ou la désactiver manuellement.

---

## 2quater. SolarFlow 800 Plus — Batterie Zendure

> Batterie solaire Zendure SolarFlow 800 Plus intégrée à HA le 18/05/2026.
> Voir [zendure-entities-reference.md](file:///c:/Users/kriko/Cowork/HA_Automatisations/zendure-entities-reference.md) pour la liste exhaustive et l'explication détaillée de l'utilité de chaque entité.

### 2quater.1 Intégration

| Paramètre | Valeur |
|---|---|
| Intégration HACS | "Zendure Home Assistant Integration" (fireson, v1.3.1) |
| Téléchargements | ~8 000 (référence communautaire) |
| Entités créées | 59 entités automatiques après redémarrage HA |

### 2quater.2 Entités clés

| Entité | entity_id | Type | Notes |
|---|---|---|---|
| Niveau batterie (SOC) | `sensor.solarflow_800_plus_electric_level` | sensor | % |
| Puissance batterie | `sensor.solarflow_800_plus_bat_in_out` | sensor | W — négatif = charge, positif = décharge |
| Température | `sensor.solarflow_800_plus_hyper_tmp` | sensor | °C |
| Mode AC | `select.solarflow_800_plus_ac_mode` | select | "Mode entrée AC" / "Mode sortie AC" — **piloté automatiquement** (ne pas toucher manuellement) |
| Limite d'entrée (charge) | `number.solarflow_800_plus_input_limit` | number | 0–1000 W — Consigne transitoire (écrasée par HEMS Cloud). |
| Limite de sortie (décharge) | `number.solarflow_800_plus_output_limit` | number | 0–800 W — Consigne transitoire (écrasée par HEMS Cloud). |
| Limite physique de charge | `number.solarflow_800_plus_charge_max_limit` | number | Plafond matériel de charge (0–1200 W). Utilisé pour l'écrêtage thermique. |
| Limite physique de décharge | `number.solarflow_800_plus_inverse_max_power` | number | Plafond matériel de décharge (0–1200 W). Utilisé pour l'écrêtage thermique. |

### 2quater.3 Helpers de contrôle (interface utilisateur)

| Helper | entity_id | Options | Rôle |
|---|---|---|---|
| Limite charge | `input_select.solarflow_limite_charge` | 0 W … 1000 W (pas 100 W) | Dropdown charge — source de vérité UI |
| Limite décharge | `input_select.solarflow_limite_decharge` | 0 W … 800 W (pas 100 W) | Dropdown décharge — source de vérité UI |

**Ne jamais écrire directement sur `number.solarflow_800_plus_charge_max_limit` / `inverse_max_power`** depuis le dashboard — passer toujours par les `input_select`.

### 2quater.4 Automations de contrôle

| Automation | entity_id | config_hash | Logique |
|---|---|---|---|
| Sync limite charge | `automation.solarflow_sync_limite_charge` | — | Select charge → `input_limit` (consigne transitoire). Si > 0 : mode `"input"` + décharge forcée à 0 W. **Ne touche plus aux plafonds de sécurité.** |
| Sync limite décharge | `automation.solarflow_sync_limite_decharge` | — | Select décharge → `output_limit` (consigne transitoire). Si > 0 : mode `"output"` + charge forcée à 0 W. **Ne touche plus aux plafonds de sécurité.** |
| Alerte température | `automation.solarflow_alerte_temperature_elevee` | — | > 45 °C pendant 2 min → notif persistante. Dismiss auto < 42 °C (hystérésis 3 °C) |
| Écrêteur temp. (charge) | `automation.solarflow_ecreteur_temperature_batterie` | `1779624839201` | Régule **exclusivement** le plafond `charge_max_limit` (700W/300W/100W) selon la température (47/49/51 °C). Notif + Hystérésis 5 min. |
| Écrêteur temp. (décharge) | `automation.solarflow_ecreteur_temperature_batterie_decharge` | `1779624839202` | Régule **exclusivement** le plafond `inverse_max_power` (600W/300W/100W) selon la température (47/49/51 °C). Notif + Hystérésis 5 min. |

> [!IMPORTANT]
> **Séparation des responsabilités critique** : Les sync écrivent sur les consignes transitoires (`input_limit`/`output_limit`), les écrêteurs thermiques écrivent **uniquement** sur les plafonds matériels (`charge_max_limit`/`inverse_max_power`). Ne jamais mélanger ces deux niveaux sous peine de verrouillage à 0 W.

**⚠️ Valeurs du `select.solarflow_800_plus_ac_mode`** : l'intégration Zendure utilise `"input"` et `"output"` (pas de labels français). Si les commandes du dashboard cessent de fonctionner après une mise à jour HACS, vérifier en premier que ces valeurs n'ont pas changé :
```
ha_get_state("select.solarflow_800_plus_ac_mode") → attributes.options
```
ou via Developer Tools → Template : `{{ state_attr('select.solarflow_800_plus_ac_mode', 'options') }}`

**Exclusion mutuelle** : fixer charge > 0 force décharge à 0 et vice-versa. Pas de boucle infinie : quand l'un remet l'autre à 0, la condition `> 0` n'est pas vérifiée donc pas de retour.

**Bascule mode automatique** : le mode AC (`select.solarflow_800_plus_ac_mode`) est géré exclusivement par les automations — ne jamais le modifier manuellement depuis le dashboard.

### 2quater.5 Dashboard Aperçu — carte SolarFlow (carte n°9)

Structure `vertical-stack` actuelle (5 lignes) :

```
## ⚡ SolarFlow 800 Plus
[Batterie %] [Puissance W] [Temp. SolarFlow] [Temp. Batterie]
🔋 Charge (0–1000 W)    [ 400 W ▼ ]
🔋 Décharge (0–800 W)   [ 200 W ▼ ]
```

Le bloc "Mode de fonctionnement" a été supprimé — le mode est géré automatiquement par les automations.

### 2quater.6 Automations futures à créer

- **Décharge automatique au coucher du soleil** : quand production < 100 W + SOC > 20% → décharge select à une valeur configurable (récupère le soir ce qui a été stocké le jour).
- **Coordination écrêteur HMS** : voir §2ter.7.

### 2quater.7 Suivi de rentabilité (Tempo)

- **Capteur de prix** : `sensor.edf_tempo_prices` stocke les tarifs EDF Tempo dans ses attributs (évite les répétitions et centralise la configuration) :
  - `hc_bleu` = 0.1325 €, `hp_bleu` = 0.1612 €
  - `hc_blanc` = 0.1499 €, `hp_blanc` = 0.1871 €
  - `hc_rouge` = 0.1575 €, `hp_rouge` = 0.7060 €
- **Ventilation de la décharge** : `utility_meter.solarflow_discharge_by_tariff` (source `sensor.solarflow_800_plus_aggr_discharge`) répartit la décharge de la batterie dans 6 sous-registres.
- **Synchronisation du tarif** : `automation.solarflow_synchronisation_tarif_decharge` écoute les variations du tarif Tempo (`sensor.leexi_current_price`) et bascule le tarif du compteur de décharge.
- **Économies totales** : `sensor.solarflow_discharge_cost_saved_total` fait la somme pondérée par tarif des kWh déchargés pour calculer l'économie totale en €.
- **Cumuls temporels** : 4 utility meters dérivés suivent la rentabilité sur différentes périodes :
  - Jour : `sensor.solarflow_discharge_cost_saved_daily`
  - Semaine : `sensor.solarflow_discharge_cost_saved_weekly`
  - Mois : `sensor.solarflow_discharge_cost_saved_monthly`
  - Année : `sensor.solarflow_discharge_cost_saved_yearly`
- **Dashboard** : affichage dans le dashboard "Énergie détail" (`lovelace.energie-detail`) avec une carte verticale principale (total économisé) et une grille à 4 colonnes pour le Jour, Semaine, Mois, Année.

---

## 3. Automations clés

Les automations HA se répartissent en familles :

- **Solaire/chauffe-eau** : §2.4 et §2.6
- **Emporia** : §2bis.4
- **HMS-1600 écrêteur** : §2ter.5 (`automation.hms_1600_ecreteur_1100w_anti_surtension` — alias "800W anti-surtension")
- **SolarFlow contrôle** : §2quater.4 et §2quater.7 (`automation.solarflow_sync_limite_charge`, `automation.solarflow_sync_limite_decharge`, `automation.solarflow_alerte_temperature_elevee`, `automation.solarflow_synchronisation_tarif_decharge`)
- **Santé système (auto-heal)** : §3.bis (🔧 Auto-heal Tado)
- **Programmation/Minuterie switches Aperçu** : §3.ter
- **Cast Nest Hub Cuisine** : §3quater (`script.cast_apercu_cuisine`, `script.cast_energie_cuisine`)
- **Éclairage** : `lumiere_hall_atelier`, `lumiere_auto_atelier`, `lumiere_auto_hall_cine`, `lumiere_auto_cine`, `lumiere_auto_porte`, `inter_lumiere_exterieur`, `lumiere_porte_desactivation_auto`, `lumiere_toilette_auto`, `netatmo_lumiere_exterieur`, `inter_lumiere_cine`
- **Divers** : `extinction`, `wakeonlan`, `test_ha_dethalatelier`, `fin_cycle_chauffe_eau_cuisine`, `pc_bureau_ecrans_on_apres_arret_ha`, `webhooks_lustre`, `inter_portail`

Pour la liste exacte et à jour : `ha_search_entities(query="", domain_filter="automation")`.

### 3.bis 🔧 Auto-heal Tado

| Champ | Valeur |
|---|---|
| Automation | `automation.auto_heal_tado` |
| unique_id | `1776721574868` |
| Mode | `single` |
| Trigger 1 | `climate.salon` OU `climate.chambres` → `unavailable` depuis **15 min** |
| Trigger 2 | `time_pattern minutes: "/15"` |
| Condition globale | `climate.salon` OR `climate.chambres` est `unavailable` |
| Action 1 | `homeassistant.reload_config_entry` avec `entry_id: 01KR406D3HNSDFXENFP3TKN9AX` |
| Attente | **15 min** |
| Action 2 (conditionnelle) | Si `climate.salon` toujours unavailable → `persistent_notification.create` (id: `tado_auto_heal_failed`) |
| config_hash actuel | `e78bc42a2c1c0940` |

**Maintenance :** si entry_id Tado change (delete+re-add) → mettre à jour ici ET dans §5.3.

### 3.ter 🎛 Programmation hebdo + Minuterie — switches Aperçu

> **Statut** : ✅ déployé end-to-end le 2026-05-14.

#### 3.ter.1 Architecture

- **Programmation hebdo** : intégration HACS *Scheduler* (`nielsfaber/scheduler-component`) → entités `switch.schedule_*`
- **Minuterie indépendante** : helper `timer` + `input_number` (durée) + script + 2 automations par switch
- **Override** : la minuterie ignore le planning pendant qu'elle tourne.

#### 3.ter.2 Entités créées

| Switch | Timer | input_number | Script |
|---|---|---|---|
| `switch.chauffe_eau_cuisine` | `timer.minuterie_chauffe_eau_cuisine` | `input_number.duree_custom_chauffe_eau_cuisine` | `script.lancer_minuterie_chauffe_eau_cuisine` |
| `switch.0x00124b0024c79699` *(principal)* | `timer.minuterie_chauffe_eau_principal` | `input_number.duree_custom_chauffe_eau_principal` | `script.lancer_minuterie_chauffe_eau_principal` |
| `switch.pompe_piscine_zigbee` *(piscine)* | `timer.minuterie_pompe_piscine` | `input_number.duree_custom_pompe_piscine` | `script.lancer_minuterie_pompe_piscine` |

**Sensors de consommation des 3 switches :**

| Switch | Sensor puissance (W) | Sensor énergie (kWh cumul.) | Baseline cycle |
|---|---|---|---|
| Chauffe-eau cuisine | — | `sensor.chauffe_eau_cuisine` (Wh total) | `input_number.chauffe_eau_cuisine_wh_debut_de_cycle` |
| Chauffe-eau principal | `sensor.puissance_chauffe_eau_principal` (W) | — (estimé × durée) | `input_number.chauffe_eau_principal_timestamp_debut_de_cycle` (Unix ts) |
| Pompe piscine | `sensor.pompe_piscine_ph3_3_1min` (W, avg 1 min) | `sensor.pompe_piscine` (kWh cumul., source `ph3_3_1min`) | Pas de baseline — kWh estimés via puissance × durée |

#### 3.ter.3 Dashboard Aperçu V4 (version actuelle)

- 3 cartes `tile` natives sur vue Home, chacune avec `navigation_path: /lovelace/programmation_<slug>`
- 3 sous-vues unitaires (`subview: true`) : `programmation_cuisine`, `programmation_principal`, `programmation_piscine`
- **Cartes `conditional` + `markdown` ajoutées dans chaque sous-vue** (2026-05-22) : affichées uniquement quand le switch est ON, montrent le temps d'activation (depuis `last_changed`) et la consommation estimée du cycle en cours
- Backup : `dashboard_backup/aperçu_v4_subviews_unitaires_*.json`

#### 3.ter.4 Dépendances HACS

| Repo | Rôle | Config entry_id |
|---|---|---|
| `nielsfaber/scheduler-component` | Moteur planning | `01KRJVP5399M8C4VXGR6659HPM` |
| `nielsfaber/scheduler-card` | UI planning | — |
| `thomasloven/hass-browser_mod` | Inutilisé (laissé installé) | `01KRJVPK5FT72J16MC98AWEV69` |

---

## 3quater. Cast vers Nest Hub Cuisine

> Objectif : envoyer à la demande un dashboard HA sur le Google Nest Hub de la cuisine.
> **Statut** : ✅ scripts déployés le 2026-05-22. Commandes vocales Google Home à configurer ultérieurement (§7.6).

### Entités Cast

| Entité | entity_id | État | Notes |
|---|---|---|---|
| **Hub Cuisine** | `media_player.cuisine` | `off` (joignable) | **C'est le bon Hub cible** — plateforme `cast` |
| Hub générique | `media_player.google_hub` | `unavailable` | Ancienne entrée — voir §5.1 |

### Scripts de cast

| Script | entity_id | Cible | Dashboard |
|---|---|---|---|
| Cast Aperçu | `script.cast_apercu_cuisine` | `media_player.cuisine` | `lovelace` (Aperçu) — vue 0 |
| Cast Énergie | `script.cast_energie_cuisine` | `media_player.cuisine` | `energie-detail` — vue 0 |

### Déclenchement

- **Boutons dashboard Aperçu** : bloc "📺 Envoyer sur Cuisine Hub" en bas de la vue principale (`config_hash lovelace : 1c1cb47bac0d00fe`)
- **Commandes vocales** : non encore configurées — procédure complète en §7.6

### ⚠️ Limitations connues

- Le Hub peut quitter l'affichage du dashboard si une interaction vocale ou un minuteur intervient (comportement natif Google, pas de verrou possible sans affichage permanent)
- Pour un affichage permanent / rotation automatique, créer une automation avec trigger périodique appelant les scripts (à faire si besoin)

---

## 4. Intégrations & add-ons

### Protocoles / intégrations actifs

Zigbee (ZHA ou Z2M), Z-Wave JS, Matter, Philips Hue, Broadlink RM Pro, Harmony Hub, Tado, Arlo / Aarlo, Google AI (conversation, TTS, STT, tasks), NVIDIA Shield, KEF LS50 Wireless, Samsung (mobiles), Foobot, Emporia Vue, **Zendure (SolarFlow 800 Plus, HACS fireson v1.3.1)**.

**Intégrations désactivées :**
- **Harmony Hub 3** (`192.168.1.42`) — désactivée le 2026-05-22 (1804+ erreurs OSError 113, appareil inaccessible)
- **Pronote** (3 entrées : Arthur, Mathieu, Raphaël) — désactivées le 2026-05-22 (`NoneType object is not subscriptable`, intégration cassée)

### Intégrations MQTT / OpenDTU

- **OpenDTU** : gateway HMS-1600, MQTT Discovery activé, topic base `solar/`, broker `192.168.1.79:1883`
- Entités préfixées `opendtu_4c9028_*` (voir §2ter.2)

### Zones / pièces

Salon, Bureau, Cuisine, Salle à manger, Chambres (parentale, Arthur, jumeaux, Raphaël, Mathieu), Hall d'entrée, Atelier, Hall Atelier, Hall Ciné, Salle Ciné, Extérieur, Porte d'entrée, Energie, Sous-sol. Total 28 pièces.

### Add-ons installés

Samba, Studio Code Server, Terminal & SSH, Z-Wave JS, Silicon Labs Multiprotocol, Matter Server, DuckDNS, NGINX SSL, ESPHome, RPC Shutdown, File Editor, Zigbee2MQTT, Mosquitto, Matterbridge.

### Plateformes YAML conservées dans `configuration.yaml`

Foobot, Statistics, Wake-on-LAN, KEF. *(Bloc `aarlo:` commenté.)*

---

## 5. Santé système

### 5.1 Ouverts (à traiter)

| Problème | Domaine | Priorité | Notes |
|---|---|---|---|
| Collision d'identifiants Z-Wave (nœud 3761196044) | zwave_js | Moyenne | Plusieurs entités doublonnées. ERROR au boot. Repair actif. |
| Réauthentification Tado instable (récurrent) | tado | Basse (géré) | Auto-heal actif §3.bis. |
| `media_player.google_hub` unavailable | cast | Très basse | Ancienne entrée Cast non résolue. Le Hub actif est `media_player.cuisine`. Peut être supprimée si non utilisée. |
| Chromecast : plusieurs IPs inaccessibles | pychromecast | Basse | 192.168.1.10, .19, .24, .50. À vérifier réseau. |
| **Emporia Vue timeouts API** | emporia_vue (custom) | Basse | Analyse 10 jours (2026-05-12→22) : 4 événements sporadiques + 1 vague DNS le 2026-05-21 à 13h19 (Paris) — probablement résolution DNS intermittente. Voir logs `/config/python_scripts/emporia/logs/`. |
| **`sensor.chauffe_eau_opportunite_stats` : vérifier unité** | statistics | **À vérifier** | Si valeur 0–100, corriger trigger SIMU_OFF : `below: 0.40` → `below: 40` |
| **Surtension réseau HMS-1600** | réseau EDF | Moyenne | Contacter Enedis. Pics > 253 V hors tolérance EN 50160. Géré temporairement par l'écrêteur §2ter.5. |

### 5.2 Résolus récents

| Problème | Résolution | Date |
|---|---|---|
| Templates helpers `puissance_edf`, `puissance_phase1/2/3` cassaient sur `unknown`/`unavailable` | Fix `\|float` → `\|float(0)` dans les 4 helpers via `ha_config_set_helper`. Entry IDs dans §5.3. | 2026-05-22 |
| Harmony Hub 3 (192.168.1.42) — 1804+ erreurs OSError 113 | Intégration désactivée via MCP (`ha_set_integration_enabled`). | 2026-05-22 |
| Pronote — 3 intégrations en erreur (`NoneType...`) | 3 intégrations désactivées via MCP (Arthur, Mathieu, Raphaël). | 2026-05-22 |
| HMS-1600 écrêteur — gap démarrage (zone 800–850 W sans limite) | Condition `above: 850` → `above: 799` + notification conditionnelle si > 850 W. Config_hash : `dd09da9dfc6cbac4`. | 2026-05-22 |
| SolarFlow commandes charge/décharge inactives | Options `select.solarflow_800_plus_ac_mode` changées par mise à jour Zendure (`"Mode entrée AC"` → `"input"`, `"Mode sortie AC"` → `"output"`). Automations sync corrigées (§2quater.4). | 2026-05-20 |
| HMS-1600 trips surtension | Écrêteur automation 900W, trigger 850W sans debounce (§2ter.5) | 2026-05-19 |
| OAuth Google refresh_token expiré | App publiée "In Production" + tokens régénérés | 2026-05-02 |
| `pip3` absent du shell core-ssh | Bypass : projet Emporia stdlib uniquement | 2026-05-02 |
| SIMU_OFF ne s'arrêtait jamais | Refonte trigger §2.4 | 2026-04-22 |

### 5.3 Rappels utiles

- **Tado en erreur manuellement** : `ha_call_service("homeassistant", "reload_config_entry", data={"entry_id": "01KR406D3HNSDFXENFP3TKN9AX"})`.
- **Tado OAuth en boucle d'échec** : delete config entry + re-add depuis l'UI.
- **Arlo Cloudflare 429** : `ssh hass "rm /config/.aarlo/session.pickle"` + redémarrer HA.
- **OAuth Google "invalid_grant"** : régénérer le refresh_token via deploy_phase3.md §2.
- **HMS-1600 trip surtension** : utiliser `button.hms_1600_restart_inverter` depuis HA ou le bouton ON/OFF dans l'UI OpenDTU (`192.168.1.137`).
- **Template helpers puissance** — entry IDs (pour `ha_config_set_helper`) :
  - `sensor.puissance_edf` → `36ace9b639d8c8777599a5817f443f2f`
  - `sensor.puissance_phase1` → `67ef3c2723d243f1c6086e198012bfa8`
  - `sensor.puissance_phase2` → `bf0b0767a57d26a6c1b5a877d2fd79da`
  - `sensor.puissance_phase3` → `11f7e4e466ce3fa5dc49d215d85ce71b`

---

## 6. Bibliothèque de données solaires

Tous les CSV dans `/config/claude_data/` côté HA.

### Convention de nommage

`solaire_AAAAMMJJ_[type_ciel].csv`

| Code type ciel | Description |
|---|---|
| `ensoleille` | Journée claire, production stable et haute |
| `nuageux_eclaircies` | Alternance nuages/soleil, σ élevé, production variable |
| `couvert` | Couverture nuageuse totale, production faible et stable |
| `pluvieux` | Production quasi nulle |
| `hivernal` | Production faible (angle solaire bas) |
| `mixte_matin` | Clair le matin, nuageux l'après-midi |
| `mixte_apresmidi` | Nuageux le matin, clair l'après-midi |

### Structure CSV

- **Colonnes** : `timestamp` (ISO 8601 Paris), `production_w`, `sigma_w`, `age_coverage_ratio`, `chauffe_eau_opportun` (0/1), `production_moins_sigma`
- **Résolution** : 1 min, de 06:00 à 20:00 heure Paris

### Index fichiers

| Fichier | Date | Type | Prod max | Prod moyenne |
|---|---|---|---|---|
| `solaire_20260420_nuageux_eclaircies.csv` | 2026-04-20 | Nuageux éclaircies | 3073 W | 1392 W |

### Script de simulation offline — `simu_chauffe_eau_replay.py`

**⚠️ À mettre à jour** pour refléter le trigger SIMU_OFF duty cycle (fenêtre 30 min, taux < 40% pendant 10 min).

---

## 7. Workflow & commandes utiles

### 7.1 Ordre des outils (règle d'or)

1. `ha-mcp` natif d'abord
2. SSH de Krikor en fallback
3. Chrome/Comet jamais sauf dernier recours
4. Écriture dans `/config` : passer par outputs + copie SSH

### 7.2 Commandes SSH utiles (depuis PowerShell)

```powershell
# Copie du fichier de contexte
scp "$env:USERPROFILE\Cowork\HA_Automatisations\claude-hass-preferences.md" hass:/config/claude-hass-preferences.md

# Copie d'un CSV solaire
scp "$env:USERPROFILE\Downloads\solaire_20260420_nuageux_eclaircies.csv" hass:/config/claude_data/

# Redémarrer HA
ssh hass "ha core restart"

# Réinitialiser session Arlo
ssh hass "rm /config/.aarlo/session.pickle"

# Lister les CSV solaires
ssh hass "ls -la /config/claude_data/"

# --- Emporia ---
ssh hass "cd /config/python_scripts/emporia && python3 export_emporia_weekly.py"
ssh hass "cd /config/python_scripts/emporia && python3 fetch_emporia_to_drive.py"
ssh hass "tail -30 /config/python_scripts/emporia/logs/weekly_*.log | tail -30"

# Rafraîchir le code Emporia
scp "$env:USERPROFILE\Cowork\Emporia_csv\emporia\*.py" hass:/config/python_scripts/emporia/

# --- HMS-1600 ---
# Voir les logs OpenDTU (si SSH vers le gateway OpenDTU disponible)
# Envoyer une limite manuellement (test) :
# ssh hass "mosquitto_pub -h 192.168.1.79 -u mqtt_user -P <pwd> -t solar/116495202971/cmd/limit_nonpersistent_absolute -m 1000"
```

### 7.6 Procédure — Commandes vocales Google Home (sans Nabu Casa)

> À faire quand Krikor est prêt. Durée estimée : ~45 min.

**Prérequis** : accès à [console.cloud.google.com](https://console.cloud.google.com) et [console.home.google.com](https://console.home.google.com).

1. **Google Cloud Console** → Créer un projet → Activer l'**API HomeGraph** → Créer un compte de service → Télécharger la clé JSON → Copier dans `/config/google_service_account.json` → Créer des identifiants OAuth (type "Application Web", redirect URI : `https://triko26.duckdns.org/auth/external/callback`)
2. **Google Home Developer Console** → Nouveau projet → Add cloud-to-cloud integration → Renseigner Authorization URL (`https://triko26.duckdns.org/auth/authorize`), Token URL (`https://triko26.duckdns.org/auth/token`), Client ID/Secret → Mode Test
3. **`configuration.yaml`** : ajouter bloc `google_assistant:` avec `project_id`, `service_account: !include google_service_account.json`, `report_state: true`, exposer `script.cast_apercu_cuisine` (name: "Cast Aperçu") et `script.cast_energie_cuisine` (name: "Cast Énergie") → Redémarrer HA
4. **App Google Home** → + → Configurer un appareil → Fonctionne avec Google → lier le projet → HA apparaît
5. **Commandes vocales** : "OK Google, active Cast Aperçu" / "OK Google, active Cast Énergie"

### 7.7 Skill de gestion HA (ha_tool.py)

Un skill personnalisé `home-assistant-management` est disponible localement :
- **Documentation** : [SKILL.md](file:///C:/Users/kriko/.gemini/config/skills/home-assistant-management/SKILL.md)
- **Script CLI** : `ha_tool.py` (interagit via REST/WebSocket API en utilisant le fichier `.env` local).

**Commandes courantes** :
- Récupérer état : `python "C:\Users\kriko\.gemini\config\skills\home-assistant-management\scripts\ha_tool.py" get-state <entity_id>`
- Télécharger dashboard : `python "C:\Users\kriko\.gemini\config\skills\home-assistant-management\scripts\ha_tool.py" download-dashboard <lovelace_key> --output <local_file.json>`
- Téléverser dashboard (Mise à jour à chaud) : `python "C:\Users\kriko\.gemini\config\skills\home-assistant-management\scripts\ha_tool.py" upload-dashboard <lovelace_key> --input <local_file.json>`
- Vérifier config : `python "C:\Users\kriko\.gemini\config\skills\home-assistant-management\scripts\ha_tool.py" check-config`

### 7.3 Protocole "mets à jour le fichier de contexte"

1. Claude produit la nouvelle version dans `C:\Users\krikor\Cowork\HA_Automatisations\claude-hass-preferences.md`.
2. Claude ajoute une entrée au Changelog §9.
3. Claude fournit la commande SSH de copie vers `/config/`.
4. Krikor exécute depuis PowerShell.

### 7.4 Protocole "simulation offline"

1. Récupérer un CSV de `/config/claude_data/`.
2. Lancer `simu_chauffe_eau_replay.py` (⚠️ mettre à jour `simulate()` si la logique a changé).
3. Valider sur 2+ journées avant déploiement.

### 7.5 Protocole "snapshot HA"

À la demande, Claude appelle `ha_get_overview` — pas besoin de toucher au fichier.

---

## 8. Snapshot HA (volatile — à rafraîchir à la demande)

> ⚠️ Ces valeurs sont une photo datée. Pour l'exact, appeler `ha_get_overview()`.

| Paramètre | Valeur au 2026-05-14 |
|---|---|
| Version core | 2026.5.1 |
| HAOS | 17.2 |
| Total entités | ~980 (919 au 2026-05-14 + ~59 SolarFlow + nouveaux HMS) |
| Automations | ~36 actives (+1 écrêteur HMS) |
| Repairs actifs | 2 (Z-Wave collision, Tado reauth) |

---

## 9. Changelog

### 2026-06-17 v16

- 🐛 **Fix critique : verrouillage 0 W des plafonds SolarFlow** : Les automations `Sync limite charge` et `Sync limite décharge` écrasaient les plafonds matériels (`charge_max_limit` / `inverse_max_power`) à 0 W via `min(consigne_user, limite_thermique)` quand l'exclusion mutuelle mettait les `input_select` à 0 W. Correction : les sync écrivent désormais sur les consignes transitoires (`input_limit` / `output_limit`) uniquement. Les plafonds de sécurité sont gérés **exclusivement** par les écrêteurs thermiques.

### 2026-06-16 v15

- 🛠 **Découplage Consigne Utilisateur / Écrêteurs Thermiques SolarFlow** : Modification de `automation.solarflow_ecreteur_temperature_batterie` et `automation.solarflow_ecreteur_temperature_batterie_decharge` pour qu'elles appliquent strictement les limites physiques absolues (`charge_max_limit` et `inverse_max_power`) basées sur la température, sans faire de calcul de minimum avec les consignes des `input_select` utilisateur. Cela empêche le verrouillage à 0 W causé par l'exclusion mutuelle des modes charge et décharge.

### 2026-06-13 v14

- 🛠 **Correction de l'Écrêtage Thermique SolarFlow** : Exposition de `inverseMaxPower` (plafond de décharge) et `chargeMaxLimit` (plafond de charge) comme entités `ZendureNumber` éditables pour contourner la réécriture continue du HEMS Cloud.
- 🛠 **Mises à jour des Automations** : Mise à jour de `automation.solarflow_sync_limite_charge`, `automation.solarflow_sync_limite_decharge`, `automation.solarflow_ecreteur_temperature_batterie` et `automation.solarflow_ecreteur_temperature_batterie_decharge` pour cibler ces nouvelles entités `number` au lieu des consignes transitoires (`input_limit` / `output_limit`).
- 🆕 **Amélioration du Skill Home Assistant** : Ajout du subcommand `call-service` à `ha_tool.py` permettant d'appeler des services à chaud avec des payloads JSON depuis la ligne de commande.

### 2026-06-13 v13

- 🛠 **Correction du Dashboard Énergie** : Prise en compte du retrait de `sensor.beauvallon_mainstogrid_1d` de l'export réseau de la connexion `@Bleu_HC` afin que les calculs de coût de grille se basent sur les imports réels uniquement.
- 🆕 **Dashboard 2.Energie Détail — Graphique d'export** : Remplacement de la simple carte historique de l'export par un graphique à colonnes (`custom:apexcharts-card`) sur les 10 derniers jours avec affichage direct des valeurs quotidiennes en kWh via `datalabels`.
- 🛠 **Dashboard 2.Energie Détail — Sankey Chart** : Réorganisation complète de la première carte pour aligner toutes les sources (EDF, Power_1400W, Power_800W, Power_300W et Batterie Décharge) dans la même colonne de gauche (première section). Le flux de charge de la batterie (`sensor.solarflow_800_plus_output_pack_power`) a été branché comme récepteur direct du surplus des trois kits solaires uniquement (bypassant la consommation générale et le réseau grid).

### 2026-06-13 v12

- 🆕 **Écrêteur thermique SolarFlow 800+ (Charge & Décharge)** : Mise en place d'une régulation automatique et progressive des puissances maximales de charge et de décharge en fonction de la température de l'appareil (`sensor.solarflow_800_plus_hyper_tmp`).
  - **Paliers Charge** : 700 W max à 47 °C, 300 W max à 49 °C, 100 W max à 51 °C.
  - **Paliers Décharge** : 600 W max à 47 °C, 300 W max à 49 °C, 100 W max à 51 °C.
  - **Hystérésis** : Intégration d'une hystérésis temporelle de 5 minutes de stabilité sous le seuil lors de la redescente.
- 🛠 **Résolution des conflits d'écritures (Sync charge & décharge)** : Adaptation des automatisations `automation.solarflow_sync_limite_charge` et `automation.solarflow_sync_limite_decharge` pour calculer et appliquer le minimum entre la consigne utilisateur et le bridage thermique afin d'éviter toute concurrence MQTT.
- 🆕 **Notifications persistantes** : Ajout des notifications d'alertes `solarflow_ecretage_temp` et `solarflow_ecretage_temp_decharge` actives en cours de bridage thermique et fermées automatiquement après redescente sous 46 °C.

### 2026-05-31 v11

- 🛠 **Refonte écrêteur HMS-1600 (Option A)** : Mise en place d'une remontée progressive par paliers de 10 min (800 W ➔ 1000 W ➔ 1200 W ➔ 1600 W) avec maintien sécurisé par mode `restart`. Ajout de la réinitialisation automatique à 1600 W au démarrage de HA si la tension est normale. Config_hash : `9ee97c47804acd63`.
- 🆕 **Dashboard Aperçu** : Ajout d'une carte d'état dynamique de l'écrêteur (grille à 2 colonnes avec le Chauffe-eau solaire). Affiche en temps réel le statut (surveillance vs actif), la tension réseau, la production, et permet d'activer/désactiver le bridage en un clic.

### 2026-06-13 v11

- 🆕 **Suivi de rentabilité SolarFlow (Tempo)** :
  - Centralisation des tarifs EDF Tempo via `sensor.edf_tempo_prices` (HC/HP Bleu, Blanc, Rouge).
  - Ventilation de la décharge batterie par tarif via `utility_meter.solarflow_discharge_by_tariff` synchronisé via `automation.solarflow_synchronisation_tarif_decharge`.
  - Calcul et cumul des économies financières en € via `sensor.solarflow_discharge_cost_saved_total` et ses compteurs d'utilité Jour, Semaine, Mois, Année.
  - Déploiement d'une carte d'affichage dans le dashboard "Énergie détail" (`lovelace.energie-detail`) avec Mushroom Cards.

### 2026-05-28 v10

- 🆕 **Nouveau Skill HA** : Création et déploiement du skill [home-assistant-management](file:///C:/Users/kriko/.gemini/config/skills/home-assistant-management/SKILL.md) avec le script CLI `scripts/ha_tool.py` pour gérer de manière sécurisée et dynamique les entités, configurations et téléversements de dashboards à chaud.

### 2026-05-28 v9

- 🆕 **Documentation Zendure/SolarFlow** : Création de [zendure-entities-reference.md](file:///c:/Users/kriko/Cowork/HA_Automatisations/zendure-entities-reference.md) répertoriant l'utilité de chaque entité Zendure et SolarFlow après recherche et interrogation de l'API HA.
- 🆕 **Dashboard Aperçu** : Ajout du capteur de température de la batterie AB2000 (`sensor.ab2000_06618_max_temp`) dans la carte `glance` de la section SolarFlow, aux côtés de la température du SolarFlow (`sensor.solarflow_800_plus_hyper_tmp` renommée en "Temp. SolarFlow").

### 2026-05-25 v8

- 🛠 **Refonte finale écrêteur HMS-1600** : suppression du trigger puissance (trop restrictif — écrêtage à 799W alors que tension = 247V le 25/05). Nouvelle logique : `voltage > 250V` → 800W pendant 10 min (delay fixe) → 900W. Mode `restart` : si tension repasse > 250V pendant les 10 min, cycle repart. Retour à 900W (pas 1600W). Config_hash : `0a04db722440aa8c` → `b07d86c26e39f095`.

### 2026-05-24 v7

- 🛠 **Refonte écrêteur HMS-1600** (`automation.hms_1600_ecreteur_1100w_anti_surtension`, alias "800W anti-surtension") :
  - 🆕 **Trigger tension AC** : `sensor.hms_1600_voltage > 250V` déclenche l'écrêtage proactivement (3V avant le seuil HV1 de 253V). Trip du 24/05 analysé : survenu à 835W sous la limite de 900W — impédance réseau élevée, la puissance seule ne suffit pas.
  - 🐛 **Fix bug trip vs nuage** : quand power < 5W (trip onduleur), l'automation gardait 800W au lieu d'envoyer 1600W. L'ancien comportement causait une reconnexion à 1022W (rattrapée de justesse).
  - 🔽 **Limite abaissée 900W → 800W** : marge accrue sous le seuil de trip empirique observé (835W).
  - 🔧 **`number.set_value` remplace `mqtt.publish` brut** : entité HA native `number.hms_1600_limit_nonpersistent_absolute`.
  - 📌 **Entités `hms_1600_*` documentées** (§2ter.2) : `sensor.hms_1600_voltage`, `number.hms_1600_limit_nonpersistent_absolute`, `binary_sensor.hms_1600_producing`, etc.
  - Config_hash : `dd09da9dfc6cbac4` → `0a04db722440aa8c`

### 2026-05-22 v6

- 🛠 **Fix templates helpers puissance** : `|float` → `|float(0)` dans `sensor.puissance_edf`, `puissance_phase1/2/3` — plus d'erreurs `unknown`/`unavailable`. Entry IDs ajoutés en §5.3.
- 🗑 **Harmony Hub 3 désactivé** (`192.168.1.42`) : 1804+ erreurs OSError 113. Intégration désactivée via MCP.
- 🗑 **Pronote désactivé** (3 entrées : Arthur, Mathieu, Raphaël) : `NoneType object is not subscriptable`. Intégrations désactivées via MCP.
- 🛠 **HMS-1600 écrêteur — fix gap démarrage** : condition montée `above: 850` → `above: 799` pour couvrir la zone 800–850 W qui laissait l'onduleur sans limite. Notification déplacée dans un `if/then` (ne s'affiche que si > 850 W). Config_hash : `dd09da9dfc6cbac4` (§2ter.5).
- 🔍 **Analyse Emporia Vue timeouts** (10 jours 2026-05-12→22) : 4 événements sporadiques + vague DNS le 2026-05-21 à 13h19 Paris. Documenté en §5.1.
- 🆕 **Dashboard Aperçu — cartes activation/conso** : 3 cartes `conditional` + `markdown` ajoutées dans les sous-vues chauffe-eau cuisine, chauffe-eau principal et pompe piscine. Affichage : temps actif depuis `last_changed` + énergie consommée ce cycle. Config_hash lovelace : `1c1cb47bac0d00fe`.
- 📌 **Sensor pompe piscine documenté** (§3.ter.2) : puissance instantanée `sensor.pompe_piscine_ph3_3_1min` (W), énergie cumulative `sensor.pompe_piscine` (kWh, source `ph3_3_1min`).

### 2026-05-22 v5

- 🆕 **§3quater — Cast vers Nest Hub Cuisine** : documentation du Hub (`media_player.cuisine`, état `off`, plateforme `cast`). Création de 2 scripts de cast : `script.cast_apercu_cuisine` (dashboard `lovelace`) et `script.cast_energie_cuisine` (dashboard `energie-detail`). Boutons "📺 Envoyer sur Cuisine Hub" ajoutés en bas du dashboard Aperçu (`config_hash lovelace : 114cb86bf521ded6`).
- 📌 **Commandes vocales Google Home** : procédure manuelle documentée en §7.6 (sans Nabu Casa, via Google Cloud Console + Google Home Developer Console). À déployer ultérieurement.
- 🛠 **§5.1** : ajout `media_player.google_hub` (unavailable, ancienne entrée Cast à nettoyer).
- 🛠 **Fix automations sync SolarFlow** (déjà noté en v4) : rappel — options `select.solarflow_800_plus_ac_mode` sont `"input"` / `"output"` depuis la mise à jour Zendure.

### 2026-05-20 v4

- 🛠 **Fix automations sync SolarFlow** : options `select.solarflow_800_plus_ac_mode` changées par mise à jour intégration Zendure — `"Mode entrée AC"` → `"input"`, `"Mode sortie AC"` → `"output"`. Les commandes charge/décharge du dashboard ne fonctionnaient plus (échec silencieux). Config_hash mis à jour : charge `14a5ba6b496d0021`, décharge `d043b4286e7248a6`.
- 📌 **Rappel maintenance** : après toute mise à jour HACS de l'intégration Zendure, vérifier `attributes.options` du `select.solarflow_800_plus_ac_mode` avant de diagnostiquer une autre cause (§2quater.4).

### 2026-05-19 v3

- 🛠 **Écrêteur HMS-1600 — correctifs post-analyse trip 13h48** :
  - Trigger montée : `1000 W + for 10s` → **`850 W` sans debounce** (réaction immédiate pour couvrir les rampes < 10 s)
  - Limite MQTT : `1000 W` → **`900 W`** (marge 100 W sous seuil empirique de trip)
  - Trigger descente : `900 W` → **`800 W`** (hystérésis descente = 50 W sous la limite active)
  - `config_hash` mis à jour : `f6f95fb4e08ae43a` → `71506920c279a29a`
- 📌 **Rappel action pendante** : réduire l'intervalle MQTT OpenDTU de 5 s à 1 s (`192.168.1.137` → Paramètres → MQTT → publish interval) pour améliorer la réactivité de toutes les automations solaires.

### 2026-05-19 v2

- 🆕 **Helpers `input_select` SolarFlow** : `input_select.solarflow_limite_charge` (0–1000 W, pas 100 W) et `input_select.solarflow_limite_decharge` (0–800 W, pas 100 W). Interface de contrôle principale — les entités Zendure `number.*` ne doivent plus être touchées directement.
- 🛠 **Automations sync SolarFlow enrichies** : ajout de l'exclusion mutuelle charge/décharge (fixer l'un remet l'autre à 0) + bascule automatique du mode AC ("entrée AC" si charge > 0, "sortie AC" si décharge > 0). Pas de boucle infinie car la condition `> 0` n'est pas vérifiée pour la valeur 0.
- 🆕 **Automation alerte température SolarFlow** (`automation.solarflow_alerte_temperature_elevee`) : notif persistante si `hyper_tmp` > 45 °C pendant 2 min, dismiss auto sous 42 °C.
- 🗑 **Dashboard Aperçu — carte SolarFlow** : suppression du bloc "Mode de fonctionnement" (mode piloté automatiquement). Suppression des sliders natifs Zendure + boutons presets. La carte passe à 5 lignes (header + glance + 2 dropdowns).

### 2026-05-19

- 🆕 **§2ter HMS-1600 (OpenDTU)** : documentation complète du micro-onduleur Hoymiles HMS-1600-4T (IP OpenDTU `192.168.1.137`, SN `116495202971`, entités `opendtu_4c9028_*`). Grid profile NF EN 50549-1:2019, HV1=253V.
- 🆕 **Automation écrêteur HMS-1600** (`automation.hms_1600_ecreteur_1000w_anti_surtension`, unique_id `1779033898281`) : limite la production à 1000 W (seuil empirique sûr) pour éviter les trips surtension. Hystérésis 1000/900 W, for 10s montée / 10min descente (volontaire), trigger démarrage HA pour rétablir la limite nonpersistent. Déployé via MCP.
- 🆕 **§2quater SolarFlow 800 Plus (Zendure)** : intégration HACS fireson v1.3.1, 59 entités. Carte dashboard Aperçu (carte n°9) avec glance + mode AC + sliders charge/décharge + presets.
- 🆕 **Bouton Restart Inverter HMS-1600** (`button.hms_1600_restart_inverter`) ajouté au dashboard 1.Mobile.
- 📝 **Piste ouverte** : coordination écrêteur HMS ↔ SolarFlow (§2ter.7) — laisser HMS en pleine puissance, absorber l'excédent via SolarFlow en mode entrée AC, injection nette ≤ 1000 W. À tester manuellement avant automatisation.
- 🛠 **§5.1** : ajout "Surtension réseau HMS-1600" dans les ouverts (action Enedis à faire).

### 2026-05-14

- 🆕 **Programmation hebdo + Minuterie sur les 3 switches du dashboard Aperçu** (§3.ter).
- 🆕 **12 nouveaux objets HA** : 3 timers, 3 input_numbers, 3 scripts, 6 automations minuterie.
- 🆕 **Dashboard Aperçu V4** : 3 sous-vues unitaires (`programmation_cuisine`, `programmation_principal`, `programmation_piscine`), 100 % natif, compatible Android Companion.
- 🛠 **Fix Auto-heal Tado** : entry_id mis à jour → `01KR406D3HNSDFXENFP3TKN9AX`, trigger périodique /15min ajouté, notification dédupliquée.

### 2026-05-10

- 🛠 **Fix timezone CSV solaire** : timestamps convertis UTC → Europe/Paris.
- 📝 **Format CSV documenté** : `datetime;production_W` heure locale.

### 2026-05-02

- 🎉 **Projet Emporia déployé** (§2bis) : 3 phases en une journée, stdlib only, OAuth app en Production.

### 2026-04-22

- 🛠 **Nouveau sensor `sensor.chauffe_eau_opportunite_stats`** + refonte automation `simu_chauffe_eau_off`.

### 2026-04-21

- 🛠 **Fix `simu_chauffe_eau_on`** : seuil `age_coverage_ratio` abaissé à 0.25.

### 2026-04-20

- 🆕 **Refonte complète du fichier de contexte**.
- 🛠 **Auto-heal Tado** initial + résolution Arlo.
