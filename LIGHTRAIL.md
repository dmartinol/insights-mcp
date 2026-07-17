# Lightrail Onboarding — insights-mcp

Lightrail is Red Hat's internal hosting platform for AI-powered Python applications running on Managed Platform Plus (MP+) OpenShift clusters. It supports MCP servers natively. This document summarises the steps needed to onboard `insights-mcp` as a Lightrail-hosted MCP server.

> Full reference docs are in the [Lightrail repo](https://gitlab.cee.redhat.com/dxp/platforms-pipelines/lightrail-platform/lightrail.git) (internal).
> Reference implementation validated against: [mcp_server_for_red_hat_security_content](https://gitlab.cee.redhat.com/lightforge/mcp-servers/mcp_server_for_red_hat_security_content.git)

---



## Engaging the Platform Team

The Lightrail platform is owned by the **3DO Platforms and Pipelines workstream** (GitLab group: `@3do-platforms-pipelines`).

**To request onboarding of a new application:**

Submit a request at [source.redhat.com → DXP Portfolio request form](https://source.redhat.com/departments/products_and_global_engineering/digital_experience_platform_portfolio/request).

You can also reach the team via the Lightrail announcements Slack channel: `#announce-ix-platforms-pipelines` — this is where they post releases and where new questions can be directed.

> For MCP servers under the Lightforge umbrella specifically, contact `lightforge-eng@redhat.com`.

The platform team will provision: OpenShift namespace, ArgoCD instance, GitLab runner, and Rover groups (`lightrail-<cmdb>-preprod` / `lightrail-<cmdb>-prod`).

---



## Prerequisites

Before starting, the following must be in place:

- [ ] Confirm with platform team whether the repo must be on `gitlab.cee.redhat.com` or if GitHub is supported (e.g. via a GitLab mirror)
- [ ] A **CMDB code** — request via [ServiceNow](https://redhat.service-now.com/help?id=sc_cat_item&sys_id=88c9c7bb137f1340196f7e276144b020)
- [ ] **Data classification** set on the CMDB record
- [ ] Platform team engagement initiated (see above)

---



## Application Team Steps



### 1. Add the `lightrail-local` dev dependency

The `lightrail-local` package provides a local CLI for running the app in a Lightrail-like environment. It is an optional, host-only dev dependency (not installed in the container).

```toml
# pyproject.toml
[tool.poetry.group.local.dependencies]
lightrail-local = { git = "https://gitlab.cee.redhat.com/dxp/platforms-pipelines/lightrail-platform/lightrail.git", tag = "1.19.0", subdirectory = "local" }
```

Install it with:

```bash
poetry install --with local
```



### 2. Create the `.light/` directory structure

```
.light/
├── light.yaml
├── local/
│   ├── PartialContainerfile   # optional: build-time patches
│   ├── config.env             # non-sensitive env vars for local dev
│   └── secrets.env            # NOT committed — local secrets (see secrets.env.example)
├── preview/
│   └── config.env
├── qa/
│   └── config.env
├── stage/
│   └── config.env
└── prod/
    └── config.env
```

`secrets.env` files are **not committed**. Only commit a `secrets.env.example` with placeholder values for local dev.

### 3. Create `.light/light.yaml`

```yaml
metadata:
  cmdb: <your-cmdb-code>   # e.g. LFG-002
application:
  entrypoint: main.sh      # shell script that starts the server on port 8080
health_check:
  path: /health
hooks:
  build:
    containerfile: .light/local/PartialContainerfile   # only if build-time patches are needed
```

Lightrail expects the application to listen on **port 8080**. TLS termination is handled by the platform's nginx proxy.

Create a `main.sh` entrypoint script:

```bash
#!/usr/bin/env bash
exec uv run insights-mcp http --host 0.0.0.0 --port 8080
```



### 4. Add env vars to `.light/<env>/config.env`

Non-sensitive configuration per environment. Auth env vars must be set **explicitly** per environment — Lightrail does not derive them automatically.

`.light/local/config.env` (for local dev with `lightrail-local-cli`):

```bash
AUTH_SERVER=https://mcp-auth.stage.api.redhat.com
AUTH_ISSUER=https://sso.stage.redhat.com/auth/realms/redhat-external
# AUTH_RESOURCE is NOT set here — override manually when testing OAuth locally:
#   export AUTH_RESOURCE=http://localhost:8000/mcp
INSIGHTS_BASE_URL=https://console.stage.redhat.com
```

`.light/qa/config.env`:

```bash
AUTH_SERVER=https://mcp-auth.stage.api.redhat.com
AUTH_ISSUER=https://sso.stage.redhat.com/auth/realms/redhat-external
AUTH_RESOURCE=https://insights-mcp.qa.api.redhat.com/mcp   # explicit per env
INSIGHTS_BASE_URL=https://console.stage.redhat.com
```

`.light/prod/config.env`:

```bash
AUTH_SERVER=https://mcp-auth.api.redhat.com
AUTH_ISSUER=https://sso.redhat.com/auth/realms/redhat-external
AUTH_RESOURCE=https://insights-mcp.api.redhat.com/mcp      # explicit per env
INSIGHTS_BASE_URL=https://console.redhat.com
```

> **Important:** `AUTH_RESOURCE` is **not** derived automatically from `LIGHTRAIL_ROUTE_HOSTNAME` or any Lightrail-injected variable. It must be set explicitly in each environment's `config.env`. For local dev without OAuth, leave it unset and override at the shell if needed.

> **Note:** Do not use the `LIGHTRAIL_`* prefix for custom variables — it is reserved by the platform.



### 5. Handle local secrets (no Vault required)

There is **no Vault integration** in the Lightrail model for this class of MCP server. Secrets for local development (e.g. CA bundle paths, override credentials) are managed with a `secrets.env` file that is never committed.

Create `.light/local/secrets.env.example`:

```bash
# Red Hat internal CA for stage endpoints (macOS local dev).
# Use EXTRA_CA_CERTS, NOT SSL_CERT_FILE — exporting SSL_CERT_FILE via set -a
# breaks JWKS/OAuth TLS handshakes.
EXTRA_CA_CERTS=/path/to/2022-IT-Root-CA.pem
```

Load env for local dev:

```bash
set -a && source .light/local/config.env && source .light/local/secrets.env && set +a
```

> In deployed environments (qa/stage/prod), Lightrail injects secrets through its own mechanism. No `secrets.env` files are needed for deployed envs.



### 6. Create `.light/local/PartialContainerfile` (optional)

Used to patch the Lightrail base image at build time — e.g. to strip dev dependencies from the container:

```dockerfile
# Strip dev deps: only install main group in the container
RUN sed -i 's/poetry install --no-interaction --no-ansi/poetry install --no-interaction --no-ansi --only main/' /lightrail/entrypoint.bash
```



### 7. Create `.gitlab-ci.yml`

Note: this pipeline is typically prepared before deployment and can be left commented out until the platform team confirms the tenant is ready.

```yaml
stages:
  - build
  - deploy-preview
  - deploy-qa
  - deploy-stage
  - deploy-prod
  - clean

variables:
  LIGHTRAIL_VERSION: &LIGHTRAIL_VERSION 1.19.0   # update to latest tag
  LIGHTRAIL_RELEASE_STRATEGY: branch
  LIGHTRAIL_RELEASE_BRANCH: main

include:
  - project: dxp/platforms-pipelines/lightrail-platform/lightrail
    ref: release-*{LIGHTRAIL_VERSION}
    file:
      - pipeline/global.yaml
      - pipeline/stages/build/build.yaml
      - pipeline/stages/deploy/deploy.yaml
      - pipeline/stages/clean/clean.yaml
```

No `validate` stage is needed — the reference implementation does not use it.

### 8. Update `catalog-info.yaml`

Use `kind: MCPServer` (not `kind: Component`) and declare Lightrail as a dependency:

```yaml
apiVersion: mcp/v1beta1
kind: MCPServer
metadata:
  name: insights-mcp
  namespace: redhat
  annotations:
    servicenow.com/appcode: <your-cmdb-code>
spec:
  owner: group:redhat/<your-team>
  dependsOn:
    - component:uxe/lightrail
    - system:redhat/mcp-auth-adapter
  auth:
    type: oauth2
    issuer: https://mcp-auth.api.redhat.com
    scope: <required-scope>
  remote:
    - url: https://insights-mcp.api.redhat.com/mcp
      type: streamable-http
```



### 9. Comply with required assessments

Before going to production:

- [ ] Privacy Impact Assessment (PIA)
- [ ] Enterprise Security Standard v8 (ESS) — Lightrail's pre-written responses cover most controls
- [ ] AI assessment

---



## Local Development with `lightrail-local-cli`

Three ways to run locally:

```bash
# Option 1: Direct (fastest for iteration)
set -a && source .light/local/config.env && source .light/local/secrets.env && set +a
uv run insights-mcp http --host 0.0.0.0 --port 8080

# Option 2: lightrail-local CLI (closest to deployed behavior)
poetry run lightrail-local-cli build
poetry run lightrail-local-cli start

# Option 3: via main.sh
bash main.sh
```

For local OAuth testing, override `AUTH_RESOURCE` after loading env:

```bash
export AUTH_RESOURCE=http://localhost:8080/mcp
```

---



## Environment URLs


| Environment | URL pattern                                               |
| ----------- | --------------------------------------------------------- |
| Preview     | `https://insights-mcp.preview-<mr-id>.api.redhat.com/mcp` |
| QA          | `https://insights-mcp.qa.api.redhat.com/mcp`              |
| Stage       | `https://insights-mcp.stage.api.redhat.com/mcp`           |
| Prod        | `https://insights-mcp.api.redhat.com/mcp`                 |


> Exact URL patterns depend on naming agreed with the platform team. The above follows the convention observed in the reference implementation (`security-mcp.<env>.api.redhat.com/mcp`).

---



## Auth in the Hosted Deployment

`mcp_rh_auth.build_auth_provider()` is already wired into the server. In each Lightrail environment:

- Set `AUTH_SERVER` and `AUTH_ISSUER` in `config.env` (non-sensitive)
- Set `AUTH_RESOURCE` **explicitly** to the environment's full MCP URL (e.g. `https://insights-mcp.qa.api.redhat.com/mcp`)
- `MCP_BASE_URL` is **not needed** in Lightrail deployments — `AUTH_RESOURCE` is set directly
- For local dev without auth, leave both unset; `build_auth_provider()` returns `None`

When `AUTH_SERVER` is set, the server enforces JWT validation on all inbound MCP requests.

---



## Observability

Lightrail injects `OTEL_EXPORTER_OTLP_ENDPOINT` automatically in deployed environments — no manual configuration needed for tracing.

Log queries (Splunk):

```
# Production
index=rh_paas kubernetes.labels.paas_redhat_com_appcode="<CMDB>"

# Preprod
index=rh_paas_preprod kubernetes.labels.paas_redhat_com_appcode="<CMDB>"
```

Filter `kubernetes.container_name` to `application` or `nginx`.

---



## Open Questions / TODOs

- [ ] Confirm CMDB code with the platform team
- [ ] Confirm the deployed URL convention for `insights-mcp` (used in `AUTH_RESOURCE` and `catalog-info.yaml`)
- [ ] Decide whether to use Poetry (required by `lightrail-local`) or `uv` as the primary package manager — the reference uses Poetry; `insights-mcp` currently uses `uv`
- [ ] Clarify whether the GitLab CI pipeline should be committed (even commented out) before engaging the platform team, or after
- [ ] Implement a `/health` endpoint if not already present (required by `light.yaml`)