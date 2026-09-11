import asyncio
import hashlib
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from api.routers import workspace as router
from api.schemas.workspace import WorkflowArtifactReviewDecisionRequest, WorkflowSourceRunRequest
from packages.workspace_service.tests.test_workflow_artifact_review import run_review, source


def scope_service(root, svc):
    svc.lifecycle=SimpleNamespace(get_by_session=lambda session: {'workspace_id':'ws' if session=='s' else 'other','local_path':str(root)})
    svc.ensure_workspace_path_safe=lambda path:path
    return svc


def test_review_endpoints_scope_identity_and_unverified_local_attribution(tmp_path):
    result,svc,_,_=asyncio.run(run_review(tmp_path));scope_service(tmp_path,svc)
    review=result['review']
    async def scenario():
        listed=await router.workflow_artifact_reviews('s','workflows/rfq.workflow.wflow',svc)
        assert listed['reviews']==[{**review,'evidence_status':'current'}]
        with pytest.raises(HTTPException) as error:await router.workflow_artifact_review(review['review_id'],'foreign',svc)
        assert error.value.status_code==404
        bad=WorkflowArtifactReviewDecisionRequest(session_id='s',expected_package_digest='0'*64,decision='approved')
        with pytest.raises(HTTPException) as error:await router.workflow_artifact_review_decision(review['review_id'],bad,svc)
        assert error.value.status_code==409 and error.value.detail['code']=='workflow_review_stale'
        body=WorkflowArtifactReviewDecisionRequest(session_id='s',expected_package_digest=review['package_digest'],decision='changes_requested',reason='Missing material',actor='Pretend authenticated approver')
        changed=await router.workflow_artifact_review_decision(review['review_id'],body,svc)
        assert changed['state']=='changes_requested' and changed['actor']=='local-workspace-user'
        assert changed['attribution']=='local_workspace_user_not_authenticated'
        history=await router.workflow_recent_runs('s','workflows/rfq.workflow.wflow',svc)
        assert history['runs'][0]['status']=='changes_requested' and history['runs'][0]['review']=={**changed,'evidence_status':'current'}
        (tmp_path/'context.md').write_text('A later design context')
        later=await router.workflow_artifact_review(review['review_id'],'s',svc)
        assert later['evidence_status']=='stale' and later['state']=='changes_requested'
    asyncio.run(scenario())


def test_native_stream_terminates_pending_review_without_waiting_or_autoapproval(tmp_path,monkeypatch):
    _,svc,_,_=asyncio.run(run_review(tmp_path));scope_service(tmp_path,svc)
    calls=[]
    async def generate(prompt,fmt,**kwargs):
        calls.append(fmt)
        return '{"revision":"B"}' if fmt=='json' else '<!doctype html><html><body>Another draft</body></html>'
    monkeypatch.setattr(router,'generate_workflow_response',generate)
    request=SimpleNamespace(headers={'accept':'application/x-ndjson'})
    body=WorkflowSourceRunRequest(session_id='s',path='workflows/rfq.workflow.wflow',expected_storage_digest=hashlib.sha256(source().encode()).hexdigest())
    async def scenario():
        response=await router.run_workflow_source_endpoint(body,request,svc)
        chunks=[]
        async with asyncio.timeout(5):
            async for chunk in response.body_iterator:chunks.append(json.loads(chunk))
        assert chunks[-1]['kind']=='pending_review'
        assert chunks[-1]['result']['status']=='pending_review'
        assert chunks[-1]['result']['review']['state']=='pending'
        assert not any(item['kind']=='completed' for item in chunks)
        assert calls==['json','html']
    asyncio.run(scenario())
