# ProofPilot

ProofPilot is a company-side case-assessment dashboard. It helps teams review consumer cases, evidence, company policy, multi-agent findings, and the final human company decision.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Add your real GEMINI_API_KEY to .env
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Create a **private** GitHub repository and push this folder. Do not include `.env`, `data/cases.json`, or `data/evidence/`.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), select **Create app**, choose the repository and branch, and set the entrypoint to `app.py`.
3. Under **Advanced settings → Secrets**, add:

   ```toml
   GEMINI_API_KEY = "your_key_here"
   ```

4. Deploy and test the generated `streamlit.app` URL with sample data.

## Important deployment note

This starter uses local files (`data/cases.json` and `data/evidence/`) for storage. That is suitable for local development and short demos only. Before using real customer data in production, move case records and evidence to durable, access-controlled storage and add user authentication.
