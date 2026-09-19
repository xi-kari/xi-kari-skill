"""Runtime projection of observed Codex web execution into retrieval artifacts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from html.parser import HTMLParser
import http.client
import ipaddress
from pathlib import Path
import re
import socket
import ssl
from typing import Any
from urllib.parse import urljoin, urlsplit

from .canonical_json import (
    atomic_write_bytes,
    atomic_write_json,
    canonical_bytes,
    confined_path,
    read_bounded_regular_file,
    read_json_text,
    sha256_bytes,
    sha256_json,
    sha256_text,
)
from .problem_contract import parse_instant
from .retrieval import has_bound_host_observation


RECEIPT_SCHEMA_ID = "xi-kari.v3.retrieval-execution-receipt"
RECEIPT_PROTOCOL = "xi-kari.v3.codex-jsonl-web-execution/v1"
MAX_EVENT_STREAM_BYTES = 16 * 1024 * 1024
MAX_EVENT_COUNT = 10_000
MAX_HOST_CAPTURE_BYTES = 2 * 1024 * 1024
MAX_HOST_CAPTURE_REDIRECTS = 5
MAX_HOST_CAPTURE_URL_LENGTH = 4096
MAX_HOST_CAPTURE_HEADER_COUNT = 200
MAX_HOST_CAPTURE_HEADER_NAME_BYTES = 256
MAX_HOST_CAPTURE_HEADER_VALUE_BYTES = 16 * 1024
MAX_HOST_CAPTURE_HEADERS_BYTES = 128 * 1024
HOST_CAPTURE_INDEX_SCHEMA_ID = "xi-kari.v3.host-capture-index"
HOST_CAPTURE_INDEX_RELATIVE = Path("authoring/XK02-host-capture-index.json")
HOST_CAPTURE_BODY_DIRECTORY = Path("retrieval/captures")
HOST_CAPTURE_PROTOCOL = "xi-kari.v3.host-source-capture/v1"
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_TEXT_CONTENT_TYPES = frozenset(
    {
        "application/json",
        "application/ld+json",
        "application/xhtml+xml",
        "application/xml",
        "application/rss+xml",
        "application/atom+xml",
        "text/html",
        "text/plain",
        "text/xml",
    }
)
_HEADER_NAME = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")
_SINGLETON_RESPONSE_HEADERS = frozenset(
    {"content-encoding", "content-length", "content-type", "location"}
)
FIVE_DIRECTION_QUERY_DIRECTIONS = (
    "current_baseline",
    "mechanism_support",
    "counterevidence",
    "comparable_case",
    "affected_low_power_position",
)
SEMANTIC_FIELDS = frozenset(
    {
        "queries",
        "sources",
        "assessments",
        "saturation_status",
        "capability_gap",
        "remaining_unknowns",
    }
)
QUERY_FIELDS = frozenset({"direction", "query", "purpose"})
SOURCE_FIELDS = frozenset(
    {
        "origin",
        "title",
        "url",
        "publisher",
        "excerpt",
        "published_at",
        "event_at",
    }
)
ASSESSMENT_FIELDS = frozenset(
    {
        "source_url",
        "authority",
        "independence",
        "independence_identity",
        "source_lineage_urls",
        "interest_relevance",
        "affected_positions",
        "low_power_positions",
        "conflict_source_urls",
        "freshness",
        "relevance",
        "verdict",
        "limitations",
        "cannot_prove",
    }
)
RUNTIME_QUERY_FIELDS = frozenset(
    {"query_id", "status", "executed_at", "result_source_ids"}
)
RUNTIME_SOURCE_FIELDS = frozenset(
    {
        "source_id",
        "accessed_at",
        "content_sha256",
        "content_authority",
        "host_observation",
        "run_id",
    }
)
DIRECTIONAL_EVIDENCE_FIELDS = frozenset(
    {
        "direction",
        "search_event_id",
        "stop_boundary",
        "source_urls",
        "source_ids",
        "distinct_url_count",
        "distinct_source_count",
        "distinct_content_count",
        "distinct_independence_count",
        "new_information_count",
        "stop_reason",
    }
)
RECEIPT_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "protocol",
        "run_id",
        "execution_context_id",
        "provider_binding_sha256",
        "adapter_executable_sha256",
        "adapter_input_sha256",
        "parent_pid",
        "child_pid",
        "started_at",
        "completed_at",
        "exit_status",
        "stdout_sha256",
        "stderr_sha256",
        "event_stream_sha256",
        "event_count",
        "thread_id",
        "web_events",
        "semantic_retrieval_sha256",
        "retrieval_sha256",
        "query_bindings",
        "source_bindings",
        "directional_evidence",
        "receipt_sha256",
    }
)


def _exact_mapping(
    value: Any, expected: frozenset[str], *, label: str
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    forbidden = (set(value) & RUNTIME_QUERY_FIELDS) | (
        set(value) & RUNTIME_SOURCE_FIELDS
    )
    if forbidden:
        raise ValueError(
            "runtime-owned retrieval field is forbidden in semantic authoring: "
            + sorted(forbidden)[0]
        )
    if set(value) != expected:
        raise ValueError(f"{label} fields are not exact")
    return value


def _text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def _text_list(
    value: Any, *, label: str, require_nonempty: bool
) -> list[str]:
    if not isinstance(value, list) or (require_nonempty and not value):
        raise ValueError(f"{label} must be a list")
    result = [_text(item, label=f"{label} item") for item in value]
    if len(result) != len(set(result)):
        raise ValueError(f"{label} contains duplicate values")
    return result


def _sha256(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a SHA-256")
    return value


def _positive_pid(value: Any, *, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{label} must be a positive process id")
    return value


def _https_url(value: Any, *, label: str) -> str:
    url = _text(value, label=label)
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ValueError(f"{label} must be a verifiable HTTPS URL")
    return url


@dataclass(frozen=True)
class HostCapture:
    """A bounded HTTPS response observed by the runtime, before projection."""

    requested_url: str
    final_url: str
    status: int
    content_type: str
    charset: str
    body: bytes
    text: str
    body_sha256: str
    text_sha256: str
    redirect_chain: tuple[str, ...]
    peer_ip: str | None = None

    @property
    def capture_id(self) -> str:
        return "CAPTURE-WEB-" + sha256_json(
            {
                "requested_url": self.requested_url,
                "final_url": self.final_url,
                "body_sha256": self.body_sha256,
            }
        )[:20].upper()


HostFetcher = Callable[[str], tuple[Mapping[str, Any], bytes]]


class _HostTextExtractor(HTMLParser):
    """Extract visible HTML text without treating scripts as source prose."""

    _SUPPRESSED_TAGS = frozenset({"script", "style", "template", "noscript"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() in self._SUPPRESSED_TAGS:
            self._suppressed_depth += 1
        elif tag.casefold() in {"br", "hr", "li", "p", "div", "section", "tr"}:
            self._parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.casefold()
        if lowered in self._SUPPRESSED_TAGS and self._suppressed_depth:
            self._suppressed_depth -= 1
        elif lowered in {"p", "div", "section", "li", "tr"}:
            self._parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._suppressed_depth:
            self._parts.append(data)

    def text(self) -> str:
        return _normalise_capture_text("".join(self._parts))


def _normalise_capture_text(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("host capture text must be text")
    normalized = " ".join(value.split())
    if not normalized or "\x00" in normalized:
        raise ValueError("host capture text is empty or unsafe")
    return normalized


def _capture_url(value: Any, *, resolve: bool) -> str:
    url = _https_url(value, label="host capture URL")
    if len(url) > MAX_HOST_CAPTURE_URL_LENGTH:
        raise ValueError("host capture URL exceeds the maximum length")
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("host capture URL port is invalid") from exc
    if port not in {None, 443}:
        raise ValueError("host capture URL port is not HTTPS-default")
    hostname = parsed.hostname
    if hostname is None:
        raise ValueError("host capture URL has no hostname")
    host = hostname.rstrip(".").casefold()
    if (
        not host
        or host in {"localhost", "localhost.localdomain"}
        or host.endswith(".localhost")
        or host.endswith(".local")
    ):
        raise ValueError("host capture URL is private or unsafe")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None and not literal.is_global:
        raise ValueError("host capture URL is private or unsafe")
    if resolve:
        _resolve_public_host(host, port or 443)
    return url


def _validate_public_ip(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} is missing")
    try:
        parsed = ipaddress.ip_address(value)
    except ValueError as exc:
        raise ValueError(f"{label} is invalid") from exc
    if not parsed.is_global:
        raise ValueError(f"{label} is private or unsafe")
    return str(parsed)


def _resolve_public_host(hostname: str, port: int) -> set[str]:
    try:
        addresses = socket.getaddrinfo(
            hostname,
            port,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
    except OSError as exc:
        raise ValueError("host capture DNS resolution failed") from exc
    public: set[str] = set()
    for _family, _socktype, _protocol, _canonname, sockaddr in addresses:
        address = sockaddr[0]
        public.add(_validate_public_ip(address, label="host capture DNS address"))
    if not public:
        raise ValueError("host capture DNS resolution returned no addresses")
    return public


ResponseHeaders = dict[str, str | list[str]]


def _response_headers(value: Any) -> ResponseHeaders:
    if isinstance(value, Mapping):
        items = value.items()
    elif isinstance(value, (list, tuple)):
        items = value
    else:
        raise ValueError("host capture response headers are invalid")
    headers: ResponseHeaders = {}
    field_count = 0
    total_bytes = 0
    for pair in items:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("host capture response headers are invalid")
        raw_name, raw_value = pair
        if not isinstance(raw_name, str) or not _HEADER_NAME.fullmatch(raw_name):
            raise ValueError("host capture response headers are invalid")
        if isinstance(raw_value, str):
            values = (raw_value,)
        elif isinstance(raw_value, (list, tuple)) and raw_value:
            values = raw_value
        else:
            raise ValueError("host capture response headers are invalid")
        name = raw_name.casefold()
        name_bytes = len(raw_name.encode("ascii"))
        if name_bytes > MAX_HOST_CAPTURE_HEADER_NAME_BYTES:
            raise ValueError("host capture response headers exceed the maximum size")
        for raw_item in values:
            if not isinstance(raw_item, str) or any(
                ord(character) < 32 or ord(character) == 127
                for character in raw_item
            ):
                raise ValueError("host capture response headers are invalid")
            item = raw_item.strip()
            if not item:
                raise ValueError("host capture response headers are invalid")
            try:
                item_bytes = len(item.encode("utf-8"))
            except UnicodeEncodeError as exc:
                raise ValueError("host capture response headers are invalid") from exc
            if item_bytes > MAX_HOST_CAPTURE_HEADER_VALUE_BYTES:
                raise ValueError("host capture response headers exceed the maximum size")
            field_count += 1
            total_bytes += name_bytes + item_bytes + 4
            if (
                field_count > MAX_HOST_CAPTURE_HEADER_COUNT
                or total_bytes > MAX_HOST_CAPTURE_HEADERS_BYTES
            ):
                raise ValueError("host capture response headers exceed the maximum size")
            existing = headers.get(name)
            if existing is None:
                headers[name] = item
            elif isinstance(existing, str):
                headers[name] = [existing, item]
            else:
                existing.append(item)
    return headers


def _single_response_header(
    headers: Mapping[str, str | list[str]], name: str
) -> str | None:
    value = headers.get(name)
    if isinstance(value, list):
        raise ValueError(f"host capture response {name} header is ambiguous")
    if value is not None and not isinstance(value, str):
        raise ValueError("host capture response headers are invalid")
    return value


def _validate_response_control_headers(
    headers: Mapping[str, str | list[str]],
) -> None:
    for name in _SINGLETON_RESPONSE_HEADERS:
        _single_response_header(headers, name)


def _content_type(
    headers: Mapping[str, str | list[str]],
) -> tuple[str, str]:
    raw = _single_response_header(headers, "content-type")
    if raw is None:
        raise ValueError("host capture response has no content type")
    pieces = [piece.strip() for piece in raw.split(";")]
    media_type = pieces[0].casefold()
    if media_type not in _TEXT_CONTENT_TYPES:
        raise ValueError("host capture response content type is unsupported")
    charset = "utf-8"
    for piece in pieces[1:]:
        if not piece:
            continue
        name, separator, value = piece.partition("=")
        if separator and name.strip().casefold() == "charset":
            charset = value.strip().strip('"').casefold()
    if not charset:
        raise ValueError("host capture response charset is invalid")
    try:
        "".encode(charset)
    except LookupError as exc:
        raise ValueError("host capture response charset is unsupported") from exc
    return media_type, charset


def _bounded_body(
    headers: Mapping[str, str | list[str]], body: Any, *, max_bytes: int
) -> bytes:
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 1 <= max_bytes <= MAX_HOST_CAPTURE_BYTES:
        raise ValueError("host capture maximum body size is invalid")
    declared = _single_response_header(headers, "content-length")
    if declared is not None:
        if not declared.isdecimal() or int(declared) > max_bytes:
            raise ValueError("host capture response exceeds the maximum body size")
    encoding = (
        _single_response_header(headers, "content-encoding") or "identity"
    ).casefold()
    if encoding not in {"identity", ""}:
        raise ValueError("host capture response content encoding is unsupported")
    if not isinstance(body, bytes) or len(body) > max_bytes:
        raise ValueError("host capture response exceeds the maximum body size")
    if not body:
        raise ValueError("host capture response body is empty")
    return body


def _capture_text(body: bytes, *, content_type: str, charset: str) -> str:
    try:
        decoded = body.decode(charset, errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("host capture response text cannot be decoded") from exc
    if content_type in {"text/html", "application/xhtml+xml"}:
        parser = _HostTextExtractor()
        try:
            parser.feed(decoded)
            parser.close()
        except Exception as exc:
            raise ValueError("host capture HTML cannot be parsed") from exc
        return parser.text()
    return _normalise_capture_text(decoded)


def _fetch_https_once(url: str, *, max_bytes: int) -> tuple[dict[str, Any], bytes]:
    parsed = urlsplit(url)
    hostname = parsed.hostname
    if hostname is None:
        raise ValueError("host capture URL has no hostname")
    port = parsed.port or 443
    resolved = _resolve_public_host(hostname, port)
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query
    connection = http.client.HTTPSConnection(
        hostname,
        port=port,
        timeout=15,
        context=ssl.create_default_context(),
    )
    try:
        connection.putrequest("GET", target, skip_accept_encoding=True)
        connection.putheader("Accept", ", ".join(sorted(_TEXT_CONTENT_TYPES)))
        connection.putheader("Accept-Encoding", "identity")
        connection.putheader("User-Agent", "xi-kari-host-capture/1")
        connection.endheaders()
        response = connection.getresponse()
        socket_handle = connection.sock
        if socket_handle is None:
            raise ValueError("host capture connection has no peer socket")
        peer_ip = _validate_public_ip(
            socket_handle.getpeername()[0], label="host capture peer address"
        )
        if peer_ip not in resolved:
            raise ValueError("host capture peer address differs from validated DNS")
        headers = _response_headers(response.getheaders())
        declared = _single_response_header(headers, "content-length")
        if declared is not None and (not declared.isdecimal() or int(declared) > max_bytes):
            raise ValueError("host capture response exceeds the maximum body size")
        body = response.read(max_bytes + 1)
        return (
            {
                "url": url,
                "status": response.status,
                "headers": headers,
                "peer_ip": peer_ip,
            },
            body,
        )
    except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
        raise ValueError("host capture HTTPS request failed") from exc
    finally:
        connection.close()


def _capture_response_metadata(
    value: Any,
) -> tuple[str, int, ResponseHeaders, str | None]:
    if not isinstance(value, Mapping) or set(value) - {
        "url",
        "status",
        "headers",
        "peer_ip",
    }:
        raise ValueError("host capture response metadata is invalid")
    response_url = _capture_url(value.get("url"), resolve=False)
    status = value.get("status")
    if not isinstance(status, int) or isinstance(status, bool) or not 100 <= status <= 599:
        raise ValueError("host capture response status is invalid")
    headers = _response_headers(value.get("headers"))
    _validate_response_control_headers(headers)
    peer_ip = value.get("peer_ip")
    if peer_ip is not None:
        peer_ip = _validate_public_ip(peer_ip, label="host capture peer address")
    return response_url, status, headers, peer_ip


def capture_host_response(
    url: str,
    *,
    fetcher: HostFetcher | None = None,
    max_bytes: int = MAX_HOST_CAPTURE_BYTES,
    max_redirects: int = MAX_HOST_CAPTURE_REDIRECTS,
) -> HostCapture:
    """Capture one source through a bounded HTTPS-only host boundary."""

    if not isinstance(max_redirects, int) or isinstance(max_redirects, bool) or not 0 <= max_redirects <= MAX_HOST_CAPTURE_REDIRECTS:
        raise ValueError("host capture redirect limit is invalid")
    requested = _capture_url(url, resolve=fetcher is None)
    current = requested
    redirects: list[str] = []
    for hop in range(max_redirects + 1):
        metadata, raw_body = (
            fetcher(current) if fetcher is not None else _fetch_https_once(current, max_bytes=max_bytes)
        )
        response_url, status, headers, peer_ip = _capture_response_metadata(metadata)
        if response_url != current:
            raise ValueError("host capture response URL differs from requested URL")
        if status in _REDIRECT_STATUSES:
            location = _single_response_header(headers, "location")
            if location is None:
                raise ValueError("host capture redirect has no location")
            if hop >= max_redirects:
                raise ValueError("host capture redirect limit was exceeded")
            next_url = urljoin(current, location)
            current = _capture_url(next_url, resolve=fetcher is None)
            redirects.append(current)
            continue
        if not 200 <= status < 300:
            raise ValueError("host capture response status is not successful")
        content_type, charset = _content_type(headers)
        body = _bounded_body(headers, raw_body, max_bytes=max_bytes)
        text = _capture_text(body, content_type=content_type, charset=charset)
        return HostCapture(
            requested_url=requested,
            final_url=current,
            status=status,
            content_type=content_type,
            charset=charset,
            body=body,
            text=text,
            body_sha256=sha256_bytes(body),
            text_sha256=sha256_text(text),
            redirect_chain=tuple(redirects),
            peer_ip=peer_ip,
        )
    raise ValueError("host capture redirect limit was exceeded")


def _source_excerpt(value: Mapping[str, Any]) -> str:
    excerpt = value.get("excerpt", value.get("content"))
    return _normalise_capture_text(_text(excerpt, label="retrieval source excerpt"))


def _excerpt_locator(capture: HostCapture, excerpt: str) -> tuple[int, int]:
    if len(excerpt.encode("utf-8")) > 64 * 1024:
        raise ValueError("retrieval source excerpt exceeds the maximum length")
    start = capture.text.find(excerpt)
    if start < 0:
        raise ValueError("retrieval source excerpt is not located in the host capture")
    return start, start + len(excerpt)


def capture_host_sources(
    semantic_retrieval: Mapping[str, Any],
    *,
    fetcher: HostFetcher | None = None,
    max_bytes: int = MAX_HOST_CAPTURE_BYTES,
    max_redirects: int = MAX_HOST_CAPTURE_REDIRECTS,
) -> dict[str, HostCapture]:
    """Capture every model-named open-world source before source projection."""

    sources = semantic_retrieval.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("host capture requires retrieval sources")
    captures: dict[str, HostCapture] = {}
    for source in sources:
        if not isinstance(source, Mapping):
            raise ValueError("host capture source is invalid")
        url = _https_url(source.get("url"), label="retrieval source URL")
        if url in captures:
            raise ValueError("host capture source URLs must be unique")
        capture = capture_host_response(
            url,
            fetcher=fetcher,
            max_bytes=max_bytes,
            max_redirects=max_redirects,
        )
        _excerpt_locator(capture, _source_excerpt(source))
        captures[url] = capture
    return captures


def _host_observation_binding(
    source_id: str,
    content_sha256: str,
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "content_sha256": content_sha256,
        "event_stream_sha256": observation.get("event_stream_sha256"),
        "open_event_ids": observation.get("open_event_ids"),
        "capture_id": observation.get("capture_id"),
        "requested_url": observation.get("requested_url"),
        "final_url": observation.get("final_url"),
        "peer_ip": observation.get("peer_ip"),
        "response_status": observation.get("response_status"),
        "content_type": observation.get("content_type"),
        "charset": observation.get("charset"),
        "body_sha256": observation.get("body_sha256"),
        "text_sha256": observation.get("text_sha256"),
        "body_byte_count": observation.get("body_byte_count"),
        "text_character_count": observation.get("text_character_count"),
        "redirect_chain": observation.get("redirect_chain"),
        "excerpt_sha256": observation.get("excerpt_sha256"),
        "excerpt_start": observation.get("excerpt_start"),
        "excerpt_end": observation.get("excerpt_end"),
    }


def build_host_capture_index(
    *,
    run_id: str,
    event_stream_sha256: str,
    retrieval: Mapping[str, Any],
    semantic_retrieval: Mapping[str, Any],
    host_captures: Mapping[str, HostCapture],
) -> dict[str, Any]:
    """Build the disk index that binds source IDs to replayable response bytes."""

    run = _text(run_id, label="host capture run_id")
    event_sha = _sha256(event_stream_sha256, label="host capture event stream hash")
    sources = retrieval.get("sources")
    semantic_sources = semantic_retrieval.get("sources")
    if (
        not isinstance(sources, list)
        or not isinstance(semantic_sources, list)
        or not isinstance(host_captures, Mapping)
    ):
        raise ValueError("host capture index inputs are invalid")
    semantic_by_url = {
        source.get("url"): source
        for source in semantic_sources
        if isinstance(source, Mapping) and isinstance(source.get("url"), str)
    }
    rows: list[dict[str, Any]] = []
    seen_capture_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, Mapping):
            raise ValueError("host capture index source is invalid")
        source_id = source.get("source_id")
        url = source.get("url")
        observation = source.get("host_observation")
        if not isinstance(source_id, str) or not source_id or not isinstance(url, str):
            raise ValueError("host capture index source identity is invalid")
        capture = host_captures.get(url)
        if not isinstance(capture, HostCapture):
            raise ValueError("host capture index is missing a source response")
        capture_id = capture.capture_id
        if capture_id in seen_capture_ids:
            raise ValueError("host capture IDs are not unique")
        seen_capture_ids.add(capture_id)
        if capture.requested_url != url:
            raise ValueError("host capture requested URL differs from source URL")
        if not isinstance(observation, Mapping) or observation.get("status") != "bound":
            raise ValueError("host capture source has no bound observation")
        semantic_source = semantic_by_url.get(url)
        if not isinstance(semantic_source, Mapping):
            raise ValueError("host capture index has no semantic source URL")
        excerpt = _source_excerpt(semantic_source)
        excerpt_start, excerpt_end = _excerpt_locator(capture, excerpt)
        body_path = (HOST_CAPTURE_BODY_DIRECTORY / f"{capture_id}.bin").as_posix()
        expected = {
            "capture_id": capture_id,
            "source_id": source_id,
            "requested_url": capture.requested_url,
            "final_url": capture.final_url,
            "status": capture.status,
            "content_type": capture.content_type,
            "charset": capture.charset,
            "peer_ip": capture.peer_ip,
            "redirect_chain": list(capture.redirect_chain),
            "body_path": body_path,
            "body_sha256": capture.body_sha256,
            "body_byte_count": len(capture.body),
            "text_sha256": capture.text_sha256,
            "text_character_count": len(capture.text),
            "excerpt_sha256": sha256_text(excerpt),
            "excerpt_start": excerpt_start,
            "excerpt_end": excerpt_end,
            "event_stream_sha256": event_sha,
            "open_event_ids": list(observation.get("open_event_ids", [])),
        }
        if observation.get("capture_id") != capture_id:
            raise ValueError("host capture observation capture ID differs")
        if observation.get("body_sha256") != capture.body_sha256:
            raise ValueError("host capture observation body hash differs")
        if observation.get("text_sha256") != capture.text_sha256:
            raise ValueError("host capture observation text hash differs")
        if observation.get("peer_ip") != capture.peer_ip:
            raise ValueError("host capture observation peer address differs")
        if source.get("content_sha256") != sha256_text(excerpt):
            raise ValueError("host capture source content hash differs")
        expected_observation_binding = {
            "source_id": source_id,
            "content_sha256": sha256_text(excerpt),
            "event_stream_sha256": event_sha,
            "open_event_ids": list(observation.get("open_event_ids", [])),
            **{
                field: observation.get(field)
                for field in (
                    "capture_id",
                    "requested_url",
                    "final_url",
                    "peer_ip",
                    "response_status",
                    "content_type",
                    "charset",
                    "body_sha256",
                    "text_sha256",
                    "body_byte_count",
                    "text_character_count",
                    "redirect_chain",
                    "excerpt_sha256",
                    "excerpt_start",
                    "excerpt_end",
                )
            },
        }
        if observation.get("binding_sha256") != sha256_json(expected_observation_binding):
            raise ValueError("host capture observation binding hash differs")
        rows.append(expected)
    rows.sort(key=lambda item: item["source_id"])
    index: dict[str, Any] = {
        "schema_id": HOST_CAPTURE_INDEX_SCHEMA_ID,
        "schema_version": 1,
        "protocol": HOST_CAPTURE_PROTOCOL,
        "run_id": run,
        "event_stream_sha256": event_sha,
        "captures": rows,
        "capture_count": len(rows),
        "index_sha256": "",
    }
    index["index_sha256"] = sha256_json(
        {key: value for key, value in index.items() if key != "index_sha256"}
    )
    return index


def _capture_from_index_row(row: Mapping[str, Any], body: bytes) -> HostCapture:
    required = {
        "capture_id",
        "source_id",
        "requested_url",
        "final_url",
        "status",
        "content_type",
        "charset",
        "peer_ip",
        "redirect_chain",
        "body_path",
        "body_sha256",
        "body_byte_count",
        "text_sha256",
        "text_character_count",
        "excerpt_sha256",
        "excerpt_start",
        "excerpt_end",
        "event_stream_sha256",
        "open_event_ids",
    }
    if set(row) != required:
        raise ValueError("host capture index row fields are not exact")
    requested = _capture_url(row.get("requested_url"), resolve=False)
    final = _capture_url(row.get("final_url"), resolve=False)
    status = row.get("status")
    if not isinstance(status, int) or not 200 <= status < 300:
        raise ValueError("host capture index response status is invalid")
    content_type = row.get("content_type")
    charset = row.get("charset")
    if not isinstance(content_type, str) or content_type not in _TEXT_CONTENT_TYPES:
        raise ValueError("host capture index content type is invalid")
    if not isinstance(charset, str) or not charset:
        raise ValueError("host capture index charset is invalid")
    if row.get("peer_ip") is not None:
        _validate_public_ip(row.get("peer_ip"), label="host capture index peer address")
    if not isinstance(row.get("redirect_chain"), list) or any(
        not isinstance(item, str) for item in row["redirect_chain"]
    ):
        raise ValueError("host capture index redirect chain is invalid")
    if not isinstance(row.get("open_event_ids"), list) or not row["open_event_ids"]:
        raise ValueError("host capture index open event IDs are invalid")
    if not isinstance(row.get("body_byte_count"), int) or row["body_byte_count"] != len(body):
        raise ValueError("host capture index body byte count differs")
    if row.get("body_sha256") != sha256_bytes(body):
        raise ValueError("host capture index body hash differs")
    text = _capture_text(body, content_type=content_type, charset=charset)
    if row.get("text_sha256") != sha256_text(text):
        raise ValueError("host capture index text hash differs")
    if row.get("text_character_count") != len(text):
        raise ValueError("host capture index text length differs")
    start = row.get("excerpt_start")
    end = row.get("excerpt_end")
    if (
        not isinstance(start, int)
        or isinstance(start, bool)
        or not isinstance(end, int)
        or isinstance(end, bool)
        or not 0 <= start < end <= len(text)
        or row.get("excerpt_sha256") != sha256_text(text[start:end])
    ):
        raise ValueError("host capture index excerpt locator differs")
    return HostCapture(
        requested_url=requested,
        final_url=final,
        status=status,
        content_type=content_type,
        charset=charset,
        body=body,
        text=text,
        body_sha256=sha256_bytes(body),
        text_sha256=sha256_text(text),
        redirect_chain=tuple(row["redirect_chain"]),
        peer_ip=row.get("peer_ip"),
    )


def write_host_capture_bundle(
    run_dir: Path,
    *,
    index: Mapping[str, Any],
    host_captures: Mapping[str, HostCapture],
) -> None:
    """Persist replay bytes and the canonical index without following links."""

    root = Path(run_dir).resolve()
    if not isinstance(index, Mapping) or index.get("schema_id") != HOST_CAPTURE_INDEX_SCHEMA_ID:
        raise ValueError("host capture index identity is invalid")
    rows = index.get("captures")
    if not isinstance(rows, list):
        raise ValueError("host capture index captures are invalid")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("host capture index row is invalid")
        capture = host_captures.get(row.get("requested_url"))
        if not isinstance(capture, HostCapture) or capture.capture_id != row.get("capture_id"):
            raise ValueError("host capture index does not bind response bytes")
        path = confined_path(root, row.get("body_path", ""))
        if path.parent != (root / HOST_CAPTURE_BODY_DIRECTORY).resolve():
            raise ValueError("host capture body path leaves capture directory")
        atomic_write_bytes(path, capture.body)
    atomic_write_json(confined_path(root, HOST_CAPTURE_INDEX_RELATIVE), dict(index))


def load_host_capture_bundle(
    run_dir: Path,
    *,
    run_id: str,
) -> tuple[dict[str, Any], dict[str, HostCapture]]:
    """Read and verify capture index plus raw response bytes from disk."""

    root = Path(run_dir).resolve()
    index_path = confined_path(root, HOST_CAPTURE_INDEX_RELATIVE, must_exist=True)
    index = read_json_text(index_path.read_text(encoding="utf-8"))
    if not isinstance(index, dict):
        raise ValueError("host capture index is not an object")
    required = {
        "schema_id",
        "schema_version",
        "protocol",
        "run_id",
        "event_stream_sha256",
        "captures",
        "capture_count",
        "index_sha256",
    }
    if set(index) != required:
        raise ValueError("host capture index fields are not exact")
    if (
        index.get("schema_id") != HOST_CAPTURE_INDEX_SCHEMA_ID
        or index.get("schema_version") != 1
        or index.get("protocol") != HOST_CAPTURE_PROTOCOL
        or index.get("run_id") != run_id
        or index.get("index_sha256")
        != sha256_json({key: value for key, value in index.items() if key != "index_sha256"})
    ):
        raise ValueError("host capture index binding or hash differs")
    rows = index.get("captures")
    if not isinstance(rows, list) or index.get("capture_count") != len(rows):
        raise ValueError("host capture index count differs")
    captures: dict[str, HostCapture] = {}
    seen_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("host capture index row is invalid")
        capture_id = row.get("capture_id")
        if not isinstance(capture_id, str) or capture_id in seen_ids:
            raise ValueError("host capture index IDs are not unique")
        seen_ids.add(capture_id)
        if row.get("event_stream_sha256") != index.get("event_stream_sha256"):
            raise ValueError("host capture index event stream hash differs")
        body_path = row.get("body_path")
        if not isinstance(body_path, str) or not body_path.startswith(
            f"{HOST_CAPTURE_BODY_DIRECTORY.as_posix()}/"
        ):
            raise ValueError("host capture body path is invalid")
        path = confined_path(root, body_path, must_exist=True)
        body = read_bounded_regular_file(path, limit=MAX_HOST_CAPTURE_BYTES)
        capture = _capture_from_index_row(row, body)
        if capture.capture_id != capture_id:
            raise ValueError("host capture ID differs from response bytes")
        requested_url = capture.requested_url
        if requested_url in captures:
            raise ValueError("host capture requested URLs are not unique")
        captures[requested_url] = capture
    return index, captures


def _event_stream(raw: bytes) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_EVENT_STREAM_BYTES:
        raise ValueError("Codex JSONL event stream size is invalid")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Codex JSONL event stream is not UTF-8") from exc
    lines = text.splitlines()
    if not lines or len(lines) > MAX_EVENT_COUNT or any(not line for line in lines):
        raise ValueError("Codex JSONL event stream line count is invalid")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            event = read_json_text(line)
        except ValueError as exc:
            raise ValueError(
                f"Codex JSONL event is invalid at line {line_number}"
            ) from exc
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise ValueError(
                f"Codex JSONL event is not an object at line {line_number}"
            )
        events.append(event)
    if any(
        event.get("type") in {"turn.failed", "error"}
        or (
            event.get("type") in {"item.started", "item.updated", "item.completed"}
            and isinstance(event.get("item"), Mapping)
            and event["item"].get("type") == "error"
        )
        for event in events
    ):
        raise ValueError("Codex JSONL stream contains a failed or error event")
    if events[0].get("type") != "thread.started":
        raise ValueError("Codex JSONL stream must begin with thread.started")
    if len(events) < 3 or events[1].get("type") != "turn.started":
        raise ValueError("Codex turn.started must follow thread.started")
    thread_events = [event for event in events if event.get("type") == "thread.started"]
    turn_started = [event for event in events if event.get("type") == "turn.started"]
    turn_completed = [event for event in events if event.get("type") == "turn.completed"]
    if len(thread_events) != 1 or set(thread_events[0]) != {"type", "thread_id"}:
        raise ValueError("Codex JSONL stream has no unique thread authority")
    thread_id = _text(thread_events[0].get("thread_id"), label="Codex thread_id")
    if len(turn_started) != 1 or len(turn_completed) != 1:
        raise ValueError("Codex JSONL stream has no unique completed turn")
    if events[-1].get("type") != "turn.completed":
        raise ValueError("Codex JSONL stream does not end at turn.completed")

    web_events: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for sequence, event in enumerate(events):
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, Mapping) or item.get("type") != "web_search":
            continue
        if set(item) != {"id", "type", "query", "action"}:
            raise ValueError("completed Codex web_search item fields are not exact")
        event_id = _text(item.get("id"), label="Codex web_search id")
        if event_id in seen_ids:
            raise ValueError("completed Codex web_search ids are not unique")
        seen_ids.add(event_id)
        display_query = _text(
            item.get("query"), label="Codex web_search display query"
        )
        action = item.get("action")
        if not isinstance(action, Mapping) or not isinstance(action.get("type"), str):
            raise ValueError("completed Codex web_search action is invalid")
        action_type = action["type"]
        if action_type == "search":
            if not set(action).issubset({"type", "query", "queries"}):
                raise ValueError("Codex search action fields are not exact")
            query = action.get("query")
            queries = action.get("queries")
            if query is not None:
                _text(query, label="Codex search query")
            if queries is not None:
                _text_list(
                    queries,
                    label="Codex search queries",
                    require_nonempty=True,
                )
            if query is None and queries is None:
                raise ValueError("Codex search action has no query")
        elif action_type == "open_page":
            if set(action) != {"type", "url"}:
                raise ValueError("Codex open_page action fields are not exact")
            _https_url(action.get("url"), label="Codex open_page URL")
        elif action_type == "find_in_page":
            if not set(action).issubset({"type", "url", "pattern"}):
                raise ValueError("Codex find_in_page action fields are not exact")
            _https_url(action.get("url"), label="Codex find_in_page URL")
            if action.get("pattern") is not None:
                _text(action["pattern"], label="Codex find_in_page pattern")
        else:
            raise ValueError("Codex web_search action type is unsupported")
        web_events.append(
            {
                "sequence": sequence,
                "event_id": event_id,
                "event_sha256": sha256_json(event),
                "query": display_query,
                "action": deepcopy(dict(action)),
            }
        )
    if not web_events:
        raise ValueError("Codex JSONL stream has no completed web_search events")
    return thread_id, events, web_events


def _normalise_semantic(value: Any) -> dict[str, Any]:
    document = _exact_mapping(value, SEMANTIC_FIELDS, label="semantic retrieval")
    queries = document.get("queries")
    sources = document.get("sources")
    assessments = document.get("assessments")
    if not all(isinstance(item, list) for item in (queries, sources, assessments)):
        raise ValueError("semantic retrieval queries, sources, and assessments must be lists")
    if len(queries) != 5:
        raise ValueError("production open-world retrieval requires exactly five query intents")
    normalised_queries: list[dict[str, Any]] = []
    seen_queries: set[str] = set()
    seen_directions: list[str] = []
    for index, raw_query in enumerate(queries):
        query = _exact_mapping(
            raw_query, QUERY_FIELDS, label=f"semantic retrieval query {index + 1}"
        )
        direction = _text(query.get("direction"), label="retrieval direction")
        query_text = _text(query.get("query"), label="retrieval query")
        purpose = _text(query.get("purpose"), label="retrieval purpose")
        if query_text in seen_queries:
            raise ValueError("semantic retrieval query texts must be unique")
        seen_queries.add(query_text)
        seen_directions.append(direction)
        normalised_queries.append(
            {
                "direction": direction,
                "query": query_text,
                "purpose": purpose,
            }
        )
    if tuple(seen_directions) != FIVE_DIRECTION_QUERY_DIRECTIONS:
        raise ValueError("semantic retrieval directions do not match the five-direction order")

    normalised_sources: list[dict[str, Any]] = []
    source_urls: list[str] = []
    for index, raw_source in enumerate(sources):
        source = _exact_mapping(
            raw_source, SOURCE_FIELDS, label=f"semantic retrieval source {index + 1}"
        )
        if source.get("origin") != "external":
            raise ValueError("production open-world retrieval sources must be external")
        url = _https_url(source.get("url"), label="retrieval source URL")
        record = {
            "origin": "external",
            "title": _text(source.get("title"), label="retrieval source title"),
            "url": url,
            "publisher": _text(
                source.get("publisher"), label="retrieval source publisher"
            ),
            "content": _text(
                source.get("excerpt"), label="retrieval source excerpt"
            ),
            "published_at": _text(
                source.get("published_at"), label="retrieval source published_at"
            ),
            "event_at": _text(
                source.get("event_at"), label="retrieval source event_at"
            ),
        }
        if url in source_urls:
            raise ValueError("semantic retrieval source URLs must be unique")
        source_urls.append(url)
        normalised_sources.append(record)
    if not normalised_sources:
        raise ValueError("production open-world retrieval requires sources")
    normalised_assessments: list[dict[str, Any]] = []
    assessment_urls: list[str] = []
    for index, raw_assessment in enumerate(assessments):
        assessment = _exact_mapping(
            raw_assessment,
            ASSESSMENT_FIELDS,
            label=f"semantic retrieval assessment {index + 1}",
        )
        source_url = _https_url(
            assessment.get("source_url"), label="assessment source URL"
        )
        if source_url not in source_urls or source_url in assessment_urls:
            raise ValueError("semantic retrieval assessments must cover source URLs once")
        assessment_urls.append(source_url)
        list_fields = {
            field: _text_list(
                assessment.get(field),
                label=f"assessment {field}",
                require_nonempty=field
                in {"affected_positions", "low_power_positions", "cannot_prove"},
            )
            for field in (
                "source_lineage_urls",
                "affected_positions",
                "low_power_positions",
                "conflict_source_urls",
                "limitations",
                "cannot_prove",
            )
        }
        for field in ("source_lineage_urls", "conflict_source_urls"):
            list_fields[field] = [
                _https_url(url, label=f"assessment {field} URL")
                for url in list_fields[field]
            ]
            if any(url not in source_urls for url in list_fields[field]):
                raise ValueError(f"assessment {field} has an unknown source URL")
        normalised_assessments.append(
            {
                "source_url": source_url,
                "authority": _text(
                    assessment.get("authority"), label="assessment authority"
                ),
                "independence": _text(
                    assessment.get("independence"), label="assessment independence"
                ),
                "independence_identity": _text(
                    assessment.get("independence_identity"),
                    label="assessment independence identity",
                ),
                "source_lineage_urls": list_fields["source_lineage_urls"],
                "interest_relevance": _text(
                    assessment.get("interest_relevance"),
                    label="assessment interest relevance",
                ),
                "affected_positions": list_fields["affected_positions"],
                "low_power_positions": list_fields["low_power_positions"],
                "conflict_source_urls": list_fields["conflict_source_urls"],
                "freshness": _text(
                    assessment.get("freshness"), label="assessment freshness"
                ),
                "relevance": _text(
                    assessment.get("relevance"), label="assessment relevance"
                ),
                "verdict": _text(
                    assessment.get("verdict"), label="assessment verdict"
                ),
                "limitations": list_fields["limitations"],
                "cannot_prove": list_fields["cannot_prove"],
            }
        )
    if set(assessment_urls) != set(source_urls):
        raise ValueError("one semantic assessment is required per source URL")
    remaining_unknowns = _text_list(
        document.get("remaining_unknowns"),
        label="retrieval remaining_unknowns",
        require_nonempty=False,
    )
    return {
        "queries": normalised_queries,
        "sources": normalised_sources,
        "assessments": normalised_assessments,
        "saturation_status": _text(
            document.get("saturation_status"), label="retrieval saturation_status"
        ),
        "capability_gap": _text(
            document.get("capability_gap"), label="retrieval capability_gap"
        ),
        "remaining_unknowns": remaining_unknowns,
    }


def _query_sessions(
    semantic_queries: list[dict[str, Any]],
    source_urls: set[str],
    web_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    searches: list[tuple[dict[str, Any], list[str]]] = []
    for event in web_events:
        action = event["action"]
        if action["type"] != "search":
            continue
        terms: list[str] = []
        if isinstance(action.get("query"), str):
            terms.append(action["query"].strip())
        if isinstance(action.get("queries"), list):
            terms.extend(item.strip() for item in action["queries"])
        searches.append((event, list(dict.fromkeys(terms))))
    if len(searches) != len(semantic_queries):
        raise ValueError(
            "Codex retrieval must contain exactly one search action per five-direction query"
        )

    sessions: list[dict[str, Any]] = []
    associated_urls: set[str] = set()
    for index, query in enumerate(semantic_queries):
        search_event, terms = searches[index]
        if terms != [query["query"]]:
            raise ValueError(
                "Codex search action order differs from five-direction query intents"
            )
        start = search_event["sequence"]
        stop = searches[index + 1][0]["sequence"] if index + 1 < len(searches) else None
        opened_urls: list[str] = []
        for event in web_events:
            action = event["action"]
            sequence = event["sequence"]
            if (
                action["type"] == "open_page"
                and sequence > start
                and (stop is None or sequence < stop)
                and action["url"] in source_urls
                and action["url"] not in opened_urls
            ):
                opened_urls.append(action["url"])
        if not opened_urls:
            raise ValueError(
                f"retrieval query session has no associated opened source: {query['query']}"
            )
        associated_urls.update(opened_urls)
        sessions.append(
            {
                "search_event_ids": [search_event["event_id"]],
                "search_event_id": search_event["event_id"],
                "stop_boundary": (
                    f"next_search:{searches[index + 1][0]['event_id']}"
                    if index + 1 < len(searches)
                    else "turn.completed"
                ),
                "source_urls": opened_urls,
            }
        )
    if associated_urls != source_urls:
        missing = sorted(source_urls - associated_urls)
        raise ValueError(
            "retrieval source is outside every five-direction query session: "
            + missing[0]
        )
    return sessions


def _directional_evidence(
    semantic_queries: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    assessments_by_url: Mapping[str, dict[str, Any]],
    source_ids: Mapping[str, str],
) -> list[dict[str, Any]]:
    source_by_url = {source["url"]: source for source in sources}
    seen_information: set[tuple[str, str]] = set()
    directional: list[dict[str, Any]] = []
    for query, session in zip(semantic_queries, sessions):
        urls = list(session["source_urls"])
        ids = [source_ids[url] for url in urls]
        content_hashes = [
            source_by_url[url].get("content_sha256")
            or sha256_text(source_by_url[url]["content"])
            for url in urls
        ]
        independence_identities = [
            assessments_by_url[url]["independence_identity"] for url in urls
        ]
        information = {
            (content_hashes[index], independence_identities[index])
            for index, url in enumerate(urls)
            if has_bound_host_observation(source_by_url[url])
        }
        new_information = information - seen_information
        seen_information.update(information)
        directional.append(
            {
                "direction": query["direction"],
                "search_event_id": session["search_event_id"],
                "stop_boundary": session["stop_boundary"],
                "source_urls": urls,
                "source_ids": ids,
                "distinct_url_count": len(set(urls)),
                "distinct_source_count": len(set(ids)),
                "distinct_content_count": len(set(content_hashes)),
                "distinct_independence_count": len(set(independence_identities)),
                "new_information_count": len(new_information),
                "stop_reason": (
                    "next_direction_search"
                    if session["stop_boundary"].startswith("next_search:")
                    else "turn_completed"
                ),
            }
        )
    return directional


def _runtime_saturation(
    semantic: Mapping[str, Any],
    directional: list[dict[str, Any]],
    runtime_sources: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    status = semantic["saturation_status"]
    unknowns = list(semantic["remaining_unknowns"])
    if status != "evidence_saturated":
        return status, unknowns

    source_by_url = {source["url"]: source for source in runtime_sources}
    trusted_urls = {
        url
        for url, source in source_by_url.items()
        if has_bound_host_observation(source)
    }
    source_ids = {
        source_id
        for item in directional
        for url, source_id in zip(item["source_urls"], item["source_ids"])
        if url in trusted_urls
    }
    assessment_by_url = {
        assessment["source_url"]: assessment
        for assessment in semantic["assessments"]
    }
    urls = {
        url
        for item in directional
        for url in item["source_urls"]
    }
    content_hashes = {
        source_by_url[url].get("content_sha256")
        or sha256_text(source_by_url[url]["content"])
        for url in urls
        if url in trusted_urls
    }
    independence_identities = {
        assessment_by_url[url]["independence_identity"]
        for url in urls
        if url in trusted_urls
    }
    has_directional_increment = sum(
        item["new_information_count"] > 0 for item in directional
    ) >= 2
    has_independent_coverage = (
        len(source_ids) >= 2
        and len(content_hashes) >= 2
        and len(independence_identities) >= 2
    )
    event_saturates = (
        len(directional) == len(FIVE_DIRECTION_QUERY_DIRECTIONS)
        and all(
            item["source_ids"]
            and item["stop_boundary"]
            and item["stop_reason"]
            for item in directional
        )
        and has_directional_increment
        and has_independent_coverage
    )
    if not event_saturates:
        status = "bounded_saturation"
        if not unknowns:
            unknowns.append(
                "independent evidence saturation was not established by the observed event stream"
            )
        return status, unknowns
    if not unknowns:
        unknowns.append(
            "evidence outside the observed directional event stream remains unknown"
        )
    return status, unknowns


def project_runtime_retrieval(
    semantic_retrieval: Mapping[str, Any],
    event_stream: bytes,
    *,
    run_id: str,
    execution_context_id: str,
    provider_binding_sha256: str,
    adapter_executable_sha256: str,
    adapter_input: bytes,
    parent_pid: int,
    child_pid: int,
    started_at: str,
    completed_at: str,
    exit_status: int,
    stderr_sha256: str,
    evidence_cutoff: str,
    host_captures: Mapping[str, HostCapture] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project process observations; the process-owning adapter supplies them."""

    run = _text(run_id, label="run_id")
    context = _text(execution_context_id, label="execution_context_id")
    provider_sha = _sha256(
        provider_binding_sha256, label="provider_binding_sha256"
    )
    adapter_sha = _sha256(
        adapter_executable_sha256, label="adapter_executable_sha256"
    )
    if not isinstance(adapter_input, bytes) or not adapter_input:
        raise ValueError("retrieval adapter input must be non-empty bytes")
    try:
        adapter_input_document = read_json_text(adapter_input.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("retrieval adapter input is not canonical UTF-8 JSON") from exc
    if (
        not isinstance(adapter_input_document, Mapping)
        or adapter_input_document.get("run_id") != run
        or adapter_input != canonical_bytes(dict(adapter_input_document)) + b"\n"
    ):
        raise ValueError("retrieval adapter input does not bind run_id canonically")
    input_sha = sha256_bytes(adapter_input)
    stderr_sha = _sha256(stderr_sha256, label="stderr_sha256")
    parent = _positive_pid(parent_pid, label="parent_pid")
    child = _positive_pid(child_pid, label="child_pid")
    if parent == child:
        raise ValueError("retrieval parent and child process ids must differ")
    started = _text(started_at, label="retrieval started_at")
    completed = _text(completed_at, label="retrieval completed_at")
    cutoff = _text(evidence_cutoff, label="evidence_cutoff")
    if exit_status != 0:
        raise ValueError("Codex retrieval execution did not exit successfully")
    started_instant = parse_instant(started, field="retrieval started_at")
    completed_instant = parse_instant(completed, field="retrieval completed_at")
    cutoff_instant = parse_instant(cutoff, field="evidence_cutoff")
    if started_instant > completed_instant or completed_instant > cutoff_instant:
        raise ValueError("retrieval execution time is outside the evidence cutoff")

    semantic_input_sha256 = sha256_json(dict(semantic_retrieval))
    semantic = _normalise_semantic(semantic_retrieval)
    thread_id, events, web_events = _event_stream(event_stream)
    event_stream_sha256 = sha256_bytes(event_stream)
    opened_urls: dict[str, list[str]] = {}
    for event in web_events:
        action = event["action"]
        if action["type"] == "open_page":
            opened_urls.setdefault(action["url"], []).append(event["event_id"])
    query_sessions = _query_sessions(
        semantic["queries"],
        {source["url"] for source in semantic["sources"]},
        web_events,
    )
    assessment_by_url = {
        assessment["source_url"]: assessment
        for assessment in semantic["assessments"]
    }

    source_ids: dict[str, str] = {}
    runtime_sources: list[dict[str, Any]] = []
    source_bindings: list[dict[str, Any]] = []
    if host_captures is not None and set(host_captures) != {
        source["url"] for source in semantic["sources"]
    }:
        raise ValueError("host capture sources differ from semantic retrieval URLs")
    for source in semantic["sources"]:
        url = source["url"]
        event_ids = opened_urls.get(url, [])
        if not event_ids:
            raise ValueError(f"retrieval source has no completed open_page event: {url}")
        capture = host_captures.get(url) if host_captures is not None else None
        if capture is not None and not isinstance(capture, HostCapture):
            raise ValueError("host capture is invalid")
        source_content = source["content"]
        content_sha256 = sha256_text(source_content)
        source_id = "SOURCE-WEB-" + sha256_json(
            {
                "run_id": run,
                "url": url,
                "final_url": capture.final_url if capture is not None else url,
                "content_sha256": content_sha256,
            }
        )[:20].upper()
        source_ids[url] = source_id
        if capture is None:
            host_observation: dict[str, Any] = {
                "status": "unbound",
                "event_stream_sha256": event_stream_sha256,
                "open_event_ids": list(event_ids),
            }
            content_authority = "model-authored-excerpt"
        else:
            excerpt = source["content"]
            excerpt_start, excerpt_end = _excerpt_locator(capture, excerpt)
            host_observation = {
                "status": "bound",
                "event_stream_sha256": event_stream_sha256,
                "open_event_ids": list(event_ids),
                "capture_id": capture.capture_id,
                "requested_url": capture.requested_url,
                "final_url": capture.final_url,
                "peer_ip": capture.peer_ip,
                "response_status": capture.status,
                "content_type": capture.content_type,
                "charset": capture.charset,
                "body_sha256": capture.body_sha256,
                "text_sha256": capture.text_sha256,
                "body_byte_count": len(capture.body),
                "text_character_count": len(capture.text),
                "redirect_chain": list(capture.redirect_chain),
                "excerpt_sha256": sha256_text(excerpt),
                "excerpt_start": excerpt_start,
                "excerpt_end": excerpt_end,
            }
            host_observation["binding_sha256"] = sha256_json(
                _host_observation_binding(
                    source_id, content_sha256, host_observation
                )
            )
            content_authority = "host-observed"
        runtime_source = {
            "source_id": source_id,
            **{key: value for key, value in source.items() if key != "content"},
            "content": source_content,
            "accessed_at": completed,
            "content_sha256": content_sha256,
            "content_authority": content_authority,
            "host_observation": host_observation,
            "run_id": run,
        }
        runtime_sources.append(runtime_source)
        source_bindings.append(
            {
                "source_id": source_id,
                "url": url,
                "content_sha256": content_sha256,
                "content_authority": content_authority,
                "accessed_at": completed,
                "open_event_ids": list(event_ids),
                "host_observation": host_observation,
            }
        )

    directional_evidence = _directional_evidence(
        semantic["queries"],
        query_sessions,
        runtime_sources,
        assessment_by_url,
        source_ids,
    )
    saturation_status, remaining_unknowns = _runtime_saturation(
        semantic,
        directional_evidence,
        runtime_sources,
    )

    runtime_queries: list[dict[str, Any]] = []
    query_bindings: list[dict[str, Any]] = []
    for index, (query, session) in enumerate(
        zip(semantic["queries"], query_sessions), start=1
    ):
        result_source_ids = [source_ids[url] for url in session["source_urls"]]
        query_id = (
            f"QUERY-WEB-{index:02d}-"
            + sha256_json(
                {
                    "run_id": run,
                    "direction": query["direction"],
                    "query": query["query"],
                }
            )[:16].upper()
        )
        runtime_queries.append(
            {
                "query_id": query_id,
                "direction": query["direction"],
                "query": query["query"],
                "status": "executed",
                "executed_at": completed,
                "result_source_ids": result_source_ids,
            }
        )
        query_bindings.append(
            {
                "query_id": query_id,
                "query_sha256": sha256_text(query["query"]),
                "purpose_sha256": sha256_text(query["purpose"]),
                "search_event_ids": session["search_event_ids"],
                "result_source_ids": result_source_ids,
            }
        )

    runtime_assessments: list[dict[str, Any]] = []
    for source in semantic["sources"]:
        url = source["url"]
        assessment = assessment_by_url[url]
        runtime_assessments.append(
            {
                "source_id": source_ids[url],
                "authority": assessment["authority"],
                "independence": assessment["independence"],
                "independence_identity": assessment["independence_identity"],
                "source_lineage": [
                    source_ids[item] for item in assessment["source_lineage_urls"]
                ],
                "interest_relevance": assessment["interest_relevance"],
                "affected_positions": assessment["affected_positions"],
                "low_power_positions": assessment["low_power_positions"],
                "conflict_source_ids": [
                    source_ids[item] for item in assessment["conflict_source_urls"]
                ],
                "freshness": assessment["freshness"],
                "relevance": assessment["relevance"],
                "verdict": assessment["verdict"],
                "limitations": assessment["limitations"],
                "cannot_prove": assessment["cannot_prove"],
            }
        )
    retrieval = {
        "mode": "open-world",
        "queries": runtime_queries,
        "sources": runtime_sources,
        "assessments": runtime_assessments,
        "saturation_status": saturation_status,
        "capability_gap": semantic["capability_gap"],
        "remaining_unknowns": remaining_unknowns,
        "directional_evidence": directional_evidence,
    }
    receipt: dict[str, Any] = {
        "schema_id": RECEIPT_SCHEMA_ID,
        "schema_version": 1,
        "protocol": RECEIPT_PROTOCOL,
        "run_id": run,
        "execution_context_id": context,
        "provider_binding_sha256": provider_sha,
        "adapter_executable_sha256": adapter_sha,
        "adapter_input_sha256": input_sha,
        "parent_pid": parent,
        "child_pid": child,
        "started_at": started,
        "completed_at": completed,
        "exit_status": 0,
        "stdout_sha256": event_stream_sha256,
        "stderr_sha256": stderr_sha,
        "event_stream_sha256": event_stream_sha256,
        "event_count": len(events),
        "thread_id": thread_id,
        "web_events": web_events,
        "semantic_retrieval_sha256": semantic_input_sha256,
        "retrieval_sha256": sha256_json(retrieval),
        "query_bindings": query_bindings,
        "source_bindings": source_bindings,
        "directional_evidence": directional_evidence,
        "receipt_sha256": "",
    }
    receipt["receipt_sha256"] = sha256_json(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )
    return retrieval, receipt


def validate_retrieval_execution_receipt(
    receipt: Any,
    retrieval: Any,
    *,
    run_id: str,
    evidence_cutoff: str,
    semantic_retrieval: Mapping[str, Any],
    event_stream: bytes,
    adapter_input: bytes,
    host_captures: Mapping[str, HostCapture] | None = None,
) -> list[str]:
    """Freshly recheck a sealed host receipt against its retrieval projection."""

    errors: list[str] = []
    if not isinstance(receipt, Mapping) or set(receipt) != RECEIPT_FIELDS:
        return ["retrieval execution receipt fields are not exact"]
    if receipt.get("schema_id") != RECEIPT_SCHEMA_ID or receipt.get(
        "schema_version"
    ) != 1 or receipt.get("protocol") != RECEIPT_PROTOCOL:
        errors.append("retrieval execution receipt identity is invalid")
    if receipt.get("run_id") != run_id:
        errors.append("retrieval execution receipt run_id differs")
    if not isinstance(retrieval, Mapping):
        errors.append("retrieval execution projection is not an object")
        return errors
    if receipt.get("retrieval_sha256") != sha256_json(dict(retrieval)):
        errors.append("retrieval execution receipt does not bind retrieval")
    if receipt.get("directional_evidence") != retrieval.get("directional_evidence"):
        errors.append("retrieval execution directional evidence differs")
    if receipt.get("receipt_sha256") != sha256_json(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    ):
        errors.append("retrieval execution receipt hash differs")
    try:
        started = parse_instant(
            receipt.get("started_at"), field="retrieval started_at"
        )
        completed = parse_instant(
            receipt.get("completed_at"), field="retrieval completed_at"
        )
        cutoff = parse_instant(evidence_cutoff, field="evidence_cutoff")
        if started > completed:
            errors.append("retrieval execution completed before it started")
        if completed > cutoff:
            errors.append("retrieval execution completed after evidence cutoff")
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))
    if receipt.get("exit_status") != 0:
        errors.append("retrieval execution receipt exit status is not zero")
    for field in (
        "provider_binding_sha256",
        "adapter_executable_sha256",
        "adapter_input_sha256",
        "stdout_sha256",
        "stderr_sha256",
        "event_stream_sha256",
        "semantic_retrieval_sha256",
        "retrieval_sha256",
        "receipt_sha256",
    ):
        try:
            _sha256(receipt.get(field), label=field)
        except ValueError as exc:
            errors.append(str(exc))
    try:
        parent = _positive_pid(receipt.get("parent_pid"), label="parent_pid")
        child = _positive_pid(receipt.get("child_pid"), label="child_pid")
        if parent == child:
            errors.append("retrieval parent and child process ids must differ")
    except ValueError as exc:
        errors.append(str(exc))
    web_events = receipt.get("web_events")
    if not isinstance(web_events, list):
        errors.append("retrieval execution web events are not a list")
        web_events = []
    event_ids: set[str] = set()
    search_events: dict[str, list[str]] = {}
    open_events: dict[str, list[str]] = {}
    prior_sequence = -1
    for index, event in enumerate(web_events):
        if not isinstance(event, Mapping) or set(event) != {
            "sequence",
            "event_id",
            "event_sha256",
            "query",
            "action",
        }:
            errors.append(f"retrieval execution web event fields differ: {index}")
            continue
        sequence = event.get("sequence")
        event_id = event.get("event_id")
        if (
            not isinstance(sequence, int)
            or isinstance(sequence, bool)
            or sequence <= prior_sequence
        ):
            errors.append(f"retrieval execution web event sequence differs: {index}")
        else:
            prior_sequence = sequence
        if not isinstance(event_id, str) or not event_id or event_id in event_ids:
            errors.append(f"retrieval execution web event id differs: {index}")
            continue
        event_ids.add(event_id)
        try:
            _sha256(event.get("event_sha256"), label="web event_sha256")
            _text(event.get("query"), label="web event query")
        except ValueError as exc:
            errors.append(str(exc))
        action = event.get("action")
        if not isinstance(action, Mapping):
            errors.append(f"retrieval execution web action differs: {event_id}")
            continue
        action_type = action.get("type")
        if action_type == "search" and set(action).issubset(
            {"type", "query", "queries"}
        ):
            values: list[str] = []
            if isinstance(action.get("query"), str):
                values.append(action["query"].strip())
            if isinstance(action.get("queries"), list):
                values.extend(
                    item.strip()
                    for item in action["queries"]
                    if isinstance(item, str)
                )
            if not values:
                errors.append(f"retrieval execution search action differs: {event_id}")
            for query in dict.fromkeys(values):
                event_ids_for_query = search_events.setdefault(query, [])
                if event_id not in event_ids_for_query:
                    event_ids_for_query.append(event_id)
        elif action_type == "open_page" and set(action) == {"type", "url"}:
            try:
                url = _https_url(action.get("url"), label="web open_page URL")
                open_events.setdefault(url, []).append(event_id)
            except ValueError as exc:
                errors.append(str(exc))
        elif action_type == "find_in_page" and set(action).issubset(
            {"type", "url", "pattern"}
        ):
            try:
                _https_url(action.get("url"), label="web find_in_page URL")
                if action.get("pattern") is not None:
                    _text(action.get("pattern"), label="web find_in_page pattern")
            except ValueError as exc:
                errors.append(str(exc))
        else:
            errors.append(f"retrieval execution web action differs: {event_id}")

    queries = retrieval.get("queries")
    query_bindings = receipt.get("query_bindings")
    if not isinstance(queries, list) or not isinstance(query_bindings, list) or len(
        queries
    ) != len(query_bindings):
        errors.append("retrieval execution query bindings differ")
    else:
        for index, (query, binding) in enumerate(zip(queries, query_bindings)):
            query_id = query.get("query_id") if isinstance(query, Mapping) else None
            expected = (
                {
                    "query_id": query_id,
                    "query_sha256": sha256_text(str(query.get("query", ""))),
                    "purpose_sha256": binding.get("purpose_sha256")
                    if isinstance(binding, Mapping)
                    else None,
                    "search_event_ids": search_events.get(
                        query.get("query"), []
                    ),
                    "result_source_ids": query.get("result_source_ids"),
                }
                if isinstance(query, Mapping) and isinstance(binding, Mapping)
                else None
            )
            if isinstance(binding, Mapping):
                try:
                    _sha256(
                        binding.get("purpose_sha256"),
                        label="query purpose_sha256",
                    )
                except ValueError as exc:
                    errors.append(str(exc))
            if (
                not isinstance(binding, Mapping)
                or set(binding)
                != {
                    "query_id",
                    "query_sha256",
                    "purpose_sha256",
                    "search_event_ids",
                    "result_source_ids",
                }
                or dict(binding) != expected
            ):
                errors.append(
                    f"retrieval execution query binding differs: {query_id or index}"
                )

    sources = retrieval.get("sources")
    source_bindings = receipt.get("source_bindings")
    if not isinstance(sources, list) or not isinstance(source_bindings, list) or len(
        sources
    ) != len(source_bindings):
        errors.append("retrieval execution source bindings differ")
    else:
        for index, (source, binding) in enumerate(zip(sources, source_bindings)):
            source_id = source.get("source_id") if isinstance(source, Mapping) else None
            expected = (
                {
                    "source_id": source_id,
                    "url": source.get("url"),
                    "content_sha256": source.get("content_sha256"),
                    "content_authority": source.get("content_authority"),
                    "accessed_at": source.get("accessed_at"),
                    "open_event_ids": open_events.get(source.get("url"), []),
                    "host_observation": source.get("host_observation"),
                }
                if isinstance(source, Mapping)
                else None
            )
            if (
                not isinstance(binding, Mapping)
                or set(binding)
                != {
                    "source_id",
                    "url",
                    "content_sha256",
                    "content_authority",
                    "accessed_at",
                    "open_event_ids",
                    "host_observation",
                }
                or dict(binding) != expected
                or source.get("run_id") != run_id
            ):
                errors.append(
                    f"retrieval execution source binding differs: {source_id or index}"
                )

    if not isinstance(receipt.get("event_count"), int) or receipt.get(
        "event_count", 0
    ) < len(web_events) + 3:
        errors.append("retrieval execution event count is invalid")
    try:
        _normalise_semantic(semantic_retrieval)
        if receipt.get("semantic_retrieval_sha256") != sha256_json(
            dict(semantic_retrieval)
        ):
            errors.append("retrieval execution semantic input hash differs")
    except (TypeError, ValueError) as exc:
        errors.append(f"retrieval execution semantic input is invalid: {exc}")
    if receipt.get("event_stream_sha256") != sha256_bytes(event_stream):
        errors.append("retrieval execution event stream hash differs")
    if receipt.get("stdout_sha256") != sha256_bytes(event_stream):
        errors.append("retrieval execution stdout hash differs")
    if receipt.get("adapter_input_sha256") != sha256_bytes(adapter_input):
        errors.append("retrieval execution adapter input hash differs")
    try:
        observed_thread, observed_events, observed_web = _event_stream(event_stream)
        if receipt.get("thread_id") != observed_thread:
            errors.append("retrieval execution thread id differs")
        if receipt.get("event_count") != len(observed_events):
            errors.append("retrieval execution event count differs from stream")
        if web_events != observed_web:
            errors.append("retrieval execution web events differ from stream")
    except (TypeError, ValueError) as exc:
        errors.append(f"retrieval execution event stream is invalid: {exc}")
    try:
        expected_retrieval, expected_receipt = project_runtime_retrieval(
            semantic_retrieval,
            event_stream,
            run_id=run_id,
            execution_context_id=receipt.get("execution_context_id"),
            provider_binding_sha256=receipt.get("provider_binding_sha256"),
            adapter_executable_sha256=receipt.get("adapter_executable_sha256"),
            adapter_input=adapter_input,
            parent_pid=receipt.get("parent_pid"),
            child_pid=receipt.get("child_pid"),
            started_at=receipt.get("started_at"),
            completed_at=receipt.get("completed_at"),
            exit_status=receipt.get("exit_status"),
            stderr_sha256=receipt.get("stderr_sha256"),
            evidence_cutoff=evidence_cutoff,
            host_captures=host_captures,
        )
        if dict(retrieval) != expected_retrieval:
            errors.append(
                "retrieval execution projection differs from semantic input and events"
            )
        if dict(receipt) != expected_receipt:
            errors.append(
                "retrieval execution receipt differs from fresh reconstruction"
            )
    except (TypeError, ValueError) as exc:
        errors.append(f"retrieval execution reconstruction failed: {exc}")
    return errors


__all__ = (
    "HOST_CAPTURE_BODY_DIRECTORY",
    "HOST_CAPTURE_INDEX_RELATIVE",
    "HOST_CAPTURE_INDEX_SCHEMA_ID",
    "HOST_CAPTURE_PROTOCOL",
    "HostCapture",
    "RECEIPT_PROTOCOL",
    "RECEIPT_SCHEMA_ID",
    "build_host_capture_index",
    "capture_host_response",
    "capture_host_sources",
    "load_host_capture_bundle",
    "project_runtime_retrieval",
    "validate_retrieval_execution_receipt",
    "write_host_capture_bundle",
)
