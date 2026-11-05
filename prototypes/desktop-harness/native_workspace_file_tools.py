"""Compatibility import for retained desktop probes; implementation is packaged."""

import sys
from api.desktop import native_workspace_file_tools as _implementation

sys.modules[__name__] = _implementation
