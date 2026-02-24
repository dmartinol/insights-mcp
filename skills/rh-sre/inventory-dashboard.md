---
name: inventory-dashboard
description: Opens the Inventory Dashboard UI. The dashboard shows the fleet (or a single device) in a carousel, CVE severity counts per host, CVE list by severity, CVE details, and remediation playbook creation. Orchestration runs in the UI.
---

# Inventory Dashboard

Open the **Inventory Dashboard** when the user wants to view the fleet, explore systems with their vulnerabilities, or remediate CVEs per host. The dashboard is a single UI that orchestrates the workflow: it invokes MCP tools (list_hosts, get_host_details, find_host_by_name, get_system_cves, get_cve, get_cve_systems, explain_cves, create_vuln_playbook) and displays results in one place.

## When to use

- User wants to see the fleet or a specific system with its vulnerabilities.
- User asks to view CVE severity per host (Critical, Important, Moderate, Low).
- User wants to drill into a CVE, see details, and create a remediation playbook for a host.

## What the dashboard does

- **Scope**: For a given system (optional system UUID or display name) or all systems.
- **Carousel**: Shows hosts one at a time with Previous/Next navigation.
- **Per host**: Basic info (name, staleness, FQDN, OS, etc.) plus severity buttons showing CVE counts (Critical (3), Important (5), etc.).
- **Severity click**: Shows the list of CVEs for that severity on that host.
- **CVE click**: Opens a modal with Description, Metadata, Why it affects, Affected devices, Advisories, Links, and Remediate.
- **Remediate**: Create and download a playbook for the selected CVE on the host.

All behavior is driven by the dashboard; the agent only needs to open it (e.g. by calling **load_inventory_dashboard_skill** or reading the resource at the skill URI). The host opens the UI at `ui://inventory_/inventory_dashboard`.

## Tool reference (for the dashboard or agent)

| Tool (with toolset prefix) | Purpose |
|----------------------------|---------|
| `inventory__list_hosts` | List hosts in the fleet (per_page, page). |
| `inventory__get_host_details` | Get details for specific host(s) by UUID. |
| `inventory__find_host_by_name` | Resolve hostname/display name to UUID. |
| `vulnerability__get_system_cves` | List CVEs for one system. |
| `vulnerability__get_cve` | Get CVE details. |
| `vulnerability__get_cve_systems` | Systems affected by a CVE. |
| `vulnerability__explain_cves` | Why a CVE affects a system. |
| `remediations__create_vuln_playbook` | Create playbook for selected CVEs and system UUIDs. |

## How the model opens the dashboard

1. Call **inventory_load_inventory_dashboard_skill**. The tool returns the skill content and instructions; the host may open the dashboard UI.
2. Alternatively, the client can open the UI resource directly at `ui://inventory_/inventory_dashboard` when the user asks to view the fleet or inventory.

Ensure the server is started with at least `--toolset inventory,vulnerability` (and `remediations` for playbook creation).
