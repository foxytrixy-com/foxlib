import calendar
import logging
import os

import pytz
import re
import yaml
from datetime import datetime, timedelta
from dateutil import relativedelta
from functools import lru_cache
from future.utils import lmap
from nose.tools import assert_equal

from foxylib.tools.collections.iter_tool import IterTool
from foxylib.tools.collections.collections_tool import lchain, ListTool, l_singleton2obj
from foxylib.tools.file.file_tool import FileTool
from foxylib.tools.log.foxylib_logger import FoxylibLogger
from foxylib.tools.native.native_tool import IntegerTool
from foxylib.tools.span.span_tool import SpanTool
from foxylib.tools.string.string_tool import format_str
from foxylib.tools.version.version_tool import VersionTool

FILE_PATH = os.path.abspath(__file__)
FILE_DIR = os.path.dirname(FILE_PATH)

class DatetimeUnit:
    class Value:
        MILLISEC = "millisec"

class DatetimeTool:
    @classmethod
    def truncate(cls, dt_in, unit):
        if unit == DatetimeUnit.Value.MILLISEC:
            microsec = dt_in.microsecond // 1000 * 1000
            return datetime(dt_in.year, dt_in.month, dt_in.day, dt_in.hour, dt_in.minute, dt_in.second, microsec)

        raise NotImplementedError("Unsupported unit: {}".format(unit))


    @classmethod
    def iso8601(cls):
        return "%Y-%m-%dT%H:%M:%S"

    @classmethod
    def tz2now(cls, tz):
        return datetime.now(tz)

    @classmethod
    def now_utc(cls):
        return cls.tz2now(pytz.utc)

    @classmethod
    def astimezone(cls, dt, tz):
        return dt.astimezone(tz)

    @classmethod
    def span2iter(cls, date_span):
        d_start,d_end = date_span
        days = int((d_end - d_start).days)
        for n in range(days):
            yield d_start + timedelta(n)


    @classmethod
    def datetime_pair2days_difference(cls, dt_pair):
        dt_from, dt_to = dt_pair
        assert_equal(dt_from.tzinfo, dt_to.tzinfo)

        date_from = dt_from.date()
        date_to = dt_to.date()

        return (date_to-date_from).days

    # @classmethod
    # def datetime2days_from_now(cls, datetime_in):
    #
    #     dt_from, dt_to = dt_pair
    #     assert_equal(dt_from.tzinfo, dt_to.tzinfo)
    #
    #     date_from = dt_from.date()
    #     date_to = dt_to.date()
    #
    #     return (date_to - date_from).days





class DayOfWeek:
    MONDAY = 0
    SUNDAY = 6

    @classmethod
    def add_n(cls, dow, n):
        return (dow + n) % 7

    @classmethod
    def sub_n(cls, dow, n):
        return ((dow - n % 7) + 7) % 7 # just to be safe

    @classmethod
    def incr(cls, dow):
        return cls.add_n(dow, 1)

    @classmethod
    def decr(cls, dow):
        return cls.sub_n(dow, 1)

    @classmethod
    def date2is_dow(cls, d, dow):
        return d.weekday() == dow

    @classmethod
    def date2is_monday(cls, d):
        return cls.date2is_dow(d, cls.MONDAY)

    @classmethod
    def date2is_sunday(cls, d):
        return cls.date2is_dow(d,cls.SUNDAY)


