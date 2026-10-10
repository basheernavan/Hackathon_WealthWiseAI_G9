# Demo runbook (D2, issue #17)

How to get the demo laptop ready, run the dry run, rehearse, and recover if something breaks on stage. The demo script itself is in [00-overview.md](specs/00-overview.md#demo-script-acceptance-test-for-the-whole-app); the pitch is `documents/WealthWise_Heading_Robots.pptx`.

## Sunday timeline

| When | What | Who |
| --- | --- | --- |
| 08:00 | Fresh clone on the demo laptop, then the automated dry run (below). File every problem. | D2 owner |
| 08:00–10:30 | Bug fixes only. Re-run the dry run after each fix is merged. | everyone |
| 10:30 | **Code freeze.** Final dry run on `main`, then rehearse pitch + demo twice. | whole team |
| 11:30 | Laptop staged (checklist below). Nothing gets pulled or installed after this. | presenter |
| 12:00 | Submit. | Basheer |

## 1. Set up the demo laptop (once, about 10 minutes)

Follow [COLLABORATION.md step 1](COLLABORATION.md#1-one-time-setup-about-10-minutes) on a **fresh clone of `main`**, then:

```powershell
copy .env.example .env          # paste the OPENROUTER_API_KEY from the team chat
python scripts/demo_check.py --warm-chroma
```

`--warm-chroma` downloads Chroma's ~80 MB embedding model now instead of during the demo. It is cached in `%USERPROFILE%\.cache\chroma`, so it needs the internet only once.

## 2. Automated dry run

`python scripts/demo_check.py` runs the demo script against the real page (Streamlit's headless `AppTest`): it uploads the three sample files, presses **Analyse**, reads the report, asks the takeaway question, then repeats with the CSV. It does all of that twice, without and with `OPENROUTER_API_KEY`, and checks every figure against `samples/expected.json`.

| Result | Meaning |
| --- | --- |
| `PASS` | As the demo script says. |
| `FAIL` | Broken. File it (below) and fix before the freeze. |
| `WARN` | Works, but worth a look: slow analysis, the LLM failed and templates were used, or the LLM text didn't quote a figure. |
| `NOT BUILT` | The task is still a stub; it already has an issue. |

It ends with `Demo ready.` (exit code 0) only when nothing failed and nothing is unbuilt. `--offline` skips the run with a key. `pytest` also covers the script (`tests/test_demo_check.py`), so it keeps working as the app changes.

**File each problem** as a `needs-triage` issue. The script prints a ready `gh issue create` command for every `FAIL` and `WARN`; add what you saw on screen.

The automated run can't judge how the page *looks*. Do one manual pass too: `streamlit run app.py`, upload the three files from `samples/`, and check that the report is readable on the projector resolution.

## 3. The live demo (about 3 minutes)

Upload from a folder holding only the four sample files, so the file picker shows nothing personal.

| Step | Do | Say (short) | Check on screen |
| --- | --- | --- | --- |
| 1 | Upload the bank statement PDF, payslip PDF and loan XLSX; press **Analyse**. | "Three ordinary documents: a bank statement, a payslip and a loan statement." | Spinner for a few seconds |
| 2 | Point at the document list. | "WealthWise reads all three and flags anything it can't read." | "3 documents read", no warnings |
| 3 | Point at the score. | "One number: 67 out of 100, fair. Here's why." | **67 (fair)** and its 4 components |
| 4 | Walk through the three recommendations. | "Halve takeaway and free €107.56 a month. Put half of the freed money on the card first: debt-free 8 months earlier, €513.39 less interest." | €107.56, 8 months, €513.39 |
| 5 | Type *How much do I spend on takeaway?* | "And you can just ask." | An answer citing about €215/month |
| 6 | (If time) Upload the CSV instead of the PDF. | "Same data as a CSV: identical numbers, because the maths is code, not AI." | Same figures |

## 4. If something goes wrong on stage

| Problem | Do this | Say |
| --- | --- | --- |
| No internet / OpenRouter down | Carry on. The report still works; explanations use template text. Skip step 5. | "All the numbers are calculated on this laptop. The AI only writes the words." |
| LLM slow (spinner > 10 s) | Stop the app (Ctrl+C), comment out the key in `.env`, `streamlit run app.py`, re-upload. | Same as above. |
| Upload dialog is fiddly | Press **Use sample documents** instead. | — |
| Ask WealthWise gives a poor answer | Move on; don't retry live. | "It only answers from your own data, and says so when it can't tell." |
| App crashes or freezes | Ctrl+C, `streamlit run app.py`, use **Use sample documents**. | — |
| Laptop fails | Open the backup recording (below) on any machine. | — |

**Backup recording:** after the final dry run, record one clean run of the demo (Win+G, Game Bar) and keep it on a USB stick and in the team chat.

## 5. Stage the laptop (11:30)

- [ ] `git status` clean, on `main` at the frozen commit; `python scripts/demo_check.py` says `Demo ready.`
- [ ] `.env` holds the key; Chroma model already downloaded (step 1)
- [ ] App running (`streamlit run app.py`) in one browser tab, slides in another; browser zoom set for the projector
- [ ] Sample-files folder open; notifications, chat apps and updates off; laptop on mains power
- [ ] Backup recording on the USB stick

## 6. Rehearsal log

Rehearse the full pitch plus demo twice after the freeze. Aim for the slot time, with a minute spare for questions.

| Run | Time taken | What went wrong | Fixed? |
| --- | --- | --- | --- |
| Dry run (08:00) | | | |
| Rehearsal 1 | | | |
| Rehearsal 2 | | | |
