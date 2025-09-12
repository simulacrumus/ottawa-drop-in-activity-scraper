# =============================================================================
#  Project:   City of Ottawa Drop-in Activity Scraper
#  File:      uploader.py
#  Author:    Emrah Kinay
#  Created:   2025-09-12
#  License:   MIT
#
#  Description:
#      Upload schedule objects from json file in batches to API URL
# =============================================================================

import os
import logging
import json
import aiohttp
import asyncio
import time
from config import *
from model import ScheduleData
from utility import format_duration

logger = logging.getLogger(__name__)

class Uploader:
    def __init__(
        self,
        upload_api_url: str,
        upload_api_key: str,
        schedules_filename: str,
        max_schedules_upload_batch_size: int
    ):
        self.upload_api_url = upload_api_url
        self.upload_api_key = upload_api_key
        self.schedules_filename = schedules_filename
        self.max_schedules_upload_batch_size = max_schedules_upload_batch_size
        self.schedules:list[ScheduleData] = []
        self.num_schedules_saved:int = 0
        self.save_errors: set[str] = set()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def _save_schedules(self):
        try:
            # Upload schedules in batches of 100
            total_schedules = len(self.schedules)
            for i in range(0, total_schedules, self.max_schedules_upload_batch_size):
                batch = self.schedules[i:i+self.max_schedules_upload_batch_size]
                payload = {"schedules": batch}
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Content-Type": "application/json",
                        "x-api-key": self.upload_api_key
                    }
                    async with session.post(self.upload_api_url, json=payload, headers=headers) as resp:
                        response_json = await resp.json()

                        if resp.status in (200,201):
                            self.num_schedules_saved += response_json.get('successful')                                

                            response_errors = response_json.get('errors')
                            if response_errors:
                                if isinstance(response_errors, (list, set)):
                                    self.save_errors.update(response_errors)
                                else:
                                    self.save_errors.add(str(response_errors))

                            logger.info(f"Saved {response_json.get('successful')} schedules")
                        elif resp.status >= 500:
                            logger.error(f'Server error: {await resp.text()}')
                        else:
                            error_msg = f"Failed to save schedules: {resp.status} {await resp.text()}"
                            logger.error(error_msg)
        except Exception as e:
            logger.error('Error while saving schedules')
            logger.error(e)

    async def _load_schedules_from_file(self):
        if os.path.exists(self.schedules_filename):
            try:
                with open(self.schedules_filename, "r", encoding="utf-8") as f:
                    self.schedules = json.load(f)
                logger.info(f"Loaded schedules from {self.schedules_filename}")
            except Exception as e:
                logger.error(f"Failed to load schedules: {e}")
                self.schedules = []
        else:
            self.schedules = []

    def _log_results(self):
        results = {
            "Schedules loaded": len(self.schedules),
            "Schedules saved": self.num_schedules_saved,
            "Errors": list(self.save_errors),
        }
        results = json.dumps(results, indent=2)
        logger.info(results)

    async def run(self):
        # Load the file with structured schedules
        await self._load_schedules_from_file()
        # Upload to the server
        await self._save_schedules()
        # Log results
        self._log_results()

async def main():
    start_time = time.time()
    logging.basicConfig(level=LOG_LEVEL)

    config = {
        'upload_api_url':UPLOAD_API_URL,
        'upload_api_key':UPLOAD_API_KEY,
        'schedules_filename':SCHEDULES_FILENAME,
        'max_schedules_upload_batch_size':MAX_SCHEDULES_UPLOAD_BATCH_SIZE
    }

    async with Uploader(**config) as uploader:
        await uploader.run()

    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Execution duration: {format_duration(duration)}")

if __name__ == "__main__":
    asyncio.run(main())


