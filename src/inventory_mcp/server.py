"""Red Hat Insights Host Inventory MCP Server.

MCP server for host inventory data via Red Hat Insights API.
Provides tools to get host inventory data for systems connected to Insights.
"""

import importlib.resources
from pathlib import Path
from typing import Annotated, Any

from fastmcp.server.apps import AppConfig, ResourceCSP  # pylint: disable=import-error,no-name-in-module
from pydantic import Field

from insights_mcp.mcp import InsightsMCP

# For the API documentation, see:
# https://github.com/RedHatInsights/insights-host-inventory/tree/master/swagger

mcp = InsightsMCP(
    name="$container_brand_long Inventory MCP Server",
    toolset_name="inventory",
    api_path="api/inventory/v1",
    instructions="""
    This server provides tools to get host inventory data for systems connected to $container_brand_long.
    You can get information about connected systems, their operating systems, installed packages, etc.

    When the user wants to **remediate CVEs**, mitigate the most severe vulnerabilities, or create a
    remediation playbook: call **inventory_load_remediation_dashboard_skill** to open the Remediation
    Dashboard. The dashboard orchestrates tools (get_cves, get_cve_systems, explain_cves,
    create_vuln_playbook) from within the UI.

    $container_brand_long Host Inventory requires correct RBAC permissions to be able to use the tools. Ensure that your
    Service Account has at least this role:
    - Inventory Hosts viewer
    """,
)


REMEDIATION_DASHBOARD_UI_RESOURCE_URI = "ui://remediation_dashboard"
REMEDIATION_DASHBOARD_UI_MOUNTED_URI = "ui://inventory_/remediation_dashboard"


@mcp.resource(  # type: ignore[call-arg]  # pylint: disable=unexpected-keyword-arg
    REMEDIATION_DASHBOARD_UI_RESOURCE_URI,
    app=AppConfig(csp=ResourceCSP(resource_domains=["https://unpkg.com"])),
)
def remediation_dashboard_ui() -> str:
    """Load the remediation dashboard UI (orchestration in UI; invokes MCP tools)."""
    return EMBEDDED_REMEDIATION_DASHBOARD_HTML


REMEDIATION_DASHBOARD_SKILL_RESOURCE_URI = "skill://remediation-dashboard"
REMEDIATION_DASHBOARD_SKILL_MOUNTED_URI = "skill://inventory_/remediation-dashboard"
REMEDIATION_DASHBOARD_SKILL_MIME_TYPE = "text/markdown"

_SKILL_PATHS = [
    Path(__file__).parent.parent.parent / "skills" / "rh-sre" / "remediation-dashboard.md",
    Path("skills/rh-sre/remediation-dashboard.md"),
]
_SKILL_FALLBACK = (
    "Remediation dashboard: open UI at ui://inventory_/remediation_dashboard; "
    "dashboard uses get_cves/get_system_cves, get_cve_systems, explain_cves, create_vuln_playbook."
)


def _load_remediation_dashboard_skill_at_init() -> str:
    """Load the remediation-dashboard skill markdown at resource registration time (once)."""
    for path in _SKILL_PATHS:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return _SKILL_FALLBACK


# Load skill content once at module load (resource registration time).
REMEDIATION_DASHBOARD_SKILL_CONTENT = _load_remediation_dashboard_skill_at_init()


@mcp.resource(
    REMEDIATION_DASHBOARD_SKILL_RESOURCE_URI,
    annotations={"readOnlyHint": True},
    mime_type=REMEDIATION_DASHBOARD_SKILL_MIME_TYPE,
    meta={
        "ui": {
            "resourceUri": REMEDIATION_DASHBOARD_UI_MOUNTED_URI,
            "displayHints": {"title": "Remediation Dashboard", "description": "CVE remediation and playbook creation"},
        },
        "ui/resourceUri": REMEDIATION_DASHBOARD_UI_MOUNTED_URI,
    },
)
def remediation_dashboard_skill() -> str:
    """Serve the remediation-dashboard skill (content loaded at resource registration time)."""
    return REMEDIATION_DASHBOARD_SKILL_CONTENT


# Skills discoverable by the host (list_skills / get_skill). Required by some hosts to discover
# and load skills before opening the UI.
INVENTORY_SKILLS = [
    {
        "name": "remediation-dashboard",
        "uri": REMEDIATION_DASHBOARD_SKILL_MOUNTED_URI,
        "title": "Remediation Dashboard",
        "description": "CVE remediation and playbook creation",
    },
]


