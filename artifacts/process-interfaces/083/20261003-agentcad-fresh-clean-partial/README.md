# Fresh AgentCAD installation and partial qualification

AgentCAD 0.6.0, build123d 0.10.0, NumPy 2.5.2 and MCP 1.28.1 were freshly
installed with selected prerequisites from the neutral Linux/amd64 Wright image.
The base had no AgentCAD/build123d/OCP host dependency. Official stdio MCP lists
eleven tools; schemas match both production gateway projections exactly.

One production-gateway run tool call created a valid 2 x 3 x 4 mm STEP/native
version but returned JSON status=error because its formatter received progress
text mixed with CLI JSON. The strict qualification assertion failed. This
reproduces the earlier Windows issue on fresh Linux and does not qualify the
creation success receipt. No creation was repeated after native completion.

A separately recorded read-only gateway measure call reopened those exact STEP
bytes successfully: dimensions 2/3/4 mm, volume 24 mm3, valid deliverable. The
creation error, successful native metadata and successful readback remain
separate evidence. Wright adds no provider formatter/protocol workaround.

The backend ran with network none and one isolated workspace mount; the
production gateway ran on the current native Windows source environment.
Both exact owned containers are revalidated stopped; stdio gateway runners also
closed. No campaign, human acceptance or physical operation is implied. T043
remains open for unresolved selected bindings and other provider qualification.
Authentication contexts, private databases and traces are excluded.
