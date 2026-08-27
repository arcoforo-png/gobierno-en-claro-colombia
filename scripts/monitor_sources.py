#!/usr/bin/env python3
"""Detecta cambios en fuentes oficiales sin modificar los datos publicados."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "monitor" / "sources.json"
STATE_PATH = ROOT / ".monitor-state.json"
REPORT_PATH = ROOT / "monitor-report.md"
MONTH_SLUGS = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def visible_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|svg).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\s+", " ", raw).strip().lower()
    return raw


def resolved_url(template: str, now: datetime) -> str:
    return template.format(year=now.year, month_slug=MONTH_SLUGS[now.month - 1])


def fetch(source: dict[str, str], now: datetime) -> tuple[str, int, str]:
    url = resolved_url(source["url"], now)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GobiernoEnClaroMonitor/1.0 (+GitHub Actions)"},
    )
    with urllib.request.urlopen(request, timeout=35) as response:
        raw = response.read().decode("utf-8", errors="replace")
        text = visible_text(raw)
        return hashlib.sha256(text.encode("utf-8")).hexdigest(), len(text), url


def main() -> int:
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    previous = {}
    if STATE_PATH.exists():
        previous = json.loads(STATE_PATH.read_text(encoding="utf-8"))

    checked_at = datetime.now(timezone.utc)
    now = checked_at.isoformat()
    current: dict[str, dict[str, object]] = {}
    changes: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []

    for source in sources:
        try:
            digest, length, url = fetch(source, checked_at)
            current[source["id"]] = {
                "sha256": digest,
                "length": length,
                "checked_at": now,
                "url": url,
            }
            old = previous.get(source["id"], {}).get("sha256")
            if old and old != digest:
                changes.append({**source, "url": url})
        except Exception as exc:  # La alerta informa el fallo; no publica datos.
            url = resolved_url(source["url"], checked_at)
            errors.append({"name": source["name"], "url": url, "error": str(exc)})
            if source["id"] in previous:
                current[source["id"]] = previous[source["id"]]

    STATE_PATH.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Revisión automática de fuentes oficiales",
        "",
        f"Fecha UTC: `{now}`",
        "",
        "Este informe **no modifica la aplicación**. Todo hallazgo requiere verificación humana.",
    ]
    if changes:
        lines += ["", "## Fuentes con cambios detectados"]
        for source in changes:
            lines.append(f"- **{source['name']}** ({source['category']}): {source['url']}")
    if errors:
        lines += ["", "## Fuentes que no pudieron consultarse"]
        for error in errors:
            lines.append(f"- **{error['name']}**: {error['url']} — `{error['error']}`")
    lines += [
        "",
        "## Protocolo editorial",
        "",
        "1. Abrir la fuente oficial y determinar el cambio exacto.",
        "2. Contrastar con una segunda fuente oficial cuando sea posible.",
        "3. Identificar la entidad adscrita, el cargo, la persona nombrada y el acto administrativo.",
        "4. Actualizar `app/data.ts` (gabinete y entidades) o `app/page.tsx` (agenda legislativa).",
        "5. Registrar la fuente y la fecha de revisión.",
        "6. Revisar la vista previa antes de incorporar el cambio a `main`.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    alerting_errors = [
        error for error in errors
        if next(
            (source.get("alert_on_error", True) for source in sources if source["name"] == error["name"]),
            True,
        )
    ]
    changed = bool(changes or alerting_errors)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"alert={'true' if changed else 'false'}\n")
    print(f"Fuentes: {len(sources)}; cambios: {len(changes)}; errores: {len(errors)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

