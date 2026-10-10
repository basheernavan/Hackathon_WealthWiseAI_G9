# How we work together

Anyone can pick up any task. Each task is one GitHub issue, one branch and one PR, and it never waits for another task. If you run out of time or tokens mid-task, hand it over (step 6) and someone else continues from your branch.

**The five rules**

1. One task = one issue = one branch `<issue#>-<short-name>` = one PR into `main`.
2. Touch only the files your task names. Shared files go in their own small PR.
3. Push at least every 30 minutes. Unpushed work can't be taken over.
4. `pytest` green before every merge.
5. Assignee set = taken. No assignee = free to take.

## 1. One-time setup (about 10 minutes)

1. You're already a collaborator on the repo (the team is listed in [00-overview.md](specs/00-overview.md#team)). If you haven't yet, accept the invite from your GitHub notifications or email, or you can't push.
2. Install [Python 3.11+](https://www.python.org/downloads/), [Git](https://git-scm.com/download/win) and the [GitHub CLI](https://cli.github.com/), then run `gh auth login`.
3. Set your real name, so commits show who did what:
   ```powershell
   git config --global user.name "Your Real Name"
   git config --global user.email "you@example.com"
   ```
4. Get the code and run it:
   ```powershell
   git clone https://github.com/basheernavan/Hackathon_WealthWiseAI_G9.git
   cd Hackathon_WealthWiseAI_G9
   python -m venv .venv; .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   copy .env.example .env      # paste the OPENROUTER_API_KEY from the team chat; optional
   pytest                      # expect: all passed or skipped, none failed
   streamlit run app.py        # opens the app in your browser
   ```
5. Read [CONTEXT.md](../CONTEXT.md) (5 minutes: the words we use) and [docs/specs/00-overview.md](specs/00-overview.md) (the task list).

## 2. Pick a task

1. Open the [issue list](https://github.com/basheernavan/Hackathon_WealthWiseAI_G9/issues?q=is%3Aopen+is%3Aissue+no%3Aassignee) (open, unassigned). Prefer the tasks named in the next milestone in [00-overview.md](specs/00-overview.md#milestones).
2. Claim it: `gh issue edit <N> --add-assignee @me`. If someone else got there first, pick another.
3. If the issue has a **Handoff** comment, follow step 7 instead.

## 3. Start the branch and a draft PR

```powershell
git switch main; git pull
git switch -c <N>-<short-name>              # e.g. 4-bank-csv
git commit --allow-empty -m "Start #<N>"
git push -u origin HEAD
gh pr create --draft --title "<issue title>" --body "Closes #<N>"
```

The draft PR tells everyone the work is in progress and shows your latest pushed state.

## 4. Build it

Everything you need is in the issue: the spec section, the file, the function and the test file. The stub file already exists with the exact signature. Don't change the signature.

With Claude Code, start with:

> Implement issue #&lt;N&gt; test-first using /mattpocock-skills:tdd. Read the issue (`gh issue view <N>`) and the spec section it links. Only edit the files the issue names.

While working:
- Commit and push at least every 30 minutes: `git add -A; git commit -m "<what changed>"; git push`.
- Spec unclear? Ask in the team chat, or run `/mattpocock-skills:grilling` to settle it, then write the answer as a comment on the issue.
- Need a change to `contracts.py` or another shared file? Open a separate issue and PR, and post in the chat. Keep building against the current contract meanwhile.

## 5. Finish and merge

```powershell
git pull origin main          # take in what others merged
pytest                        # must be green (skips are fine)
git push
gh pr ready
```

1. Post the PR link in the team chat and tag Basheer (@basheernavan).
2. Only Basheer can merge into `main` (a GitHub ruleset blocks everyone else). He squash-merges and deletes the branch. If the PR shows conflicts, fix them on your branch (`git pull origin main`, resolve, `pytest`, `git push`) and tag him again.
3. The issue closes by itself (thanks to `Closes #<N>`). Pick the next task.

Changes to `contracts.py` are the only exception: they need a 👍 from two other active people.

## 6. Hand over (out of tokens, time or energy)

1. Save everything, even if tests fail:
   ```powershell
   git add -A; git commit -m "WIP #<N>: <where you stopped>"; git push
   ```
2. Comment on the issue, using exactly this shape:
   ```
   **Handoff**
   Done: <what works, which tests pass>
   Next: <the very next step>
   Watch out: <anything surprising, or "nothing">
   ```
   e.g. `gh issue comment <N> --body "**Handoff** ..."`
3. Unassign yourself: `gh issue edit <N> --remove-assignee @me`.

## 7. Take over someone's task

```powershell
gh issue edit <N> --add-assignee @me
gh issue view <N> --comments           # read the Handoff comment
git fetch; git switch <N>-<short-name>  # branch name is on the PR
```

Continue from **Next** in the handoff comment, then carry on from step 4.

## Where things are

| You need | Look in |
| --- | --- |
| What to build | the issue → the spec section it links in `docs/specs/` |
| Words and rules | `CONTEXT.md` |
| Why something is done this way | `docs/adr/` (decisions; follow them, or raise a conflict in the chat) |
| Shared data models | `wealthwise/contracts.py` (frozen) |
| Sample input files | `samples/*.pdf`, `samples/*.csv`, `samples/*.xlsx` (fictional) |
| Correct answers | `samples/expected_profile.json` (ingestion), `samples/expected.json` (analysis), `samples/mock_report.json` (dashboard) |
| Test helpers and fixtures | `tests/conftest.py` |
| The LLM client | `wealthwise/llm.py`, `get_chat_model()`, which returns `None` without a key |
| Pitch and background | `documents/` (background only; see its README) |

## When something goes wrong

| Problem | Do this |
| --- | --- |
| "Merging is blocked" on your PR | Expected: only Basheer can merge. Tag him in the chat. |
| Merge conflict | Run `/mattpocock-skills:resolving-merge-conflicts`, or ask in the chat. |
| `pytest` fails on `main` | Post in the chat at once. Fixing `main` comes before any task. |
| A bug outside your task | `gh issue create --label needs-triage --title "..." --body "..."`, then carry on. |
| You ran `generate_samples.py` by accident | `git checkout -- samples/` |
| Push rejected (`403`) | Accept your collaborator invite (step 1.1), and check `gh auth status` shows your own account. |
| Push rejected (`non-fast-forward`) | `git pull`, then `git push`. |
| After 08:00 Sunday | Bug fixes only. Code freeze at 10:30. |
