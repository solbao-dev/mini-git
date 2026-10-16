"""필수 명령어와 자료구조·알고리즘을 검증하는 테스트."""

import ast
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import patch

from algorithms import merge_sort, parent_first, shortest_path
from main import execute, main
from mini_git import Commit, MiniGit


class MiniGitTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2024, 1, 1, 9)
        self.repo = MiniGit(clock=lambda: self.now)
        self.repo.init("Alice")

    def test_init_and_main(self):
        self.assertEqual(self.repo.author, "Alice")
        self.assertEqual(self.repo.current_branch, "main")
        self.assertIsNone(self.repo.branches["main"])

    def test_first_commit_has_no_parent(self):
        self.assertEqual(self.repo.commit("start").parents, ())

    def test_branch_and_switch(self):
        first = self.repo.commit("start")
        self.repo.branch("feature")
        self.repo.switch("feature")
        self.assertEqual(self.repo.branches["feature"], first.hash)
        self.assertEqual(self.repo.current_branch, "feature")

    def test_branches_have_independent_heads(self):
        root = self.repo.commit("root")
        self.repo.branch("feature")
        self.repo.switch("feature")
        feature = self.repo.commit("feature work")
        self.repo.switch("main")
        main_commit = self.repo.commit("main work")
        self.assertEqual(feature.parents, (root.hash,))
        self.assertEqual(main_commit.parents, (root.hash,))
        self.assertNotEqual(feature.hash, main_commit.hash)

    def test_hashes_are_unique(self):
        hashes = [self.repo.commit(str(i)).hash for i in range(100)]
        self.assertEqual(len(hashes), len(set(hashes)))

    def test_dag_parents_must_exist(self):
        with self.assertRaisesRegex(ValueError, "Unknown commit"):
            self.repo.create_commit("bad", ["missing"])
        root = self.repo.create_commit("root", [])
        child = self.repo.create_commit("child", [root.hash])
        both = self.repo.create_commit("both", [root.hash, child.hash])
        self.assertEqual(both.parents, (root.hash, child.hash))
        self.assertLess(self.repo.next_hash - 1, 4)

    def test_log_parent_first_across_branches(self):
        root = self.repo.commit("root")
        self.repo.branch("side")
        self.repo.commit("main child")
        self.repo.switch("side")
        self.repo.commit("side child")
        order = [c.hash for c in self.repo.log()]
        self.assertEqual(order[0], root.hash)
        self.assertEqual(len(order), 3)

    def test_log_parent_first_with_two_parents(self):
        a = self.repo.create_commit("a", [])
        b = self.repo.create_commit("b", [])
        child = self.repo.create_commit("child", [a.hash, b.hash])
        order = [c.hash for c in self.repo.log()]
        self.assertLess(order.index(a.hash), order.index(child.hash))
        self.assertLess(order.index(b.hash), order.index(child.hash))

    def test_date_sort_and_tie(self):
        a = self.repo.commit("a")
        self.now -= timedelta(days=1)
        b = self.repo.commit("b")
        self.now += timedelta(days=1)
        c = self.repo.commit("c")
        self.assertEqual([x.hash for x in self.repo.log("date")], [b.hash, a.hash, c.hash])

    def test_author_sort_and_tie(self):
        a = self.repo.commit("a")
        self.repo.author = "Bob"
        b = self.repo.commit("b")
        self.repo.author = "Alice"
        c = self.repo.commit("c")
        self.assertEqual([x.hash for x in self.repo.log("author")], [a.hash, c.hash, b.hash])

    def test_path_shortest(self):
        a = self.repo.commit("a")
        b = self.repo.commit("b")
        c = self.repo.commit("c")
        self.assertEqual(self.repo.path(a.hash, c.hash), f"{a.hash}->{b.hash}->{c.hash}")

    def test_path_undirected(self):
        a = self.repo.commit("a")
        b = self.repo.commit("b")
        self.assertEqual(self.repo.path(b.hash, a.hash), f"{b.hash}->{a.hash}")

    def test_path_lexical_tie_uses_whole_string(self):
        # 'a' < 'a-' 이지만 's->a-->t' < 's->a->t'이다.
        t = self.now
        graph = {
            "s": Commit("s", "", "", t, ()),
            "a": Commit("a", "", "", t, ("s",)),
            "a-": Commit("a-", "", "", t, ("s",)),
            "t": Commit("t", "", "", t, ("a", "a-")),
        }
        self.assertEqual(shortest_path(graph, "s", "t"), "s->a-->t")

    def test_path_same_commit(self):
        a = self.repo.commit("a")
        self.assertEqual(self.repo.path(a.hash, a.hash), a.hash)

    def test_path_disconnected(self):
        a = self.repo.create_commit("a", [])
        b = self.repo.create_commit("b", [])
        self.assertIsNone(self.repo.path(a.hash, b.hash))
        self.assertEqual(execute(self.repo, f"PATH {a.hash} {b.hash}"), "No path")

    def test_ancestors_all_and_no_duplicates(self):
        a = self.repo.create_commit("a", [])
        b = self.repo.create_commit("b", [a.hash])
        c = self.repo.create_commit("c", [a.hash])
        d = self.repo.create_commit("d", [b.hash, c.hash])
        result = self.repo.ancestors(d.hash)
        self.assertEqual(set(result), {a.hash, b.hash, c.hash})
        self.assertEqual(len(result), 3)
        self.assertNotIn(d.hash, result)

    def test_keyword_index_and_deduplication(self):
        commit = self.repo.commit("Login login LOGIN")
        self.assertEqual(self.repo.keyword_index["login"], [commit.hash])
        self.assertEqual(self.repo.search_keyword("LoGiN"), [commit])

    def test_quoted_multiword_keyword(self):
        self.repo.commit("login only")
        both = self.repo.commit("Add login feature")
        self.assertEqual(self.repo.search_keyword("LOGIN feature"), [both])
        self.assertIn(both.hash, execute(self.repo, 'SEARCH "login feature"'))

    def test_author_index_and_case(self):
        a = self.repo.commit("a")
        self.repo.author = "alice"
        b = self.repo.commit("b")
        self.assertEqual(self.repo.search_author("Alice"), [a])
        self.assertEqual(self.repo.search_author("alice"), [b])

    def test_command_case_and_quoted_arguments(self):
        repo = MiniGit()
        self.assertIn("Current user: Alice Bob", execute(repo, 'iNiT "Alice Bob"'))
        self.assertIn("Add login feature", execute(repo, 'cOmMiT "Add login feature"'))
        self.assertIn("Found 1", execute(repo, 'sEaRcH LOGIN'))
        self.assertIn("Found 1", execute(repo, 'SEARCH --author="Alice Bob"'))

    def test_bad_commands_options_and_quotes(self):
        self.assertEqual(execute(self.repo, "nonsense"), "Unknown command")
        self.assertEqual(execute(self.repo, "LOG --sort-by=foo"), "Invalid args")
        self.assertEqual(execute(self.repo, "SEARCH --foo=bar"), "Invalid args")
        self.assertEqual(execute(self.repo, 'COMMIT "unclosed'), "Invalid args")
        self.assertEqual(execute(self.repo, "COMMIT two words"), "Invalid args")
        self.assertEqual(execute(self.repo, ""), "")

    def test_unknown_branch_and_duplicate(self):
        self.assertEqual(execute(self.repo, "SWITCH absent"), "Unknown branch: absent")
        self.assertEqual(execute(self.repo, "BRANCH main"), "Branch already exists: main")

    def test_unknown_commit(self):
        self.assertEqual(execute(self.repo, "ANCESTORS absent"), "Unknown commit: absent")
        self.assertEqual(execute(self.repo, "PATH absent other"), "Unknown commit: absent")

    def test_pre_init_commands(self):
        repo = MiniGit()
        for command in ("BRANCH x", "SWITCH x", "COMMIT x", "LOG", "PATH a b", "ANCESTORS a", "SEARCH x"):
            self.assertEqual(execute(repo, command), "Repository not initialized")

    def test_exit_and_quit(self):
        self.assertIsNone(execute(self.repo, "exit"))
        self.assertIsNone(execute(self.repo, "QUIT"))
        self.assertEqual(execute(self.repo, "quit now"), "Invalid args")

    def test_repl_exits(self):
        for ending in ("exit", "quit"):
            output = StringIO()
            with patch("builtins.input", side_effect=["init Alice", ending]), redirect_stdout(output):
                main()
            self.assertIn("Initialized repository", output.getvalue())

    def test_merge_sort_accuracy_and_stability(self):
        items = [(2, "first"), (1, "a"), (2, "second"), (1, "b")]
        self.assertEqual(merge_sort(items, lambda x: x[0]),
                         [(1, "a"), (1, "b"), (2, "first"), (2, "second")])
        self.assertEqual(items[0], (2, "first"))

    def test_no_standard_sort_api(self):
        root = Path(__file__).resolve().parents[1]
        for filename in ("algorithms.py", "mini_git.py", "main.py"):
            tree = ast.parse((root / filename).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    self.assertFalse(isinstance(node.func, ast.Name) and node.func.id == "sorted")
                    self.assertFalse(isinstance(node.func, ast.Attribute) and node.func.attr == "sort")

    def test_cycle_detection(self):
        t = self.now
        graph = {"a": Commit("a", "", "", t, ("b",)),
                 "b": Commit("b", "", "", t, ("a",))}
        with self.assertRaisesRegex(ValueError, "cycle"):
            parent_first(graph)


if __name__ == "__main__":
    unittest.main()
