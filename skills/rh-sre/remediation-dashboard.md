---
name: remediation-dashboard
description: Opens the Remediation Dashboard UI. The dashboard lets you scope by system (or all systems), view critical CVEs, explain a CVE, see affected systems, and create or download a remediation playbook. Orchestration runs in the UI; the dashboard invokes MCP tools for data and actions.
---

# Remediation Dashboard

Open the **Remediation Dashboard** when the user wants to remediate CVEs, mitigate vulnerabilities, or work with playbooks. The dashboard is a single UI that orchestrates the workflow: it invokes MCP tools (get_cves, get_system_cves, get_cve_systems, explain_cves, create_vuln_playbook) and displays results in one place.

## When to use

- User wants to remediate CVEs or create a playbook.
- User asks to see critical vulnerabilities and fix them.
- User wants to explain why a CVE affects the environment or see affected systems before creating a playbook.

## What the dashboard does

- **Scope**: For a given system (optional system UUID) or all systems.
- **CVE list**: Shows the most critical CVEs (via get_cves or get_system_cves). User can select one or more.
- **Explain**: For a selected CVE, the dashboard can call explain_cves and show affected packages and fix strategy.
- **Affected systems**: For a selected CVE, the dashboard can call get_cve_systems and show the list.
- **Create playbook**: User selects CVEs (and optionally restricts systems); the dashboard calls create_vuln_playbook and shows or downloads the YAML.

All behavior is driven by the dashboard; the agent only needs to open it (e.g. by calling **load_remediation_dashboard_skill** or reading the resource at the skill URI). The host opens the UI at `ui://inventory_/remediation_dashboard`.

## Tool reference (for the dashboard or agent)

| Tool (with toolset prefix) | Purpose |
|----------------------------|--------|
| `vulnerability_get_cves` | List CVEs for the account (e.g. sort=-cvss_score, advisory_available=true). |
| `vulnerability_get_system_cves` | List CVEs for one system (when scope is a specific system). |
| `vulnerability_get_cve_systems` | Systems affected by a CVE (UUIDs for playbook). |
| `vulnerability_explain_cves` | Why a CVE affects a system (packages, fix). |
| `remediations_create_vuln_playbook` | Create playbook for selected cves and system UUIDs. |

## How the model opens the dashboard

1. Call **inventory_load_remediation_dashboard_skill**. The tool returns the skill content and instructions; the host may open the dashboard UI.
2. Alternatively, the client can open the UI resource directly at `ui://inventory_/remediation_dashboard` when the user asks to remediate.

Ensure the server is started with at least `--toolset inventory,vulnerability` (and `remediations` for playbook creation).
