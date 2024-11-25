#! /bin/sh


get_versions () {
    git fetch --all --tags
    git tag | grep '^v[0-9]'
}

checkout_version () {
    local ver="$1"
    git checkout "tags/$ver" -b "$ver"
}

build_version () {
    local ver="$1"
    local dstdir="docs/releases/$ver"
    mkdir -p "$dstdir"
    cd docs
    make html
    cd -
    mv docs/build/html/* "$dstdir/"
}

mydir=$(dirname "$0")
mydir=$(realpath $mydir/..)

mkdir -p docs/releases
for version in $(get_versions)
do
    echo "Building version $version"
    checkout_version "$version"
    build_version "$version"
    cd "$mydir"
done

latest=$version
mv "docs/releases/$version" docs/releases/latest