#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from stegtalk.auri.containment import ContainmentState, quarantine_provider, revoke_credentials, begin_recovery, complete_recovery

def verify():
    healthy=ContainmentState()
    q=quarantine_provider(healthy,'provider.exception')
    assert q.fail_closed and not q.provider_enabled and not q.session_allowed and not q.execution_allowed
    r=revoke_credentials(healthy,'credential.compromised')
    assert r.fail_closed and not r.credential_valid and not r.session_allowed
    recovering=begin_recovery(r,known_good_identity_ref='auri/identity.v1.json',rollback_ref='git:known-good')
    failed=complete_recovery(recovering,identity_verified=True,rollback_verified=False,credential_reissued=True,provider_verified=True)
    assert failed.fail_closed and failed.reason_code=='recovery.gate_failed'
    recovered=complete_recovery(recovering,identity_verified=True,rollback_verified=True,credential_reissued=True,provider_verified=True)
    assert recovered.status=='healthy' and not recovered.fail_closed and recovered.execution_allowed is False
    return {'result':'PASS','scope':'AURI-006 containment and recovery','provider_quarantine_verified':True,'credential_revocation_verified':True,'failed_recovery_fail_closed':True,'verified_recovery_restores_advisory_only':True,'execution_remains_forbidden':True,'next_task':'AURI-007 end-to-end activation proof'}

if __name__=='__main__':
    try: print(json.dumps(verify(),indent=2,sort_keys=True))
    except Exception as exc:
        print(json.dumps({'result':'FAIL','error':f'{type(exc).__name__}: {exc}'},indent=2)); raise SystemExit(1)
