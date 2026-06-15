import json
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.parent / '.env')

COOKIE_STRING = os.environ.get("AUTH_COOKIE_STRING", "").strip().strip('"').strip("'")

DOMAIN = "lacps--uat.sandbox.my.site.com"

def parse_cookie_string(cookie_string, domain):
    cookies = []
    for part in cookie_string.split(';'):
        part = part.strip()
        if '=' in part:
            name, _, value = part.partition('=')
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": domain,
                "path": "/",
                "expires": -1,
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            })
    return cookies

cookies = parse_cookie_string(COOKIE_STRING, DOMAIN)

storage_state = {
    "cookies": cookies,
    "origins": []
}

HTTPONLY_COOKIES = ["sid"]  # replace with names you noted

for cookie in cookies:
    if cookie["name"] in HTTPONLY_COOKIES:
        cookie["httpOnly"] = True


output_path = "/workspaces/autouattest/tests/setup/.auth/user.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w") as f:
    json.dump(storage_state, f, indent=2)

print(f"✅ Saved {len(cookies)} cookies to {output_path}")
for c in cookies:
    print(f"   - {c['name']}")