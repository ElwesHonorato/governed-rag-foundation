#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from urllib import error, request

EVENT_FILE_BY_NAME = {
    "worker_scan_start": "01_worker_scan_start.openlineage.json",
    "worker_scan_complete": "02_worker_scan_complete.openlineage.json",
    "worker_parse_document_start": "03_worker_parse_document_start.openlineage.json",
    "worker_parse_document_complete": "04_worker_parse_document_complete.openlineage.json",
    "worker_chunk_text_start": "05_worker_chunk_text_start.openlineage.json",
    "worker_chunk_text_complete": "06_worker_chunk_text_complete.openlineage.json",
    "worker_embed_chunks_start": "07_worker_embed_chunks_start.openlineage.json",
    "worker_embed_chunks_complete": "08_worker_embed_chunks_complete.openlineage.json",
    "worker_index_weaviate_start": "09_worker_index_weaviate_start.openlineage.json",
    "worker_index_weaviate_complete": "10_worker_index_weaviate_complete.openlineage.json",
}

DEFAULT_SCAN_EVENTS = [
    "worker_scan_start",
    "worker_scan_complete",
]

FULL_CHAIN_EVENTS = [
    "worker_scan_start",
    "worker_scan_complete",
    "worker_parse_document_start",
    "worker_parse_document_complete",
    "worker_chunk_text_start",
    "worker_chunk_text_complete",
    "worker_embed_chunks_start",
    "worker_embed_chunks_complete",
    "worker_index_weaviate_start",
    "worker_index_weaviate_complete",
]


def _read_env_var_from_file(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() != key:
            continue
        return value.strip().strip("'").strip('"')
    return ""


def _env_candidates(script_dir: Path) -> list[Path]:
    return [Path.cwd() / ".env", script_dir.parent / ".env"]


def resolve_setting(cli_value: str | None, env_key: str, script_dir: Path) -> str:
    if cli_value:
        return cli_value.strip()
    env_value = os.getenv(env_key, "").strip()
    if env_value:
        return env_value
    for env_path in _env_candidates(script_dir):
        file_value = _read_env_var_from_file(env_path, env_key)
        if file_value:
            return file_value
    return ""


def build_openlineage_url(cli_openlineage_url: str | None, base_url: str, script_dir: Path) -> str:
    explicit = resolve_setting(cli_openlineage_url, "DATAHUB_OPENLINEAGE_URL", script_dir)
    if explicit:
        return _normalize_for_host_runtime(explicit, script_dir)

    gms_url = resolve_setting(None, "DATAHUB_GMS_URL", script_dir)
    if gms_url:
        candidate = f"{gms_url.rstrip('/')}/openapi/openlineage/api/v1/lineage"
        return _normalize_for_host_runtime(candidate, script_dir)

    candidate = f"{base_url.rstrip('/')}/openapi/openlineage/api/v1/lineage"
    return _normalize_for_host_runtime(candidate, script_dir)


def _normalize_for_host_runtime(url: str, script_dir: Path) -> str:
    parsed = urlparse(url)
    # If running outside containers, "datahub-gms:8080" is not resolvable from host shell.
    if parsed.hostname != "datahub-gms" or Path("/.dockerenv").exists():
        return url

    mapped_port = resolve_setting(None, "DATAHUB_MAPPED_GMS_PORT", script_dir) or "8081"
    netloc = f"localhost:{mapped_port}"
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth += f":{parsed.password}"
        netloc = f"{auth}@{netloc}"
    return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))


def post_json(url: str, token: str, payload_path: Path) -> dict:
    body = payload_path.read_bytes()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = request.Request(url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8").strip()
            if not raw:
                return {"status": resp.status, "message": "empty response body"}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"status": resp.status, "raw": raw}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for {payload_path.name}: {detail}") from exc
    except error.URLError:
        # Some restricted environments block Python socket calls but allow curl.
        return _post_json_with_curl(url=url, token=token, payload_path=payload_path)


def _post_json_with_curl(url: str, token: str, payload_path: Path) -> dict:
    cmd = [
        "curl",
        "-sS",
        "-X",
        "POST",
        url,
        "-H",
        "Content-Type: application/json",
        "--data-binary",
        f"@{payload_path}",
        "-w",
        "\n__HTTP_STATUS__:%{http_code}",
    ]
    if token:
        cmd.extend(["-H", f"Authorization: Bearer {token}"])

    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError("Failed to POST: urllib blocked and curl not found") from exc

    if completed.returncode != 0:
        raise RuntimeError(f"curl failed for {payload_path.name}: {completed.stderr.strip()}")

    marker = "\n__HTTP_STATUS__:"
    if marker not in completed.stdout:
        raise RuntimeError(f"curl response parse failed for {payload_path.name}")

    raw_body, status_text = completed.stdout.rsplit(marker, 1)
    status = int(status_text.strip())
    body = raw_body.strip()
    if status >= 400:
        raise RuntimeError(f"HTTP {status} for {payload_path.name}: {body}")
    if not body:
        return {"status": status, "message": "empty response body"}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"status": status, "raw": body}


def resolve_payloads(folder: Path, full_chain: bool, events: list[str] | None) -> list[Path]:
    if events:
        unknown = [event for event in events if event not in EVENT_FILE_BY_NAME]
        if unknown:
            valid = ", ".join(EVENT_FILE_BY_NAME.keys())
            raise ValueError(f"Unknown event(s): {', '.join(unknown)}. Valid values: {valid}")
        return [folder / EVENT_FILE_BY_NAME[event] for event in events]

    names = FULL_CHAIN_EVENTS if full_chain else DEFAULT_SCAN_EVENTS
    return [folder / EVENT_FILE_BY_NAME[name] for name in names]


def main() -> int:
    parser = argparse.ArgumentParser(description="Send OpenLineage events to DataHub.")
    parser.add_argument(
        "--openlineage-url",
        default=None,
        help="OpenLineage ingestion URL (overrides DATAHUB_OPENLINEAGE_URL from env/.env)",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8081",
        help="Used only when --openlineage-url and DATAHUB_OPENLINEAGE_URL are not set.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Optional bearer token (overrides DATAHUB_TOKEN from env/.env)",
    )
    parser.add_argument(
        "--full-chain",
        action="store_true",
        help="Send scan + parse_document + chunk_text + embed_chunks + index_weaviate. If omitted, sends scan only.",
    )
    parser.add_argument(
        "--events",
        nargs="+",
        help=(
            "Explicit event names to send in order. "
            "Example: --events worker_scan_start worker_scan_complete"
        ),
    )
    args = parser.parse_args()

    folder = Path(__file__).resolve().parent

    openlineage_url = build_openlineage_url(args.openlineage_url, args.base_url, folder)

    token = resolve_setting(args.token, "DATAHUB_TOKEN", folder)

    try:
        payloads = resolve_payloads(folder, full_chain=args.full_chain, events=args.events)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"OpenLineage URL: {openlineage_url}")
    print(f"Auth token: {'present' if token else 'not set'}")

    for payload in payloads:
        print(f"POST {payload.name}")
        result = post_json(openlineage_url, token, payload)
        print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
