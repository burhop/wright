"""Selected KiCad provider retaining upstream tools plus native report export."""
import logging

from kicad_mcp.server import create_server
from native_rule_check import register

logging.basicConfig(level=logging.INFO)
server = create_server()
register(server)
server.run(transport="stdio", show_banner=False)
