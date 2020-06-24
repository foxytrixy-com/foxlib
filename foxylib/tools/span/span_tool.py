from collections import defaultdict
from typing import Set, Tuple, List

from future.utils import lmap, lfilter
from nose.tools import assert_greater_equal, assert_less_equal

from foxylib.tools.collections.iter_tool import IterTool, iter2singleton
from foxylib.tools.collections.collections_tool import lchain, tmap, merge_dicts, \
    DictTool, sfilter


class SpanTool:
    @classmethod
    def span2is_valid(cls, span):
        if not span:
            return False

        s, e = span

        if s * e == 0:
            if s == 0 and e == 0:
                return True

            return s == 0

        elif s * e > 0:
            return s <= e

        else:
            return s > 0

    @classmethod
    def spans2nonoverlapping_greedy(cls, spans):
        span_list = sorted(spans)

        end = None
        for span in span_list:
            s, e = span
            if end is not None and end > s:
                continue

            yield span
            end = e

    @classmethod
    def span_pair2between(cls, span1, span2):
        s1, e1 = span1
        s2, e2 = span2

        assert_less_equal(s1, e1)
        assert_less_equal(s2, e2)

        if e1 <= s2:
            return e1, s2

        # if e2 <= s1:
        #     return e2, s1

        return None

    @classmethod
    def spans2is_consecutive(cls, spans):
        span_prev = None
        for span in spans:
            if span is None:
                return False

            if span_prev is None:
                span_prev = span
                continue

            if span_prev[1] + 1 != span[0]:
                return False

            span_prev = span
        return True

    @classmethod
    def is_adjacent(cls, span1, span2):
        return cls.spans2is_consecutive([span1, span2])

    @classmethod
    def overlaps(cls, se1, se2):
        if se1 is None:
            return False
        if se2 is None:
            return False

        s1, e1 = se1
        s2, e2 = se2

        if e1 <= s2:
            return False
        if e2 <= s1:
            return False
        return True

    @classmethod
    def overlaps_any(cls, span_list):
        span_list_sorted = sorted(span_list)
        n = len(span_list_sorted)

        if n <= 1:
            return False

        for i in range(n - 1):
            if cls.overlaps(span_list[i], span_list[i + 1]):
                return True
        return False

    @classmethod
    def span2iter(cls, span):
        return range(*span)

    @classmethod
    def span_size2is_valid(cls, span, n):
        s,e = span
        return s>=0 and e<=n and s<=e

    @classmethod
    def span_size2valid(cls, span, n):
        s, e = span
        return (max(0,s),min(e,n))

    @classmethod
    def add_each(cls, span, v):
        return tmap(lambda x: x + v, span)

    @classmethod
    def covers_index(cls, span, index):
        if index is None:
            return False

        s, e = span

        return s <= index < e

    @classmethod
    def covers(cls, span1, span2):
        s1, e1 = span1
        s2, e2 = span2

        return s1 <= s2 and e1 >= e2

    @classmethod
    def is_covered_by(cls, span1, span2):
        return cls.covers(span2, span1)


    @classmethod
    def span_list2indexes_uncovered(cls, span_list_in) -> Set[int]:

        span_list = lmap(tuple, span_list_in)
        n = len(span_list)

        h_duplicate = merge_dicts([{span: [i]} for i, span in enumerate(span_list)],
                                  vwrite=DictTool.VWrite.extend)

        i_list_sorted_start = sorted(range(n), key=lambda i: (span_list[i][0], -span_list[i][1]), )
        i_list_sorted_end = sorted(range(n), key=lambda i: (-span_list[i][1], span_list[i][0]), )

        h_i2i_set_hyp_start = {i: set(i_list_sorted_start[:j])
                               for j, i in enumerate(i_list_sorted_start)}
        h_i2i_set_hyp_end = {i: set(i_list_sorted_end[:j])
                             for j, i in enumerate(i_list_sorted_end)}

        i_set_uncovered_raw = sfilter(lambda i: not (h_i2i_set_hyp_start[i] & h_i2i_set_hyp_end[i]), range(n))

        index_set_uncovered = set(index
                                  for i in i_set_uncovered_raw
                                  for index in h_duplicate[span_list[i]])

        return index_set_uncovered


    @classmethod
    def index_iter2span_iter(cls, index_iter):
        start, end = None, None

        for i in index_iter:
            if start is None:
                start = end = i
                continue

            if i == end+1:
                end = i
                continue

            yield (start, end+1)

            start = end = i

        if start is not None:
            yield (start, end+1)

    @classmethod
    @IterTool.f_iter2f_list
    def index_list_exclusive2span_iter(cls, index_list_exclusive, n):
        start, end = 0, 0

        for i in index_list_exclusive:
            if i>end:
                yield (end, i)

            end = i+1

        if n > end:
            yield (end,n)



    @classmethod
    def obj_list2uncovered(cls, obj_list, f_obj2span=None):
        if f_obj2span is None:
            f_obj2span = lambda x:x

        span_list = lmap(f_obj2span, obj_list)
        i_set_uncovered = cls.span_list2indexes_uncovered(span_list)
        return lmap(lambda i:obj_list[i], i_set_uncovered)

    @classmethod
    def list_spans_func2processed(cls, l_in, span_list, func, f_list2chain=None):
        if f_list2chain is None:
            f_list2chain = lambda ll:lchain(*ll)

        if not span_list:
            return l_in

        ll = []
        n = len(span_list)
        for i in range(n):
            s_this, e_this = span_list[i]
            e_prev = span_list[i - 1][1] if i > 0 else 0

            if s_this > e_prev:
                ll.append(l_in[e_prev:s_this])

            l_in_this = l_in[s_this:e_this]
            l_out_this = func(l_in_this)
            ll.append(l_out_this)

        e_last = span_list[-1][1]
        if e_last < len(l_in):
            ll.append(l_in[e_last:])

        l_out = f_list2chain(ll)
        return l_out

    @classmethod
    def list_span2is_valid(cls, l, span):
        if l is None:
            return False

        if not SpanTool.span2is_valid(span):
            return False

        n = len(l)
        s, e = span
        if s-e > n:
            return False

        if s > n:
            return False

        if -e > n:
            return False

        return True

    @classmethod
    def list_span2sublist(cls, l, span):
        if not cls.list_span2is_valid(l, span):
            return None

        s, e = span
        return l[s:e]

    @classmethod
    def span2len(cls, span): return max(span[1]-span[0],0)


    @classmethod
    def _spans_index_limit2j_end_longest(cls, span_list, i, j_prev, len_limit):
        n = len(span_list)
        span_start = span_list[i]
        for j in range(j_prev, n):
            span_end = span_list[j]

            span_big = [span_start[0], span_end[1]]
            len_big = cls.span2len(span_big)

            if len_big <= len_limit: continue
            # if j-1 == j_prev: return None

            return j # last valid one
        return n

    @classmethod
    def span_list_limit2span_of_span_longest_iter(cls, span_list, len_limit):
        n = len(span_list)

        j_prev = 0
        for i in range(n):
            j_prev = max(i, j_prev)
            j_new = cls._spans_index_limit2j_end_longest(span_list, i, j_prev, len_limit, )
            if j_new == j_prev: continue

            yield (i, j_new)
            if j_new == n: break

            j_prev = j_new




    @classmethod
    def span_limit2extended(cls, span, limit):
        n = cls.span2len(span)
        buffer = max(limit - n, 0)

        s, e = span

        s_new = max(s - buffer//2, 0)
        e_new = e + buffer//2

        return (s_new, e_new)

    @classmethod
    def span_list_span2span_big(cls, span_list, span_of_span):
        span_list_partial = cls.list_span2sublist(span_list, span_of_span)
        return [span_list_partial[0][0], span_list_partial[-1][1]]


    @classmethod
    def span_iter2merged(cls, span_iter):
        span_list_in = lfilter(bool, span_iter)  # se might be None
        if not span_list_in: return []

        l_sorted = sorted(map(list, span_list_in))
        n = len(l_sorted)

        l_out = []
        ispan_start = 0
        iobj_end = l_sorted[0][-1]
        for ispan in range(n - 1):
            s2, e2 = l_sorted[ispan + 1]

            if iobj_end >= s2:
                iobj_end = max(iobj_end, e2)
                continue

            span_out = cls.span_list_span2span_big(l_sorted, (ispan_start, ispan+1))
            l_out.append(span_out)
            ispan_start = ispan + 1

        span_last = cls.span_list_span2span_big(l_sorted, (ispan_start, n))
        l_out.append(span_last)

        return l_out

    @classmethod
    def size2beam(cls, size):
        buffer_up = (size - 1) // 2
        buffer_down = (size - 1) // 2 + size % 2
        beam = (buffer_up, buffer_down)
        return beam

    @classmethod
    def index_total_beam2span(cls, index, total, beam):
        buffer_pre, buffer_post = beam

        count_return = sum(beam)+1
        if index <= buffer_pre:
            return (0, min(count_return,total),)

        if index + buffer_post >= total-1:
            return (max(0,total-buffer_post),total)

        return (index-buffer_pre,index+buffer_post+1)

    @classmethod
    def index_values_beam2neighbor_indexes(cls, i_pivot, v_list, beam):
        v_count = len(v_list)
        i_list_sorted = sorted(range(v_count), key=lambda i:v_list[i])
        k_pivot = iter2singleton(filter(lambda k: i_list_sorted[k] == i_pivot, range(v_count)))
        k_span = cls.index_total_beam2span(k_pivot, v_count, beam)

        i_sublist = cls.list_span2sublist(i_list_sorted, k_span)
        return i_sublist


list_span2sublist = SpanTool.list_span2sublist
span2iter = SpanTool.span2iter