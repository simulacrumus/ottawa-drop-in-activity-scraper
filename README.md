# Scraper

A Python scraper for downloading and processing City of Ottawa drop-in activity schedules.

## Features

- Scrapes activity schedules from multiple sources
- Stores schedules in JSON
- Supports automated updates via GitHub Actions

## Requirements

- Python 3.11+
- Dependencies in `requirements.txt`

## Installation

1. Clone the repository:

```bash
git clone https://github.com/simulacrumus/ottawa-drop-in-activity-scraper.git
cd ottawa-drop-in-activity-scraper
```

2. Create a virtual environment:

```
python -m venv .venv
source .venv/bin/activate # macOS/Linux
.venv\Scripts\activate # Windows
```

3. Install dependencies:

`pip install -r requirements.txt`

4. Set your environment variables

```
export UPLOAD_API_KEY="your_upload_api_key"
export UPLOAD_API_URL="your_upload_api_url"
export DEEPSEEK_API_KEY="your_deepseek_api_key"
```

## Usage

```
python scraper.py
python uploader.py
```
