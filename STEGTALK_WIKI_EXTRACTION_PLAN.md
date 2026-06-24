# StegTalk Wiki Extraction Plan

## Status

A dedicated StegTalk wiki repository was not found during repository search. The StegTalk wiki package is now staged, indexed, receipted, and covered by CI inside `StegVerse-Labs/StegTalk`.

## Staged Package

Source location: `wiki-staging/`

Installed staged files:

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

## Verification

Installed verification files:

- `scripts/report_wiki_staging_install.py`
- `scripts/report_wiki_target_blocker.py`
- `tests/test_wiki_staging_install.py`
- `tests/test_wiki_target_blocker.py`

CI verifies staged source files and the target-repo blocker report.

## Linked Wikis

- `StegVerse-002/stegguardian-wiki`
- `StegVerse-Labs/admissibility-wiki`
- `StegVerse-Labs/Site`

## Remaining Open Check

- `SW-001`: target repo exists

Preferred target repo:

- `StegVerse-Labs/stegtalk-wiki`

## Boundary

StegTalk remains a non-production local prototype candidate. Wiki extraction must not imply production readiness.
