from functools import wraps

import cachetools
import cachetools.keys
from nose.tools import assert_true, assert_is_not_none

from foxylib.tools.function.function_tool import FunctionTool


class CachetoolsToolDecorator:
    @classmethod
    def attach2func(cls, func=None, cached=None, cache=None):
        assert_is_not_none(cached)
        assert_is_not_none(cache)

        def wrapper(f):
            f.cache = cache
            return cached(cache)(f)

        return wrapper(func) if func else wrapper


class CachetoolsTool:
    Decorator = CachetoolsToolDecorator

    @classmethod
    def key4classmethod(cls, key):
        return FunctionTool.shift_args(key, 1)

    @classmethod
    def key4objectmethod(cls, key):
        return FunctionTool.shift_args(key, 1)


class CooldownTool:
    class NotCallableException(Exception):
        pass

    @classmethod
    def invoke_or_cooldown_error(cls, cache_cooldown, key=None, lock=None,):
        key = key or cachetools.keys.hashkey

        def wrapper(f):
            f_wrapped = cachetools.cached(cache_cooldown, key=key, lock=lock)(f)

            @wraps(f)
            def wrapped(*_, **__):
                k = key(*_, **__)
                if k in cache_cooldown:
                    raise cls.NotCallableException()

                return f_wrapped(*_, **__)
            return wrapped
        return wrapper

    @classmethod
    def invoke_or_cooldown_error_cachedmethod(cls, cachedmethod, key=None, lock=None, ):
        key = key or cachetools.keys.hashkey

        def wrapper(f):
            f_wrapped = cachetools.cachedmethod(cachedmethod, key=key, lock=lock)(f)

            @wraps(f)
            def wrapped(self, *_, **__):
                k = key(*_, **__)
                if k in cachedmethod(self):
                    raise cls.NotCallableException()

                return f_wrapped(self, *_, **__)

            return wrapped

        return wrapper



# class MultilayercacheTool:
#     @classmethod
#     def cached(cls, cache_list):
#         def wrapper(f):
#             return reduce(lambda f, c: cached(c)(f), cache_list, f)
#
#         return wrapper
#
#     @classmethod
#     @IterTool.f_iter2f_list
#     def pop_depthspan(cls, cache_list, hashkey, depthspan, ):
#         for c in SpanTool.list_span2sublist(cache_list, depthspan):
#             yield c.pop(hashkey)
#
#     @classmethod
#     def pop(cls, cache_list, hashkey, ):
#         return cls.pop_depth_or_lower(cache_list, hashkey, 0)
#
#     @classmethod
#     def put(cls, cache_list, hashkey, value):
#         for c in cache_list:
#             c[hashkey] = value
#

