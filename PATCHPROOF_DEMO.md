# Trying PatchProof

PatchProof answers one focused question about a bug-fix pull request:

> Does the new or changed regression test fail against the base implementation and pass against the proposed implementation?

It does not claim that the entire patch is correct. It records evidence for the changed test.

## The results you will see

| Result | What happened |
|---|---|
| `proven` | The test failed with an assertion on the base code and passed on the PR code. |
| `not_proven` | The test passed on both revisions. |
| `still_failing` | The test failed with an assertion on both revisions. |
| `inconclusive` | Setup, import, collection, timeout, or another infrastructure problem prevented a reliable comparison. |
| `regression` | The normal suite passes on base but fails on the PR revision. |
| `no_tests` | The PR does not add or materially change an eligible test. |

## Run it locally in PowerShell

PatchProof is not published to npm yet. Install the locally built tarball from the PatchProof workspace:

```powershell
npm install --global C:\Jayaditya\Projects\PatchProof\artifacts\patchproof-0.1.0.tgz
```

Clone this repository and switch to one of the demonstration branches:

```powershell
git clone https://github.com/JayadityaVetsa/queue-reactive-limit-order-book-market-simulator.git
cd queue-reactive-limit-order-book-market-simulator
git fetch origin
git switch <demo-branch>
```

Run PatchProof from the repository root:

```powershell
patchproof check --base origin/main --head HEAD
```

Before running project commands, PatchProof displays the resolved revisions, temporary worktree location, setup command, targeted test command, and full-suite command. Type `y` to approve.

For machine-readable evidence:

```powershell
patchproof check --base origin/main --head HEAD --format json --output patchproof-report.json
```

Useful troubleshooting options:

```powershell
patchproof check --base origin/main --head HEAD --debug
patchproof check --base origin/main --head HEAD --keep-worktrees
```

## Run it through GitHub Actions

You do not need to install anything locally for this path.

1. Open a pull request or push another commit to an existing pull request.
2. Open the pull request's **Checks** section.
3. Select the **PatchProof** workflow and its `patchproof` job.
4. Open the job summary to see the aggregate and per-test evidence.

You can also select the repository's **Actions** tab, choose **PatchProof**, and open the run associated with the pull request.

## Run it again yourself

From the pull request's Checks page or the workflow run page:

1. Select **Re-run jobs**.
2. Choose **Re-run all jobs**.
3. Wait for the `patchproof` job to finish.

## Download the JSON evidence

On the completed workflow run page:

1. Scroll to **Artifacts**.
2. Download `patchproof-report`.
3. Extract `patchproof-report.json`.

The report contains the exact base/head SHAs, commands, durations, normalized outcomes, diagnostics, and aggregate status.

## Why the Action works without npm

The workflow references the public PatchProof GitHub repository at a full immutable commit:

```yaml
uses: JayadityaVetsa/PatchProof@b5302026c4238a0aa3f6159cb6f1dc719797a62c
```

GitHub downloads the bundled JavaScript Action directly from that commit. PatchProof does not need to be on npm or the GitHub Marketplace.

## Safety

PatchProof executes this repository's setup and test commands on the GitHub-hosted runner or your local computer. Temporary Git worktrees protect the active checkout, but they are not an operating-system sandbox.
