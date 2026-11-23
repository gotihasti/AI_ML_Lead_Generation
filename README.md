# AI/ML Lead Generation & Opportunity Scoring System

Find local businesses, clean their data, and rank them by how much they could benefit from digital services such as a website, better contact details, or digital marketing.

The system pulls businesses from OpenStreetMap, standardizes and de-duplicates them, stores them in SQLite, and assigns each an **opportunity score (0-100)** with a plain-language explanation. A dashboard lets you search, add, edit, and prioritize leads.

Screenshots
Dashboard

<img width="1600" height="1011" alt="dashboard" src="https://github.com/user-attachments/assets/5ffacebd-77f7-4f66-8850-fe6983aae0b7" />


Scored and prioritized leads


<img width="1600" height="1060" alt="lead-table" src="https://github.com/user-attachments/assets/5094db20-693a-440c-b18e-8d015f672abd" />


Editing a lead

<img width="1600" height="1060" alt="edit-lead" src="https://github.com/user-attachments/assets/82da9a6c-ff8a-4fdf-9cba-6546c32246f4" />

API documentation

<img width="1600" height="1059" alt="api-docs" src="https://github.com/user-attachments/assets/fcf881db-6843-4061-b588-a2167ff78ce4" />


## Features

- **Lead discovery**: search by industry and location (India) using the OpenStreetMap Nominatim API
- **Data cleaning**: normalizes names, emails, phone numbers, and websites
- **De-duplication**: case-insensitive matching on name and location, both while searching and when saving
- **Opportunity scoring**: transparent rule-based scoring with a High / Medium / Low priority level and a list of reasons
- **Lead management**: full CRUD, filtering, search by name, and a status field
- **Analytics**: totals, leads by industry, leads by priority, and average score
- **Dashboard**: vanilla HTML/CSS/JS front end
- **ML scorer (experimental)**: a scikit-learn logistic regression module that starts from a domain prior and can learn from real outcomes. It is not yet connected to the API (see below).

## Tech stack

Python 3.12, FastAPI, SQLAlchemy, SQLite, Pydantic, Requests, scikit-learn, joblib, pytest, and a vanilla HTML/CSS/JS front end.

## Project structure

```
AI_ML_Lead_Generation/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app and CORS
│       ├── api/leads.py         # lead and search endpoints
│       ├── database/connection.py
│       ├── models/lead.py       # SQLAlchemy model
│       ├── schemas/lead.py      # Pydantic schemas
│       ├── services/
│       │   ├── lead_source.py       # OpenStreetMap search
│       │   ├── data_cleaner.py      # cleaning functions
│       │   └── opportunity_scorer.py # rule-based scoring
│       └── ml/lead_model.py     # experimental ML scorer
├── frontend/                    # index.html, script.js, style.css
├── test/                        # pytest tests
├── data/                        # SQLite DB (git-ignored)
└── requirements.txt
```

## Getting started

### Installation

```bash
git clone https://github.com/<your-username>/AI_ML_Lead_Generation.git
cd AI_ML_Lead_Generation

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
mkdir -p data                    # the SQLite database is created here
```

### Run the backend

Run this from the project root:

```bash
uvicorn backend.app.main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs

### Run the dashboard

Serve the `frontend/` folder on port 5500, for example with the VS Code **Live Server** extension, or:

```bash
cd frontend
python -m http.server 5500
```

Then open http://127.0.0.1:5500. The backend allows CORS from port 5500 only, and the dashboard calls the API at `http://127.0.0.1:8000`.

### Run the tests

```bash
python -m pytest
```

## Typical workflow

1. **Search and save** leads: `POST /search/leads/save?industry=restaurant&location=Surat`
2. **Score** all saved leads: `POST /leads/score`
3. **Review** the best opportunities: `GET /leads/prioritized`

Supported industries: `restaurant`, `cafe`, `hotel`, `hospital`, `pharmacy`, `school`.

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/search/leads?industry=&location=` | Preview businesses without saving |
| POST | `/search/leads/save?industry=&location=` | Search, clean, de-duplicate, and save |
| POST | `/leads/` | Create a lead manually |
| GET | `/leads/` | List all leads |
| GET | `/leads/{id}` | Get one lead |
| PUT | `/leads/{id}` | Partially update a lead |
| DELETE | `/leads/{id}` | Delete a lead |
| GET | `/leads/filter?industry=&location=&skip=&limit=` | Filter with pagination |
| GET | `/leads/search?business_name=` | Search by name |
| POST | `/leads/score` | Score all saved leads |
| GET | `/leads/prioritized` | Scored leads, highest first |
| GET | `/leads/priority/{High\|Medium\|Low}` | Leads by priority level |
| GET | `/leads/stats` | Summary statistics |

## How scoring works

The score measures **opportunity** for outreach. A business with more gaps gets a higher score.

| Signal | Points |
|--------|--------|
| No website | +25 |
| No email | +10 |
| No phone | +10 |
| No description | +5 |
| Restaurant, cafe, or hotel | +15 |
| Any other industry | +5 |

Scores are capped at 100. A score of **60 or more is High**, **30 to 59 is Medium**, and anything below 30 is Low. Each lead also stores a readable explanation, such as "Website development, Email contact information missing".

### ML scoring module (experimental)

`backend/app/ml/lead_model.py` trains a logistic regression on the same signals. With no real outcomes yet, it starts from synthetic data labelled by a documented domain prior. Once at least 30 leads have an outcome (`qualified` or `converted` versus `contacted`), real labels are mixed in with a higher weight and gradually take over. It also reports the top contributing factors for each prediction.

This module is included but not yet exposed through an endpoint, so the API currently uses the rule-based scorer.

## Limitations and roadmap

- Lead data comes from OpenStreetMap, so many businesses have no website, email, or phone listed. This inflates opportunity scores. Treat results as leads to investigate, not verified facts.
- Nominatim has a strict usage policy (about one request per second and a descriptive User-Agent), so this is suited to small-scale use
- Search is limited to India and to six industries
- No authentication, so it is intended for local use

Planned:

- [ ] Expose the ML scorer through the API and add a retrain endpoint
- [ ] Additional lead sources (for example Google Places or web enrichment)
- [ ] Export leads to CSV
- [ ] Authentication and PostgreSQL support
- [ ] Expand test coverage to the API layer

