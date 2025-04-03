import calendar
import re

from abc import ABC, abstractmethod
from datetime import datetime


class DatePreparator(ABC):
    @abstractmethod
    def can_handle(self, period_begin, period_end):
        pass

    @abstractmethod
    def prepare(self, period_begin, period_end):
        pass

class ValidateFormat(DatePreparator):
    """ 1. if provided date contains any other signs than numbers and '-', or if it has less than 7 characters """
    def can_handle(self, period_begin, period_end):
        return re.search(r'[^0-9\-]', period_begin) or re.search(r'[^0-9\-]', period_end) or \
               len(period_begin) < 7 or len(period_end) < 7

    def prepare(self, period_begin, period_end):
        raise ValueError("Invalid date format. Expected format is YYYY-MM-DD or YYYY-MM")

class PrepareWholeMonthDate(DatePreparator):
    """ 2. if someone provided the same start and end date without any day, we should show whole month report """
    def can_handle(self, period_begin, period_end):
        return len(period_begin) == len(period_end) == 7 and period_begin == period_end

    def prepare(self, period_begin, period_end):
        year = int(period_end[:4])
        month = int(period_end[5:7])
        last_day = calendar.monthrange(year, month)[1]
        return f"{period_begin}-01", f"{period_end}-{last_day:02d}"

class AddDefaultDayToMonth(DatePreparator):
    """ 3. if someone provided different months of year in proper format YYYY-MM, we can add '-01' as day, to make it valid """
    def can_handle(self, period_begin, period_end):
        return len(period_begin) == len(period_end) == 7

    def prepare(self, period_begin, period_end):
        return f"{period_begin}-01", f"{period_end}-01"

class ValidateDateOrder(DatePreparator):
    """4. At this point, we assume date strings are complete (YYYY-MM-DD), check if period_end is not before period_begin"""
    def can_handle(self, period_begin, period_end):
        return period_begin > period_end

    def prepare(self, period_begin, period_end):
        raise ValueError("Start date (period_begin) cannot be after end date (period_end).")

class FinalParser(DatePreparator):
    """ 5. Always applies at the end, to convert the date strings to datetime.date objects """
    def can_handle(self, period_begin, period_end):
        return True

    def prepare(self, period_begin, period_end):
        try:
            period_begin = datetime.strptime(period_begin, "%Y-%m-%d").date()
            period_end = datetime.strptime(period_end, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Check if year/month/day exists. Expected format is YYYY-MM-DD.")
        return period_begin, period_end

