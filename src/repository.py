"""Read Maven POM metadata directly, without package managers."""

import json
from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import urlopen
import xml.etree.ElementTree as xml_tree

from .model import Package

MAX_POM_BYTES = 2_000_000


class RepositoryError(Exception):
    """A repository or POM cannot be read safely."""


def load_fixture(path: Path) -> dict[str, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RepositoryError(f"Cannot read fixture: {error}") from error
    if not isinstance(data, dict) or not all(
        _valid_fixture_entry(key, value) for key, value in data.items()
    ):
        raise RepositoryError("Fixture must map names to arrays of names")
    _validate_fixture_graph(data)
    return data


def _valid_fixture_entry(key: object, value: object) -> bool:
    return (isinstance(key, str) and isinstance(value, list)
            and all(isinstance(item, str) for item in value))


def _validate_fixture_graph(data: dict[str, list[str]]) -> None:
    if not all(re.fullmatch(r"[A-Z]+", name) for name in data):
        raise RepositoryError("Fixture package names must be uppercase")
    if any(child not in data for values in data.values() for child in values):
        raise RepositoryError("Fixture references an undefined package")


class MavenRepository:
    def __init__(self, base_url: str) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise RepositoryError("Repository must be an HTTP(S) URL")
        self.base_url = base_url.rstrip("/")

    def dependencies(self, name: str) -> list[str]:
        package = Package.parse(name)
        for field in (package.group, package.artifact, package.version):
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", field):
                raise RepositoryError("Unsafe Maven coordinate")
            if field in {".", ".."}:
                raise RepositoryError("Unsafe Maven coordinate")
        group_path = package.group.replace(".", "/")
        filename = f"{package.artifact}-{package.version}.pom"
        url = (f"{self.base_url}/{group_path}/{package.artifact}/"
               f"{package.version}/{filename}")
        try:
            with urlopen(url, timeout=12) as response:
                data = response.read(MAX_POM_BYTES + 1)
        except Exception as error:
            raise RepositoryError(f"Cannot fetch {url}: {error}") from error
        if len(data) > MAX_POM_BYTES:
            raise RepositoryError("POM exceeds 2 MB limit")
        return parse_pom(data)


def parse_pom(data: bytes) -> list[str]:
    """Read direct, concrete dependencies from the project section."""
    try:
        root = xml_tree.fromstring(data)
    except xml_tree.ParseError as error:
        raise RepositoryError(f"Invalid POM XML: {error}") from error
    namespace = root.tag.partition("}")[0] + "}" if "}" in root.tag else ""

    def tag(name: str) -> str:
        return namespace + name

    properties = _pom_properties(root, tag)
    direct = root.find(tag("dependencies"))
    if direct is None:
        return []
    coordinates = (
        _dependency_coordinate(dependency, tag, properties)
        for dependency in direct.findall(tag("dependency"))
    )
    return sorted({name for name in coordinates if name is not None})


def _pom_properties(root, tag) -> dict[str, str]:
    properties = {}
    props = root.find(tag("properties"))
    if props is not None:
        properties = {child.tag.rsplit("}", 1)[-1]: child.text or ""
                      for child in props}
    for name in ("groupId", "version"):
        value = root.findtext(tag(name))
        if value is None:
            value = root.findtext(f"{tag('parent')}/{tag(name)}")
        if value:
            properties[f"project.{name}"] = value
            properties[f"pom.{name}"] = value
    return properties


def _dependency_coordinate(dependency, tag, properties) -> str | None:
    scope = dependency.findtext(tag("scope"), "compile")
    optional = dependency.findtext(tag("optional"), "false")
    if scope in {"test", "provided", "system", "import"}:
        return None
    if optional.strip().lower() == "true":
        return None
    values = [dependency.findtext(tag(part), "")
              for part in ("groupId", "artifactId", "version")]
    values = [resolve(value, properties) for value in values]
    if not all(values) or any("${" in value for value in values):
        return None
    return ":".join(values)


def resolve(value: str, properties: dict[str, str]) -> str:
    for _ in range(10):
        updated = re.sub(r"\$\{([^}]+)\}",
                         lambda match: properties.get(match[1], match[0]),
                         value)
        if updated == value:
            break
        value = updated
    return value
