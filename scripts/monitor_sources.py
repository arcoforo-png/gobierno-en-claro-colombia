#!/usr/bin/env python3
"""Detecta señales concretas en fuentes oficiales sin modificar la aplicación."""

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
FINGERPRINT_VERSION = 2
SOURCES_PATH = ROOT / "monitor" / "sources.json"
STATE_PATH = ROOT / ".monitor-state.json"
REPORT_PATH = ROOT / "monitor-report.md"
TECHNICAL_PATH = ROOT / "monitor-technical.md"
MONTH_SLUGS = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")


def visible_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|svg).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)</?(p|div|li|tr|td|th|h[1-6]|br|article|section)[^>]*>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    lines = [re.sub(r"\s+", " ", line).strip() for line in html.unescape(raw).splitlines()]
    return "\n".join(line for line in lines if line)


def focused_text(text: str, terms: list[str]) -> tuple[str, list[str]]:
    """Conserva sólo fragmentos relacionados con la pregunta vigilada."""
    if not terms:
        return text.lower(), [text[:320]] if text else []
    pattern = re.compile("|".join(re.escape(term) for term in terms), re.IGNORECASE)
    lines = text.splitlines()
    matches: list[str] = []
    for index, line in enumerate(lines):
        if pattern.search(line):
            context = " | ".join(lines[max(0, index - 1):min(len(lines), index + 2)])[:500]
            if context not in matches:
                matches.append(context)
    return "\n".join(matches).lower(), matches[:5]


def resolved_url(template: str, now: datetime) -> str:
    return template.format(year=now.year, month_slug=MONTH_SLUGS[now.month - 1])


def is_due(source: dict[str, object], now: datetime, force_all: bool) -> bool:
    if force_all:
        return True
    cadence = source.get("cadence", "daily")
    return (cadence == "daily" or
            cadence == "weekly" and now.weekday() == 0 or
            cadence == "monthly" and now.day == 1)


def fetch(source: dict[str, object], now: datetime) -> tuple[str, int, str, list[str]]:
    url = resolved_url(str(source["url"]), now)
    request = urllib.request.Request(url, headers={"User-Agent": "GobiernoEnClaroMonitor/2.0 (+GitHub Actions)"})
    with urllib.request.urlopen(request, timeout=35) as response:
        raw = response.read().decode("utf-8", errors="replace")
    focused, excerpts = focused_text(visible_text(raw), list(source.get("signal_terms", [])))
    return hashlib.sha256(focused.encode("utf-8")).hexdigest(), len(focused), url, excerpts


def doubt(source: dict[str, object], error: str | None = None) -> list[str]:
    lines = [f"## Duda editorial — {source['name']}", "", f"**Qué estaba vigilando:** {source['purpose']}", ""]
    if error:
        lines += ["**Señal detectada:** No fue posible comprobar esta vigilancia; no se afirma que haya ocurrido un cambio.", "", f"**Detalle técnico breve:** `{error}`", ""]
    else:
        excerpts = list(source.get("excerpts", []))
        signal = excerpts[0] if excerpts else "La sección temática vigilada cambió, pero la página no expuso un fragmento legible."
        lines += [f"**Señal observada en la fuente:** {signal}", ""]
    return lines + [
        f"**Pregunta exacta para revisión humana:** {source['question']}", "",
        f"**Datos que debe encontrar:** {source['evidence']}", "",
        f"**Fuente oficial exacta:** {source['url']}", "",
        "**Decisión editorial:** No modificar la aplicación hasta identificar el cambio exacto y comprobarlo en el documento oficial.",
    ]


def main() -> int:
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    previous = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}
    checked_at = datetime.now(timezone.utc)
    now = checked_at.isoformat()
    force_all = os.environ.get("FORCE_ALL", "").lower() == "true"
    current = dict(previous)
    changes: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    checked: list[dict[str, object]] = []

    for source in sources:
        if not is_due(source, checked_at, force_all):
            skipped.append(source)
            continue
        url = resolved_url(str(source["url"]), checked_at)
        try:
            digest, length, url, excerpts = fetch(source, checked_at)
            current[source["id"]] = {"fingerprint_version": FINGERPRINT_VERSION, "sha256": digest, "length": length, "checked_at": now, "url": url, "excerpts": excerpts}
            checked.append(source)
            old_entry = previous.get(source["id"], {})
            old = old_entry.get("sha256") if old_entry.get("fingerprint_version") == FINGERPRINT_VERSION else None
            if old and old != digest:
                changes.append({**source, "url": url, "excerpts": excerpts})
        except Exception as exc:
            errors.append({**source, "url": url, "error": str(exc)})

    STATE_PATH.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
    alerting_errors = [item for item in errors if item.get("alert_on_error", True)]
    actionable = changes + alerting_errors

    report = ["# Dudas concretas para revisión editorial", "", f"Fecha UTC: `{now}`", "", "Este informe no modifica Gobierno en Claro. Cada apartado formula una sola comprobación humana."]
    if actionable:
        for item in actionable:
            report += [""] + doubt(item, str(item["error"]) if "error" in item else None)
    else:
        report += ["", "No hay dudas editoriales que requieran revisión humana en esta ejecución."]
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")

    technical = ["# Registro técnico del monitor", "", f"Fecha UTC: `{now}`", "", f"- Fuentes consultadas: {len(checked)}", f"- Fuentes omitidas por frecuencia: {len(skipped)}", f"- Cambios temáticos: {len(changes)}", f"- Fallos de consulta: {len(errors)}"]
    if skipped:
        technical += ["", "## Próxima revisión según frecuencia"] + [f"- {item['name']} — {item.get('cadence', 'daily')}" for item in skipped]
    if errors:
        technical += ["", "## Fallos técnicos (no equivalen a cambios)"] + [f"- {item['name']}: {item['url']} — `{item['error']}`" for item in errors]
    TECHNICAL_PATH.write_text("\n".join(technical) + "\n", encoding="utf-8")

    first = actionable[0]["name"] if actionable else "sin novedades"
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"alert={'true' if actionable else 'false'}\n")
            handle.write(f"alert_title=Revisión concreta · {first}\n")
    print(f"Consultadas: {len(checked)}; omitidas: {len(skipped)}; cambios: {len(changes)}; errores técnicos: {len(errors)}; alertas: {len(actionable)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

