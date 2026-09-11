import asyncio

from api.routers import workspace as router
from api.schemas.workspace import WorkflowSourceRecentRunsResponse, WorkflowArtifactReviewDecisionRequest
from packages.workspace_service.tests.test_workflow_artifact_review import run_review
from apps.api.tests.test_workflow_artifact_reviews_api import scope_service


def test_latest_snapshot_preserves_authoritative_review_and_response_contract(tmp_path):
    result,svc,_,_=asyncio.run(run_review(tmp_path));scope_service(tmp_path,svc)
    async def scenario():
        pending=await router.workflow_recent_runs('s','workflows/rfq.workflow.wflow',svc,latest_only=True)
        run=pending['runs'][0]
        assert run['status']=='pending_review' and run['execution']['active_task_id'] is None
        assert run['source_matches_current'] is True and run['run_id']==result['run_id']
        assert len(run['execution']['outputs'])==2
        WorkflowSourceRecentRunsResponse.model_validate(pending)
        await router.workflow_artifact_review_decision(result['review']['review_id'],
            WorkflowArtifactReviewDecisionRequest(session_id='s',expected_package_digest=result['review']['package_digest'],
                                                  decision='changes_requested',reason='Controlled test missing dimension'),svc)
        changed=await router.workflow_recent_runs('s','workflows/rfq.workflow.wflow',svc,latest_only=True)
        assert changed['runs'][0]['status']=='changes_requested'
        assert changed['runs'][0]['execution']['active_task_id'] is None
        assert changed['runs'][0]['review']['state']=='changes_requested'
        (tmp_path/'context.md').write_text('Changed after review')
        stale=await router.workflow_recent_runs('s','workflows/rfq.workflow.wflow',svc,latest_only=True)
        assert stale['runs'][0]['review']['evidence_status']=='stale'
    asyncio.run(scenario())
