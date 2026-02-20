from typing import ClassVar, Any
import time
import json
from urllib.parse import urlencode, quote_plus
from dataclasses import dataclass, field
import http.client
import logging
from jibble_export.settings import setting


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG if setting.environment == "dev" else logging.INFO,
)


class AuthorizationExpired(Exception): ...


class AuthorizationFailed(Exception): ...


def load_encoded_jibble_creds():
    try:
        client_id = setting.jibble_client_id
        client_secret = setting.jibble_client_secret
    except KeyError:
        logging.error("client credentials not found")
        raise
    else:
        logging.debug("client credentials loaded successfully")

    encoded_creds = urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
        }
    )
    return encoded_creds


def authorize() -> AuthResponse:
    conn = http.client.HTTPSConnection("identity.prod.jibble.io")
    encoded_creds = load_encoded_jibble_creds()
    payload = f"grant_type=client_credentials&{encoded_creds}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    logging.info("Authorizing client...")
    conn.request("POST", "/connect/token", payload, headers)
    res = conn.getresponse()
    if res.status == http.HTTPStatus.OK:
        logging.info("Authorization successful!")
    else:
        logging.fatal("Authorization Failed!")
        raise AuthorizationFailed()
    data = res.read()
    logging.debug(data.decode())
    auth = AuthResponse(**json.loads(data.decode()))
    return auth


@dataclass
class AuthResponse:
    access_token: str
    expires_in: int
    token_type: str
    scope: str
    organizationId: str
    personId: str
    generated_at: int | float = field(init=False)

    def __post_init__(self):
        self.generated_at = time.monotonic()

    def has_expired(self):
        return time.monotonic() - self.generated_at > self.expires_in


@dataclass
class AuthorizedJibbleClient:
    domain: ClassVar[str] = "prod.jibble.io"
    auth: AuthResponse = field(init=False, default_factory=authorize)

    def reauthorize(self):
        self.auth = authorize()

    def get[T](
        self,
        *,
        subdomain: str,
        relative_path: str,
        params: dict[str, str],
        response_model: type[T],
        status: int,
    ) -> T:
        assert relative_path.startswith("/"), "`relative_path` must start with '/'`"
        if self.auth.has_expired():
            expired_at = self.auth.generated_at + self.auth.expires_in
            raise AuthorizationExpired(
                f"Authorization token expired {time.monotonic() - expired_at} seconds ago. Please generate a new one!"
            )
        base_url = self.domain if not subdomain else f"{subdomain}.{self.domain}"
        logging.debug("base_url = %s" % base_url)
        conn = http.client.HTTPSConnection(base_url)
        payload = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.access_token}",
        }
        if params:
            relative_path += "?" + "&".join(
                f"{key}={quote_plus(value)}" for key, value in params.items()
            )
        logging.debug("relative path = %s" % relative_path)
        conn.request("GET", relative_path, payload, headers)
        res = conn.getresponse()
        if res.status != status:
            raise ValueError(f"{res.status=}")
        data = res.read().decode()
        logging.debug("decoded response = %s" % data)
        if isinstance(None, response_model):
            return response_model()
        response = response_model(**json.loads(data))
        return response

    def post[T](
        self,
        *,
        subdomain: str,
        relative_path: str,
        payload: dict[str, Any],
        response_model: type[T],
        status: int,
    ) -> T:
        if self.auth.has_expired():
            raise AuthorizationExpired()
        base_url = self.domain if not subdomain else f"{subdomain}.{self.domain}"
        logging.debug("base_url = %s" % base_url)
        conn = http.client.HTTPSConnection(base_url)
        body = json.dumps(payload)
        logging.debug("body = %s" % body)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth.access_token}",
        }
        logging.debug("relative path = %s" % relative_path)
        conn.request("POST", relative_path, body, headers)
        res = conn.getresponse()
        if res.status != status:
            raise ValueError(f"{res.status=}")
        data = res.read().decode()
        logging.debug("decoded response = %s" % data)
        if isinstance(None, response_model):
            return response_model()
        response = response_model(**json.loads(data))
        return response

client = AuthorizedJibbleClient()
