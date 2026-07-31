"""Pure public values for Wright's no-server Python display API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .client import DisplayClient


class WrightDisplayError(RuntimeError):
    """Base class for actionable process-side display failures."""


class DisplayConfigurationError(WrightDisplayError):
    """The process was not given an explicit Wright display connection."""


class DisplayTransportError(WrightDisplayError):
    """The configured Wright display endpoint could not accept the request."""


class DisplayContractError(WrightDisplayError):
    """The value or peer response violates the negotiated display contract."""


@dataclass(frozen=True, slots=True)
class DisplayRepresentation:
    media_type: str
    encoding: Literal["utf-8", "base64", "json"]
    data: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    active_html: bool = False
    fallback_rank: int = 0

    def as_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "mediaType": self.media_type,
            "encoding": self.encoding,
            "data": self.data,
        }
        if self.metadata:
            value["metadata"] = dict(self.metadata)
        if self.active_html:
            value["activeHtml"] = True
        if self.fallback_rank:
            value["fallbackRank"] = self.fallback_rank
        return value


@dataclass(frozen=True, slots=True)
class NativeGraph:
    kind: Literal["line", "bar", "scatter", "histogram"]
    title: str
    x_label: str
    y_label: str
    description: str
    x: tuple[float | str, ...] = ()
    y: tuple[float, ...] = ()
    values: tuple[float, ...] = ()
    bins: int | None = None


@dataclass(frozen=True, slots=True)
class DisplayHandle:
    """Stable result metadata; reusable workspace credentials are never exposed."""

    surface_id: str
    display_id: str
    revision: int
    title: str | None = None
    _client: "DisplayClient | None" = field(default=None, repr=False, compare=False)
    _description: str | None = field(default=None, repr=False, compare=False)
    _durability: str = field(default="durable", repr=False, compare=False)

    def update(
        self,
        value: Any,
        *,
        title: str | None = None,
        description: str | None = None,
        active_html: bool = False,
    ) -> "DisplayHandle":
        if self._client is None:
            raise DisplayConfigurationError(
                "This DisplayHandle is detached; call wright.display with an "
                "active Wright execution to update it."
            )
        from .display import display

        return display(
            value,
            title=title or self.title,
            description=description or self._description,
            active_html=active_html,
            display_id=self.display_id,
            durability=self._durability,
            client=self._client,
        )
