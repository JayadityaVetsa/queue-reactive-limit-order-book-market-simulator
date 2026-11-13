# CI status and optional native coverage

The active GitHub Actions workflow runs the Python test suite on pushes and pull requests. The published trading-experiment update passed that workflow. Native execution was compiled and tested locally with all 31 tests passing; the current hosted workflow skips the optional native parity test because it does not set `LOB_NATIVE`.

The prepared [workflow patch](ci-update.patch) adds native compilation, enables the parity test, and smoke-runs both experiments. GitHub rejected that workflow edit because the available OAuth credential lacks the `workflow` scope; the connected integration also returned HTTP 403. The existing workflow was preserved and the rest of the project was pushed successfully.

After an authorized maintainer supplies workflow-edit permission, apply and publish the reviewed patch:

```bash
git apply docs/ci-update.patch
git add .github/workflows/ci.yml
git commit -m "Test native execution and trading experiment smoke runs in CI"
git push origin main
```

The PatchProof pull-request workflow remains unchanged.
