"""Compatibility import for retained desktop probes; implementation is packaged."""

import sys
from api.desktop import desktop_credential_form as _implementation

sys.modules[__name__] = _implementation
