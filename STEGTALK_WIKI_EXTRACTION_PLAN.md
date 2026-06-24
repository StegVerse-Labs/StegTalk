# StegTalk Wiki Extraction Plan

## Status

The dedicated StegTalk wiki repository now exists at `StegVerse-Labs/stegtalk-wiki`. The staged package from `StegVerse-Labs/StegTalk` has been installed into that target wiki with page index, receipt, and README navigation.

## Source Package

Source location: `wiki-staging/`

Staged source files retained for traceability:

- `wiki-staging/README.md`
- `wiki-staging/pages/message-lifecycle.md`
- `wiki-staging/pages/contact-routing.md`
- `wiki-staging/pages/local-inbox-and-store.md`
- `wiki-staging/pages/public-discovery.md`
- `wiki-staging/pages/shell-runtime.md`
- `wiki-staging/pages/account-runtime.md`
- `wiki-staging/pages/wiki-overlap-map.md`
- `wiki-staging/data/page-index.json`
- `wiki-staging/data/install-manifest.json`
- `wiki-staging/data/install-checklist.json`
- `wiki-staging/data/target-repo-request.json`
- `wiki-staging/receipts/wiki-staging-receipt.json`

## Target Install Complete

Destination: `StegVerse-Labs/stegtalk-wiki`

Installed target files:

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
- `receipts/wiki-migration-receipt.json`

## Verification

Installed verification files in source repo:

- `scripts/report_wiki_staging_install.py`
- `scripts/report_wiki_target_blocker.py`
- `tests/test_wiki_staging_install.py`
- `tests/test_wiki_target_blocker.py`

## Linked Wikis

- `StegVerse-002/stegguardian-wiki`
- `StegVerse-Labs/admissibility-wiki`
- `StegVerse-Labs/Site`

## Remaining Open Check

None.

## Boundary

StegTalk remains a non-production local prototype candidate. Wiki extraction does not imply production readiness.
