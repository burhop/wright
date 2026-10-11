"""Synthetic native reaction-output readiness fixture, not a bracket analysis."""
import hashlib
import shutil
import numpy as np
import meshio
from skfem import __version__ as skfem_version
import json
from pathlib import Path
import subprocess

root = Path('/workspace/qualification/oasis-native-fea-002')
root.mkdir(parents=True,exist_ok=False)
deck = '''*HEADING
Synthetic 10x10x1 mm one-element reaction-output qualification
*NODE
1,0,0,0
2,10,0,0
3,10,10,0
4,0,10,0
5,0,0,1
6,10,0,1
7,10,10,1
8,0,10,1
*ELEMENT,TYPE=C3D8,ELSET=PART
1,1,2,3,4,5,6,7,8
*NSET,NSET=FIXED
1,2,3,4
*NSET,NSET=TOP
5,6,7,8
*NSET,NSET=NALL,GENERATE
1,8
*MATERIAL,NAME=MAT
*ELASTIC
69000,0.33
*SOLID SECTION,ELSET=PART,MATERIAL=MAT
*STEP
*STATIC
*BOUNDARY
FIXED,1,3
*CLOAD
TOP,3,-0.25
*NODE PRINT,NSET=NALL
U,RF
*EL PRINT,ELSET=PART
S
*NODE FILE
U,RF
*EL FILE
S
*END STEP
'''
(root/'fixture.inp').write_text(deck,encoding='utf-8')
run = subprocess.run(['ccx','-i','fixture'],cwd=root,capture_output=True,text=True,timeout=60)
(root/'ccx.log').write_text(run.stdout+'\n'+run.stderr)
assert run.returncode==0, 'Native fixture solve failed; see preserved ccx.log'
text=(root/'fixture.dat').read_text()
forces=[]
section=False
for line in text.splitlines():
    lower=line.lower()
    if 'forces (' in lower:
        section=True
        continue
    if any(x in lower for x in ('displacements (','stresses (')):
        section=False
    values=line.split()
    if section and len(values)==4:
        try: forces.append([int(values[0]),*[float(x.replace('D','E')) for x in values[1:]]])
        except ValueError: pass
fixed=[row for row in forces if row[0] in (1,2,3,4)]
assert len(fixed)==4, 'Missing actual fixed-node reaction rows'
reaction=[sum(row[axis] for row in fixed) for axis in (1,2,3)]
assert abs(reaction[2]-1)<1e-6 and abs(reaction[0])+abs(reaction[1])<1e-6
report={'status':'native_reaction_output_observed','fixture':'Synthetic one-element 10x10x1 mm block; fixed lower nodes, -1 N total top load',
        'reactions_n':reaction,'fixed_nodes':len(fixed),'dat_sha256':hashlib.sha256((root/'fixture.dat').read_bytes()).hexdigest(),
        'deck_sha256':hashlib.sha256((root/'fixture.inp').read_bytes()).hexdigest(),'critic_approved':False,
        'limitations':['Backend readiness only; not the original equipment-mount geometry or mesh refinement.','Provider critic and actual engineering reviews remain separate.']}
# Preserve actual solver rows as a provider-supported, finite VTU field file.
assert len(forces) == 8 and {r[0] for r in forces} == set(range(1,9))
assert np.isfinite(np.asarray(forces,dtype=float)).all()
displacements=[]
section=False
for line in text.splitlines():
    lower=line.lower()
    if 'displacements (' in lower:
        section=True
        continue
    if any(x in lower for x in ('forces (','stresses (')):
        section=False
    values=line.split()
    if section and len(values)==4:
        try: displacements.append([int(values[0]),*[float(x.replace('D','E')) for x in values[1:]]])
        except ValueError: pass
assert len(displacements)==8 and {r[0] for r in displacements}==set(range(1,9))
assert np.isfinite(np.asarray(displacements,dtype=float)).all()
points=np.array([[0,0,0],[10,0,0],[10,10,0],[0,10,0],[0,0,1],[10,0,1],[10,10,1],[0,10,1]],dtype=float)
meshio.write_points_cells('native-fixture.vtu',points,[('hexahedron',np.arange(8).reshape(1,8))],
    point_data={'RF_N':np.asarray(sorted(forces))[:,1:],'U_mm':np.asarray(sorted(displacements))[:,1:]})
shutil.copyfile('native-fixture.vtu',root/'native-fixture.vtu')
report['engine']='Native CalculiX; OASiS Python execution with selected native prerequisites'
report['field_sha256']=hashlib.sha256((root/'native-fixture.vtu').read_bytes()).hexdigest()
report['skfem_environment_version']=skfem_version
(root/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
