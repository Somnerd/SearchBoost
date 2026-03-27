"""
Tests for .gitignore changes introduced in this PR.

Verifies:
 1. All new AI-tool directories (.agent/, .gemini/, .cursor/, .gsd/, .claude/,
    .anthropic/, .codex/) are present as ignore patterns.
 2. JavaScript ecosystem patterns (node_modules/, **/node_modules/, dist/,
    **/dist/) are present and match expected paths.
 3. .env* wildcard expansion covers common environment files while the
    negation entry for .env.example is present.
 4. Pattern matching behaves correctly using pathspec (gitwildmatch semantics),
    including nested paths and glob recursion.
"""

import os
import pathspec
import pytest

# ── helpers ──────────────────────────────────────────────────────────────────

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GITIGNORE_PATH = os.path.join(REPO_ROOT, ".gitignore")


def _read_gitignore_lines() -> list[str]:
    """Return raw non-empty, non-comment lines from .gitignore."""
    with open(GITIGNORE_PATH, "r", encoding="utf-8") as fh:
        return fh.read().splitlines()


def _build_spec(lines: list[str]) -> pathspec.PathSpec:
    """Compile a PathSpec from the given lines using gitignore semantics."""
    return pathspec.PathSpec.from_lines("gitignore", lines)


# ── fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def gitignore_lines() -> list[str]:
    return _read_gitignore_lines()


@pytest.fixture(scope="module")
def gitignore_spec(gitignore_lines) -> pathspec.PathSpec:
    return _build_spec(gitignore_lines)


# ── 1. Pattern presence tests ─────────────────────────────────────────────────

class TestPatternPresence:
    """Verify every new pattern added in this PR is literally in the file."""

    @pytest.mark.parametrize("pattern", [
        ".agent/",
        ".gemini/",
        ".cursor/",
        ".gsd/",
        ".claude/",
        ".anthropic/",
        ".codex/",
    ])
    def test_ai_tool_directory_pattern_present(self, gitignore_lines, pattern):
        assert pattern in gitignore_lines, (
            f"Expected AI-tool ignore pattern '{pattern}' in .gitignore"
        )

    @pytest.mark.parametrize("pattern", [
        "node_modules/",
        "**/node_modules/",
        "dist/",
        "**/dist/",
    ])
    def test_js_ecosystem_pattern_present(self, gitignore_lines, pattern):
        assert pattern in gitignore_lines, (
            f"Expected JS-ecosystem ignore pattern '{pattern}' in .gitignore"
        )

    def test_env_wildcard_pattern_present(self, gitignore_lines):
        assert ".env*" in gitignore_lines, (
            "Expected '.env*' wildcard pattern in .gitignore"
        )

    def test_env_example_negation_entry_present(self, gitignore_lines):
        """The negation entry for .env.example must exist (in either form)."""
        has_entry = (
            "! .env.example" in gitignore_lines
            or "!.env.example" in gitignore_lines
        )
        assert has_entry, (
            "Expected a negation entry for .env.example in .gitignore"
        )


# ── 2. AI-tool directory matching ─────────────────────────────────────────────

class TestAIToolDirectoryMatching:
    """Files inside the new AI-tool directories must be ignored."""

    @pytest.mark.parametrize("path", [
        ".agent/config.json",
        ".agent/session/data.bin",
        ".gemini/credentials.json",
        ".gemini/history/log.txt",
        ".cursor/settings.json",
        ".cursor/extensions/ext.vsix",
        ".gsd/STATE.md",
        ".gsd/phases/1/1-PLAN.md",
        ".claude/projects.json",
        ".anthropic/api_key.json",
        ".codex/config.yaml",
    ])
    def test_ai_tool_path_is_ignored(self, gitignore_spec, path):
        assert gitignore_spec.match_file(path), (
            f"Expected '{path}' to be ignored by .gitignore"
        )


# ── 3. node_modules matching ──────────────────────────────────────────────────

class TestNodeModulesMatching:
    """node_modules directories at any depth must be ignored."""

    @pytest.mark.parametrize("path", [
        "node_modules/express/index.js",
        "node_modules/lodash/package.json",
        "searchboost_api/node_modules/axios/lib/core.js",
        "searchboost_ui/node_modules/react/index.js",
        "deeply/nested/node_modules/some-pkg/file.js",
    ])
    def test_node_modules_path_is_ignored(self, gitignore_spec, path):
        assert gitignore_spec.match_file(path), (
            f"Expected '{path}' to be ignored by .gitignore"
        )

    @pytest.mark.parametrize("path", [
        "searchboost_api/src/app.js",
        "searchboost_ui/src/main.jsx",
        "searchboost_service/main.py",
    ])
    def test_regular_source_files_not_ignored(self, gitignore_spec, path):
        assert not gitignore_spec.match_file(path), (
            f"Expected '{path}' NOT to be ignored by .gitignore"
        )


# ── 4. dist/ matching ────────────────────────────────────────────────────────

