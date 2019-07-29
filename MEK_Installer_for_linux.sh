#!/bin/bash

# MEK Linux installer script by Kavawuvi
#
# Copyright 2019 Kavawuvi
#
# Updated 2019-07-28 gbMichelle (c)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Note: The above license only applies to this script, not Mo's Editing Kit.
# Mo's Editing Kit is by MosesofEgypt and is subject to a separate license.
#

# Check if we're running as root
if [[ "$UID" = "0" ]]; then
    echo "Error: This command cannot and should not be run as root!" 1>&2
    exit 1
fi

print_help() {
    echo "Usage: $0 [options] [destination]" 1>&2
    echo "Options:" 1>&2
    echo "  -h  Show help" 1>&2
    echo "  -r  Force reinstall when updating libraries" 1>&2
    echo "  -q  Quiet" 1>&2
}


# Parse options
reinstall="0"
quiet="0"
while getopts 'hrq' OPTION; do
    case "$OPTION" in
        h)
            print_help
            exit 1
            ;;
        r)
            reinstall="1"
            ;;
        q)
            quiet="1"
            ;;
    esac
done

# Changed it so that it doesn't select an install path on its own
# when there is none specified. Safety reasons -gbMichelle 2019-07-28

# Set the destination folder
destination="mek"
if [[ "$#" = $(($OPTIND - 1)) ]]; then
    echo "No destination specified."
    echo ""
    print_help
    exit 1
elif [[ "$#" = "$OPTIND" ]]; then
    shift $(($OPTIND - 1))
    destination=$@
else
    echo "Error: Invalid usage. Use $0 -h for help." 1>&2
    exit 1
fi

# Edit: Check if apt exists, because that will mean that we're on
# an Ubuntu based distro. This means that tkinter will need to be installed
# differently, and it also means that we can install any missing dependencies.
# -gbMichelle 2019-07-28

apt_installed="1"
if [[ $(command -v apt) = "" ]]; then
    apt_installed="0"
fi

if [[ "$apt_installed" = "1" ]]; then
    echo "We detected that you're on an ubuntu based distribution."
    echo "We can install the following packages, but it would require sudo permissions."
    echo "These packages would be installed if not already present:"
    echo "    mercurial python3 python3-pip python3-tk"
    read -p "Do you want to install these? (Yes will prompt for sudo) Y/n:" -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        sudo apt-get install mercurial python3 python3-pip python3-tk -y
    fi
fi

# End of edit

# Check for required commands
exit_missing_stuff="0"
check_if_missing() {
    if [[ $(command -v $1) = "" ]]; then
        echo "Error: $1 is not installed." 1>&2
        exit_missing_stuff="1"
    fi
}
check_if_missing hg
check_if_missing pip3
check_if_missing python3

# Exit if any are missing
if [[ "$exit_missing_stuff" = "1" ]]; then
    exit 1
fi

# Any other arguments?
args="--upgrade --no-cache-dir --target=mek_lib"
if [[ "$reinstall" = "1" ]]; then
    args="$args --force-reinstall"
fi

# Run the command
run_command() {
    if [[ "$quiet" = "1" ]]; then
        $@ >> /dev/null
    else
        $@
    fi
}

# Check to see if the directory exists. If so, pull it. Otherwise, clone it
if [ -d "$destination/.hg" ]; then
    cd "$destination"
    run_command hg pull https://bitbucket.org/Moses_of_Egypt/mek
else
    run_command hg clone https://bitbucket.org/Moses_of_Egypt/mek "$destination"
fi

# If it failed to clone, exit.
if [[ "$?" != "0" ]]; then
    exit 1
fi

# If not, cd into the directory we just cloned the repository into
cd "$destination"

# Now install refinery portably
run_command pip3 install refinery $args
