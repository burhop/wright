# Handle inspection resources

`inspection-resources-v1.zip` is an ordinary ZIP of the existing passive reader,
package inspector, proposed-selection operation and exact separately qualified
support-enabled profiles. It is a portable workflow dependency, not an executor,
provider or approval authority. No new library installation is required.

Build a fresh file with `python build_inspection_resources.py /fresh/output.zip`.
The build is deterministic. Its manifest lists file hashes and sizes; the whole
archive SHA-256 is
`d6c8710ff13deec734094443569518746010504a7723b1c43ec63654fd427fe5` (80,701 bytes).
The integrity/operation test executes the packaged passive code on synthetic
recorded observations, then verifies the selected package stays byte-identical.
Changes to the underlying code/profiles require a new version and visible accepted
workflow revision; never overwrite an already accepted dependency.

Upload is verified through candidate 036's actual compiled workspace UI:
`uploads/d6c8710ff13deec734094443569518746010504a7723b1c43ec63654fd427fe5/inspection-resources-v1.zip`.
The API download and disk bytes match exactly. Accepted workflow revision 8 did
not change. No archive member was extracted or executed by the upload operation.

Remaining binding work:
- Connect this file using the existing workspace-file input and file-dependency
  contract; freeze it before dispatch and preserve it in portable export/import.
- Through the selected independent Python provider, verify the whole archive
  against the connected file identity, then load only the three named code files
  and three profile members. Do not extract arbitrary archive paths.
- Select/freeze the support-enabled slicer profile configuration explicitly; the
  existing candidate still selects the earlier support-disabled profile.
- Supply exact recorded observation file and both actual mesh/package pairs.
- Keep final validation and real engineering review separate. The native PNG
  shows model orientation, not generated supports; use the actual nominal-path
  representation for support-path inspection and expose its limitations.

This does not establish workflow export/import, provider-side execution, actual
handle acceptance, or Windows delivery. See the story/status plan and
`../evidence/candidate-036-inspection-resources/`.

## Version 2 candidate

`inspection-resources-v2.zip` adds optional exact nominal-support retention to
`retain_selection`: supply `support_output` alongside the existing output paths.
Both alternatives' support evidence must still match their inspection receipts
before any selected output is written. The selection record retains the original
and copied support identities. A proposed choice is still not engineering approval.

SHA-256 `88cca1f2aecee63de6b8951d62a5b6ac15f8a7fcb96f828b3b190a7aaf357b4c`,
81,795 bytes. Version 1 remains unchanged for accepted revision 9. The builder
now reproduces version 2; historical versions are immutable, not rebuilt in place.
56 focused tests pass, including changed evidence for either orientation and
output-path alias denial before publication. New-version upload and deliberate
source revision are separate qualification steps.
