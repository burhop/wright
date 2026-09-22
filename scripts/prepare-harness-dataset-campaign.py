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
VALIDATION_COVERAGE=ROOT/"packages/workspace_service/src/workspace_service/process_validation/profiles/coverage.json"
spec=importlib.util.spec_from_file_location("harness_prepare_helpers",ROOT/"scripts/prepare-printed-dataset-campaign.py")
helpers=importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
renewal_spec=importlib.util.spec_from_file_location("campaign_example_renewal",ROOT/"scripts/campaign_example_renewal.py")
renewal=importlib.util.module_from_spec(renewal_spec)
renewal_spec.loader.exec_module(renewal)


def prepare(args,directory,available):
    config=json.loads(BINDING.read_text(encoding="utf-8"))
    manifest=json.loads((directory/"scenario.json").read_text(encoding="utf-8"))
    identity=manifest["scenario_id"]
    requested_kicad=getattr(args,"kicad_server_id",None)
    kicad_servers={tool["server_id"] for tool in available if tool["tool_name"]=="schematic"}
    if requested_kicad:
        kicad_servers={server for server in kicad_servers if server==requested_kicad}
    kicad_server=next((server for server in sorted(kicad_servers) if all(any(tool["server_id"]==server and tool["tool_name"]==name for tool in available) for name in config["kicad_tools"])),None)
    if kicad_server is None:
        raise ValueError("A single selected KiCad server with schematic, analyze and native_rule_check is required")
    suffix=identity.replace("-","_")+"_"+args.attempt.replace("-","_")
    inputs=f"campaign/{identity}/{args.attempt}/inputs"
    output=f"campaign/{identity}/{args.attempt}/artifacts"
    workspace=Path(args.workspace_root).resolve()
    interconnect_directory=helpers.confined(workspace,output+"/interconnect")
    interconnect_directory.mkdir(parents=True,exist_ok=False)
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
    stage_file(inputs+"/approved-engineering-brief.json",renewal.contract_bytes(manifest),{"role":"approved_engineering_brief"})
    for name in ("harness_engineering_operations.py","harness_engineering_mcp.py","harness_component_sources.json"):
        stage_file(inputs+"/"+name,(ROOT/"scripts"/name).read_bytes(),{"authored_source":"scripts/"+name})
    design_contract = dict(config["scenarios"][identity])
    contact_resistance_ohm = getattr(args, "contact_resistance_ohm", None)
    splice_port_resistance_ohm = getattr(args, "splice_port_resistance_ohm", None)
    resistance_basis = getattr(args, "resistance_basis", None)
    resistance_values = (
        contact_resistance_ohm,
        splice_port_resistance_ohm,
        resistance_basis,
    )
    if any(value is not None for value in resistance_values):
        if not all(value is not None for value in resistance_values):
            raise ValueError("Both resistance values and their engineering basis are required")
        design_contract["resistance_assumption"] = {
            "contact_ohm_each": contact_resistance_ohm,
            "splice_port_ohm_each": splice_port_resistance_ohm,
            "basis": resistance_basis,
            "status": "reviewed_engineering_assumption",
        }
    stage_file(inputs+"/design.json",(json.dumps(design_contract,indent=2)+"\n").encode(),{"derived_from":"Original context.md; explicit 50 mm installed zone pigtail design choice conserves original route lengths; optional resistance values require the workflow engineering review"})
    human="\n\n".join((directory/name).read_text(encoding="utf-8") for name in ["user-profile.md","prompt.txt",*manifest["files"]["context"]])
    stage_file(inputs+"/assembled-context.md",human.encode(),{"derived_from":manifest["files"]})
    context=helpers.add_file_input(sections,suffix,"human_context",inputs+"/assembled-context.md")
    engineering_brief=helpers.add_file_input(sections,suffix,"approved_engineering_brief",inputs+"/approved-engineering-brief.json")
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
    helpers.add_reference(sections,engineering_brief,research,"approved_engineering_brief")
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
    generated_files={
        "plan":output+"/generated/harness-plan.svg",
        "pin_schedule":output+"/generated/pin-schedule.csv",
        "cut_list":output+"/generated/cut-list.csv",
        "bom":output+"/generated/bom.csv",
        "assembly":output+"/generated/assembly.md",
    }
    if identity.endswith("03"):
        generated_files["shield"]=output+"/generated/shield-termination.json"
    stages["generate_harness"]["fields"]["outputs"].extend(helpers.port(role,"workspace_file") for role in generated_files)
    stages["generate_harness"]["fields"]["settings"]["expected_file_ports"]=generated_files
    helpers.add_reference(sections,research_ref,stages["generate_harness"],"retrieved_parts")
    verified=bind(stages["verify_harness"],f"Call verify_harness_package once with input_directory={inputs!r}, research_directory={output+'/research'!r}, generated_directory={output+'/generated'!r}, output_directory={output+'/verified'!r}, operation_source_document={inputs+'/harness_engineering_operations.py'!r}. Inspect the actual emitted native netlist independently, compare original customer nets/reserves, solve shared startup and continuous currents and calculate both initial assumed-wire and sourced-wire copper drops. Use contact/splice resistance only when design.json contains the closed reviewed_engineering_assumption record; otherwise it must remain unknown, never zero. Report rejected nets/underrated parts/excessive copper or total drop; missing application derating or fan data is explicit release HOLD, never electrical approval.","verification-report.json",["verified/verification.json","verified/voltage-drop.json","verified/independent-netlist.csv"])
    verified_files={"netlist":output+"/verified/independent-netlist.csv","voltage_drop":output+"/verified/voltage-drop.json"}
    stages["verify_harness"]["fields"]["outputs"].extend(helpers.port(role,"workspace_file") for role in verified_files)
    stages["verify_harness"]["fields"]["settings"]["expected_file_ports"]=verified_files
    helpers.add_reference(sections,generated,stages["verify_harness"],"actual_native_package")
    kicad_author=new_task("author_kicad_interconnect","Create the independent KiCad interconnect schematic")
    kicad_author_ref=bind(
        kicad_author,
        f"Use only the selected native KiCad schematic tool to create {('/work/'+output+'/'+config['kicad_handoff']['schematic'])!r}. Read the connected generated pin schedule and independent netlist. Create one connector symbol for every released connector with its exact reference and pin count, then connect or label every exact net without merging distinct returns or reserves. Save the native schematic once after all connections are complete. This is an independent interconnect representation, not a PCB or a replacement for WireViz. Report concrete unsupported pins or tool errors; never fabricate a saved file or clean check.",
        config["kicad_handoff"]["correspondence"].replace("net-correspondence","kicad-authoring"),
        (config["kicad_handoff"]["schematic"],),
        tool=False,
    )
    kicad_author["fields"]["settings"].update(
        authoring_template="mcp-task",
        mcp_server=kicad_server,
        max_tool_calls=24,
        timeout_seconds=600,
        expected_files=output+"/"+config["kicad_handoff"]["schematic"],
        task_guidance="Use actual selected KiCad operations only. Preserve every released pin and net; no PCB, fabrication, supplier or physical action.",
    )
    kicad_author["fields"]["outputs"].append(helpers.port("kicad_schematic","workspace_file"))
    kicad_author["fields"]["settings"]["expected_file_ports"]={"kicad_schematic":output+"/"+config["kicad_handoff"]["schematic"]}
    helpers.add_reference(sections,stages["generate_harness"]["id"]+".pin_schedule",kicad_author,"released_pin_schedule","workspace_file")
    helpers.add_reference(sections,stages["verify_harness"]["id"]+".netlist",kicad_author,"independent_netlist","workspace_file")
    kicad_verify=new_task("verify_kicad_interconnect","Check KiCad connectivity, correspondence and ERC")
    kicad_verify_ref=bind(
        kicad_verify,
        f"Reopen the immutable native schematic {('/work/'+output+'/'+config['kicad_handoff']['schematic'])!r}. Use KiCad analyze operations to obtain its actual connector pins and nets. Compare every released pin/net row against the connected pin schedule and independent WireViz netlist, including reserves and separated returns. Then call native_rule_check(kind='erc',source_path={('/work/'+output+'/'+config['kicad_handoff']['schematic'])!r},report_path={('/work/'+output+'/'+config['kicad_handoff']['erc'])!r}). Write the task response to the declared correspondence JSON with schema='wright-harness-kicad-correspondence-v1', status='pass' only when exact correspondence passes, schematic_sha256, pin_schedule_sha256, netlist_sha256, erc_sha256, missing_rows, extra_rows, mismatched_rows and native erc_error_count. Zero ERC errors alone is not correspondence. Do not edit the schematic during this check and do not downgrade findings.",
        config["kicad_handoff"]["correspondence"],
        (config["kicad_handoff"]["erc"],),
        tool=False,
    )
    kicad_verify["fields"]["settings"].update(
        authoring_template="mcp-task",
        mcp_server=kicad_server,
        max_tool_calls=10,
        timeout_seconds=600,
        expected_files="\n".join(
            output+"/"+config["kicad_handoff"][key]
            for key in ("erc","correspondence")
        ),
        task_guidance="Read and compare the actual immutable KiCad schematic. ERC is native evidence but never substitutes for exact pin/net correspondence.",
    )
    kicad_verify["fields"]["outputs"].extend([
        helpers.port("kicad_erc","workspace_file"),
        helpers.port("net_correspondence","workspace_file"),
    ])
    kicad_verify["fields"]["settings"]["expected_file_ports"]={
        "kicad_erc":output+"/"+config["kicad_handoff"]["erc"],
        "net_correspondence":output+"/"+config["kicad_handoff"]["correspondence"],
    }
    helpers.add_reference(sections,kicad_author_ref,kicad_verify,"kicad_authoring_result")
    helpers.add_reference(sections,stages["generate_harness"]["id"]+".pin_schedule",kicad_verify,"released_pin_schedule","workspace_file")
    helpers.add_reference(sections,stages["verify_harness"]["id"]+".netlist",kicad_verify,"wireviz_netlist","workspace_file")
    final=new_task("collect_harness","Collect generated harness documents and engineering findings")
    handoff=bind(final,"Write the final engineering handoff index for this real attempt, with exact links to native diagram/YAML/BOM, pins/cuts, assembly, source records and independent voltage/net checks. Address original human prompt/context and preserve all release HOLD/rejected findings. Report a total voltage drop only when voltage-drop.json contains the closed reviewed resistance assumption and distinguish assumed values from measured production data; never claim electrical release. Include missing exact device/chassis/derating evidence as next engineering actions. The following process validator determines requirements-compliance credit from the exact current outputs.","harness-handoff.md",tool=False)
    helpers.add_reference(sections,verified,final,"independent_findings")
    helpers.add_reference(sections,generated,final,"native_package")
    helpers.add_reference(sections,kicad_verify_ref,final,"independent_kicad_check")
    coverage=json.loads(VALIDATION_COVERAGE.read_text(encoding="utf-8"))
    support=next(row for row in coverage["scenarios"] if row["scenario_id"]==identity)
    profile=support.get("full_profile")
    if not profile:
        raise ValueError("The harness full validator profile is unavailable")
    profile_document=json.loads((ROOT/"packages/workspace_service/src/workspace_service/process_validation/profiles"/(profile["profile_resource"]+".json")).read_text(encoding="utf-8"))
    final_review=new_task("review_harness_outputs","Review exact harness package and handoff")
    final_review["fields"].update(step_type="review",performed_by="engineer",inputs=[],outputs=[],instructions="Review the exact basis, native harness plan, assembly/shield evidence and final handoff against every frozen review requirement. Preserve all release HOLD findings; approval is not physical electrical qualification.",
        settings={"authoring_template":"external-action-approval","action_kind":"local_review","approval_binding":LOCAL_REVIEW_BINDING,"approval_destination":LOCAL_REVIEW_DESTINATION,
            "approval_settings":{"review_task_id":final_review["id"],"validation_review":{"profile_ref":profile["profile_ref"],"requirement_ids":sorted(req["id"] for req in profile_document["baseline"]["requirements"] if req["review_required"])}},
            "approval_action":{"kind":"local_review","mode":"review_only"}})
    review_sources={"basis":research_ref,"plan":stages["generate_harness"]["id"]+".plan","handoff":handoff}
    if identity.endswith("03"):
        review_sources.update(shield=stages["generate_harness"]["id"]+".shield",assembly=stages["generate_harness"]["id"]+".assembly")
    for role,source_ref in review_sources.items():
        helpers.add_reference(sections,source_ref,final_review,"review_"+role,"workspace_file" if role not in {"basis","handoff"} else "engineering_document")
    validation_sources={
        "basis":(research,research["fields"]["outputs"][0]["key"],"engineering_document"),
        **{role:(stages["generate_harness"],role,"workspace_file") for role in generated_files},
        **{role:(stages["verify_harness"],role,"workspace_file") for role in verified_files},
        "kicad_schematic":(kicad_author,"kicad_schematic","workspace_file"),
        "kicad_erc":(kicad_verify,"kicad_erc","workspace_file"),
        "net_correspondence":(kicad_verify,"net_correspondence","workspace_file"),
        "handoff":(final,final["fields"]["outputs"][0]["key"],"engineering_document"),
    }
    validator=new_task("validate_harness_content","Validate current harness outputs")
    validator["fields"].update(performed_by="configured_tool",inputs=[helpers.port("validate_"+role,kind) for role,(_,_,kind) in validation_sources.items()],outputs=[helpers.port("assessment")],prompt="",
        settings={"authoring_template":"process-validator","output_format":"json","max_revisions":0,"validation":{"profile":{"source":"packaged","name":profile["profile_resource"],"reference":profile["profile_ref"]},"baseline":profile["baseline_ref"],"subjects":{role:"validate_"+role for role in validation_sources}}})
    for role,(producer,producer_port,_) in validation_sources.items():
        sections.append({"kind":"connection","id":"bind_"+validator["id"]+"_"+role,"fields":{"type":"item","from":producer["id"]+"."+producer_port,"to":validator["id"]+".validate_"+role,"label":"current harness output to validate","when":None}})
    for left,right in ((research["id"],gate["id"]),(stages["verify_harness"]["id"],kicad_author["id"]),(kicad_author["id"],kicad_verify["id"]),(kicad_verify["id"],final["id"]),(final["id"],final_review["id"]),(final_review["id"],validator["id"])):
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
    for name in config["kicad_tools"]:
        matches=[tool for tool in available if tool["server_id"]==kicad_server and tool["tool_name"]==name]
        if len(matches)!=1:
            raise ValueError("Required selected KiCad tool unavailable: "+name)
        selected.append(matches[0])
    draft.mkdir(parents=True)
    target=draft/"bound.workflow.wflow"
    target.write_text(result,encoding="utf-8")
    report={"schema_version":1,"scenario_id":identity,"template_id":manifest["template_id"],"attempt_id":args.attempt,"status":"prepared_not_dispatched","source":str(target),"source_sha256":helpers.digest(result.encode()),"template_source_sha256":helpers.digest(TEMPLATE.read_bytes()),
            "requires_template_instance_api":not bool(args.instance_source),"workspace_root":str(workspace),"output_root":output,"prepared_output_directories":[output+"/interconnect"],"input_manifest":staged,"tool_allowlist":selected,"expected_outputs":renewal.expected_outputs(manifest),"compiled_stages":[step.id for step in plan.steps],"preserved_original_stages":original_tasks,"preserved_original_edges":[edge["id"] for edge in original_edges],"expected_tool_created_files":[path for step in plan.steps for path in step.expected_files],"approval_policy_request":{"mode":"auto","scope":"integration_test","test_destinations":[]},"recorded_substitution":config["implementation"],"kicad_server_id":kicad_server}
    helpers.publish_input_binding_evidence(report, directory)
    (draft/"staging-manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    return {"scenario_id":identity,"draft":str(target),"stages":len(plan.steps),"executed":False}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root",required=True)
    parser.add_argument("--server-id",required=True)
    parser.add_argument("--kicad-server-id")
    parser.add_argument("--draft-root",default=str(ROOT/".local-run/feature-081-live/harness-campaign-drafts"))
    parser.add_argument("--attempt",default="attempt-001")
    parser.add_argument("--scenario")
    parser.add_argument("--instance-source")
    parser.add_argument("--contact-resistance-ohm",type=float)
    parser.add_argument("--splice-port-resistance-ohm",type=float)
    parser.add_argument("--resistance-basis")
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
