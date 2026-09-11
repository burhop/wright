import hashlib
import json
import pytest
from data_vault.state_store import connect_state_db
from data_vault.migrations import MIGRATIONS, validate_definitions
from data_vault.workflow_artifact_review_repository import WorkflowArtifactReviewRepository, ArtifactReviewConflict


def test_review_migration_is_additive_and_repository_survives_restart(tmp_path):
    validate_definitions()
    migration=MIGRATIONS[-1]
    assert migration.version==17 and migration.name=='terminal_workflow_artifact_reviews'
    database=str(tmp_path/'state.db')
    with connect_state_db(database) as db:
        db.execute('CREATE TABLE existing_artifacts (path TEXT, content BLOB)')
        db.execute('INSERT INTO existing_artifacts VALUES (?,?)',('draft.html',b'exact original'))
        for operation in migration.operations:operation.apply(db)
    repository=WorkflowArtifactReviewRepository(database)
    package={'snapshots':[{'path':'draft.html','sha256':hashlib.sha256(b'exact original').hexdigest()}]}
    repository.create('review','workspace','workflows/draft.wflow','a'*64,package)
    restarted=WorkflowArtifactReviewRepository(database)
    assert json.loads(restarted.get('workspace','review')['package_json'])==package
    with connect_state_db(database) as db:
        assert db.execute('SELECT content FROM existing_artifacts').fetchone()[0]==b'exact original'
    with pytest.raises(KeyError):restarted.get('another-workspace','review')


def test_decision_compare_and_set_leaves_immutable_package_and_original_timestamp(tmp_path):
    repository=WorkflowArtifactReviewRepository(str(tmp_path/'state.db'))
    repository.create('review','workspace','workflow.wflow','a'*64,{'original':'bytes'})
    before=repository.get('workspace','review')['package_json']
    decision={'state':'approved','actor':'local-workspace-user','reason':'','decided_at':'first'}
    repository.decide('workspace','review','a'*64,decision)
    record=repository.decide('workspace','review','a'*64,{**decision,'decided_at':'retry'})
    assert json.loads(record['decision_json'])['decided_at']=='first'
    assert record['package_json']==before
    with pytest.raises(ArtifactReviewConflict):repository.decide('workspace','review','b'*64,decision)
    with pytest.raises(ArtifactReviewConflict):repository.decide('workspace','review','a'*64,{**decision,'state':'changes_requested'})