class DateTool:
    @classmethod
    @IterTool.f_iter2f_list
    def date_list2span_list_weekly(cls, date_list, dow_start):
        n = len(date_list)

        start = 0
        for i, d in enumerate(date_list):
            if i == 0:
                continue

            if DayOfWeek.date2is_dow(d, dow_start):
                yield (start, i)
                start = i

        if n:
            yield (start, n)



    @classmethod
    def date_list2span_list_yearly(cls, date_list):
        def is_year_changed(date_list, i):
            return date_list[i - 1].year != date_list[i].year if i>0 else False

        span_list = ListTool.list_detector2span_list(date_list, is_year_changed)
        return span_list

    @classmethod
    @VersionTool.incomplete
    def date_list2chunks_yearly_fullweeks(cls, date_list):
        n = len(date_list)

        def is_year_changed(date_list, i):
            if i==0:
                return False

            return date_list[i-1].year != date_list[i].year



        i_start = 0
        for i, d in enumerate(date_list):
            if not is_year_changed(date_list, i):
                continue

            span_fullweek_raw = cls.date_list_span_weekday2span_fullweek(date_list, (i_start,i), DayOfWeek.SUNDAY)
            i_start = i # update to next

            span_fullweek = SpanTool.span_size2valid(span_fullweek_raw, n)
            yield span_fullweek

    @classmethod
    @VersionTool.incomplete
    def date_list_span_weekday2span_fullweek(cls, date_list, span, weekday):
        s0, e0 = span
        count_sunday_future = cls.date_weekday2count(date_list[e0 - 1], weekday)
        count_sunday_past = cls.weekday_date2count(weekday, date_list[s0])
        e1 = (e0 - 1) + count_sunday_future + 1
        s1 = s0 - count_sunday_past
        return (s1, e1)

    @classmethod
    def date2is_end_of_month(cls, d):
        return d.day == calendar.monthrange(d.year, d.month)[1]

    @classmethod
    def date_weekday2count(cls, d, target_weekday):
        return (target_weekday + 7 - d.weekday()) % 7

    @classmethod
    def weekday_date2count(cls, target_weekday, d):
        return (d.weekday() + 7 - target_weekday) % 7


    @classmethod
    def date2is_jan_1st(cls, d):
        return d.month==1 and d.day==1

    @classmethod
    def date2is_dec_31st(cls, d):
        return d.month == 12 and d.day == 31

    @classmethod
    def date_pair2matches_week_boundary(cls, date_pair):
        if not DayOfWeek.date2is_monday(date_pair[0]):
            return False

        if not DayOfWeek.date2is_sunday(date_pair[1]):
            return False

        return True

    @classmethod
    def date_pair2matches_year_boundary(cls, date_pair):
        if not DateTool.date2is_jan_1st(date_pair[0]):
            return False

        if not DateTool.date2is_dec_31st(date_pair[1]):
            return False

        return True

    @classmethod
    def date_locale2str(cls, d, locale):
        from foxylib.tools.locale.locale_tool import LocaleTool
        if LocaleTool.locale2lang(locale) == "ko":
            l = ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"]
            return l[d.weekday()]

        l = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        return l[d.weekday()]


class TimedeltaTool:
    @classmethod
    def unit_list(cls):
        return [timedelta(days=1),
                timedelta(hours=1),
                timedelta(minutes=1),
                timedelta(seconds=1),
                ]

class RelativedeltaTool:
    @classmethod
    def unit_list(cls):
        return [relativedelta(years=1),
                relativedelta(months=1),
                relativedelta(weeks=1),
                relativedelta(days=1),
                relativedelta(hours=1),
                relativedelta(minutes=1),
                relativedelta(seconds=1),
                ]


class RelativeTimedeltaTool:

    @classmethod
    @lru_cache(maxsize=2)
    def yaml(cls):
        filepath = os.path.join(FILE_DIR, "RelativeTimedelta.yaml")
        utf8 = FileTool.filepath2utf8(filepath)
        j_yaml = yaml.load(utf8, yaml.SafeLoader)
        return j_yaml

    # @classmethod
    # def _name_list(cls):
    #     return ["years", "months", "weeks", "days", "hours", "minutes", "seconds",]

    # @classmethod
    # def name_value_list2reldelta(cls, ):
    #     return relativedelta.relativedelta(**{name:value})


    @classmethod
    def pattern_timedelta(cls):
        logger = FoxylibLogger.func_level2logger(cls.pattern_timedelta, logging.DEBUG)

        j_yaml = cls.yaml()

        j_name2strs = lambda j: lchain.from_iterable(j.values())
        rstr_reldelta_list = [format_str(r"(?:(?P<{0}>\d+)\s*(?:{1}))?",
                                         k,
                                         r"|".join(lmap(re.escape, j_name2strs(j_yaml[k]))),
                                         )
                     for k in j_yaml.keys()]
        rstr_reldeltas = r"\s*".join([r"(?:{0})".format(rstr) for rstr in rstr_reldelta_list])

        rstr = r"\s*".join([r"(?P<sign>[+-])", rstr_reldeltas])
        logger.debug({"rstr":rstr})
        pattern = re.compile(rstr, re.IGNORECASE)
        return pattern

    @classmethod
    def parse_str2reldelta(cls, s):
        logger = FoxylibLogger.func_level2logger(cls.parse_str2reldelta, logging.DEBUG)

        j_yaml = cls.yaml()

        p = cls.pattern_timedelta()
        m_list = list(p.finditer(s))
        if not m_list: return None

        m = l_singleton2obj(m_list)
        int_sign = IntegerTool.parse_sign2int(m.group("sign"))

        kv_list = [(k, int_sign*int(m.group(k)))
                   for k in j_yaml.keys() if m.group(k)]

        logger.debug({"kv_list":kv_list})
        reldelta = relativedelta.relativedelta(**dict(kv_list))
        return reldelta

tz2now = DatetimeTool.tz2now
now_utc = DatetimeTool.now_utc