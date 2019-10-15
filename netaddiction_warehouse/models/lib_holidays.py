# -*- coding: utf-8 -*-
from datetime import date, timedelta, datetime

class LibHolidays():

    HOLIDAYS = (
       (1, 1), (6, 1),
       (14, 2),
       (25, 4),
       (1, 5),
       (2, 6),
       (15, 8),
       (1, 11),
       (8, 12), (25, 12), (26, 12),
    )

    def is_national_holiday(self,day):
       """
       Considera festivi i giorni presenti in HOLIDAYS e la Pasquetta
       """
       def get_easter(year):
           a = year % 19
           b = year // 100
           c = year % 100
           d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
           e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
           f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
           month = f // 31
           day = f % 31 + 1
           return date(year, month, day)

       easter = get_easter(day.year)
       easter_monday = easter + timedelta(days=1)

       return (
           (day.day, day.month) in self.HOLIDAYS or  # Festa nazionale fissa
           day == easter_monday  # Pasquetta
       )


    def is_saturday(self,day):
       return day.weekday() == 5


    def is_sunday(self,day):
       return day.weekday() == 6


    def is_weekend(self,day):
       return self.is_saturday(day) or self.is_sunday(day)


    def is_holiday(self,day):
       """
       Considera festivi i giorni presenti in HOLIDAYS, la Pasquetta,
       i sabati e le domeniche.
       """
       return self.is_weekend(day) or self.is_national_holiday(day)