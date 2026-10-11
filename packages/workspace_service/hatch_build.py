"""Include public frontend resources from the monorepo or this service's sdist."""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        root = Path(self.root)
        public = root / "src/workspace_service/process_interfaces/resources/public"
        for name in ("process_client", "ui_kit"):
            source = public / name
            packaged = source.is_dir()
            if not packaged:
                source = root.parent / name
            for member in ("src", "package.json", "README.md"):
                path = source / member
                if not path.exists():
                    raise FileNotFoundError(
                        f"Missing public process UI resource: {name}/{member}"
                    )
                if not packaged:
                    build_data["force_include"][str(path)] = (
                        f"workspace_service/process_interfaces/resources/public/{name}/{member}"
                    )
