from steve import Design
from components.marker import marker
design = Design()
design.add(marker, name="first_marker")
design.add(marker, name="second_marker", at=(100, 0, 0))
result = design.result()
