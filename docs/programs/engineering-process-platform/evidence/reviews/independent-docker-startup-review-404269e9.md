# Independent Docker offline-startup correction review

Reviewed commit: `404269e9d8a7d6ff3f122877f0c19322fe99b47c`, parent `eb63344c`.
Reviewed tree: `2cd822df271eaf4de05f6a2856fcecbf3d16eeb7`.
Reviewer: independently delegated `native_candidate_review`; authored none of this change.

**No actionable P1/P2 finding. Correction accepted for this bounded scope.**

The supervisor now invokes `uv run --no-sync --project /workspace`, preserving the same uvicorn application, project, working directory, environment, process supervision and shutdown settings while using the environment installed during image construction. This addresses runtime dependency synchronization without substituting another interpreter environment or changing application behavior.

The smoke test's final stage starts a fresh container from the supplied exact `IMAGE_TAG`, with the normal entrypoint and default supervised command. It uses `--network none`, mounts no warmed state, provides no UV diagnostic override and publishes no host port. Container-local `docker exec` requests verify Wright API readiness, both supervised processes in RUNNING state, the Wright-to-Hermes connected state, and direct Hermes health. Loopback remains available inside an otherwise network-disabled container. The existing bounded retries, failure exits, diagnostic logs and EXIT-trap container cleanup remain intact. The changed check no longer tests host-port publishing; the relevant startup and two-service connectivity checks remain covered inside the exact container, as the new documentation states.

Inspected all three changed files, the image's environment-install/COPY sequence and the entrypoint's credential/provider bootstrap. Independently checked Bash syntax of the exact committed smoke script: passed. The author's reported 26 focused contract checks were not repeated or relabeled as independent runs. No image build or actual container invocation was performed by this reviewer; those remain the parent's actual candidate validation. The check proves service startup/connectivity when executed, not a real LLM response or native engineering run by itself.
