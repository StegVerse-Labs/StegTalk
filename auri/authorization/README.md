# Auri Authorization Intake

This directory is the canonical repository intake point for externally authorized AURI-L1 deployment records.

The activation process remains fail-closed unless both files exist and pass machine verification:

```text
provider-binding.json
deployment-authorization.json
```

Required schemas:

```text
auri/schemas/provider-binding.schema.json
auri/schemas/deployment-authorization.schema.json
```

Automation:

```text
.github/workflows/auri-authorization-intake.yml
```

When both canonical documents are committed to the default branch, the intake workflow verifies them and dispatches the gated live-proof workflow automatically. No person needs to trigger the proof workflow, copy values into repository variables, or edit the activation state manually.

The documents must originate from an authorized external deployment and provider-binding process. This repository does not fabricate authorization, credentials, provider standing, or live deployment evidence.

Auri remains inactive until live health, cross-repository evidence, revocation evidence, and the final activation receipt all pass.
