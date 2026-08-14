# Directives de Développement & Maintenance Home Assistant (Krikor)

Bienvenue sur le dépôt de configuration et d'automatisations Home Assistant de Krikor.

---

## 📜 RÈGLES D'OR OBLIGATOIRES POUR TOUT ASSISTANT IA

Avant toute intervention, modification, ajout de fonctionnalité ou correction de bug :

### 1. 🔍 Consultation Obligatoire du REX & de l'Historique
- Vous **DEVEZ** lire les fichiers de contexte suivants avant toute modification :
  - [`claude-hass-preferences.md`](claude-hass-preferences.md) (Architecture globale, intégrations, automations et changelog).
  - [`zendure-entities-reference.md`](zendure-entities-reference.md) (Référence des entités Zendure & SolarFlow).
- Pour toute modification sur une intégration spécifique, vous **DEVEZ** lire sa section REX dédiée (ex: §2quater.8 pour Zendure, §2ter.5 pour Hoymiles HMS-1600).
- **Interdiction formelle de réintroduire des erreurs passées** (ex: forçage de consignes à 0 W, omission des gardes `unavailable`, confusion entre Zendure Manager `store_solar` et `input_select`).

### 2. 🚫 Interdiction du "Patch Aveugle" (Vérification Live Obligatoire)
- Ne faites **jamais** d'hypothèses sur l'état d'une entité ou son comportement matériel à partir du seul code YAML.
- Utilisez le script CLI [`ha_tool.py`](ha_tool.py) pour inspecter l'état réel et l'historique sur l'instance vivante :
  ```bash
  # Vérifier l'état réel d'une entité
  python ha_tool.py get-state <entity_id>

  # Vérifier l'historique récent
  python ha_tool.py history "<entity_id_1>,<entity_id_2>" --hours 6
  ```

### 3. ✅ Cycle de Validation Strict
Après chaque modification :
1. Valider la syntaxe : `python ha_tool.py check-config`
2. Recharger le composant à chaud : `python ha_tool.py call-service automation reload` (ou `script reload`)
3. Vérifier le statut de l'entité/automation modifiée : `python ha_tool.py get-state <entity_id>`

### 4. 🧠 Obligation d'Enrichissement du REX & du Changelog
- Mettre à jour le **Changelog (§9 de `claude-hass-preferences.md`)** avec la date et le détail précis de l'intervention.
- Si l'intervention résout un dysfonctionnement ou apporte un nouvel enseignement matériel/logiciel, **l'ajouter obligatoirement dans la Base de Connaissances & REX (§2quater.8 ou section correspondante)**.
- Commiter et pusher les modifications sur GitHub avec un message conventionnel clair (`feat:`, `fix:`, `docs:`).
