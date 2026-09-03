"""
Human-readable STIX bundle report generator.
Used by Phase 2 to produce <stem>.stix.txt.

The goal is to give analysts a simple overview of:
- Entities (threat actors, TTPs, observed file hashes)
- Object counts
- Bundle metadata

Sections track what convert_ir_to_stix actually emits. Add one only when a
builder starts producing that object type, or the report grows headings that
can never be filled.
"""

import datetime


def render_section(title: str, lines: list) -> str:
    if not lines:
        return f"{title}:\n  (none)\n"
    out = [f"{title}:"]
    for line in lines:
        out.append(f"  - {line}")
    return "\n".join(out) + "\n"


def _hash_lines(observed: dict) -> list:
    """One line per hash on each SCO the observed-data wraps.

    Type-guarded because the sole caller sits in Stage 2's unguarded per-IR
    loop: an unexpected shape here would abort the whole batch after the
    bundles are already on disk, rather than skip one line.
    """
    scos = observed.get("objects")
    if not isinstance(scos, dict):
        return []

    out = []
    for sco in scos.values():
        hashes = sco.get("hashes") if isinstance(sco, dict) else None
        if not isinstance(hashes, dict):
            continue
        for algo, digest in hashes.items():
            out.append(f"{algo}: {digest}  ({observed.get('id')})")
    return out


def render_stix_report(bundle: dict, ir_name: str) -> str:
    objects = bundle.get("objects") or []
    now = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")

    actors = []
    ttp = []
    hashes = []

    for o in objects:
        t = o.get("type")

        if t == "threat-actor":
            actors.append(f"{o.get('name')}  ({o.get('id')})")
        elif t == "attack-pattern":
            ttp.append(f"{o.get('name')}  ({o.get('id')})")
        elif t == "observed-data":
            hashes.extend(_hash_lines(o))

    out = []
    out.append("=" * 72)
    out.append("STIX 2.1 CONVERSION REPORT")
    out.append("=" * 72)
    out.append(f"Generated: {now}")
    out.append(f"Source IR File: {ir_name}")
    out.append(f"Bundle ID: {bundle.get('id')}")
    out.append(f"Total STIX Objects: {len(objects)}")
    out.append("")

    out.append(render_section("Threat Actors", actors))
    out.append(render_section("Attack Patterns (TTPs)", ttp))
    out.append(render_section("Observed File Hashes", hashes))

    out.append("=" * 72)
    out.append("END OF REPORT")
    out.append("=" * 72)

    return "\n".join(out)
