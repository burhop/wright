## Description
<!-- Provide a clear description of the changes you are proposing and the reasoning behind them. -->

## Related Issues
<!-- Link any related issues or discussions using standard keyword mapping (e.g. Closes #123 or Resolves #456). -->

## Workflow Platform Alignment
<!-- For workflow, review, validation, external-action, or tool-integration changes,
identify applicable V1-V7 decisions in docs/design/workflow-platform-vision.md.
State the general user journey, shared/external ownership, reused mechanisms,
evidence/revision behaviour, and the substantially different existing workflow
used to check shared mechanisms. Prefer existing external providers.
For process UI changes, apply docs/design/process-apps.md and explain interaction
bindings, shared style/client/components, workspace tabs, common-view fallback,
saved compatibility, and close/reopen behaviour against durable backend state.
Include generation through Wright's configured coding-agent role, resolved
model/instruction provenance, upfront input readiness, declared human pause/resume,
and absence of ad hoc runtime questions in unattended sections.
For unrelated changes, state why this section is not applicable. -->

## Checklist
Please review and check all items that apply to your submission:

- [ ] I have read the [CONTRIBUTING.md](CONTRIBUTING.md) guidelines.
- [ ] I read `docs/contributing/dev-push-runbook.md` before pushing this branch.
- [ ] I ran `scripts/check-dev-push.ps1` or `scripts/check-dev-push.sh` before the latest push.
- [ ] Before merge to `dev`, I ran the full dev merge gate or documented an exact host limitation.
- [ ] My changes follow the project's coding standards (ran `ruff check` / `eslint`).
- [ ] I have added or updated tests covering my changes.
- [ ] All existing and new tests pass locally.
- [ ] I have updated the documentation to reflect my changes.
- [ ] I addressed the applicable workflow platform decisions, ownership boundaries, and evidence, or explained why they do not apply.
- [ ] My branch is up to date with the target branch (`main` or `dev`).
- [ ] My changes do not introduce any breaking changes.
