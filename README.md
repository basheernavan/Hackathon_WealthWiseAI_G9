# WealthWise

Personalised financial guidance from your own documents. Upload a bank statement, payslip and loan statement, and WealthWise calculates a Financial Health Score and gives spending, debt and savings recommendations. Built with Streamlit, LangGraph, ChromaDB and an LLM via OpenRouter.

> Hackathon pilot. Not financial advice.

## Quick start (Windows)

```powershell
git clone https://github.com/basheernavan/Hackathon_WealthWiseAI_G9.git
cd Hackathon_WealthWiseAI_G9
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # add your OPENROUTER_API_KEY (optional)
streamlit run app.py
```

Try it with the fictional files in [samples/](samples/).

## For developers

Start with [docs/COLLABORATION.md](docs/COLLABORATION.md): setup, picking a task, handing over and merging. Then [CONTEXT.md](CONTEXT.md) and [docs/specs/00-overview.md](docs/specs/00-overview.md). Background material (pitch, plan, budget) is in [documents/](documents/).
