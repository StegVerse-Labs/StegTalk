# Mobile-Shell Session Checkpoint Rotation

The rotation boundary retains a bounded set of verified local checkpoints and restores the newest valid retained generation automatically.

Default retention is three generations. Generation numbering, history writes, pruning, integrity checks, and fallback selection are automatic.

The recovery path rejects altered history wrappers, altered entries, shell hash drift, receipt-chain drift, cross-session records, unsupported authority, and unsafe session identifiers. When the newest retained entry is corrupt but an earlier retained entry is valid, the most recent valid prior generation is selected automatically.

Rotation remains local-only, non-production, and non-authorizing. It grants no network, execution, external-account, or native-platform authority.