# UI Resource URIs for registration (will be transformed by mount())
# Carousel UI (inline-details: includes inline details view toggle)
CAROUSEL_RESOURCE_URI = "ui://hosts-carousel-v1"
CAROUSEL_MOUNTED_URI = "ui://inventory_/hosts-carousel-v1"

# Host Details UI
DETAILS_RESOURCE_URI = "ui://host-details-v1"
DETAILS_MOUNTED_URI = "ui://inventory_/host-details-v1"


def _load_carousel_html() -> str:
    """Load the hosts carousel HTML from the dedicated file."""
    try:
        # Try using importlib.resources first (preferred for packages)
        if hasattr(importlib.resources, "files"):
            # Python 3.9+
            return (
                importlib.resources.files("inventory_mcp").joinpath("hosts_carousel.html").read_text(encoding="utf-8")
            )
        # Python 3.8 fallback
        return importlib.resources.read_text("inventory_mcp", "hosts_carousel.html", encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, AttributeError, TypeError):  # pylint: disable=broad-exception-caught
        # Fallback to direct file read if importlib.resources doesn't work
        html_path = Path(__file__).parent / "hosts_carousel.html"
        return html_path.read_text(encoding="utf-8")


def _load_host_details_html() -> str:
    """Load the host details HTML from the dedicated file."""
    try:
        # Try using importlib.resources first (preferred for packages)
        if hasattr(importlib.resources, "files"):
            # Python 3.9+
            return importlib.resources.files("inventory_mcp").joinpath("host_details.html").read_text(encoding="utf-8")
        # Python 3.8 fallback
        return importlib.resources.read_text("inventory_mcp", "host_details.html", encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, AttributeError, TypeError):  # pylint: disable=broad-exception-caught
        # Fallback to direct file read if importlib.resources doesn't work
        html_path = Path(__file__).parent / "host_details.html"
        return html_path.read_text(encoding="utf-8")


def _load_remediation_dashboard_html() -> str:
    """Load the remediation dashboard HTML (orchestration in UI; invokes MCP tools)."""
    try:
        if hasattr(importlib.resources, "files"):
            return (
                importlib.resources.files("inventory_mcp")
                .joinpath("remediation_dashboard.html")
                .read_text(encoding="utf-8")
            )
        return importlib.resources.read_text("inventory_mcp", "remediation_dashboard.html", encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, AttributeError, TypeError):  # pylint: disable=broad-exception-caught
        html_path = Path(__file__).parent / "remediation_dashboard.html"
        return html_path.read_text(encoding="utf-8")


# Embedded HTML for MCP Apps (carousel, host details, remediation dashboard)
EMBEDDED_CAROUSEL_HTML = _load_carousel_html()
EMBEDDED_HOST_DETAILS_HTML = _load_host_details_html()
EMBEDDED_REMEDIATION_DASHBOARD_HTML = _load_remediation_dashboard_html()


# @mcp.resource(
#     CAROUSEL_RESOURCE_URI,
#     app=AppConfig(csp=ResourceCSP(resource_domains=["https://unpkg.com"])),
# )
def hosts_carousel_view() -> str:
    """Host carousel UI resource for displaying inventory hosts."""
    return EMBEDDED_CAROUSEL_HTML


# @mcp.resource(
#     DETAILS_RESOURCE_URI,
#     app=AppConfig(csp=ResourceCSP(resource_domains=["https://unpkg.com"])),
# )
def host_details_view() -> str:
    """Host details UI resource for displaying detailed host information."""
    return EMBEDDED_HOST_DETAILS_HTML


