#!/bin/bash

set -e
set -u

ARG0=${BASH_SOURCE[0]}
FILE_PATH=$(readlink -f $ARG0)
FILE_DIR=$(dirname $FILE_PATH)
FILE_NAME=$(basename $FILE_PATH)

errcho(){ >&2 echo "$@"; }
func_count2reduce(){
    local v="${1?missing}"; local cmd="${2?missing}"; local n=${3?missing};
    for ((i=0;i<$n;i++)); do v=$($cmd $v) ; done; echo "$v"
}
usage(){ errcho "usage: $ARG0 <filepath_list>"; }

FOXYLIB_DIR=$(func_count2reduce $FILE_DIR dirname 3)

pull_each(){
    lpass_id=${1?"missing"}
    filepath=${2?"missing"}

    errcho "[$FILE_NAME] pull_each START ($lpass_id $filepath)"

    dirname $filepath | xargs mkdir -p
    if [[ -w "$filepath" ]]; then is_writable="1"; else is_writable=""; if [[ -e "$filepath" ]]; then chmod u+w "$filepath"; fi; fi

    if [ "" ]; then
        lpass show --sync=now \
            -j "$lpass_id" \
            | jq -r '.[0]["note"]' \
            > $filepath
    else
        lpass show --sync=now \
            "$lpass_id" \
            | tail -n +3 \
            | grep -v -Fx "URL: http://sn" \
            | grep -v -Fx "Notes:" \
            | sed "s/^Notes: //g" \
            > $filepath
    fi

    if [[ ! "$is_writable" ]]; then chmod u-w "$filepath"; fi
    errcho "[$FILE_NAME] pull_each END ($lpass_id $filepath)"

}

main(){
    pushd $FOXYLIB_DIR

    lpass logout --force || errcho "Warning: no need to logout"
    $FILE_DIR/login.bash || exit 1

    cat $tmplt_filepath \
        | grep -Ev '^#|^\s*$' \
        | python -m foxylib.tools.jinja2.str_env2jinjad \
        | while read lpass_id filepath_yaml; do

        errcho "[$FILE_NAME] main START ($filepath_yaml)"
        pull_each "$lpass_id" "$filepath_yaml"
        errcho "[$FILE_NAME] main END ($filepath_yaml)"
    done

    popd
}

tmplt_filepath=${1:-}
if [[ -z "$tmplt_filepath" ]]; then usage; exit 1; fi

errcho "[$FILE_NAME] START"
main || exit 1
errcho "[$FILE_NAME] END"
