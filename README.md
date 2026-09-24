# Credit Card Analyzer

Fetches your HDFC/ICICI/Axis credit card statements from Gmail, extracts
transactions, categorizes spend, and shows a local dashboard.

## Setup

1. **Google Cloud (free, no billing needed)**
   - Go to console.cloud.google.com, create a project.
   - Enable the **Gmail API**.
   - Configure the OAuth consent screen: type **External**, publishing
     status **Testing**, add your own Gmail address as a test user.
   - Create credentials: **OAuth client ID**, application type **Desktop app**.
   - Download the JSON and save it as `credentials/credentials.json`.

2. **Python environment**
   ```
   cd credit-card-analyzer
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Secrets**
   - Copy `.env.example` to `.env`.
   - Fill in `HDFC_PDF_PASSWORD`, `ICICI_PDF_PASSWORD`, `AXIS_PDF_PASSWORD`
     (the password that unlocks each bank's statement PDF — check one real
     statement email, the bank states its rule there).
   - Fill in `ANTHROPIC_API_KEY` from console.anthropic.com.

4. **First run**
   ```
   python src/main.py
   ```
   This opens a browser window once for Gmail login/consent, then fetches
   statement PDFs, unlocks them, extracts transactions via Claude, and
   stores them in `data/transactions.sqlite3`. Safe to re-run — duplicates
   are skipped automatically.

5. **Dashboard**
   ```
   streamlit run src/dashboard.py
   ```

## Notes

- `credentials/`, `.env`, and downloaded PDFs are all gitignored — nothing
  sensitive should ever get committed.
- Gmail search queries per bank live in `src/config.py` (`BANKS` dict) —
  adjust the sender address there if a real statement email doesn't match.
- To automate monthly runs, schedule `python src/main.py` via Windows Task
  Scheduler.
