# Security and privacy

RUMBO IA treats public identity, credentials, and deployment configuration as controlled surfaces.

## Public repository rules

- Do not commit credentials, tokens, private keys, `.env` files, private client data, or legal-identity material.
- Public founder attribution must use only the approved public display name.
- Commit author metadata must use the approved public identity and business or GitHub noreply email.
- Pull requests and protected-branch updates must pass the privacy and deployment checks before promotion.
- Security headers are verified deterministically from repository configuration.

## Reporting

For responsible reports about this public surface, use `sebastian@rumbo.verso.fans` and avoid including secrets or unnecessary personal data in public issues.