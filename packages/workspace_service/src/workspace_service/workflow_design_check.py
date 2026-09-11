"""Fail-closed, bounded design checks over existing native workflow tasks."""
import json

from .workflow_source_execution import _invalid


CHECK_INSTRUCTIONS = """
Return JSON with verdict (pass, revise, or needs_input), checks (a nonempty array
of objects with requirement, expected, observed, status (pass/fail/unverified),
and evidence (a nonempty array of successful tool-call numbers)), and corrections
(an array of concrete corrections or missing decisions). Pass requires every
check to pass and no corrections. Revise requires at least one failed check
with successful tool-call evidence and concrete corrections. It may retain
unverified checks: preserve each unknown and its missing evidence or decision
alongside the measured failures. Revision authorizes only the configured bounded
correction attempt, not acceptance or downstream release. With no evidenced
failure to correct, return needs_input for unresolved requirements or evidence.
Never turn absent measurements, unknown requirements, or unavailable capability
into a passing check. Inspect without changing the supplied model.
Use the datum definitions required by the specification. For physical or virtual
datums, establish their mapping to observed geometry; do not invent a requirement
for named native PMI or annotations unless the specification requests them.
"""


def _native_evidence_allows_pass(value):
    """Honor explicit provider verdicts; do not infer acceptance from prose.

    Solid Edge's inspection-verification tool can complete successfully while
    allCriticalRequirementsPass is false. Its transport status is not a gate.
    Evidence numbers cite whole calls, so a mixed verification report cannot
    establish a passing check by silently dropping its rejected observations.
    Raw observed geometry marked not_evaluated remains available for the AI's
    separate comparison; this guard does not claim numeric or coverage checks.
    """
    for _ in range(4):
        if not isinstance(value, dict):
            return True
        if any(key in value and value[key] is not True for key in ('isValid', 'isSuccess')):
            return False
        for key in ('overall', 'verdict'):
            if key not in value:
                continue
            outcome = value[key]
            if isinstance(outcome, dict):
                labels = [outcome[k] for k in ('status', 'verdict', 'disposition') if k in outcome]
                flags = [outcome[k] for k in ('isValid', 'isSatisfied') if k in outcome]
                if not labels and not flags:
                    return False
                if any(flag is not True for flag in flags):
                    return False
            else:
                labels = [outcome]
            if any(not isinstance(label, str) or label.casefold() not in {'pass', 'passed', 'valid', 'succeeded'} for label in labels):
                return False
        verification = any(key in value for key in ('inspection', 'requirementEvaluations', 'allCriticalRequirementsPass'))
        if verification:
            inspection = value.get('inspection')
            evaluations = value.get('requirementEvaluations')
            if (value.get('allCriticalRequirementsPass') is not True
                    or not _inspection_passes(inspection)
                    or not isinstance(evaluations, list) or not evaluations):
                return False
            for evaluation in evaluations:
                observation = evaluation.get('observation') if isinstance(evaluation, dict) else None
                if (not isinstance(evaluation, dict) or evaluation.get('isSatisfied') is not True
                        or evaluation.get('isBlocking') is not False or evaluation.get('disposition') != 'pass'
                        or not isinstance(observation, dict)
                        or not _observed_status(observation.get('evidenceStatus'), verification=True)):
                    return False
        elif value.get('evidenceKind') == 'inspection':
            if not _inspection_passes(value):
                return False
        elif 'evidenceStatus' in value and not _observed_status(value['evidenceStatus'], verification=False):
            return False
        wrapper = next((key for key in ('result', 'structuredContent', 'structured_content') if isinstance(value.get(key), dict)), None)
        if wrapper is None:
            return True
        value = value[wrapper]
    return False  # Unexpected wrapper depth is not accepted verification.


def _observed_status(status, *, verification):
    return (isinstance(status, dict) and status.get('provenance') == 'observed'
            and status.get('disposition') in ({'pass'} if verification else {'pass', 'not_evaluated'}))


def _inspection_passes(inspection):
    if not isinstance(inspection, dict) or not _observed_status(inspection.get('evidenceStatus'), verification=True):
        return False
    observations = inspection.get('observations')
    return (isinstance(observations, list) and bool(observations)
            and all(isinstance(item, dict) and _observed_status(item.get('evidenceStatus'), verification=True)
                    for item in observations))


