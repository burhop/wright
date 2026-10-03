from pathlib import Path
import asyncio
import hashlib
import json
import sys
from types import SimpleNamespace

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "wheel-root"))
from core.process_interactions import OptionBinding, ProcessRef
from workspace_service.process_interfaces import inputs, options
from workspace_service.process_interfaces.errors import ProcessInterfaceError

class ReadOnlyProvider:
    def __init__(self, value):
        self.value, self.calls = value, []
    def resolve(self, step):
        return SimpleNamespace(annotations={"readOnlyHint":True}, required_approvals=())
    def preflight(self, step):
        assert step.schema_digest == "a" * 64
    async def call(self, step, arguments, **kwargs):
        assert kwargs == {"monitor":False}
        self.calls.append(step.tool_name)
        return {"options":[{"id":"one", "title":"Declared choice", "value":self.value}]}, "options"

async def run():
    configuration = options.OptionSource(binding_id="choices", server_id="proof", tool_name="choices", schema_digest="a"*64)
    tested = []
    for provider_value, supplied_value in [(0, False), (1, True), ({"flag":0}, {"flag":False}), ([1], [True])]:
        provider = ReadOnlyProvider(provider_value)
        catalog = await options.read_options(configuration, provider, input_id="choice", value_schema={}, now="2026-10-03T12:00:00Z")
        binding = OptionBinding(input_id="choice", option_id="one", capability=catalog.capability,
            value=supplied_value, observed_at=catalog.observed_at, stale_after=catalog.stale_after)
        try:
            options.verify_option(binding, catalog)
        except ProcessInterfaceError as error:
            assert error.reason.code == "OPTION_STALE"
        else:
            raise AssertionError("A different JSON type was accepted")
        assert provider.calls == ["choices"]
        tested.append({"provider":provider_value, "supplied":supplied_value, "rejected":True})
    provider = ReadOnlyProvider({"count":0, "enabled":False})
    catalog = await options.read_options(configuration, provider, input_id="choice", value_schema={}, now="2026-10-03T12:00:00Z")
    binding = OptionBinding(input_id="choice", option_id="one", capability=catalog.capability,
        value={"enabled":False, "count":0}, observed_at=catalog.observed_at, stale_after=catalog.stale_after)
    options.verify_option(binding, catalog)
    source = (root / "missing-later-choice.workflow.wflow").read_text(encoding="utf-8")
    process = ProcessRef(workspace_id="proof", source_path="workflows/missing.workflow.wflow", source_digest=hashlib.sha256(source.encode()).hexdigest())
    prepared = await inputs.prepare_inputs(service=SimpleNamespace(), workspace_dir=str(root), process=process, source=source)
    readiness = inputs.input_readiness(prepared)
    assert readiness.state == "blocked"
    reason = next(item for item in readiness.reasons if item.code == "INPUT_REQUIRED")
    assert reason.binding_id == "brief" and reason.navigation.kind == "block" and reason.navigation.block_id == "brief"
    assert not (root / "first.txt").exists()
    namespaces = {"core", "workspace_service", "data_vault", "tool_registry", "agent_runtime", "api", "workspace_files", "code_tools", "document_manager", "native_viewer"}
    paths = {name:str(Path(module.__file__).resolve()) for name,module in sys.modules.items()
             if name.split(".")[0] in namespaces and getattr(module,"__file__",None)}
    assert paths
    for name,path in paths.items():
        assert Path(path).is_relative_to(root / "wheel-root"), (name,path)
    report = {"status":"passed", "scope":"Detached fresh-wheel input/option owners; controlled read-only provider values",
        "live_provider_model_hardware_or_native_browser_acceptance":False,
        "type_rejections":tested, "object_key_order_accepted":True,
        "missing_later_choice_reason":reason.model_dump(mode="json"),
        "loaded_project_modules":paths,
        "module_sha256":{name:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                         for name,module in [("inputs",inputs),("options",options)]}}
    (root / "detached-result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":"passed", "type_rejections":len(tested), "loaded_project_modules":len(paths)}))

asyncio.run(run())
