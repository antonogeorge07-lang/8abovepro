# 8above Sovereign Deployment Model

8above uses one canonical product codebase.

Client deployments are composed from:

1. immutable application release
2. non-secret client deployment profile
3. environment-specific secrets
4. infrastructure deployment adapter

## Rules

- Never fork product source for a client customization.
- Never commit client secrets.
- Never commit production credentials.
- Never embed tenant identity into application source.
- Client identity and configuration are injected at deployment time.
- Every production deployment must reference an immutable Git commit or release tag.
- Every client environment must have an auditable deployment record.
- Production environments must not share persistent databases unless the approved deployment model explicitly permits it.
- Client entitlements remain server-authoritative.
- UI configuration must never grant backend authority.

## Deployment modes

Supported architecture target:

- shared application / isolated logical tenant
- dedicated application / dedicated data store
- private-cloud deployment
- customer-controlled infrastructure

The deployment adapter is responsible for translating the common
8above release package into the target infrastructure.
