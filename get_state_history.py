import urllib.request
import json
import os
from datetime import datetime, timedelta

# Load env
env = {}
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()

token = env.get("HOMEASSISTANT_TOKEN")
url = env.get("HOMEASSISTANT_URL_LOCAL", "http://192.168.1.79:8123").rstrip("/")

# Get history for the last 14 hours
start_time = (datetime.utcnow() - timedelta(hours=14)).isoformat() + "Z"
entities = [
    "sensor.solarflow_800_plus_hyper_tmp",
    "number.solarflow_800_plus_output_limit",
    "number.solarflow_800_plus_input_limit",
    "number.solarflow_800_plus_charge_max_limit",
    "number.solarflow_800_plus_inverse_max_power",
    "input_select.solarflow_limite_decharge",
    "input_select.solarflow_limite_charge"
]


req_url = f"{url}/api/history/period/{start_time}?filter_entity_id={','.join(entities)}"
req = urllib.request.Request(
    req_url,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
)

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))
        print("Entity History:")
        for entity_list in data:
            if not entity_list:
                continue
            entity_id = entity_list[0]["entity_id"]
            print(f"\nEntity: {entity_id}")
            # Print the last 40 changes
            for state_change in entity_list[-40:]:
                last_changed = state_change.get("last_changed")
                state = state_change.get("state")
                print(f"  [{last_changed}] -> {state}")
except Exception as e:
    print("Error:", e)
