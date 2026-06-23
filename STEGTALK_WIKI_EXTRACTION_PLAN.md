# StegTalk Wiki Extraction Plan

## Status

A dedicated StegTalk wiki repository was not found during repository search. Until that repository exists, this file records the planned split between StegTalk-owned documentation and overlapping ecosystem wiki pages.

## StegTalk-Owned Wiki Scope

StegTalk should own pages describing product/runtime behavior:

- message lifecycle
- contact routing
- local inbox projection
- local persistence
- public discovery record, index, search, and demo
- shell state and shell actions
- account profile and account session runtime
- local prototype candidate status

## StegGuardian Overlap

StegGuardian owns guardian, recovery, account authority, device trust, and protective boundary concepts that overlap with StegTalk account/session behavior.

Linked pages:

- `StegVerse-002/stegguardian-wiki/pages/stegtalk-guardian-account-boundary.md`
- `StegVerse-002/stegguardian-wiki/pages/guardian-account-boundary-vocabulary.md`
- `StegVerse-002/stegguardian-wiki/pages/recovery-authority.md`
- `StegVerse-002/stegguardian-wiki/pages/account-federation.md`
- `StegVerse-002/stegguardian-wiki/pages/device-bound-guardian-enforcement.md`

## Admissibility Overlap

Admissibility owns standing, authority, execution, and transition validity concepts that overlap with StegTalk account/session and guardian-recovery flows.

Linked page:

- `StegVerse-Labs/admissibility-wiki/pages/stegtalk-admissibility-boundary.md`

## Site Overlap

Site owns public-facing explanation, navigation, and demo visibility. It should publish StegTalk concept summaries, not merely mirror repo status.

Linked records:

- `StegVerse-Labs/Site/data/stegtalk-local-candidate.json`
- `StegVerse-Labs/Site/data/stegtalk-local-candidate-receipt.json`

## Next Automated Task

When a StegTalk wiki repository exists, install:

- `STEGTALK_WIKI_MIRROR_HANDOFF.md`
- `README.md`
- `pages/message-lifecycle.md`
- `pages/contact-routing.md`
- `pages/local-inbox-and-store.md`
- `pages/public-discovery.md`
- `pages/shell-runtime.md`
- `pages/account-runtime.md`
- `pages/wiki-overlap-map.md`
- `data/page-index.json`
- `receipts/wiki-extraction-receipt.json`

## Boundary

StegTalk remains a non-production local prototype candidate. Wiki extraction must not imply production readiness.
