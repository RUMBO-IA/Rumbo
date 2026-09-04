# Security and privacy

RUMBO IA treats public identity, credentials, and deployment configuration as controlled surfaces.

## Public repository rules

- Do not commit credentials, tokens, private keys, `.env` files, private client data, or legal-identity material.
- Public founder attribution must use only the approved public display name.
- Commit author metadata must use the approved public identity and business or GitHub noreply email.
- Pull requests and protected-branch updates must pass the privacy and deployment checks before promotion.
- Security headers are verified deterministically from repository configuration.

## Reporting

Use GitHub's **Report a vulnerability** flow under the repository Security tab for undisclosed security issues. Private vulnerability reporting is enabled for this repository.

If the GitHub private-reporting channel is unavailable, use `sebastian@rumbo.verso.fans`. Do not include secrets, private client data, or exploit details in public issues.

GitHub secret scanning and push protection are enabled on this public repository as an additional guard against accidental credential disclosure.