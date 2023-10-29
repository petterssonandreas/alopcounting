#!/usr/bin/env bash

usage="$(basename "$0") [-h] [-F] -- program to create a release of ALOPCounting

where:
    -h  show this help text
    -F  force clean release"

while getopts ':hF' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
    F) force='true'
       ;;
    :) printf "missing argument for -%s\n" "$OPTARG" >&2
       echo "$usage" >&2
       exit 1
       ;;
    \?) printf "illegal option: -%s\n" "$OPTARG" >&2
       echo "$usage" >&2
       exit 1
       ;;
  esac
done
shift $((OPTIND - 1))

semver="$(python _version.py 2>&1)"
release_version="v$semver"
echo "release_version=$release_version"

name="alopcounting_$release_version"
dir="$name"

if [ -d "$dir" ]; then
    echo "$dir exists."
    if [ -n "$force" ]; then
        echo "Using force, cleaning $dir"
        rm -rf $dir
        rm $name.zip
    else
        echo "Aborting! Use force if you want to override."
        exit 1
    fi
fi

mkdir -p $dir/userdata/verifications
pyinstaller -wF --name ALOPCounting.exe --distpath $dir main.py
cp build-bundles/accounts.json $dir/userdata/accounts.json
cp config.toml $dir/config.toml

cd $dir
/c/Program/7-Zip/7z.exe a "../$name.zip" ./*
cd ..

echo "Release created: ${PWD}/$name.zip"
