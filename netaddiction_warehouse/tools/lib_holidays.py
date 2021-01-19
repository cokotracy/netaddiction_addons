"""
If ``workalendar`` module is not available, ``LibHolidays`` is defined as the
old v9.0 class.
Otherwise, it is defined as a subclass of ``Italy``, plus a few overrides that
allow calling the methods with the same names of the old version.
"""


from logging import getLogger

logger = getLogger(__name__)

try:
    from workalendar.core import SAT, SUN
    from workalendar.europe import Italy

    class LibHolidays(Italy):

        def is_holiday(self, day, *a, **k):
            """ Use weekend days as holidays """
            return self.is_weekend(day) or super().is_holiday(day, *a, **k)

        @staticmethod
        def is_saturday(day):
            return day.weekday() == SAT

        @staticmethod
        def is_sunday(day):
            return day.weekday() == SUN

        def is_weekend(self, day):
            return self.is_saturday(day) or self.is_sunday(day)


except ImportError:
    logger.warning("Could not import module 'workalendar'!")
    Italy = None

    from datetime import date, timedelta

    class LibHolidays:

        HOLIDAYS = (
            # day, month
            (1, 1),
            (6, 1),
            (14, 2),
            (25, 4),
            (1, 5),
            (2, 6),
            (15, 8),
            (1, 11),
            (8, 12),
            (25, 12),
            (26, 12),
        )

        def is_holiday(self, day, *a, **k):
            """
            Considera festivi i giorni presenti in HOLIDAYS, la Pasquetta,
            i sabati e le domeniche.
            NB: parametri *a e **k aggiunti per compatibilità con
            l'omonimo metodo della classe ``Italy`` di ``workalendar``
            """
            return self.is_weekend(day) or self.is_national_holiday(day)

        def is_national_holiday(self, day):
            """
            Considera festivi i giorni presenti in HOLIDAYS e la Pasquetta
            """

            def get_easter(_year):
                a = _year % 19
                b = _year // 100
                c = _year % 100
                d = 19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15
                e = (32 + 2 * (b % 4) + 2 * (c // 4) - d % 30 - (c % 4)) % 7
                f = d % 30 + e - 7 * ((a + 11 * d % 30 + 22 * e) // 451) + 114
                return date(_year, f // 31, f % 31 + 1)

            return (day.day, day.month) in self.HOLIDAYS \
                or day == get_easter(day.year) + timedelta(days=1)

        @staticmethod
        def is_saturday(day):
            return day.weekday() == 5

        @staticmethod
        def is_sunday(day):
            return day.weekday() == 6

        def is_weekend(self, day):
            return self.is_saturday(day) or self.is_sunday(day)


# Create an instance here to be used instead of always creating a new instance
# when an holiday check must be performed
lib_holidays = LibHolidays()


# Define ``is_holiday`` method so that we can import it and use it directly
# from other files
def is_holiday(day, *a, **k):
    return lib_holidays.is_holiday(day, *a, **k)
