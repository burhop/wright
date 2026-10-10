"""Exercise the JWT operations used by the packaged Hermes authentication plugins.

Run with the image's Hermes Python interpreter. Keys are generated in memory and
tokens are never logged. This complements pip metadata and vulnerability checks.
"""

from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric import rsa
import jwt


def main() -> None:
    assert jwt.__version__ == "2.15.1", "Unexpected PyJWT security override"
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = jwt.PyJWK.from_dict(
        jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    )
    claims = {
        "sub": "isolated-smoke-subject",
        "iss": "https://issuer.example.invalid",
        "aud": "isolated-smoke-audience",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    options = {
        "algorithms": ["RS256"],
        "issuer": claims["iss"],
        "audience": claims["aud"],
    }
    token = jwt.encode(claims, key, algorithm="RS256")
    assert jwt.decode(token, public.key, **options)["sub"] == claims["sub"]

    def must_reject(candidate: str, expected: type[Exception]) -> None:
        try:
            jwt.decode(candidate, public.key, **options)
        except expected:
            return
        raise AssertionError(f"JWT was accepted; expected {expected.__name__}")

    wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    must_reject(
        jwt.encode(claims, wrong_key, algorithm="RS256"), jwt.InvalidSignatureError
    )
    must_reject(
        jwt.encode({**claims, "exp": 1}, key, algorithm="RS256"),
        jwt.ExpiredSignatureError,
    )
    must_reject(
        jwt.encode({**claims, "iss": "wrong-issuer"}, key, algorithm="RS256"),
        jwt.InvalidIssuerError,
    )
    must_reject(
        jwt.encode({**claims, "aud": "wrong-audience"}, key, algorithm="RS256"),
        jwt.InvalidAudienceError,
    )
    print(
        "Hermes JWT operations pass; invalid signature, expiry, issuer and audience rejected."
    )


if __name__ == "__main__":
    main()
