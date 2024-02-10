#! /bin/sh

dir=${1:-.}

# test
for i in $(find "$dir" -name tests)
do
    cd $i
    rm -rf .coverage
    PYTHONPATH=~/gitlab/tattler/tattler/package/src coverage run -m unittest discover || exit 1
    cd -
done

# generate report
rm -rf .coverage
coverage combine $(find "$dir" -name .coverage) && coverage html --omit='**/tests/**' ; open htmlcov/index.html