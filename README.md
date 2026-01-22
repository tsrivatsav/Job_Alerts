# Job Scraper on AWS (Lambda + DynamoDB + EventBridge + SNS)

A lightweight job monitoring system that:
- Scrapes company job boards on a schedule (AWS EventBridge)
- Stores job postings in DynamoDB (dedupes by URL)
- Sends notifications for *new* postings via SNS
- Lets you manage which companies are tracked without redeploying everything

This repo is designed to be developed on **Windows** and deployed to **AWS (Linux)**. Some scripts (packaging/deployment) may need tweaks if your environment differs.

---

## Architecture

**EventBridge (schedule)** → **Orchestrator Lambda** → triggers **Scraper Lambda** per company  
**Scraper Lambda** → writes new jobs to **DynamoDB** → publishes to **SNS** when new jobs are found

**DynamoDB tables**
- `job_scraper_companies` : list of companies + enabled/disabled flags
- `job_scraper_jobs` : discovered jobs (primary key = `job_url`)

---

## Repository Layout (high-level)

- `lambdas/`
  - `orchestrator`
    - `lambda_function.py`
    - `requirements.txt`
  - `scraper/`
    - `scrapers/`  
      Your scraper implementations live here.
      - `__init__.py` must expose/route to scrapers via `get_scraper()` / `has_scraper()`
    - `lambda_function.py`
    - `requirements.txt`  
      Python dependencies used by the Scraper Lambda
- `scripts/`
  - `create_eventbridge.py`  
    Creates/updates the EventBridge schedule (cron/rate)
  - `create_iam_roles.py`  
    Creates IAM roles based on AWS creds
  - `create_sns.py`  
    Creates notification system based on your configured email
  - `create_tables.py`  
    Creates DynamoDB tables 
  - `deploy_lambdas.py`  
    Builds + packages Lambdas and deploys to AWS (Windows-focused)
  - `manage_companies.py`  
    Enable/disable companies, add/remove companies, edit URLs
  - `seed_companies.py`  
    Seed initial companies into DynamoDB
  - `setup_all.py`  
    One-shot setup script to provision/deploy everything
  - `test_manual.py`  
    Tests for individual scrapers and the end-to-end orchestrator
  - `test_scrape.py`  
    Local testing for individual scrapers

---

## Prerequisites

### Local
- Python 3.9
- AWS CLI installed
- AWS CLI credentials configured (`aws configure`)
- Permissions to create/manage:
  - Lambda
  - DynamoDB
  - SNS
  - EventBridge (CloudWatch Events)
  - IAM roles/policies

---

## Quick Start (Recommended)

1. Configure AWS CLI credentials:
   ```bash
   aws configure
   ```

2. Run the full setup (provisions + deploys everything your scripts manage):
    ```bash
    python scripts/setup_all.py
    ```

3. Add/manage companies (choose one approach):

    - Seed initial company list:
        ```bash
        python scripts/seed_companies.py
        ```
    - Or manage the live companies table:
        ```bash
        python scripts/manage_companies.py
        ```

4. Implement/enable scrapers (see **Adding a New Scraper** below).

5. Test:

    - Use `scripts/test_manual.py` to test a scraper directly or the full orchestrator flow.

---

## Modifying the Schedule (EventBridge)

The schedule that triggers the orchestrator is managed via:
- `scripts/create_eventbridge.py`

Update the cron/rate expression there (examples):
- `rate(15 minutes)`
- `rate(1 hour)`
- `cron(0 */6 * * ? *)` (every 6 hours)

Then re-run:
```bash
python scripts/create_eventbridge.py
```

---

## Managing Companies

You have two ways to control which companies are scraped.

### Option A — Seed the list
Edit/add entries in:
- `scripts/seed_companies.py`

Then run:
```bash
python scripts/seed_companies.py
```

### Option B — Manage the live table (recommended once deployed)
Use:
- `scripts/manage_companies.py`

Operations include:
- Add a company (name + url)
- Enable/disable scraping for a company
- Update a company’s job board URL
- Remove a company

---

## Adding a New Scraper
### 1. Implement the scraper function
Create a new file under:
- `lambdas/scraper/scrapers/`

Expected function shape:
```python
def scrape_some_company(url: str) -> list[dict[str, str]]:
    return [{"title": "...", "url": "...", "location": "..."}]
```
**Required fields per job dict:**
- `title`
- `url`

Optional:
- `location` (recommended)

### 2. Register it in `__init__.py`
Link the company name to the scraper in:
- `lambdas/scraper/scrapers/__init__.py`

This is what makes `has_scraper(company_name)` and `get_scraper(company_name)` work.

### 3. Add dependencies (if needed)
If your new scraper introduces a new Python package, add it to:
- `lambdas/scraper/requirements.txt`

Then re-run `scripts/setup_all.py`.

---

## Testing
### Test a scraper locally
First implement your scraper in:
- `scripts/test_scrape.py`

This is the fastest way to iterate on a scraper without involving AWS triggers.

### Test end-to-end orchestration
`scripts/test_manual.py` can be used to test the AWS implementation for one company or all companies:

1. Run individual scraper lambda or entire orchestrator lambda
2. Verify jobs inserted into DynamoDB
3. Verify SNS notifications for new jobs

--- 

## Deployment Notes (Windows → AWS/Linux)
This project is authored with **Windows** in mind, but deployed to AWS where the runtime is Linux.

If your system differs, update:
- `scripts/deploy_lambdas.py`

Packaging steps (zip creation, dependency installation) can vary between:
- Windows
- WSL
- Mac/Linux

If you change how packaging is done (e.g. build in Docker), `scripts/deploy_lambdas.py` is the place to adapt.

---

## Common Gotchas
- **New scraper but no jobs/notifications**
    - Ensure the scraper is registered in `scrapers/__init__.py`
    - Ensure the company is enabled in the companies table
- **Dependency import errors in Lambda**
    - Add the package to `lambdas/scraper/requirements.txt`
    - Redeploy
- **Schedule not running**
    - Check EventBridge rule + target permissions
    - Re-run `scripts/create_eventbridge.py`
- **Duplicate jobs**
    - Deduping is by `job_url`. Ensure your scraper outputs stable canonical URLs.

--- 

## Suggested Workflow for Adding a Company
1. Add company to DynamoDB (via `scripts/manage_companies.py` or `scripts/seed_companies.py`)
2. Develop/Test scraper locally in `scripts/test_scrape.py`
3. Implement scraper in `lambdas/scraper/scrapers/`
4. Register scraper in `lambdas/scraper/scrapers/__init__.py`
5. Add dependencies to `lambdas/scraper/requirements.txt` (if needed)
6. Deploy (`scripts/setup_all.py` or `scripts/deploy_lambdas.py`)
7. Invoke individual scraper lambda or entire orchestrator lambda (`scripts/test_manual.py`)

--- 

## Disclaimer
This project is intended for monitoring publicly available job postings. Ensure your usage complies with each site’s Terms of Service and rate-limit responsibly.