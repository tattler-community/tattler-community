#! /bin/sh

# Use as follows:
#
# cd docs
# ./build_doc_versions.sh
#
# rsync -avz --delete releases/en/ mic.frontdam.com:/var/www/sites/docs.tattler.dev/en/


base_outdir=releases/en
ts=$(date +%s)

logmsg () {
    echo $* >&2
}

get_versions () {
    git fetch --all --tags
    git tag | grep '^v[0-9]'
}

checkout_version () {
    local ver="$1"
    logmsg "========== $ver =========="
    git checkout tags/$ver -b "$ver-$ts"
    true
}

build_version () {
    local ver="$1"
    local dstdir="$base_outdir/$ver"
    rm -rf "$dstdir"
    mkdir -p "$dstdir" || return 1
    . ../../venv/bin/activate
    PYTHONPATH=../src make html || return 1
    deactivate
    mv build/html/* "$dstdir/" || return 1
}

link_latest () {
    cd $base_outdir
    rm -f latest
    logmsg "===== Latest -> $latest_version ====="
    ln -s "$latest_version" "latest"
    cd -
}

initial_dir=$(pwd)

docroot=$(realpath "$0")
docroot=$(dirname "$docroot")

cd "$docroot"

for version in $(get_versions)
do
    git checkout main
    checkout_version "$version" || break
    build_version "$version" || break
    cd $docroot
done

latest_version=$(get_versions | sort -rn | head -n1)
link_latest

cd "$initial_dir"