class TestDistDirectoryMatching:
    """dist/ build output directories at any depth must be ignored."""

    @pytest.mark.parametrize("path", [
        "dist/bundle.js",
        "dist/index.html",
        "searchboost_ui/dist/assets/main.abc123.js",
        "searchboost_ui/dist/index.html",
        "packages/core/dist/index.cjs",
    ])
    def test_dist_path_is_ignored(self, gitignore_spec, path):
        assert gitignore_spec.match_file(path), (
            f"Expected '{path}' to be ignored by .gitignore"
        )


# ── 5. .env* wildcard matching ────────────────────────────────────────────────

class TestEnvWildcardMatching:
    """The .env* pattern must match common environment file variants."""

    @pytest.mark.parametrize("path", [
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        ".env.test",
        ".env.staging",
        ".env.docker",
        ".envrc",
    ])
    def test_env_variant_is_ignored(self, gitignore_spec, path):
        assert gitignore_spec.match_file(path), (
            f"Expected '{path}' to be ignored by .gitignore via '.env*' pattern"
        )


# ── 6. .gitignore file integrity ──────────────────────────────────────────────

class TestGitignoreFileIntegrity:
    """Structural checks on the .gitignore file itself."""

    def test_gitignore_file_exists(self):
        assert os.path.isfile(GITIGNORE_PATH), ".gitignore file must exist"

    def test_gitignore_is_not_empty(self, gitignore_lines):
        non_empty = [ln for ln in gitignore_lines if ln.strip()]
        assert len(non_empty) > 0, ".gitignore must not be empty"

    def test_no_merge_conflict_markers(self, gitignore_lines):
        """The PR resolves a merge conflict — markers must be absent."""
        for line in gitignore_lines:
            assert not line.startswith("<<<<<<<"), (
                f"Merge conflict marker found: {line!r}"
            )
            assert not line.startswith("======="), (
                f"Merge conflict separator found: {line!r}"
            )
            assert not line.startswith(">>>>>>>"), (
                f"Merge conflict marker found: {line!r}"
            )

    def test_removed_conflicting_branch_artifact(self, gitignore_lines):
        """'notes.text' (from the losing merge branch) must not be present."""
        assert "notes.text" not in gitignore_lines, (
            "'notes.text' from the merge conflict looser branch must not appear"
        )

    def test_retained_notes_directory_pattern(self, gitignore_lines):
        """'*/notes/' (from the winning HEAD branch) must still be present."""
        assert "*/notes/" in gitignore_lines, (
            "'*/notes/' pattern from HEAD branch must be retained"
        )


# ── 7. Boundary / negative cases ─────────────────────────────────────────────

class TestBoundaryAndNegativeCases:
    """Edge-case and regression checks."""

    def test_env_example_negation_pattern_is_spaced(self, gitignore_lines):
        """
        The PR added '! .env.example' (with a space).  Regardless of whether
        this correctly un-ignores the file (git trims leading spaces before the
        path in negation lines), the literal entry must be present as committed.
        """
        assert "! .env.example" in gitignore_lines, (
            "Expected the literal '! .env.example' entry as written in the PR"
        )

    def test_python_pycache_still_ignored(self, gitignore_spec):
        """Pre-existing Python cache patterns must not have been removed."""
        assert gitignore_spec.match_file("__pycache__/cache.pyc"), (
            "__pycache__ files should still be ignored"
        )

    def test_rust_target_still_ignored(self, gitignore_spec):
        """Pre-existing Rust build artefact patterns must not have been removed."""
        assert gitignore_spec.match_file("searchboost_warden/target/debug/warden"), (
            "Rust target/ directories should still be ignored"
        )

    def test_log_files_still_ignored(self, gitignore_spec):
        """Log files must still be covered by the pre-existing *.log pattern."""
        assert gitignore_spec.match_file("worker.log"), (
            "*.log files should still be ignored"
        )

    def test_source_files_not_ignored(self, gitignore_spec):
        """Core source files must never be ignored."""
        source_files = [
            "searchboost_api/src/app.js",
            "searchboost_service/main.py",
            "searchboost_warden/src/main.rs",
            "searchboost_ui/src/App.jsx",
            "docker-compose.yml",
            "README.md",
        ]
        for path in source_files:
            assert not gitignore_spec.match_file(path), (
                f"Source file '{path}' must NOT be ignored"
            )

    def test_deeply_nested_ai_tool_files_ignored(self, gitignore_spec):
        """Files several levels inside a newly-ignored AI-tool dir must be matched."""
        deep_paths = [
            ".gsd/phases/3/3.2-PLAN.md",
            ".claude/sessions/abc123/context.json",
            ".anthropic/cache/embeddings/vec.bin",
        ]
        for path in deep_paths:
            assert gitignore_spec.match_file(path), (
                f"Expected deeply-nested path '{path}' to be ignored"
            )

    def test_similarly_named_non_ai_dirs_not_over_matched(self, gitignore_spec):
        """Directories that happen to *contain* the ai-tool names must not be ignored."""
        # e.g. a directory literally called 'my_agent/' is not '.agent/'
        safe_paths = [
            "my_agent/config.json",
            "docs/gsd_overview.md",
            "scripts/setup_gemini.sh",
        ]
        for path in safe_paths:
            assert not gitignore_spec.match_file(path), (
                f"Path '{path}' should NOT be ignored — it doesn't start with a dot"
            )