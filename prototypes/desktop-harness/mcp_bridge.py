"""Compatibility import for retained desktop probes; implementation is packaged."""

import sys
from api.desktop import mcp_bridge as _implementation

if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
