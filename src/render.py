"""PlantUML text and standalone SVG rendering."""

from html import escape
from pathlib import Path


def plantuml(graph: dict[str, list[str]]) -> str:
    names = sorted(graph)
    aliases = {name: f"n{index}" for index, name in enumerate(names)}
    lines = ["@startuml", "left to right direction"]
    for name in names:
        label = name.replace('"', "'")
        lines.append(f'component "{label}" as {aliases[name]}')
    for parent in names:
        for child in graph[parent]:
            if child in aliases:
                lines.append(f"{aliases[parent]} --> {aliases[child]}")
    return "\n".join(lines + ["@enduml", ""])


def svg(graph: dict[str, list[str]]) -> str:
    """Render SVG directly; PlantUML source is saved separately."""
    names = sorted(graph)
    width = max(720, 36 * max((len(n) for n in names), default=1))
    height = max(180, 88 * len(names) + 40)
    positions = {name: 55 + 88 * index for index, name in enumerate(names)}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" '
        'refX="9" refY="5" orient="auto">'
        '<path d="M0 0 L10 5 L0 10 Z" fill="#475569"/>'
        '</marker></defs>',
    ]
    for parent in names:
        for child in graph[parent]:
            if child not in positions:
                continue
            y1, y2 = positions[parent], positions[child]
            x1 = width - 150
            x2 = width - 75
            path = (f'M {x1} {y1} C {x2} {y1} '
                    f'{x2} {y2} {x1} {y2}')
            if y1 == y2:
                path = (f'M {x1} {y1} C {x2} {y1 - 50} '
                        f'{x2} {y1 + 50} {x1} {y1 + 5}')
            parts.append(f'<path d="{path}" fill="none" '
                         'stroke="#475569" stroke-width="1.5" '
                         'marker-end="url(#arrow)"/>')
    for name in names:
        y = positions[name]
        parts.append(f'<rect x="20" y="{y - 22}" width="{width - 170}" '
                     'height="44" rx="8" fill="#dbeafe" '
                     'stroke="#2563eb"/>')
        parts.append(f'<text x="36" y="{y + 5}" font-size="15" '
                     f'font-family="sans-serif">{escape(name)}</text>')
    return "\n".join(parts + ["</svg>", ""])


def save_graph(graph: dict[str, list[str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg(graph), encoding="utf-8")
    path.with_suffix(".puml").write_text(plantuml(graph),
                                         encoding="utf-8")
