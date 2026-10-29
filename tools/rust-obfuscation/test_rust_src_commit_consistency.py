"""The sysroot path remaps must agree everywhere they are defined.

The rust source checkout is remapped to /rustc/<commit>/ in the CI
workflow's job environment, in the cargo-level config the workflow
writes, in the stdseed build-std step and in bootstrap.py's generated
bootstrap.toml. The commit value itself is pinned in
bootstrap.RUST_SRC_COMMIT; these tests keep the other definitions from
drifting away from it (a stale path would fingerprint the custom
toolchain in every produced binary).
"""

import pathlib
import unittest

import bootstrap


class RustSrcCommitConsistencyTest(unittest.TestCase):
    def test_constant_is_a_full_commit_hash(self):
        self.assertRegex(bootstrap.RUST_SRC_COMMIT, r"^[0-9a-f]{40}$")

    def test_workflow_uses_the_pinned_commit(self):
        workflow = (
            pathlib.Path(".github/workflows/rust-m0.yml").read_text()
        )
        self.assertIn(bootstrap.RUST_SRC_COMMIT, workflow)
        # The whole file must be free of the release-version style path
        # (a custom toolchain tell)
        self.assertNotIn("/rustc/1.99.0", workflow)

    def test_bootstrap_remaps_use_the_pinned_commit(self):
        source = pathlib.Path("tools/rust-obfuscation/bootstrap.py").read_text()
        self.assertIn(bootstrap.RUST_SRC_COMMIT, source)
        self.assertNotIn("/rustc/1.99.0", source)


if __name__ == "__main__":
    unittest.main()