def _is_native_verification_report(value, *, complete=False):
    """Recognize the provider's inspection contract, not arbitrary metadata."""
    for _ in range(4):
        if not isinstance(value, dict):
            return False
        keys = ('inspection', 'requirementEvaluations', 'allCriticalRequirementsPass')
        if (all(key in value for key in keys) if complete else
                value.get('evidenceKind') == 'inspection' or any(key in value for key in keys)):
            return True
        wrapper = next((key for key in ('result', 'structuredContent', 'structured_content') if isinstance(value.get(key), dict)), None)
        if wrapper is None:
            return False
        value = value[wrapper]
    return False


def inspect_verdict(response, calls):
    try:
        report = json.loads(response)
        assert isinstance(report, dict)
        verdict, checks = report['verdict'], report['checks']
        assert verdict in {'pass', 'revise', 'needs_input'}
        assert isinstance(checks, list) and 0 < len(checks) <= 100
        assert isinstance(report.get('corrections'), list)
        assert all(isinstance(item, str) and item.strip() for item in report['corrections'])
        for check in checks:
            assert isinstance(check, dict)
            assert all(isinstance(check.get(key), str) and check[key].strip()
                       for key in ('requirement', 'expected', 'observed'))
            assert check.get('status') in {'pass', 'fail', 'unverified'}
            evidence = check.get('evidence')
            assert isinstance(evidence, list)
            assert all(type(n) is int and 1 <= n <= len(calls)
                       and calls[n - 1].get('status') == 'succeeded' for n in evidence)
            if check['status'] != 'unverified':
                assert evidence
        if verdict == 'pass':
            assert all(c['status'] == 'pass' for c in checks)
            assert not report['corrections']
            cited = {n for check in checks for n in check['evidence']}
            # A failed verification of this bound model cannot disappear by
            # citing another call. Capability discovery and other uncited raw
            # observations are not treated as verification reports.
            native_reports = {index + 1 for index, call in enumerate(calls)
                              if _is_native_verification_report(call.get('result'))}
            # Gateway tool names are server_id__upstream_tool_name. Do not let
            # a known verification call lose its contract by returning no JSON.
            # Locally rejected arguments did not invoke the provider at all.
            native_calls = {index + 1 for index, call in enumerate(calls)
                            if str(call.get('tool', '')).rsplit('__', 1)[-1] == 'cad.verify_inspection_requirements'
                            and call.get('status') != 'invalid_arguments'}
            for number in cited | native_reports | native_calls:
                value = calls[number - 1].get('result')
                if ((number in native_calls and not _is_native_verification_report(value, complete=True))
                        or not _native_evidence_allows_pass(value)):
                    raise _invalid('The design check claimed a pass despite native evidence that failed or is unverified.',
                                   'Review the native inspection results in this check. Correct the measured failure or obtain the missing evidence before releasing downstream work.')
        else:
            assert report['corrections']
        if verdict == 'revise':
            assert any(c['status'] == 'fail' for c in checks)
        return report
    except (ValueError, KeyError, TypeError, AssertionError):
        raise _invalid('The design check did not return a supported, evidenced verdict.',
                       'Inspect the check report and tool log. Downstream work has not been released.') from None


def validate_rework(steps, revisions):
    """One explicit contiguous rework segment; never infer a back-edge."""
    if len(revisions) > 1:
        raise _invalid('This executor supports one bounded design-check revision path per workflow.')
    order = {step.id: i for i, step in enumerate(steps)}
    for check_id, target_id in revisions.items():
        check = steps[order[check_id]]
        if not check.design_check or target_id not in order or order[target_id] >= order[check_id]:
            raise _invalid('A revision path must return from a design check to an earlier task.')
        segment = steps[order[target_id]:order[check_id]]
        if len(segment) != 1 or check.cad_from not in {f'{target_id}.{key}' for key, kind in segment[0].output_ports if kind == 'cad_model'} or any(not s.agent_task or not s.cad or s.cad.get('source') != 'new'
                              or s.cad.get('policy', 'indexed') != 'indexed' for s in segment):
            raise _invalid('Automatic rework currently requires one preceding CAD creation task, its model connected to this check, and indexed files.',
                           'Use a create-new CAD task for the revision target. Existing/session edits require an explicit new run.')
        if check.max_revisions < 1:
            raise _invalid('Set a revision limit before connecting a revision path.')
