# Plan

Add a default-off operations facade over workspace files, the review index, and
the supervised runner. The facade reads the authoritative file before every
review and launch, so approval is revision-exact. Its API is thin and its web
tab uses only Wright endpoints; no editor code is imported into the React tree.

Migration 11 stores review metadata only. Rollback is the feature flag plus
leaving the table unused; migration is additive and preserves prior workflow
metadata. Program-wide approval applies.
