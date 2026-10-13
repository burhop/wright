"""Original bounded conduction case; millimetres, no holes or interfaces."""
from steve import Model

length = 100  # mm Conduction length
width = 60  # mm Candidate width
thickness = 2  # mm Plate thickness
model = Model()
with model.sketch("outline", on="XY", name="Heat strap outline") as s:
    s.rect("r1", (0, 0), (length, width))
model.extrude("strap", "outline", distance=thickness)
result = model.result()
