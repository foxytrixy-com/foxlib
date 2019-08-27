import logging
import os
from functools import lru_cache

from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk, scan
from future.utils import lmap
from nose.tools import assert_equal

from foxylib.tools.collections.collections_tools import merge_dicts, vwrite_no_duplicate_key
from foxylib.tools.json.json_tools import JToolkit, jdown

# logger = logging.getLogger(__name__)
from foxylib.tools.log.logger_tools import FoxylibLogger


class ElasticsearchToolkit:
    class Type:
        DOCUMENT = 'document'
    @classmethod
    def env2host(cls):
        return os.environ.get("ELASTICSEARCH_HOST")

    @classmethod
    def env2auth(cls):
        return os.environ.get("ELASTICSEARCH_AUTH")

    @classmethod
    @lru_cache(maxsize=2)
    def env2client(cls, *_, **__):
        logger = FoxylibLogger.func2logger(cls.env2client)

        auth = cls.env2auth()
        host = cls.env2host()
        logger.info({"auth":auth, "host":host})

        if auth:
            return Elasticsearch([auth], *_, **__)

        if host:
            return Elasticsearch([host], *_, **__)

        raise Exception("ELASTICSEARCH_HOST not defined")

    @classmethod
    def index2exists(cls, es_client, es_index):
        return es_client.indices.exists(index=es_index)

    @classmethod
    def index2create_or_skip(cls, es_client, es_index, body=None):
        if cls.index2exists(es_client,es_index):
            return

        j_index = es_client.indices.create(index=es_index, body=body)


        return j_index

    @classmethod
    def ids2delete(cls, es_client, es_index, ids,):
        j = {
            "query": {
                "terms": {
                    "_id": ids,
                }
            }
        }
        return es_client.delete_by_query(es_index, j)

    @classmethod
    def index2delete_or_skip(cls, es_client, es_index,):
        if not es_client.indices.exists(index=es_index): return

        es_client.indices.delete(index=es_index)

    @classmethod
    def j_result2j_hit_list(cls, j_result):
        j_hit_list = jdown(j_result, ["hits","hits"])
        return j_hit_list

    @classmethod
    def j_result2scroll_id(cls, j_result): return j_result["_scroll_id"]

    @classmethod
    def index2ids(cls, es_client, index):
        if not ESToolkit.index2exists(es_client, index):
            raise StopIteration()

        j_iter = scan(es_client,
                         query={"query": {"match_all": {}}, "stored_fields": []},
                         index=index,)
        for j in j_iter:
            yield j["_id"]

    @classmethod
    def j_result2j_hit_singleton(cls, j_result):
        j_hits = cls.j_result2j_hit_list(j_result)
        assert_equal(len(j_hits), 1)

        return j_hits[0]

    @classmethod
    def j_result2j_source_singleton(cls, j_result):
        j_hit = cls.j_result2j_hit_singleton(j_result)
        return j_hit["_source"]

    @classmethod
    def j_result2j_hit_src_singleton(cls, j_result):
        return (cls.j_result2j_hit_singleton(j_result),
                cls.j_result2j_source_singleton(j_result),
                )
    @classmethod
    def j_hit2j_src(cls, j_hit):
        if not j_hit: return j_hit
        return j_hit["_source"]

    @classmethod
    def j_hit2doc_id(cls, j_hit): return j_hit["_id"] if j_hit else None

    @classmethod
    def client_index_query2j_result(cls, es_client, index, j_query):
        logger = FoxylibLogger.func2logger(cls.client_index_query2j_result)
        logger.debug({"index":index, "j_query":j_query})

        j_result = es_client.search(index, j_query)
        return j_result

    @classmethod
    def item_count2request_timeout_default(cls, item_count):
        return item_count*10

