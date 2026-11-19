"""Graph traversal shared by repository and fixture modes."""

from dataclasses import dataclass
from typing import Callable

MAVEN_COORDINATE_PARTS = 3


@dataclass(frozen=True, order=True)
class Package:
    group: str
    artifact: str
    version: str

    @classmethod
    def parse(cls, value: str) -> "Package":
        parts = value.split(":")
        if len(parts) != MAVEN_COORDINATE_PARTS or not all(parts):
            raise ValueError("Package must be group:artifact:version")
        return cls(*parts)

    def __str__(self) -> str:
        return f"{self.group}:{self.artifact}:{self.version}"


def collect_graph(
    root: str,
    dependencies: Callable[[str], list[str]],
    max_depth: int,
    exclude: str,
) -> dict[str, list[str]]:
    """Iterative DFS; keep edges to visited nodes, including cycles."""
    graph: dict[str, list[str]] = {}
    best_depth: dict[str, int] = {}
    stack = [(root, 0)]
    while stack:
        name, depth = stack.pop()
        if depth >= best_depth.get(name, max_depth + 1):
            continue
        if exclude and exclude in name:
            continue
        best_depth[name] = depth
        children = [] if depth >= max_depth else dependencies(name)
        children = sorted(set(child for child in children
                              if not exclude or exclude not in child))
        graph[name] = children
        for child in reversed(children):
            stack.append((child, depth + 1))
    return graph


def reverse_graph(graph: dict[str, list[str]]) -> dict[str, list[str]]:
    reverse = {name: [] for name in graph}
    for parent, children in graph.items():
        for child in children:
            if child in reverse:
                reverse[child].append(parent)
    return {name: sorted(parents) for name, parents in reverse.items()}


def ascii_tree(graph: dict[str, list[str]], root: str) -> str:
    lines = [root]
    stack = [(root, "", frozenset({root}), True, False)]
    while stack:
        node, prefix, ancestors, last, render = stack.pop()
        if render:
            cycle = node in ancestors
            lines.append(prefix + ("└── " if last else "├── ") + node +
                         (" [cycle]" if cycle else ""))
            if cycle:
                continue
            prefix += "    " if last else "│   "
            ancestors = ancestors | {node}
        children = graph.get(node, [])
        for index in range(len(children) - 1, -1, -1):
            child = children[index]
            stack.append((child, prefix, ancestors,
                          index == len(children) - 1, True))
    return "\n".join(lines)