@mcp.tool(  # type: ignore[call-overload]  # pylint: disable=unexpected-keyword-arg
    annotations={"readOnlyHint": True},
    app=AppConfig(resource_uri=CAROUSEL_MOUNTED_URI),
)
async def list_hosts(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    hostname_or_id: Annotated[str, Field("", description="Filter by display_name, fqdn, or id (case-insensitive).")],
    display_name: Annotated[str, Field("", description="Filter by display name (case-insensitive).")],
    fqdn: Annotated[str, Field("", description="Filter by FQDN (case-insensitive).")],
    tags: Annotated[str, Field("", description="Filter by tags (e.g., 'ns1/key1=val1,ns2/key2=val2').")],
    staleness: Annotated[
        str, Field("", description="Filter by staleness status (one of 'fresh', 'stale', 'stale_warning', 'unknown').")
    ],
    registered_with: Annotated[str, Field("", description="Filter by reporter that registered the host.")],
    provider_type: Annotated[str, Field("", description="Filter by provider type (e.g., 'aws', 'azure', 'gcp').")],
    updated_start: Annotated[str, Field("", description="Filter hosts updated after this timestamp (RFC3339).")],
    updated_end: Annotated[str, Field("", description="Filter hosts updated before this timestamp (RFC3339).")],
    per_page: Annotated[
        int,
        Field(
            10,
            description=(
                "Number of hosts to return per page "
                "**ALWAYS use the default value of 10 for the first call.** "
                "This default is carefully chosen for performance and context management. "
                "Only increase this value if the user explicitly asks to see more systems at once "
            ),
        ),
    ],
    page: Annotated[int, Field(1, description="Page number to return.")],
    order_by: Annotated[str, Field("", description="Field to sort by ('display_name', 'updated', 'created').")],
    order_how: Annotated[str, Field("ASC", description="Sort direction ('ASC' or 'DESC').")],
) -> dict[str, Any] | str:
    """List hosts with filtering and sorting options.
    CRITICAL: For the 'per_page' parameter, you MUST use a value of 10 on the first call to avoid performance
    degradation and context overflow.
    Only use a larger value if the user explicitly requests to see more systems at once.
    """
    params: dict[str, Any] = {}

    if hostname_or_id:
        params["hostname_or_id"] = hostname_or_id
    if display_name:
        params["display_name"] = display_name
    if fqdn:
        params["fqdn"] = fqdn
    if tags:
        params["tags"] = tags
    if staleness:
        params["staleness"] = staleness
    if registered_with:
        params["registered_with"] = registered_with
    if provider_type:
        params["provider_type"] = provider_type
    if updated_start:
        params["updated_start"] = updated_start
    if updated_end:
        params["updated_end"] = updated_end
    if order_by:
        params["order_by"] = order_by
        params["order_how"] = order_how

    params["per_page"] = min(per_page, 100)
    params["page"] = page

    response = await mcp.insights_client.get("hosts", params=params)

    if isinstance(response, str):
        return response
    return response


@mcp.tool(  # type: ignore[call-overload]  # pylint: disable=unexpected-keyword-arg
    annotations={"readOnlyHint": True},
    app=AppConfig(resource_uri=DETAILS_MOUNTED_URI),
)
async def get_host_details(host_ids: str = "") -> dict[str, Any] | str:
    """Get detailed information for specific hosts by their IDs.

    Returns comprehensive host data including identifiers (insights_id, satellite_id, bios_uuid),
    display names, network info (IP/MAC addresses), cloud provider details, account/org metadata,
    timestamps (created, updated, stale_timestamp), reporter info, groups, facts, and basic
    system_profile data.

    Args:
        host_ids: Comma-separated list of host IDs (UUIDs) to retrieve. If empty, returns an error message.
    """
    if not host_ids or not host_ids.strip():
        return {
            "error": "No host ID provided",
            "message": "Please provide at least one host ID (UUID) to retrieve details.",
            "hint": "Click on a host name in the inventory carousel to view its details.",
        }

    response = await mcp.insights_client.get(f"hosts/{host_ids}")
    if isinstance(response, str):
        return response
    return response


@mcp.tool(annotations={"readOnlyHint": True})
async def get_host_system_profile(
    host_ids: Annotated[
        str,
        Field(
            "",
            description=(
                "Comma-separated list of host IDs (UUIDs) to get system profiles for. "
                "ALWAYS supply one or two UUIDs at a time! "
                "Expect really large responses which will overload your context."
            ),
        ),
    ],
) -> dict[str, Any] | str:
    """Get detailed system profile information for specific hosts.

    Returns comprehensive hardware and software configuration data including CPU details
    (model, count, cores per socket), memory info (system_memory_bytes), infrastructure
    details (type, vendor), network interfaces, disk devices, BIOS information, and
    various system state data. For RHEL hosts, also includes software information such as
    enabled repositories, installed packages, and enabled services. This provides the most
    detailed technical specifications for each host.
    """
    response = await mcp.insights_client.get(f"hosts/{host_ids}/system_profile")
    if isinstance(response, str):
        return response
    return response


@mcp.tool(annotations={"readOnlyHint": True})
async def get_host_tags(host_ids: str) -> dict[str, Any] | str:
    """Get tags for specific hosts.

    Args:
        host_ids: Comma-separated list of host IDs (UUIDs) to get tags for.
    """
    response = await mcp.insights_client.get(f"hosts/{host_ids}/tags")
    if isinstance(response, str):
        return response
    return response


