import unittest

from src.model import ascii_tree, collect_graph, reverse_graph
from src.repository import parse_pom


class GraphTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {"A": ["B", "C"], "B": ["D"],
                        "C": ["D", "E"], "D": ["A"], "E": []}

    def test_cycle_and_shared_node(self):
        graph = collect_graph("A", self.fixture.__getitem__, 4, "")
        self.assertEqual(graph["D"], ["A"])
        self.assertEqual(graph["C"], ["D", "E"])
        self.assertIn("[cycle]", ascii_tree(graph, "A"))

    def test_depth_and_filter(self):
        graph = collect_graph("A", self.fixture.__getitem__, 1, "C")
        self.assertEqual(graph, {"A": ["B"], "B": []})

    def test_reverse(self):
        self.assertEqual(reverse_graph(self.fixture)["D"], ["B", "C"])

    def test_pom_direct_only(self):
        pom = b"""<project><dependencies>
        <dependency><groupId>org.example</groupId><artifactId>one</artifactId>
        <version>1.0</version></dependency>
        <dependency><groupId>org.example</groupId><artifactId>test</artifactId>
        <version>1.0</version><scope>test</scope></dependency>
        </dependencies></project>"""
        self.assertEqual(parse_pom(pom), ["org.example:one:1.0"])


if __name__ == "__main__":
    unittest.main()
