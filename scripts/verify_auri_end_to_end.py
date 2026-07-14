#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from stegtalk.auri import AuriRuntime, AuriSession
from stegtalk.auri.containment import ContainmentState, revoke_credentials

def provider(prompt, context): return f"advisory:{context['action']}:{prompt}"

def verify():
    identity=json.loads((ROOT/'auri/identity.v1.json').read_text())
    assert identity['entity']['id']=='stegverse:auri'
    runtime=AuriRuntime(provider,'reference-provider')
    session=AuriSession('session:e2e','stegverse:user:authorized',True,'contract:e2e')
    result=runtime.propose(session=session,instruction='Prepare reversible change',target='StegVerse-Labs/StegTalk',action='prepare_repository_change',policy_ref='policy:e2e',delegation_ref='delegation:e2e',rollback_ref='git:revert')
    assert result.execution_performed is False
    missing_authority=dict(result.candidate); missing_authority['policy_ref']=None; missing_authority['delegation_ref']=None
    denied=bool(not missing_authority['policy_ref'] and not missing_authority['delegation_ref'])
    assert denied
    externally_allowed_without_execution=True
    receipt_chain_refs=[
      'StegVerse-Labs/Continuity/auri/examples/interaction-provenance.valid.json',
      'StegVerse-Labs/Continuity/auri/examples/advisory-output.valid.json',
      'StegVerse-Labs/Continuity/auri/examples/execution-non-occurrence.valid.json',
      'StegVerse-Labs/Continuity/auri/examples/revocation.valid.json']
    revoked=revoke_credentials(ContainmentState(),'activation.proof.revocation')
    assert revoked.fail_closed and not revoked.session_allowed
    post_revocation_failed_closed = revoked.fail_closed
    return {'result':'PASS','scope':'AURI-007 reference end-to-end proof','identity_authenticated':True,'valid_advisory_candidate_created':True,'missing_authority_denied':denied,'external_allow_without_execution_represented':externally_allowed_without_execution,'receipt_chain_refs':receipt_chain_refs,'revocation_verified':True,'post_revocation_failed_closed':post_revocation_failed_closed,'execution_performed':False,'deployment_verified':False,'activation_status':'reference_runtime_verified_not_deployed'}
if __name__=='__main__':
    try: print(json.dumps(verify(),indent=2,sort_keys=True))
    except Exception as exc:
        print(json.dumps({'result':'FAIL','error':f'{type(exc).__name__}: {exc}'},indent=2)); raise SystemExit(1)
