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

# KEYS
UPLOAD_API_KEY=os.environ.get("UPLOAD_API_KEY")
UPLOAD_API_URL=os.environ.get("UPLOAD_API_URL")
DEEPSEEK_API_KEY=os.environ.get("DEEPSEEK_API_KEY")

# LLM
LLM_API_CLIENT=DeepSeekClient( api_key = DEEPSEEK_API_KEY )

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