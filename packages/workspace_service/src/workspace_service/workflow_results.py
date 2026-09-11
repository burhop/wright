"""Engineering deliverables, independent of MCP transport and activity text.

Representations describe how the same result can be consumed. They are not
additional models. Adapters must verify identities/files before publishing them.
"""
from dataclasses import asdict, dataclass
from typing import Literal

ResultKind = Literal['text', 'image', 'file', 'structured', 'cad_model', 'analysis']


@dataclass(frozen=True)
class Representation:
    kind: Literal['value', 'workspace_file', 'application_document', 'cloud_resource']
    location: str
    format: str = ''
    provider_id: str = ''
    resource_id: str = ''
    revision: str | None = None
    durability: Literal['persistent', 'session', 'run'] = 'run'
    sha256: str | None = None
    size_bytes: int | None = None

    def __post_init__(self):
        if self.kind not in {'value','workspace_file','application_document','cloud_resource'} or self.durability not in {'persistent','session','run'}:
            raise ValueError('Unknown result representation or durability.')
        if not isinstance(self.location,str) or not self.location.strip():
            raise ValueError('A result representation needs a location.')
        if self.revision is not None and not isinstance(self.revision,str):
            raise ValueError('Resource revisions must be strings.')
        if self.kind in {'application_document', 'cloud_resource'} and not (self.provider_id and self.resource_id):
            raise ValueError('Application resources need explicit provider and resource identity.')
        if self.kind == 'workspace_file':
            from pathlib import PurePosixPath
            path = PurePosixPath(self.location.replace('\\', '/'))
            if path.is_absolute() or '..' in path.parts or ':' in self.location:
                raise ValueError('Result files must be relative to their workspace.')
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError('A file size cannot be negative.')


@dataclass(frozen=True)
class Provenance:
    run_id: str
    task_id: str
    output_port: str
    input_revisions: tuple[tuple[str, str | None], ...] = ()


@dataclass(frozen=True)
class EngineeringResult:
    id: str
    kind: ResultKind
    name: str
    representations: tuple[Representation, ...]
    provenance: Provenance
    # Named export results retain their own IDs, formats and connection targets.
    exports: tuple['EngineeringResult', ...] = ()

    def __post_init__(self):
        if self.kind not in {'text','image','file','structured','cad_model','analysis'}:
            raise ValueError('Unknown engineering result kind.')
        if not self.id or not self.name or not self.representations:
            raise ValueError('A result needs an identity and at least one verified representation.')

    @property
    def persistent(self):
        return any(r.durability == 'persistent' for r in self.representations)

    def to_dict(self):
        return {'schema_version': 1, **asdict(self)}


@dataclass(frozen=True)
class ResultCollection:
    """Collections are explicit; a singleton is never silently unwrapped."""
    items: tuple[EngineeringResult, ...]


@dataclass(frozen=True)
class InputRequirement:
    kinds: tuple[ResultKind, ...]
    provider_id: str | None = None
    formats: tuple[str, ...] = ()
    collection: bool = False
    persistent: bool = False
    representation_kinds: tuple[str, ...] = ()


def select_representation(result: EngineeringResult, requirement: InputRequirement) -> Representation:
    if result.kind not in requirement.kinds:
        raise ValueError(f'{result.name} is {result.kind}; this input needs {", ".join(requirement.kinds)}.')
    for rep in result.representations:
        if requirement.representation_kinds and rep.kind not in requirement.representation_kinds:
            continue
        if requirement.provider_id and rep.provider_id != requirement.provider_id:
            continue
        if requirement.formats and rep.format not in requirement.formats:
            continue
        if requirement.persistent and rep.durability != 'persistent':
            continue
        return rep
    formats = ', '.join(requirement.formats)
    correction = f'Configure an export in the producing block as {formats} and connect that export.' if formats else 'Select a resource supported by the consuming application.'
    raise ValueError(f'{result.name} has no compatible representation. {correction}')


def validate_result_input(value: EngineeringResult | ResultCollection, requirement: InputRequirement):
    if not isinstance(value,(EngineeringResult,ResultCollection)):
        raise ValueError('Connect a verified engineering result to this input.')
    if isinstance(value, ResultCollection) != requirement.collection:
        raise ValueError('Connect a collection to a collection input, or select an individual result.')
    items = value.items if isinstance(value, ResultCollection) else (value,)
    return tuple(select_representation(item, requirement) for item in items)


def file_representation(output: dict) -> Representation:
    return Representation('workspace_file', output['output_path'], output.get('output_format', ''),
                          durability='persistent', sha256=output.get('sha256'), size_bytes=output['output_bytes'])


def file_result(output: dict, provenance: Provenance) -> EngineeringResult:
    return EngineeringResult(f'{provenance.run_id}:{provenance.task_id}:{provenance.output_port}',
                             'file', output['output_path'], (file_representation(output),), provenance)
