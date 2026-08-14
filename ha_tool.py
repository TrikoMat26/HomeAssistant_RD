import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

def load_env():
    env = {}
    # Search for .env in current directory and parent directories
    search_paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(r"F:\GitHub\HomeAssistant_RD", ".env"),
        os.path.expanduser(r"~\.env"),
    ]
    for p in search_paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip()
            break

    token = env.get("HOMEASSISTANT_TOKEN") or os.environ.get("HOMEASSISTANT_TOKEN")
    url = (
        env.get("HOMEASSISTANT_URL_LOCAL")
        or env.get("HOMEASSISTANT_URL")
        or os.environ.get("HOMEASSISTANT_URL_LOCAL")
        or "http://192.168.1.79:8123"
    ).rstrip("/")
    return url, token

def api_request(path, method="GET", data=None):
    url, token = load_env()
    if not token:
        print("Error: HOMEASSISTANT_TOKEN not found in .env or environment.", file=sys.stderr)
        sys.exit(1)

    req_url = f"{url}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(req_url, data=encoded_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            if content:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return content
            return {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP Error {e.code}: {e.reason}\n{body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_get_state(args):
    res = api_request(f"/api/states/{args.entity_id}")
    print(json.dumps(res, indent=2, ensure_ascii=False))

def cmd_history(args):
    hours = args.hours or 6
    start_time = (datetime.now() - timedelta(hours=hours)).astimezone().isoformat()
    entities = args.entities
    res = api_request(f"/api/history/period/{start_time}?filter_entity_id={entities}")
    if isinstance(res, list):
        for elist in res:
            if not elist:
                continue
            entity_id = elist[0].get("entity_id")
            print(f"\n--- History for {entity_id} (last {hours}h) ---")
            for item in elist[-30:]:
                print(f"  [{item.get('last_changed')}] state={item.get('state')} attr={item.get('attributes')}")
    else:
        print(json.dumps(res, indent=2, ensure_ascii=False))

def cmd_call_service(args):
    payload = json.loads(args.data) if args.data else {}
    res = api_request(f"/api/services/{args.domain}/{args.service}", method="POST", data=payload)
    print("Service executed successfully:")
    print(json.dumps(res, indent=2, ensure_ascii=False))

def cmd_check_config(args):
    res = api_request("/api/config/core/check_config", method="POST")
    print(json.dumps(res, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="Home Assistant CLI Management Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # get-state
    p_get = subparsers.add_parser("get-state", help="Get entity state")
    p_get.add_argument("entity_id", help="Entity ID (e.g. sensor.solarflow_800_plus_hyper_tmp)")
    p_get.set_defaults(func=cmd_get_state)

    # history
    p_hist = subparsers.add_parser("history", help="Get entity history")
    p_hist.add_argument("entities", help="Comma-separated entity IDs")
    p_hist.add_argument("--hours", type=int, default=6, help="Hours of history")
    p_hist.set_defaults(func=cmd_history)

    # call-service
    p_svc = subparsers.add_parser("call-service", help="Call a service")
    p_svc.add_argument("domain", help="Domain (e.g. automation, homeassistant)")
    p_svc.add_argument("service", help="Service (e.g. reload, set_value)")
    p_svc.add_argument("--data", help="JSON data payload", default="{}")
    p_svc.set_defaults(func=cmd_call_service)

    # check-config
    p_check = subparsers.add_parser("check-config", help="Check Home Assistant configuration")
    p_check.set_defaults(func=cmd_check_config)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