@mcp.tool(annotations={"readOnlyHint": True})
async def find_host_by_name(hostname: str) -> dict[str, Any] | str:
    """Find a host by its hostname/display name.

    Args:
        hostname: The hostname or display name to search for.
    """
    response = await mcp.insights_client.get("hosts", params={"hostname_or_id": hostname, "per_page": 1})
    if isinstance(response, str):
        return response
    return response


@mcp.tool(annotations={"readOnlyHint": True})
async def list_skills() -> list[dict[str, Any]]:
    """List skills (e.g. remediation dashboard). Used by the host to discover skills before opening a skill UI."""
    return list(INVENTORY_SKILLS)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_skill(
    skill_name: Annotated[
        str,
        Field(description="Skill name (e.g. 'remediation-dashboard') or skill URI to load."),
    ] = "",
) -> dict[str, Any] | str:
    """Load a skill by name or URI. Returns skill content and metadata for the host when opening a skill UI."""
    name_or_uri = (skill_name or "").strip()
    for skill in INVENTORY_SKILLS:
        if skill["name"] == name_or_uri or skill.get("uri") == name_or_uri:
            return {
                "skill_name": skill["name"],
                "skill_uri": skill["uri"],
                "content": REMEDIATION_DASHBOARD_SKILL_CONTENT if skill["name"] == "remediation-dashboard" else "",
                "title": skill.get("title", skill["name"]),
                "description": skill.get("description", ""),
            }
    return {"error": f"Skill not found: {name_or_uri!r}", "available": [s["name"] for s in INVENTORY_SKILLS]}


@mcp.tool(  # type: ignore[call-overload]  # pylint: disable=unexpected-keyword-arg
    name="load_remediation_dashboard_skill",
    annotations={"readOnlyHint": True},
    app=AppConfig(resource_uri=REMEDIATION_DASHBOARD_UI_MOUNTED_URI),
)
async def load_remediation_dashboard_skill(
    device: Annotated[
        str,
        Field(
            "",
            description=(
                "Optional. Scope the dashboard to a single device: pass a system UUID or display name. "
                "If empty, the dashboard shows all the fleet. Use when the user says e.g. "
                "'open the dashboard for hostname' or 'remediation dashboard for system X'."
            ),
        ),
    ] = "",
) -> dict[str, Any]:
    """Open the Remediation Dashboard and load its skill content into context.

    Call this when the user wants to remediate CVEs, mitigate vulnerabilities, or create
    remediation playbooks. The user can request:

    - **Full fleet**: "Show the remediation dashboard", "Open the remediation dashboard"
      → call with no device (or device empty). Dashboard shows all systems.

    - **Single device**: "Open the dashboard for <hostname>", "Remediation dashboard for system X"
      → call with device set to the system UUID or display name. Dashboard will resolve
        the device and show CVEs for that system only.

    The tool returns the skill content; the host may open the Remediation Dashboard UI.
    When device is provided, the host should open the UI with that scope (e.g. append
    ?device=<value> to the UI resource URL). The dashboard orchestrates get_cves /
    get_system_cves, get_cve_systems, explain_cves, create_vuln_playbook from within the UI.

    Returns:
        Dict with "content", "instructions", "skill_name", "skill_uri", and "device"
        (present when scoped to a device, for the host to pass to the UI).
    """
    device_value = device.strip() or None
    return {
        "skill_name": "remediation-dashboard",
        "skill_uri": REMEDIATION_DASHBOARD_SKILL_MOUNTED_URI,
        "content": REMEDIATION_DASHBOARD_SKILL_CONTENT,
        "device": device_value,
        "instructions": (
            "The Remediation Dashboard UI opens when this tool is invoked. "
            + (
                "To scope the dashboard to the requested device, the host MUST do one of: "
                "(1) Append ?device=" + (device_value or "") + " to the UI resource URL when opening the iframe, or "
                "(2) Send ui/notifications/tool-input or ui/notifications/tool-result to the view with "
                "params.arguments.device or params.result.device set to this value. "
                "Otherwise the dashboard will show 'All the fleet'. "
                if device_value
                else "Open the UI for the full fleet (no device parameter). "
            )
            + "The dashboard loads critical CVEs, shows explanation and affected devices per CVE, "
            "and supports creating or downloading remediation playbooks via MCP tools."
        ),
    }
