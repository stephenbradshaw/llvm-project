"""The sysroot path remaps must agree everywhere they are defined.

The rust source checkout is remapped to /rustc/<commit>/... via
bootstrap.sysroot_remap_pairs (bootstrap.toml rustflags, cargo
config.toml, job RUSTFLAGS, build-std). The commit value itself is
pinned in bootstrap.RUST_SRC_COMMIT; these tests keep the workflow from
reintroducing a broad catch-all remap or a release-version path that
would fingerprint the custom toolchain.
"""

import os
import pathlib
import tempfile
import unittest

import bootstrap


class RustSrcCommitConsistencyTest(unittest.TestCase):
    def test_constant_is_a_full_commit_hash(self):
        self.assertRegex(bootstrap.RUST_SRC_COMMIT, r"^[0-9a-f]{40}$")

    def test_workflow_delegates_remaps_to_bootstrap(self):
        workflow = pathlib.Path(".github/workflows/rust-m0.yml").read_text()
        self.assertIn("print-remaps", workflow)
        self.assertIn("write-cargo-remaps", workflow)
        self.assertIn("check-sysroot-paths", workflow)
        self.assertNotIn("/rustc/1.99.0", workflow)
        # No broad catch-all remap flag left in the workflow
        self.assertNotIn("build-rust-1.99=/rustc/", workflow)

    def test_bootstrap_remaps_use_the_pinned_commit(self):
        pairs = bootstrap.sysroot_remap_pairs(
            "/tmp/ci-ws", "x86_64-unknown-linux-gnu"
        )
        self.assertEqual(len(pairs), 3)
        self.assertTrue(all(bootstrap.RUST_SRC_COMMIT in dst for _, dst in pairs))
        self.assertEqual(
            pairs[0],
            (
                "/tmp/ci-ws/build-rust-1.99/build/obfuscation-cargo-home",
                f"/rustc/{bootstrap.RUST_SRC_COMMIT}/vendor",
            ),
        )
        self.assertEqual(
            pairs[1],
            (
                "/tmp/ci-ws/build-rust-1.99/library",
                f"/rustc/{bootstrap.RUST_SRC_COMMIT}/library",
            ),
        )
        # Forbidden as a remap *target*; the checker may mention the
        # string as a leak needle.
        self.assertTrue(
            all(not dst.startswith("/rustc/1.99.0") for _, dst in pairs)
        )

    def test_render_config_enables_remap_debuginfo(self):
        os.environ.pop("GITHUB_WORKSPACE", None)
        cfg = bootstrap.render_config(
            pathlib.Path("/usr/bin/true"), 1, "x86_64-unknown-linux-gnu"
        )
        self.assertIn("remap-debuginfo = true", cfg)
        self.assertNotIn("rustflags", cfg)

        os.environ["GITHUB_WORKSPACE"] = "/tmp/ci-ws"
        cfg = bootstrap.render_config(
            pathlib.Path("/usr/bin/true"), 1, "x86_64-unknown-linux-gnu"
        )
        self.assertIn("remap-debuginfo = true", cfg)
        self.assertIn("/vendor", cfg)
        self.assertIn("/library", cfg)
        self.assertNotIn("build-rust-1.99=/rustc/", cfg)

    def test_check_sysroot_panic_paths_accepts_and_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = pathlib.Path(tmp) / "libstd-test.rlib"
            commit = bootstrap.RUST_SRC_COMMIT
            lib.write_bytes(
                f"/rustc/{commit}/library/std/src/panicking.rs".encode()
            )
            bootstrap.check_sysroot_panic_paths(lib)
            lib.write_bytes(
                b"obfuscation-cargo-home "
                + f"/rustc/{commit}/library/x".encode()
            )
            with self.assertRaises(RuntimeError):
                bootstrap.check_sysroot_panic_paths(lib)


if __name__ == "__main__":
    unittest.main()
