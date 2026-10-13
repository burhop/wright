# Wright 0.4.0 — desktop walkthrough

Use a **fresh conversation on the GB10 host** in your Windows desktop app. Keep that conversation for all steps. The updated plugin is `wright-desktop-gb10-prototype`.

## 1. Open existing results

Paste:

```text
Use the Wright plugin and check connection status. Read workflows/desktop-checkpoint.workflow.wflow in workspace d8497ee5-0ef9-4cfe-8f0c-10c609ddab0b, session desktop-afee602f-a641-4173-a80b-e69e0aa99233. Open completed run 92db9047617c48ec91a85dec3a3a0a1b with wright_process_view, operation snapshot, using the returned storage digest. Show the native panel, not a browser page. Do not start or resume this run. If tools are missing, stop and tell me.
```

**Check:** the right panel shows a completed run. Open `first.txt` and `second.txt` from its results. Leave this recorded example unchanged.

## 2. Create your own workspace and workflow

Paste:

```text
Create a fresh Wright workspace named UI walkthrough. Copy the saved workflow from step 1 into it as workflows/ui-walkthrough.workflow.wflow, keeping its instructions and input checkpoint. Open it with wright_workflow_open. Remember the new workspace/session/path for subsequent steps. Do not run it yet or open a browser page.
```

**Try:** move a block; Undo and Redo; inspect a step; open Source and Side by side. Save before closing. Reopen with: **“Reopen my UI walkthrough workflow in the native editor.”** Check that the saved block positions remain.

## 3. Start and supply reasoning

In the panel, choose **Run and results → Prepare and check inputs**, then start **once**. When it says **Waiting for desktop chat**, paste:

```text
Continue the existing run in my UI walkthrough workspace using this conversation. Read Wright's queued reasoning task and submit its answer through Wright. Stop at the declared input checkpoint and let me choose. Do not start another run or use a separate model worker.
```

## 4. Answer the checkpoint and inspect results

In the panel, select `a` or `b` in **selection**, then click **Submit response** once. Paste:

```text
Continue that same Wright run using my submitted selection and this conversation. Complete its next queued task, then show the recorded results. Do not create or restart a run.
```

**Check:** the same run completes and its two text outputs open. Close the panel, then ask: **“Reopen that completed run with wright_process_view, without starting anything.”** The results should remain.

## 5. Check comfort and cancellation

Resize the panel; try light/dark mode, keyboard Tab navigation, and desktop zoom. Save before closing; unsaved-draft restoration is not promised.

Optional: on your **new test workflow**, prepare another run, start once, and choose **Cancel this run** before supplying a chat answer. Confirm it becomes cancelled. Leave the original recorded example alone.

## Tell me what happened

Send a screenshot and a short note: **what worked, what was confusing, and ease of use from 1–5**. Mention any tool permission prompt or error. If a write has an uncertain outcome, stop and report it rather than retrying.
