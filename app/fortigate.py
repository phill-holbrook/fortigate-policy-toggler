import httpx
from app.config import CONFIG

def _client() -> httpx.AsyncClient:
    fg = CONFIG["fortigate"]
    verify = fg.get("verify_ssl", False)
    base_url = f"https://{fg['host']}:{fg['port']}"

    headers = {}
    params = {}
    api_key = fg.get("api_key", "")
    if api_key:
        # Modern FortiOS uses Authorization header
        headers["Authorization"] = f"Bearer {api_key}"
        # Also add as query param for older firmware compatibility
        params["access_token"] = api_key

    return httpx.AsyncClient(
        base_url=base_url,
        headers=headers,
        params=params,
        verify=verify,
        timeout=10.0,
    )

async def get_policy_status(policy_id: int) -> bool:
    """Returns True if internet is ON (deny policy is disabled)."""
    fg = CONFIG["fortigate"]
    vdom = fg.get("vdom", "root")
    async with _client() as client:
        resp = await client.get(
            f"/api/v2/cmdb/firewall/policy/{policy_id}",
            params={"vdom": vdom},
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            raise ValueError(f"Policy {policy_id} not found")
        status = results[0].get("status", "enable")
        # deny policy disabled = internet ON; deny policy enabled = internet OFF
        return status == "disable"

async def set_internet_access(policy_id: int, enabled: bool) -> None:
    """Set internet access for a policy. enabled=True disables the deny policy."""
    fg = CONFIG["fortigate"]
    vdom = fg.get("vdom", "root")
    # If internet should be ON, disable the deny policy. If OFF, enable it.
    policy_status = "disable" if enabled else "enable"
    async with _client() as client:
        resp = await client.put(
            f"/api/v2/cmdb/firewall/policy/{policy_id}",
            params={"vdom": vdom},
            json={"status": policy_status},
        )
        resp.raise_for_status()
