"""Prepare real canonical harness bindings for the explicit WireViz substitute."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import urllib.parse
import urllib.request
from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow, validate_workspace_authoring_shape
from workspace_service.workflow_integration_policy import LOCAL_REVIEW_BINDING, LOCAL_REVIEW_DESTINATION

ROOT=Path(__file__).resolve().parents[1]
BINDING=ROOT/"tests/datasets/engineering-workflows/bindings/sensor-fan-harness.json"
TEMPLATE=ROOT/"packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/sensor-fan-harness.workflow.wflow"
spec=importlib.util.spec_from_file_location("harness_prepare_helpers",ROOT/"scripts/prepare-printed-dataset-campaign.py")
helpers=importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def prepare(args,directory,available):
    config=json.loads(BINDING.read_text(encoding="utf-8"))
    manifest=json.loads((directory/"scenario.json").read_text(encoding="utf-8"))
    identity=manifest["scenario_id"]
    suffix=identity.replace("-","_")+"_"+args.attempt.replace("-","_")
    inputs=f"campaign/{identity}/{args.attempt}/inputs"
    output=f"campaign/{identity}/{args.attempt}/artifacts"
    workspace=Path(args.workspace_root).resolve()
    draft=Path(args.draft_root).resolve()/identity/args.attempt
    if draft.exists():
        raise ValueError("Preserve prior draft; choose a fresh attempt")
    source=Path(args.instance_source).read_text(encoding="utf-8") if args.instance_source else TEMPLATE.read_text(encoding="utf-8").replace("__instance__",suffix)
    sections=_parse(source)
    original_tasks=[s["id"] for s in sections if s["kind"]=="task"]
    original_edges=[s.copy() for s in sections if s["kind"]=="connection"]
    stages={key:next(s for s in sections if s["kind"]=="task" and s["id"].startswith(key+"_")) for key in ("define_harness","generate_harness","verify_harness")}
    staged=[]
    def stage_file(relative,data,provenance):
        helpers.write_once(helpers.confined(workspace,relative),data)
        staged.append({"path":relative,"sha256":helpers.digest(data),"size_bytes":len(data),**provenance})
    for path in sorted(directory.iterdir()):
        if path.is_file():
            stage_file(inputs+"/"+path.name,path.read_bytes(),{"original":path.relative_to(ROOT).as_posix()})
    for name in ("harness_engineering_operations.py","harness_engineering_mcp.py","harness_component_sources.json"):
        stage_file(inputs+"/"+name,(ROOT/"scripts"/name).read_bytes(),{"authored_source":"scripts/"+name})
    stage_file(inputs+"/design.json",(json.dumps(config["scenarios"][identity],indent=2)+"\n").encode(),{"derived_from":"Original context.md; explicit50mm installed zone pigtail design choice conserves original route lengths"})
    human="\n\n".join((directory/name).read_text(encoding="utf-8") for name in ["user-profile.md","prompt.txt",*manifest["files"]["context"]])
    stage_file(inputs+"/assembled-context.md",human.encode(),{"derived_from":manifest["files"]})
    context=helpers.add_file_input(sections,suffix,"human_context",inputs+"/assembled-context.md")
    operation=helpers.add_file_input(sections,suffix,"authored_operation",inputs+"/harness_engineering_operations.py")
    design=helpers.add_file_input(sections,suffix,"engineering_design_contract",inputs+"/design.json")
    sources=helpers.add_file_input(sections,suffix,"primary_component_research",inputs+"/harness_component_sources.json")
    image=helpers.add_file_input(sections,suffix,"human_route_sketch",inputs+"/concept.png")
    next(s for s in sections if s["id"]==image.split(".")[0])["fields"]["outputs"][0]["kind"]="reference_images"
    def new_task(key,title):
        task={"kind":"task","id":key+"_"+suffix,"fields":{"name":title,"purpose":title,"step_type":"work","group":None,"performed_by":"ai_assisted","inputs":[],"outputs":[],"settings":{},"tool":None,"reusable_step":None}}
        sections.append(task)
        return task
    def bind(task,prompt,filename,expected=(),tool=True):
        task["fields"].update(step_type="work",performed_by="ai_assisted",prompt=prompt,inputs=[],outputs=[helpers.port(task["id"]+"_result")])
        task["fields"]["settings"]={**task["fields"].get("settings",{}),"output_format":"markdown" if filename.endswith(".md") else "json","save_output":True,"output_filename":output+"/"+filename,"file_policy":"overwrite"}
        if tool:
            task["fields"]["settings"].update(authoring_template="mcp-task",mcp_server=args.server_id,max_tool_calls=4,timeout_seconds=600,expected_files="\n".join(output+"/"+p for p in expected),
                task_guidance="Use only the exact selected fixed operation with supplied paths. All files must be actually generated. This is a declared WireViz implementation, never Splice output. No purchase, account, energizing or physical connection. Preserve conditional HOLD findings; no fabricated ratings.")
        for producer,key in ((context,"human_context"),(operation,"operation_source"),(design,"design_contract"),(sources,"source_contract")):
            helpers.add_reference(sections,producer,task,key)
        return task["id"]+"."+task["id"]+"_result"
    research=new_task("research_exact_parts","Retrieve exact primary connector, wire, terminal and tooling records")
    docs=json.loads((ROOT/"scripts/harness_component_sources.json").read_text(encoding="utf-8"))["documents"]
    expected_research=["research/component-records.json"]+["research/"+d["id"]+(".pdf" if d["url"].endswith(".pdf") else ".html") for d in docs]
    research_ref=bind(research,f"Call retrieve_harness_component_records once with source_specification={inputs+'/harness_component_sources.json'!r}, output_directory={output+'/research'!r}, operation_source_document={inputs+'/harness_engineering_operations.py'!r}. Actively retrieve actual manufacturer bytes, not cached assumed ratings. Review exact record identities and unresolved loaded-contact derating/contact resistance/fan-interface evidence against the human requirements. Present the approved net/design basis using the attached route sketch and exact uploaded schedule.","research-and-design-basis.md",expected_research)
    helpers.add_reference(sections,image,research,"route_image","reference_images")
    gate=stages["define_harness"]
    gate["fields"].update(step_type="review",performed_by="engineer",instructions="Review exact uploaded pin-to-pin nets, source-indexed candidate parts, explicit WireViz substitution, service/pigtail choices, retained human policies and unresolved release HOLD conditions. Auto integration review authorizes this local generation only; it is not production electrical approval.",inputs=[],outputs=[],
        settings={**gate["fields"]["settings"],"authoring_template":"external-action-approval","action_kind":"local_review","approval_binding":LOCAL_REVIEW_BINDING,"approval_destination":LOCAL_REVIEW_DESTINATION,"approval_settings":{"review_task_id":gate["id"]},"approval_action":{"kind":"local_review","mode":"review_only"}})
    helpers.add_reference(sections,research_ref,gate,"engineering_basis")
    generated=bind(stages["generate_harness"],f"After the original engineer review, call generate_harness_package once with input_directory={inputs!r}, design_document={inputs+'/design.json'!r}, research_directory={output+'/research'!r}, output_directory={output+'/generated'!r}, operation_source_document={inputs+'/harness_engineering_operations.py'!r}. This performs real native WireViz/Graphviz generation from exact customer CSVs. Retain all original nets, separate fan/sensor returns, reserves, shared trunks, source-aware strip allowances and actual pair cut lengths. Never identify this output as Splice.","generation-report.json",["generated/harness-source.yml","generated/harness-plan.svg","generated/harness-plan.png","generated/harness-plan.bom.tsv","generated/harness-plan.json","generated/pin-schedule.csv","generated/cut-list.csv","generated/bom.csv","generated/assembly.md"])
    with (directory/"connector-requirements.csv").open(encoding="utf-8",newline="") as stream:
        counts={int(row["pins"]) for row in csv.DictReader(stream) if not row["connector"].endswith("_power_splices")}
    extras=["generated/shield-termination.json"]+[f"generated/manufacturer-mating-view-{side}{count}.png" for count in sorted(counts) for side in ("plug","socket")]
    stages["generate_harness"]["fields"]["settings"]["expected_files"] += "\n"+"\n".join(output+"/"+name for name in extras)
    helpers.add_reference(sections,research_ref,stages["generate_harness"],"retrieved_parts")
    verified=bind(stages["verify_harness"],f"Call verify_harness_package once with input_directory={inputs!r}, research_directory={output+'/research'!r}, generated_directory={output+'/generated'!r}, output_directory={output+'/verified'!r}, operation_source_document={inputs+'/harness_engineering_operations.py'!r}. Inspect the actual emitted native netlist independently, compare original customer nets/reserves, solve shared startup and continuous currents and calculate both initial assumed-wire and sourced-wire copper drops. Unknown contact resistance must remain unknown, never zero. Report rejected nets/underrated parts/excessive copper drop; missing application derating or fan data is explicit release HOLD, never electrical approval.","verification-report.json",["verified/verification.json","verified/voltage-drop.json","verified/independent-netlist.csv"])
    helpers.add_reference(sections,generated,stages["verify_harness"],"actual_native_package")
    final=new_task("collect_harness","Collect generated harness documents and engineering findings")
    bind(final,"Write the final engineering handoff index for this real attempt, with exact links to native diagram/YAML/BOM, pins/cuts, assembly, source records and independent voltage/net checks. Address original human prompt/context and preserve all release HOLD/rejected findings; never claim total voltage drop or electrical release was validated. Include missing exact device/chassis/derating evidence as next engineering actions. No correctness-validation dashboard credit is authorized.","harness-handoff.md",tool=False)
    helpers.add_reference(sections,verified,final,"independent_findings")
    helpers.add_reference(sections,generated,final,"native_package")
    for left,right in ((research["id"],gate["id"]),(stages["verify_harness"]["id"],final["id"])):
        sections.append({"kind":"connection","id":"order_"+left+"_"+right,"fields":{"type":"order","from":left,"to":right,"label":"same canonical execution","when":None}})
    result=helpers.render(sections)
    validate_workspace_authoring_shape(result)
    plan=compile_prompt_workflow(result)
    if any(edge not in sections for edge in original_edges):
        raise ValueError("Original harness control connection changed")
    selected=[]
    for name in config["allowed_tools"]:
        matches=[tool for tool in available if tool["server_id"]==args.server_id and tool["tool_name"]==name]
        if len(matches)!=1:
            raise ValueError("Required scoped harness operation unavailable: "+name)
        selected.append(matches[0])
    draft.mkdir(parents=True)
    target=draft/"bound.workflow.wflow"
    target.write_text(result,encoding="utf-8")
    report={"schema_version":1,"scenario_id":identity,"template_id":manifest["template_id"],"attempt_id":args.attempt,"status":"prepared_not_dispatched","source":str(target),"source_sha256":helpers.digest(result.encode()),"template_source_sha256":helpers.digest(TEMPLATE.read_bytes()),
            "requires_template_instance_api":not bool(args.instance_source),"workspace_root":str(workspace),"output_root":output,"input_manifest":staged,"tool_allowlist":selected,"expected_outputs":manifest["expected_outputs"],"compiled_stages":[step.id for step in plan.steps],"preserved_original_stages":original_tasks,"preserved_original_edges":[edge["id"] for edge in original_edges],"expected_tool_created_files":[path for step in plan.steps for path in step.expected_files],"approval_policy_request":{"mode":"auto","scope":"integration_test","test_destinations":[]},"recorded_substitution":config["implementation"]}
    helpers.publish_input_binding_evidence(report, directory)
    (draft/"staging-manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    return {"scenario_id":identity,"draft":str(target),"stages":len(plan.steps),"executed":False}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root",required=True)
    parser.add_argument("--server-id",required=True)
    parser.add_argument("--draft-root",default=str(ROOT/".local-run/feature-081-live/harness-campaign-drafts"))
    parser.add_argument("--attempt",default="attempt-001")
    parser.add_argument("--scenario")
    parser.add_argument("--instance-source")
    parser.add_argument("--api",default="http://127.0.0.1:8000")
    parser.add_argument("--session",default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    args=parser.parse_args()
    if args.instance_source and not args.scenario:
        parser.error("--instance-source requires --scenario")
    with urllib.request.urlopen(args.api+"/api/workspace/workflow-sources/tools?session_id="+urllib.parse.quote(args.session),timeout=60) as response:
        tools=json.load(response)["tools"]
    results=[]
    for directory in sorted((ROOT/"tests/datasets/engineering-workflows/scenarios/sensor-fan-harness").iterdir()):
        identity=json.loads((directory/"scenario.json").read_text(encoding="utf-8"))["scenario_id"]
        if not args.scenario or args.scenario==identity:
            results.append(prepare(args,directory,tools))
    print(json.dumps({"prepared":results,"executed":False},indent=2))
