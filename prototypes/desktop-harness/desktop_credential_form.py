"""One-use sealed form transport to the existing credential owner, not authentication."""

import json
import secrets
import time

from jwcrypto import jwe, jwk


class CredentialFormError(ValueError):
    pass


class DesktopCredentialForms:
    """Keep private decryption keys only in this process for at most five minutes."""

    def __init__(self, *, clock=time.monotonic):
        self._clock = clock
        self._forms = {}

    def _expire(self):
        for key in list(self._forms):
            if self._forms[key]["expires"] <= self._clock():
                self._forms.pop(key)

    def issue(self, subject, fields):
        self._expire()
        if not fields or len(fields) > 32:
            raise CredentialFormError(
                "No missing supported credential fields; replacing existing values is not qualified in this prototype"
            )
        if len(self._forms) >= 16:
            raise CredentialFormError("Too many open credential forms; wait for expiry")
        # A newly opened form replaces an older form for the same exact subject.
        for key in list(self._forms):
            if self._forms[key]["subject"] == subject:
                self._forms.pop(key)
        key = jwk.JWK.generate(kty="RSA", size=2048)
        form_id = secrets.token_urlsafe(24)
        self._forms[form_id] = {
            "subject": subject,
            "fields": frozenset(fields),
            "key": key,
            "expires": self._clock() + 300,
        }
        return {
            "form_id": form_id,
            "public_key": json.loads(key.export_public()),
            "expires_in": 300,
            "alg": "RSA-OAEP-256",
            "enc": "A256GCM",
        }

    def consume(self, form_id, subject, ciphertext):
        self._expire()
        entry = self._forms.get(form_id)
        if entry is None or entry["subject"] != subject:
            raise CredentialFormError(
                "Credential form expired or configuration changed; reopen it"
            )
        # Consume before decrypt/save. A lost acknowledgement cannot replay a write.
        self._forms.pop(form_id)
        try:
            if (
                not isinstance(ciphertext, str)
                or len(ciphertext) > 24576
                or ciphertext.count(".") != 4
            ):
                raise ValueError()
            envelope = jwe.JWE(algs=["RSA-OAEP-256", "A256GCM"])
            envelope.deserialize(ciphertext)
            if envelope.jose_header != {"alg": "RSA-OAEP-256", "enc": "A256GCM"}:
                raise ValueError()
            envelope.decrypt(entry["key"], max_plaintext=8192)
            data = json.loads(envelope.payload)
            if set(data) != {"form_id", "values"} or data["form_id"] != form_id:
                raise ValueError()
            values = data["values"]
            if (
                not isinstance(values, dict)
                or not values
                or not set(values) <= entry["fields"]
            ):
                raise ValueError()
            if any(
                not isinstance(value, str) or not value.strip() or len(value) > 4096
                for value in values.values()
            ):
                raise ValueError()
            return values
        except Exception:
            # Neither decrypted bytes nor library exception text may cross this boundary.
            raise CredentialFormError(
                "Credential form could not be saved; read configured status before reopening"
            ) from None
