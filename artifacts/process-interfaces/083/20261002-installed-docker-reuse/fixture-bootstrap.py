from pathlib import Path
import os, shutil, subprocess, sys, site
env=Path('/tmp/wright-proof-env')
subprocess.run([sys.executable,'-m','venv',str(env)],check=True)
python=env/'bin/python'
subprocess.run([str(python),'-m','pip','install','--no-index','--no-deps','/proof-input/wright_engineering-0.1.9-py3-none-any.whl'],check=True)
installed=next((env/'lib').glob('python*/site-packages'))
(installed/'cached-dependencies.pth').write_text('\n'.join(site.getsitepackages())+'\n')
root=Path('/tmp/wright-proof')
(root/'data/workspaces').mkdir(parents=True)
shutil.copytree('/proof-input/workspace',root/'data/workspaces/proof')
shutil.copyfile('/proof-input/state.db',root/'data/wright.db')
os.execv(str(python),[str(python),'/proof-input/host.py'])
