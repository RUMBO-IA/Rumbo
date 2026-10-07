# RUMBO sandbox and access matrix

Status: operating guidance. Provider pricing and quotas must be rechecked before use.

## Default order

Prefer the least privileged and least costly environment that can do the work:

1. local Dev Container on the contributor's machine;
2. DevPod using local Docker or an already-authorized SSH host;
3. the contributor's personal GitHub Codespaces allowance;
4. a dedicated private Closed Lab repository with local or contributor-funded compute;
5. self-hosted Coder Community on infrastructure RUMBO already controls;
6. metered cloud sandboxes only after explicit cost authorization.

## Matrix

| Environment | Public contributor | Private collaborator | RUMBO secrets | Default cost posture |
| --- | --- | --- | --- | --- |
| Local Dev Container | Yes | Yes | No | Preferred |
| DevPod + local Docker | Yes | Yes | No | Preferred |
| DevPod + approved SSH host | No by default | Yes | Only if separately approved | Allowed only on existing infrastructure |
| Personal GitHub Codespaces | Yes | Yes | No | Contributor's own included quota |
| Organization-funded Codespaces | No | No by default | No by default | Blocked until USD 0 is proven |
| Coder Community on existing RUMBO infrastructure | No by default | Yes | Scoped only | Optional Closed Lab backend |
| RUMBO self-hosted GitHub Actions runner | No | Trusted paths only | Scoped | Never for untrusted PR code |
| Metered cloud sandbox | No by default | No by default | No | Blocked without explicit authorization |

## Public Open Lab

The source sandbox is normally a contributor fork. Local Dev Containers, DevPod, or a personal Codespace may be used to edit and test the fork.

The environment must not receive production credentials, customer data, canonical private repository access, or RUMBO deployment authority.

## Private Closed Lab

The source boundary is a dedicated private lab repository. Access to canonical private repositories is not inherited.

Prefer outside-collaborator access when a person needs only the lab repository. Use the minimum repository role and remove access when the engagement ends.

## GitHub Codespaces cost rule

GitHub's included Codespaces allowance belongs to personal accounts, not organization or enterprise accounts. Organization-funded Codespaces therefore remain disabled by default under the RUMBO zero-spend policy.

A contributor may use their own personal included quota. RUMBO must not silently become the billing owner for that workspace.

## GitHub Actions cost rule

The future public Open Lab should use standard GitHub-hosted runners with explicit read-only permissions for untrusted CI.

Private Closed Lab workflows consume the organization's plan allowance. GitHub Free for organizations currently publishes a finite included Actions allowance. Treat it as a hard operational ceiling, not as permission for paid overage: if included private CI is exhausted, private CI stops or moves to already-owned/local infrastructure unless spending is explicitly authorized.

## Cloud sandbox rule

Usage-based cloud sandboxes are not treated as free merely because a trial or credit exists. Credits are finite and do not authorize automatic continuation into paid usage.

## Runner rule

Public or otherwise untrusted contribution code must not execute on RUMBO self-hosted runners. Use isolated GitHub-hosted CI or contributor-owned environments for that code.

## Promotion boundary

Sandbox access never implies repository write, merge, deployment, secret, or production authority.
