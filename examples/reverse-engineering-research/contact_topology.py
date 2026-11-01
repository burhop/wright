"""Inspectable CAD-authoring utility, not a Wright executor or validation gate.

Imprint a declared two-face contact inside a declared edge-connected surface
group. No face is discarded, no fuzzy tolerance override is used, and the
surface set must be unchanged. STEP persistence must be checked independently.
"""

import cadquery as cq
from OCP.BOPAlgo import BOPAlgo_Splitter
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check


def connected_contact(components, *, contact_names, group_names, sewing_tolerance=1e-6):
    if len(contact_names) != 2 or len(set(contact_names)) != 2:
        raise ValueError("Declare exactly two distinct contacting face owners")
    if len(set(group_names)) != len(group_names) or not set(contact_names) <= set(
        group_names
    ):
        raise ValueError("Declare a unique connected group containing both owners")
    if not 0 < sewing_tolerance <= 1e-6:
        raise ValueError(
            "This qualified utility does not permit enlarged sewing tolerances"
        )
    original = {name: components[name] for name in group_names}
    if any(len(f.Faces()) != 1 or not f.isValid() for f in original.values()):
        raise ValueError("Only explicitly owned valid single faces are supported")
    splitter = BOPAlgo_Splitter()
    splitter.SetNonDestructive(True)
    for name in contact_names:
        splitter.AddArgument(original[name].wrapped)
    splitter.Perform()
    if splitter.HasErrors():
        raise ValueError("Contact imprint failed")
    pair = cq.Shape.cast(splitter.Shape())
    if (
        len(pair.Faces()) != 2
        or not BRepAlgoAPI_Check(pair.wrapped, True, True).IsValid()
    ):
        raise ValueError("Imprint must retain two interference-passing faces")
    sew = BRepBuilderAPI_Sewing(sewing_tolerance, True, True, True, False)
    for name, face in original.items():
        if name not in contact_names:
            sew.Add(face.wrapped)
    for face in pair.Faces():
        sew.Add(face.wrapped)
    sew.Perform()
    result = cq.Shape.cast(sew.SewedShape())
    if (
        len(result.Faces()) != len(original)
        or len(result.Shells()) != 1
        or not result.isValid()
    ):
        raise ValueError("Declare a group that forms one valid connected surface shell")
    mapped = {}
    for name, face in original.items():
        matches = [
            q
            for q in result.Faces()
            if abs(q.Area() - face.Area()) < 0.1
            and q.Center().sub(face.Center()).Length < 0.01
        ]
        if len(matches) != 1:
            raise ValueError("Ambiguous face association: " + name)
        q = matches[0]
        if face.cut(q).Faces() or q.cut(face).Faces():
            raise ValueError("Contact imprint changed geometry: " + name)
        mapped[name] = q
    a, b = (mapped[name] for name in contact_names)
    if not any(x.wrapped.IsSame(y.wrapped) for x in a.Vertices() for y in b.Vertices()):
        raise ValueError("Declared contact has no shared topological vertex")
    return result, mapped
