"""CLI for variant 22."""

import argparse
from pathlib import Path
import sys

from .model import Package, ascii_tree, collect_graph, reverse_graph
from .render import save_graph
from .repository import MavenRepository, RepositoryError, load_fixture


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Maven dependency graph")
    result.add_argument(
        "--package", required=True,
        help="group:artifact:version, or uppercase fixture name",
    )
    result.add_argument("--repository", required=True,
                        help="Maven repository URL or fixture JSON path")
    result.add_argument("--test", action="store_true",
                        help="read uppercase graph from JSON fixture")
    result.add_argument("--output", type=Path, default=Path("output/graph.svg"))
    result.add_argument("--ascii", action="store_true")
    result.add_argument("--max-depth", type=int, default=3)
    result.add_argument("--exclude", default="")
    result.add_argument("--reverse", action="store_true",
                        help="show packages depending on the requested one")
    return result


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    if args.max_depth < 0:
        parser().error("--max-depth must be nonnegative")
    try:
        if args.test:
            fixture = load_fixture(Path(args.repository))
            if args.package not in fixture:
                raise RepositoryError("Package absent from fixture")
            source = fixture.__getitem__
        else:
            Package.parse(args.package)
            source = MavenRepository(args.repository).dependencies
        if args.reverse:
            if not args.test:
                raise RepositoryError("Reverse mode requires fixture mode; "
                                      "Maven has no reverse index")
            all_nodes = {name: list(children)
                         for name, children in fixture.items()}
            backward = reverse_graph(all_nodes)
            graph = collect_graph(args.package, backward.__getitem__,
                                  args.max_depth,
                                  args.exclude)
        else:
            graph = collect_graph(args.package, source, args.max_depth,
                                  args.exclude)
        save_graph(graph, args.output)
        if args.ascii:
            print(ascii_tree(graph, args.package))
        print(f"SVG: {args.output}")
        print(f"PlantUML: {args.output.with_suffix('.puml')}")
        return 0
    except (ValueError, RepositoryError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
