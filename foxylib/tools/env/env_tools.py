import logging
import os
import sys
from operator import itemgetter as ig
from pprint import pformat

import yaml
from future.utils import lmap, lfilter

from foxylib.tools.collections.collections_tools import DictToolkit
from foxylib.tools.jinja2.jinja2_tools import Jinja2Toolkit
from foxylib.tools.log.logger_tools import FoxylibLogger
from foxylib.tools.native.native_tools import BooleanToolkit
from foxylib.tools.string.string_tools import str2strip


class EnvToolkit:
    class K:
        ENV = "ENV"

    class EnvName:
        DEFAULT = "_DEFAULT_"
        DEV = "dev"
        PRODUCTION = "production"
        STAGING = "staging"

    # @classmethod
    # def env_dir2kv_list(cls, env_dir):
    #     env = EnvToolkit.k2v("ENV")
    #     data = {'ENV_DIR': env_dir, "ENV":env,}
    #     envname_list = [env, cls.EnvName.DEFAULT]
    #     yaml_filepath = os.path.join(env_dir, "env.part.yaml")
    #
    #     str_tmplt = Jinja2Toolkit.tmplt_file2str(yaml_filepath, data)
    #     return cls.yaml_str2kv_list(str_tmplt, envname_list)

    @classmethod
    def kv_list2str_export(cls, kv_list):
        str_export = "\n".join(['export {0}="{1}"'.format(k, v_yaml) for k, v_yaml in kv_list])
        return str_export

    @classmethod
    def yaml_str2kv_list(cls, tmplt_str, envname_list):
        logger = FoxylibLogger.func2logger(cls.yaml_str2kv_list)

        #s = Jinja2Toolkit.tmplt_file2str(tmplt_filepath, data)
        j = yaml.load(tmplt_str)

        l = []
        for k, v in j.items():
            if not isinstance(v,dict):
                l.append( (k,v) )
                continue

            vv = DictToolkit.keys2v_first_or_default(v, envname_list)
            if vv is None: continue

            l.append((k,vv))

        logger.info({"l": l,
                     "tmplt_str": tmplt_str,
                     })

        return l

    @classmethod
    def k2v(cls, key, default=None):
        return os.environ.get(key, default)

    @classmethod
    def k_list2v(cls, key_list, default=None):
        for key in key_list:
            if key not in os.environ:
                continue

            return os.environ[key]

        return default


    @classmethod
    def key2nullboolean(cls, key):
        v = cls.k2v(key)
        nb = BooleanToolkit.parse2nullboolean(v)
        return nb

    @classmethod
    def key2is_true(cls, key):
        nb = cls.key2nullboolean(key)
        return nb is True

    @classmethod
    def key2is_not_true(cls, key):
        return not cls.key2is_true(key)




class YamlConfigToolkit:
    class Key:
        _DEFAULT_ = "_DEFAULT_"

    @classmethod
    def k2v(cls, j, key, envname=None, default=None,):
        if not j: return default
        if key not in j: return default

        v = j[key]
        if not isinstance(v,dict): return v

        envkey_list = [envname, cls.Key._DEFAULT_]
        for ek in envkey_list:
            if not ek: continue
            if ek not in v: continue
            return v[ek]

        if cls.Key._DEFAULT_ in v: return v[cls.Key._DEFAULT_]

        return default

    @classmethod
    def k2v_env_or_yaml(cls, j, key, envname=None, default=None,):
        if key in os.environ:
            return os.environ[key]

        return cls.k2v(j, key, envname=envname, default=default)

def main():
    logger = FoxylibLogger.func2logger(main)

    if len(sys.argv) < 4:
        print("usage: {} <listfile_filepath> <env> <repo_dir>".format(sys.argv[0]))
        sys.exit(1)

    from foxylib.tools.file.file_tools import FileToolkit


    listfile_filepath = sys.argv[1]
    env = sys.argv[2]
    repo_dir = sys.argv[3]

    l = lfilter(bool, map(str2strip, FileToolkit.filepath2utf8_lines(listfile_filepath)))
    #logger.warning({"l": l})

    filepath_list = lmap(lambda s:s.split(maxsplit=1)[1], l)

    data = {"ENV": env, "REPO_DIR":repo_dir, "HOME_DIR":os.path.expanduser('~')}
    envname_list = [env, EnvToolkit.EnvName.DEFAULT]

    str_tmplt = "\n".join([Jinja2Toolkit.tmplt_file2str(fp, data)
                           for fp in filepath_list
                           if fp.endswith(".yaml") or fp.endswith(".yml")])
    kv_list = EnvToolkit.yaml_str2kv_list(str_tmplt, envname_list)

    str_export = "\n".join(['export {0}="{1}"'.format(k, v_yaml) for k, v_yaml in kv_list])
    print(str_export)

if __name__== "__main__":
    main()