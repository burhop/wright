"""Check the actual certifi bundle, including pip's separately vendored copy."""

import ssl
import sys

if "--pip-vendor" in sys.argv:
    from pip._vendor import certifi
    from pip._vendor.packaging.version import Version
else:
    import certifi
    from packaging.version import Version

assert Version(certifi.__version__) >= Version("2026.10.19"), (
    f"Unpatched certifi: {certifi.__version__} ({certifi.__file__})"
)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_verify_locations(cafile=certifi.where())
roots = context.get_ca_certs()
assert roots, "certifi bundle is empty"
assert not any(
    value == "emSign ECC Root CA - G3"
    for root in roots
    for attributes in root["subject"]
    for name, value in attributes
    if name == "commonName"
), "Compromised emSign trust root remains in certifi"
print(
    f"Patched certifi {certifi.__version__}: {len(roots)} roots; affected root absent"
)
