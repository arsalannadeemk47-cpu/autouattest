import json
import sys

# Load raw cookies from Cookie-Editor export
with open('/workspaces/autouattest/tests/setup/.auth/cookies.json', 'r') as f:
    raw_cookies = json.load(f)

# Convert to Playwright storageState format
playwright_cookies = []
for cookie in raw_cookies:
    playwright_cookie = {
        "name": cookie.get("name", ""),
        "value": cookie.get("value", ""),
        "domain": cookie.get("domain", ""),
        "path": cookie.get("path", "/"),
        "expires": cookie.get("expirationDate", -1),
        "httpOnly": cookie.get("httpOnly", False),
        "secure": cookie.get("secure", False),
        "sameSite": cookie.get("sameSite", "Lax")
    }
    playwright_cookies.append(playwright_cookie)

storage_state = {
    "cookies": playwright_cookies,
    "origins": []
}

output_path = '/workspaces/autouattest/tests/setup/.auth/user.json'
with open(output_path, 'w') as f:
    json.dump(storage_state, f, indent=2)

print(f"✅ Converted {len(playwright_cookies)} cookies")
print(f"✅ Saved to {output_path}")