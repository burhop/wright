"""Inventory saved workspace workflows or run explicitly selected development cases."""
import argparse,asyncio,json
from pathlib import Path
from workspace_service.workflow_campaign import inventory,run_campaign
from workspace_service.workflow_campaign_fixtures import create_bundle,restore_bundle
from workspace_service.workflow_campaign_oracles import attach_oracles

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workspace',type=Path)
parser.add_argument('--manifest',type=Path,required=True)
parser.add_argument('--run',nargs='+',help='Explicit stable IDs; omitted means inventory only')
parser.add_argument('--api',default='http://127.0.0.1:8018')
parser.add_argument('--session')
parser.add_argument('--attempts',type=Path,default=Path('artifacts/workflow-campaign/attempts'))
parser.add_argument('--max-runs',type=int,default=3)
parser.add_argument('--max-model-calls',type=int,default=40)
parser.add_argument('--timeout',type=int,default=600)
parser.add_argument('--concurrency',type=int,default=1)
parser.add_argument('--oracles',type=Path,help='Reviewed assertions tied to exact workflow source hashes')
parser.add_argument('--bundle',nargs='+',help='Snapshot these explicit case IDs with their workspace inputs')
parser.add_argument('--bundle-dir',type=Path)
parser.add_argument('--restore',type=Path,help='Restore a fixture bundle to --workspace without overwriting different files')
parser.add_argument('--subset',help='Named regression subset from --subsets')
parser.add_argument('--subsets',type=Path,default=Path('artifacts/workflow-campaign/subsets.json'))
args=parser.parse_args()
if args.subset:
    if args.run or args.bundle or args.restore:parser.error('--subset is an alternative to explicit --run IDs')
    subsets=json.loads(args.subsets.read_text(encoding='utf-8'))
    if args.subset not in subsets:parser.error('Unknown regression subset')
    args.run=subsets[args.subset]
    if not isinstance(args.run,list) or not args.run or any(not isinstance(i,str) for i in args.run):parser.error('A subset must contain workflow IDs')
if sum(bool(v) for v in (args.run,args.bundle,args.restore))>1:parser.error('Choose run, bundle, or restore.')
if args.restore:
    if not args.workspace:parser.error('--workspace is required for restore')
    print(json.dumps(restore_bundle(args.restore,args.workspace)))
elif args.bundle:
    if not args.bundle_dir:parser.error('--bundle-dir is required for a new bundle')
    data=create_bundle(json.loads(args.manifest.read_text(encoding='utf-8')),args.bundle,args.bundle_dir)
    print(json.dumps({'files':len(data['files']),'cases':len(data['cases'])}))
elif args.run:
    if not args.session:parser.error('--session is required for live runs')
    data=json.loads(args.manifest.read_text(encoding='utf-8'))
    if args.oracles:data=attach_oracles(data,json.loads(args.oracles.read_text(encoding='utf-8')))
    results=asyncio.run(run_campaign(data,ids=args.run,api=args.api,session=args.session,output_dir=args.attempts,max_runs=args.max_runs,max_model_calls=args.max_model_calls,timeout=args.timeout,concurrency=args.concurrency))
    print(json.dumps([{'case_id':r['case_id'],'status':r['status'],'attempt':r['id']} for r in results],indent=2))
else:
    if not args.workspace:parser.error('--workspace is required for inventory')
    data=inventory(args.workspace)
    if args.oracles:data=attach_oracles(data,json.loads(args.oracles.read_text(encoding='utf-8')))
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps({'authored_files':len(data['cases']),'compiles':sum(c['compiles'] for c in data['cases']),'target':100,'live_verified':0}))
