#!/usr/bin/env python3
"""Metronik SOAP relay - read SOAP payloads from reservations and bindly shoot them at Metronik."""

import json
import os
import sys
import urllib.error
import urllib.request
import xml.dom.minidom
import xml.parsers.expat

TIMEOUT_SECONDS = 15

DEFAULT_SOURCE_URL = "https://rezervacije.fri.uni-lj.si/api/metronik/payloads"

DEBUG = os.environ.get("METRONIK_DEBUG", "") not in ("", "0")


def _format_body(text: str) -> str:
    try:
        return xml.dom.minidom.parseString(text).toprettyxml(indent="  ")
    except xml.parsers.expat.ExpatError:
        return text


def _dump(label: str, headers: dict, body: bytes) -> None:
    if not DEBUG:
        return
    print(f"--- {label} ---", file=sys.stderr)
    for name, value in headers.items():
        print(f"{name}: {value}", file=sys.stderr)
    print(file=sys.stderr)
    print(_format_body(body.decode("utf-8", errors="replace")), file=sys.stderr)
    print(f"--- end {label} ---", file=sys.stderr)


def fetch_payloads(source_url: str) -> list[dict]:
    request = urllib.request.Request(source_url)
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        raw = response.read()
    return json.loads(raw)["payloads"]


def send_payload(entry: dict) -> None:
    data = entry["payload"].encode("utf-8")
    request = urllib.request.Request(entry["endpoint"], data=data, method="POST")
    request.add_header("Content-Type", "text/xml; charset=utf-8")
    request.add_header("SOAPAction", entry["soap_action"])
    _dump(f"SENT -> {entry['endpoint']}", dict(request.header_items()), data)
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        raw = response.read()
        _dump(f"RECEIVED <- {entry['endpoint']}", dict(response.headers), raw)


def main() -> int:
    source_url = os.environ.get("METRONIK_SOURCE_URL", DEFAULT_SOURCE_URL)
    try:
        payloads = fetch_payloads(source_url)
    except (urllib.error.URLError, ValueError, KeyError) as e:
        print(f"Failed to fetch payloads from {source_url}: {e}", file=sys.stderr)
        return 1

    failures = 0
    for entry in payloads:
        room = entry.get("room", "?")
        try:
            send_payload(entry)
            print(f"OK   {room} -> {entry['endpoint']}")
        except urllib.error.URLError as e:
            failures += 1
            print(f"FAIL {room} -> {entry['endpoint']}: {e}", file=sys.stderr)
            if DEBUG and isinstance(e, urllib.error.HTTPError):
                _dump(f"RECEIVED (error) <- {entry['endpoint']}", dict(e.headers), e.read())

    if failures:
        print(f"{failures}/{len(payloads)} rooms failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
