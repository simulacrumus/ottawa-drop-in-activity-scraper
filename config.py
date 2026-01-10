# =============================================================================
#  Project:   City of Ottawa Drop-in Activity Scraper
#  File:      config.py
#  Author:    Emrah Kinay
#  Created:   2025-09-12
#  License:   MIT
#
#  Description:
#      Configurations
# =============================================================================

import os
import logging
from deepseek import DeepSeekClient
from open_ai import OpenAIClient

# KEYS
UPLOAD_API_KEY=os.environ.get("UPLOAD_API_KEY")
UPLOAD_API_URL=os.environ.get("UPLOAD_API_URL")
DEEPSEEK_API_KEY=os.environ.get("DEEPSEEK_API_KEY")
OPEN_AI_API_KEY=os.environ.get("OPEN_AI_API_KEY") or os.environ.get("OPENAI_API_KEY")

if OPEN_AI_API_KEY:
    LLM_API_CLIENT=OpenAIClient( api_key = OPEN_AI_API_KEY )
else:
    raise ValueError(
        "OPEN_AI_API_KEY or OPENAI_API_KEY environment variable must be set. "
        "Please set it in your GitHub Actions secrets or environment variables."
    )

# URLS
FACILITIES_LIST_URL='https://ottawa.ca/en/recreation-and-parks/recreation-facilities/place-listing'
CITY_OF_OTTAWA_BASE_URL='https://ottawa.ca'

# FILES
SCHEDULES_FILENAME='schedules.json'
INVALID_SCHEDULES_FILENAME='invalid_schedules.json'
SCHEDULE_HTML_TABLE_CACHE_FILENAME='schedules_html_table_cache.json'

# CONSTANTS
MAX_SCHEDULES_UPLOAD_BATCH_SIZE=100
MAX_SCHEDULES_HTML_TABLE_LENGTH=10_000

# LOGGING
LOG_LEVEL=logging.INFO