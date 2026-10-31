import sys
import json
import urllib.request
import urllib.error
from ha_tool import load_env

def is_command_learned(device, command):
    url, token = load_env()
    req = urllib.request.Request(
        f"{url}/api/services/remote/send_command",
        data=json.dumps({"entity_id": "remote.rm_pro", "device": device, "command": command}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True
    except Exception:
        return False

def learn(device, command, timeout=60):
    url, token = load_env()
    req_url = f"{url}/api/services/remote/learn_command"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "entity_id": "remote.rm_pro",
        "device": device,
        "command": command,
        "command_type": "rf",
        "timeout": timeout
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(req_url, data=data, headers=headers, method="POST")
    print(f"[*] Demande d'apprentissage envoyee pour '{command}' sur '{device}' (timeout {timeout}s)...")
    try:
        with urllib.request.urlopen(req, timeout=timeout + 15) as resp:
            resp.read()
    except Exception as e:
        print(f"Exception pendant l'appel d'apprentissage : {e}")

    # Verification reelle
    if is_command_learned(device, command):
        print(f"RESULT: SUCCESS - '{command}' a ete correctement enregistre et verifie !")
        return True
    else:
        print(f"RESULT: FAILED - '{command}' n'a PAS ete enregistre (signal non capte ou delai expire).")
        return False

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "vitesse_2"
    dev = sys.argv[2] if len(sys.argv) > 2 else "ventilateur_leds_c4"
    learn(dev, cmd, 60)
