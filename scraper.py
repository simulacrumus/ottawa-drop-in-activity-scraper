# =============================================================================
#  Project:   City of Ottawa Drop-in Activity Scraper
#  File:      scraper.py
#  Author:    Emrah Kinay
#  Created:   2025-09-12
#  License:   MIT
#
#  Description:
#      Scrape all recreational drop-in activities from City of Ottawa website
# =============================================================================

import asyncio
import logging
import re
from bs4 import BeautifulSoup
from browser import BrowserManager
from model import ScheduleData
from config import *
from utility import *
import hashlib
import datetime
import time
import os
import json

logger = logging.getLogger(__name__)

class Scraper:
    def __init__(
        self,
        facilities_list_url: str,
        city_of_ottawa_base_url: str,
        schedules_html_table_cache_filename: str,
        schedules_filename: str,
        invalid_schedules_filename: str,
        llm_api_client,
    ):
        self.facilities_list_url = facilities_list_url
        self.city_of_ottawa_base_url = city_of_ottawa_base_url
        self.schedules_html_table_cache_filename = schedules_html_table_cache_filename
        self.schedules_filename = schedules_filename
        self.invalid_schedules_filename = invalid_schedules_filename
        
        self.browser:BrowserManager = BrowserManager()
        self.llm_api_client = llm_api_client

        self.facility_url_list:str = []
        self.schedules_html_table_cache:dict = {}
        self.temp_schedules_html_table_cache:dict = {}
        self.valid_schedules:list = []
        self.invalid_schedules:list = []

        self.num_facilities_with_scheds:int = 0
        self.num_schedules_created:int = 0
        self.num_valid_schedules:int = 0
        self.num_llm_api_calls:int = 0

    async def __aenter__(self):
        # Load HTML table cache to reduce LLM API calls
        await self._load_html_table_cache()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.browser.cleanup()

    async def _load_html_table_cache(self):
        if os.path.exists(self.schedules_html_table_cache_filename):
            try:
                with open(self.schedules_html_table_cache_filename, "r", encoding="utf-8") as f:
                    self.html_table_cache = json.load(f)
                logger.info(f"Loaded HTML table cache from {self.schedules_html_table_cache_filename}")
            except Exception as e:
                logger.error(f"Failed to load HTML table cache: {e}")
                self.html_table_cache = {}
        else:
            self.html_table_cache = {}

    async def _save_html_table_cache(self):
        if self.temp_schedules_html_table_cache:
            try:
                with open(self.schedules_html_table_cache_filename, "w", encoding="utf-8") as f:
                    json.dump(self.temp_schedules_html_table_cache, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved HTML table cache to {self.schedules_html_table_cache_filename}")
            except Exception as e:
                logger.error(f"Failed to save HTML table cache: {e}")
    
    async def _save_schedules(self):
        if self.valid_schedules:
            try:
                schedule_dicts = [schedule.to_dict() for schedule in self.valid_schedules]
                
                with open(self.schedules_filename, "w", encoding="utf-8") as f:
                    json.dump(schedule_dicts, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved {len(schedule_dicts)} schedules to {self.schedules_filename}")
            except Exception as e:
                logger.error(f"Failed to save schedules: {e}")

        if self.invalid_schedules:
            try:
                with open(self.invalid_schedules_filename, "w", encoding="utf-8") as f:
                    json.dump(self.invalid_schedules, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved schedules to {self.invalid_schedules_filename}")
            except Exception as e:
                logger.error(f"Failed to save invalid schedules: {e}")
    

    async def run(self):
        # Start scraping the page of list of facilities
        facility_list_soup:BeautifulSoup = await self._scrape_url(self.facilities_list_url)

        # Facilities are listed in a paginated webpage, first need to discover total number of pages
        num_of_pages = await self._discover_num_of_facility_list_pages(facility_list_soup)

        # Scrape facilities
        # Visit each page to scrape all facilities. Running in parallel fails because of the rate limit
        for page_num in range(0, num_of_pages - 1):
            logger.info(f"Scraping facility list page {page_num + 1} of {num_of_pages - 1}")
            facility_list_page_soup = await self._scrape_url(f"{self.facilities_list_url}?page={page_num}")
            # Add list of facilities to the main list
            facility_url_list_for_page = await self._process_facility_list_page(facility_list_page_soup)
            self.facility_url_list.extend(facility_url_list_for_page)

        # Scrape schedules
        # Visit each facility and process schedules. Running in parallel fails because of the rate limit
        for facility_url in self.facility_url_list:
            logger.info(f"Processing facility URL: {facility_url}")
            soup = await self._scrape_url(facility_url)
            await self._process_facility_page_content(soup)

        # Save schedules
        await self._save_schedules()
        # Save cache
        await self._save_html_table_cache()
        # Log results
        self._log_results()
        

    def _log_results(self):
        results = {
            "Number of LLM API calls": self.num_llm_api_calls,
            "Facilities with schedules": self.num_facilities_with_scheds,
            "Schedules created": self.num_schedules_created,
            "Valid schedules": len(self.valid_schedules),
            "Invalid schedules": len(self.invalid_schedules)
        }
        results = json.dumps(results, indent=2)
        logger.info(results)

    async def _scrape_url(self, url: str) -> BeautifulSoup:
        content = await self.browser.get_content(url)
        if not content:
            logger.info(f"No HTML found for {url}")
            return None
        soup = BeautifulSoup(content, 'lxml')
        return soup


    async def _discover_num_of_facility_list_pages(self, soup:BeautifulSoup) -> int:
        pagination = soup.find("ul", class_="pager__items")
        
        if not pagination:
            logger.error(f"No pagination found for facility list")
            soup.decompose()
            return 0
            
        total_pages = len(pagination.find_all("li"))
        soup.decompose()
        
        logger.info(f"Discovered {total_pages - 1} total pages")
        return max(0, total_pages)


    async def _process_facility_list_page(self, soup:BeautifulSoup) -> list:
        tbody = soup.find("tbody")
        urls = []
        if tbody:
            for row in tbody.find_all("tr"):
                    
                link = row.find("a")
                if not link:
                    continue
                    
                href = link.get("href")
                if not href:
                    continue
                    
                full_url = href if href.startswith('http') else f"https://ottawa.ca{href}"
                    
                urls.append(full_url)
                    
        soup.decompose()
        return urls


    async def _process_facility_page_content(self, soup:BeautifulSoup):
        try:
            drop_in_buttons = soup.find_all('button', string=re.compile(r'drop-in', re.I))
            if not drop_in_buttons:
                soup.decompose()
                return

            facility_title = ''
            title_element = soup.find('h1', class_='page-title')
            if title_element:
                span_element = title_element.find('span', class_='field--name-title')
                if span_element:
                    facility_title = clean_text(span_element.get_text(strip=True))
            # If title is not available, skip to next facility
            if not facility_title:
                return

            tables = soup.find_all('table')
            # Process tables in parallel
            if tables:
                logger.debug(f"Processing {len(tables)} tables for {facility_title}")
                self.num_facilities_with_scheds += 1
                table_tasks = [self._process_html_table_with_llm(table, facility_title) for table in tables]
                await asyncio.gather(*table_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error processing facility: {e}")
        finally:
            if 'soup' in locals():
                soup.decompose()

    async def _process_html_table_with_llm(self, html_table_soup: BeautifulSoup, facility_title: str):
        try:
            table_html = str(html_table_soup)
            table_html_clean = clean_html_for_llm(table_html)
            
            cache_key = hashlib.md5(table_html_clean.encode()).hexdigest()
            schedules = []
            # Check if the table is cached
            if cache_key in self.temp_schedules_html_table_cache:
                schedules = self.temp_schedules_html_table_cache[cache_key]
                logger.debug('Current table cache hit')
            elif cache_key in self.html_table_cache:
                schedules = self.html_table_cache[cache_key]
                # Copy to new cache
                self.temp_schedules_html_table_cache[cache_key] = self.html_table_cache[cache_key]
                logger.debug('Previous table cache hit')
            else:                
                message =   f"""Extract all schedule entries from this HTML table and return a JSON array.
                                Each object should have these exact fields:
                                - activity: string (remove text after * including the *)
                                - start_time: string in HH:MM format (24-hour)
                                - end_time: string in HH:MM format (24-hour)  
                                - period_start_date: string in YYYY-MM-DD format
                                - period_end_date: string in YYYY-MM-DD format
                                - day_of_week: number (1=Monday, 2=Tuesday, ..., 7=Sunday)

                                Rules:
                                - Use {datetime.datetime.now().year} for missing years
                                - Use null for unclear values
                                - Convert day names to numbers (Monday=1, Sunday=7)
                                - Return only valid JSON array, no explanations
                                - Only use ASCII characters

                                HTML table: {table_html_clean}
                            """
                
                response = await self.llm_api_client.request(message)
                self.num_llm_api_calls += 1
                schedules = robust_json_extract(response, 'list')
                
                # Cache successful responses
                if schedules:
                    self.temp_schedules_html_table_cache[cache_key] = schedules

            self.num_schedules_created += len(schedules)
            # Validate, create and update schedule objects
            for sched in schedules:
                if self._validate_schedule_data(sched):
                    schedule = ScheduleData(
                        facility=facility_title,
                        activity=sched.get('activity', '').strip(),
                        start_time=sched.get('start_time'),
                        end_time=sched.get('end_time'),
                        period_start_date=sched.get('period_start_date'),
                        period_end_date=sched.get('period_end_date'),
                        day_of_week=sched.get('day_of_week')
                    )
                    self.valid_schedules.append(schedule)
                else:
                    sched['facility'] = facility_title
                    self.invalid_schedules.append(sched)
            
        except Exception as e:
            logger.error(f"LLM processing error for table in '{facility_title}': {e}")

    def _validate_schedule_data(self, schedule: dict) -> bool:
        required_fields = ['activity', 'start_time', 'end_time', 'day_of_week']
        
        # Check required fields exist and are not None/empty
        for field in required_fields:
            value = schedule.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                logger.debug(f"Invalid schedule: missing/empty {field}")
                logger.debug(schedule)
                return False
        
        # Validate day_of_week is a number between 1-7
        day_of_week = schedule.get('day_of_week')
        if not isinstance(day_of_week, int) or not (1 <= day_of_week <= 7):
            logger.debug(f"Invalid day_of_week: {day_of_week}")
            return False
        
        # Validate time format (basic check)
        for time_field in ['start_time', 'end_time']:
            time_value = schedule.get(time_field)
            if not re.match(r'^\d{1,2}:\d{2}$', str(time_value)):
                logger.debug(f"Invalid time format: {time_field}={time_value}")
                return False
        
        return True

async def main():
    start_time = time.time()
    logging.basicConfig(level=LOG_LEVEL)

    config = {
        'facilities_list_url':FACILITIES_LIST_URL,
        'city_of_ottawa_base_url':CITY_OF_OTTAWA_BASE_URL,
        'schedules_filename':SCHEDULES_FILENAME,
        'invalid_schedules_filename':INVALID_SCHEDULES_FILENAME,
        'schedules_html_table_cache_filename':SCHEDULE_HTML_TABLE_CACHE_FILENAME,
        'llm_api_client':LLM_API_CLIENT
    }

    async with Scraper(**config) as scraper:
        await scraper.run()

    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Execution duration: {format_duration(duration)}")

if __name__ == "__main__":
    asyncio.run(main())