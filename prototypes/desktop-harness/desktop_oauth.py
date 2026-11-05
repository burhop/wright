"""Compatibility import for retained desktop probes; implementation is packaged."""

import sys
from api.desktop import desktop_oauth as _implementation

sys.modules[__name__] = _implementation
