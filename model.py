# =============================================================================
#  Project:   City of Ottawa Drop-in Activity Scraper
#  File:      model.py
#  Author:    Emrah Kinay
#  Created:   2025-09-12
#  License:   MIT
#
#  Description:
#      Model classes
#       - ScheduleData: Data class for schedule objects
# =============================================================================

from dataclasses import dataclass

@dataclass
class ScheduleData:
    facility: str
    activity: str
    start_time: str
    end_time: str
    period_start_date: str
    period_end_date: str
    day_of_week: int

    def to_dict(self) -> dict:
        return {
            'facility': self.facility,
            'activity': self.activity,
            'startTime': self.start_time,
            'endTime': self.end_time,
            'periodStartDate': self.period_start_date,
            'periodEndDate': self.period_end_date,
            'dayOfWeek': self.day_of_week
        }