class BulkToolkit:
    @classmethod
    def j_action2id(cls, j): return j.get("_id")
    @classmethod
    def j_action2index(cls, j): return j.get("_index")
    @classmethod
    def j_action2body(cls, j): return j.get("_source")
    @classmethod
    def j_action2doc_type(cls, j): return j.get("_type")
    @classmethod
    def j_action2op_type(cls, j): return j.get("_op_type", cls.op_type_default())

    @classmethod
    def op_type_default(cls): return "index"

    @classmethod
    def bulk(cls, es_client, j_action_list, run_bulk=True, es_kwargs=None,):
        logger = FoxylibLogger.func2logger(cls.bulk)

        n = len(j_action_list)
        count_list = [n*i//100 for i in range(100)]

        _run_bulk = run_bulk and n>1
        if _run_bulk:
            return bulk(es_client, j_action_list, **es_kwargs)
        else:
            result_list = []
            for i, j_action in enumerate(j_action_list):
                if i in count_list:
                    logger.debug({"i/n":"{}/{}".format(i+1,n),
                                  # "j_action":j_action,
                                  })
                    # raise Exception()

                op_type = cls.j_action2op_type(j_action)

                if op_type == "index":
                    result = cls._j_action2op_index(es_client, j_action, es_kwargs=es_kwargs)
                    result_list.append(result)
                else:
                    raise NotImplementedError()
            return result_list

    @classmethod
    def _j_action2op_index(cls, es_client, j_action, es_kwargs=None):
        id = cls.j_action2id(j_action)
        index = cls.j_action2index(j_action)
        body = cls.j_action2body(j_action)
        doc_type = cls.j_action2doc_type(j_action)
        op_type = cls.j_action2op_type(j_action)
        assert_equal(op_type, "index")

        h = merge_dicts([{"id":id, "index":index, "body":body, "doc_type":doc_type,},
                         es_kwargs], vwrite=vwrite_no_duplicate_key)
        return es_client.index(**h)


    @classmethod
    def doc_id2delete_by_query(cls, doc_id):
        """POST dev-precedents/_delete_by_query
{
  "query": {
    "term": {
            "_id": "광주고등법원-2010나6900"
        }
  }
}"""
class ElasticsearchQuery:
    @classmethod
    def j_all(cls):
        j_query = {
            "query": {
                "match_all": {}
            }
        }
        return j_query

    @classmethod
    def jqi2jq(cls, jqi): return {"query":jqi}
    @classmethod
    def jqi_all(cls): return {"match_all": {}}

    @classmethod
    def id_list2j_query(cls, doc_id_list):
        return {"query": {"terms": {"_id": doc_id_list}}}

    @classmethod
    def jq_from(cls, start):
        return {"from": start, }

    @classmethod
    def jq_size(cls, size):
        return {"size": size,}

    @classmethod
    def jq_track_total_hits(cls, track_total_hits=True,):
        return { "track_total_hits": track_total_hits,}

    @classmethod
    def fieldname_list2j_includes(cls, fieldname_list):
        return {"includes": fieldname_list}

    @classmethod
    def str_field2j_source(cls, str_field):
        return {"_source": str_field,}


    # @classmethod
    # def j_query_list2j_must(cls, j_query_list):
    #     return {
    #         "bool": {
    #             "must": j_query_list
    #         }
    #     }

    @classmethod
    def j_query_list2j_match(cls, j_match_list):
        return {
            "match": j_match_list
        }

    @classmethod
    def kv2jqi_term(cls, k, v): return {"term": {k: v}}
    @classmethod
    def kl2jqi_terms(cls, k, l): return {"terms": {k: l}}

    @classmethod
    def l2jqi_must(cls, l):
        return {"bool": {"must": l}}
    @classmethod
    def l2jqi_and(cls, *_, **__): return cls.l2jqi_must(*_, **__)

    @classmethod
    def l2jqi_should(cls, l):
        return {"bool": {"should": l}}
    @classmethod
    def l2jqi_or(cls, *_, **__): return cls.l2jqi_must(*_, **__)


    @classmethod
    def query_fields2jqi_multimatch(cls, str_query, field_list):
        return {
            "multi_match": {
                "query": str_query,
                "fields": field_list
            }
        }

    @classmethod
    def l2jq_sort(cls, l): return {"sort":l}


class IndexToolkit:
    @classmethod
    def client_name2exists(cls, es_client, index):
        return es_client.indices.exists(index=index)

    @classmethod
    def client_name2gorc(cls, es_client, name):
        j_index = es_client.indices.get(name)
        if j_index:
            return j_index

        j_index = es_client.indices.create(name)
        return j_index

    @classmethod
    def delete(cls, es_client, index):
        j_result = es_client.indices.delete(index)
        return j_result


class IndexAliasToolkit:
    @classmethod
    def delete(cls, es_client, alias):
        logger = FoxylibLogger.func2logger(cls.create)
        index_list = cls.alias2indexes(es_client, alias)
        return es_client.indices.delete_alias(index=",".join(index_list), name=alias)

    @classmethod
    def create(cls, es_client, index, alias):
        logger = FoxylibLogger.func2logger(cls.create)
        logger.debug({"index":index, "alias":alias})

        j_result = es_client.indices.put_alias(index, alias)
        return j_result

    @classmethod
    def create_or_update(cls, es_client, alias, index):
        # GET / dev - precedents / _alias / *
        cls.delete(es_client, alias)
        return cls.create(es_client, index, alias)

    @classmethod
    def alias2indexes(cls, es_client, alias):
        logger = FoxylibLogger.func2logger(cls.alias2indexes)

        try:
            j_result = es_client.indices.get_alias(name=alias)
        except NotFoundError:
            return

        index_list = list(j_result.keys())
        return index_list


class ElasticsearchOrder:
    class Value:
        ASC = "asc"
        DESC = "desc"
    V = Value


ESToolkit = ElasticsearchToolkit
ESQuery = ElasticsearchQuery
ESOrder = ElasticsearchOrder

j_hit2j_src = ElasticsearchToolkit.j_hit2j_src