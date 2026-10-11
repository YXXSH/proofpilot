# ProofPilot | Agentic AI Case Assessment Platform

**An AI-powered platform that helps companies evaluate customer claims through evidence analysis, policy compliance, and intelligent resolution recommendations.**

ProofPilot combines multi-agent AI, document processing, and rule-based assessment to help companies make structured, evidence-informed decisions while keeping the final decision under human control.

## Key Features

* **Evidence Analysis:** Identifies supporting evidence, missing information, and conflicting claims.
* **Multi-Agent AI:** Five specialized agents analyze customer requests, evidence, policies, resolutions, and assessment quality.
* **Policy Compliance:** Evaluates claims against company-specific policies.
* **Case Strength Scoring:** Generates a deterministic score based on evidence coverage, quality, consistency, and missing information.
* **AI Recommendations:** Suggests approval, additional evidence collection, or rejection/escalation.
* **Human-in-the-Loop:** Allows company reviewers to record the final decision.
* **Case Management:** Stores case details, evidence, analysis results, and decision records.

## System Architecture

```text
Customer Case
     ↓
Rule-Based Analysis
     ↓
Evidence Processing
     ↓
Query Analyst
     ↓
Evidence Analyst
     ↓
Policy Analyst
     ↓
Resolution Analyst
     ↓
Reviewer Agent
     ↓
Case Strength & Recommendation
     ↓
Company Decision
```

## Technology Stack

* **Language:** Python
* **Frontend:** Streamlit
* **AI:** Generative AI API
* **Architecture:** Multi-Agent AI Workflow
* **Data Storage:** JSON and local file storage
* **Version Control:** Git and GitHub
* **Deployment:** Streamlit Community Cloud

## Example Use Case

For a damaged-product refund claim, ProofPilot evaluates the invoice, examines available damage evidence, checks the company's return policy, and recommends an appropriate action.

The company reviewer can then approve the claim, request additional evidence, or reject/escalate it.

## Run Locally

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the application:

```bash
streamlit run app.py
```

Configure any required AI API credentials securely before running the AI-powered workflow.

## Future Improvements

* Persistent database and evidence storage.
* Authentication and role-based access control.
* Automated agent evaluation and testing.
* Production-grade monitoring and audit trails.

**Core Principle:** AI recommends. The company decides.

