#!/usr/bin/env bash
#
# logrotate-to-s3 - gzip the log file, rename the file to the current timestamp, and upload to s3
#

usage() {
  echo "Usage: logrotate-to-s3 your-bucket-name [ file ... ]" >&2
  echo "To see help text, yun can run 'logrotate-to-s3 -h' for usage." >&2
  exit 1
}

help() {
  cat << 'EOF' >&2
logrotate-to-s3:

  gzip the log file, rename the file to the current timestamp, and upload to s3.

Usage:

  logrotate-to-s3 your-bucket-name [ file ... ]

Environment variables:

  S3_PATH is the path prefix of the S3. The default is "logrotate".
  NAME_PREFIX is the name prefix of the uploaded file. The default is "".
  PREFIX is the directory prefix of the uploaded file. The default is "{hostname}/%Y/%m"
  SUFFIX is the name suffix of the uploaded file. The default is "%Y%m%d-%H%M%S"
  UPLOAD_CMD is used for uploading to S3. The default is "aws s3 cp". You may set it as "s3cmd put", "gof3r cp --endpoint s3-ap-northeast-1.amazonaws.com" and so on.

Examples:

  $ logrotate-to-s3 mybucket /var/log/nginx/access.log
    => s3://mybucket/logrotate/your-hostname/2016/01/access.log.20160102-030405.gz

  $ S3_PATH=archive/staging NAME_PREFIX=nginx logrotate-to-s3 mybucket /var/log/nginx/access.log
    => s3://mybucket/archive/staging/your-hostname/2016/01/nginx-access.log.20160102-030405.gz

  $ S3_PATH=app-log PREFIX="dt=$(date "+%Y-%m-%d")" logrotate-to-s3 mybucket /var/log/nginx/access.log
    => s3://mybucket/app-log/dt=2016-01-02/nginx-access.log.20160102-030405.gz

Configuration logroate:

  With postrotate without sharedscripts, this tool should work well.

    # good
    /var/log/nginx/*.log {
      postrotate
        NAME_PREFIX=nginx logrotate-to-s3 service-archive "$@"
      endscript
    }

  If you want to use sharescripts or lastaction, this may not work. You should avoid sharescripts and lastaction because whole pattern is passed to the script.

    # bad - because of quotes
    "/var/log/nginx/access.log" {
      sharedscripts
      postrotate
        logrotate-to-s3 mybucket "$@"
      endscript
    }

    # bad - because of wildcarded patterns
    /var/log/nginx/*.log {
      lastaction
        logrotate-to-s3 mybucket "$@"
      endscript
    }

    # bad - because space character is placed in the back of the pattern
    /var/log/nginx/access.log {
      sharedscripts
      postrotate
        logrotate-to-s3 mybucket "$@"
      endscript
    }

    # okish - it works, but "shardscripts" and "lastaction" are not recommended.
    /var/log/nginx/access.log{
      sharedscripts
      postrotate
        logrotate-to-s3 mybucket "$@"
      endscript
    }
EOF
  exit 1
}

set -euo pipefail

# If you have changed logortate setting, you may change here.
readonly dateext_suffix="-$(date "+%Y%m%d")" # "-%Y%m%d" is default `dateformat' of logrotate.
readonly start_count=1                       # "1" is default `start' of logrotate.
readonly default_prefix="$(hostname)/$(date "+%Y/%m")"
readonly default_suffix="$(date "+%Y%m%d-%H%M%S")"

# Default Configurations
readonly s3_path=${S3_PATH:-logrotate}
readonly name_prefix=${NAME_PREFIX:+$NAME_PREFIX-}
readonly upload_cmd=${UPLOAD_CMD:-aws s3 cp}

readonly prefix=${PREFIX:-$default_prefix}
readonly suffix=${SUFFIX:-$default_suffix}

# Temporary workspace
readonly tmpdir=$(mktemp -d)
cleanup() {
  [[ -d "$tmpdir" ]] && rm -rf "$tmpdir"
}
trap cleanup EXIT

upload() {
  declare bucket="$1" path="$2"

  local source compressed

  local -a targets=(
    "${path}.${start_count}"
    "${path}${dateext_suffix}"
  )

  for target in "${targets[@]}"; do
    if [[ -f $target ]]; then
      source=$target
      compressed=''
      break
    elif [[ -f ${target}.gz ]]; then
      source=${target}.gz
      compressed=y
      break
    fi
  done

  [[ ${source:-} ]] || return

  if [[ ! $compressed ]]; then
    local tmpfile
    tmpfile="${tmpdir}/$(basename "$source").gz"
    gzip -c "$source" > "$tmpfile"
    source=$tmpfile
  fi

  local filename
  filename="${name_prefix}$(basename "$path").${suffix}.gz"
  $upload_cmd "$source" "s3://${bucket}/${s3_path}/${prefix}/${filename}"
}

main() {
  local flag
  while getopts 'h' flag; do
    case ${flag} in
      *) help ;;
    esac
  done

  [[ $# -ge 1 ]] || usage

  local bucket=$1
  local -a paths=("${@:2}")

  for path in "${paths[@]}"; do
    upload "$bucket" "$path"
  done
}
main "$@"
