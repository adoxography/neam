#!/bin/bash

# from https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ ! -d $DIR/.venv ]; then
    echo "Setting up environment for first-time run..."
    python3 -m venv $DIR/.venv
    FIRST_TIME=true
fi

source $DIR/.venv/bin/activate

if [[ $FIRST_TIME ]]; then
    echo "Installing Python dependencies..."
    echo $FIRST_TIME
    pip3 install -r requirements.txt
fi

export PYWIKIBOT2_NO_USER_CONFIG=1
PYTHONIOENCODING=utf-8 python3 "$DIR/neam.py" --retag=placeName,orgName --expand=persName $@
deactivate

