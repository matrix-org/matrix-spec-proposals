#!/bin/sh
#
# This script will generate a stable release build of the spec.
# It assumes you have `hugo` set up and configured properly.
#
# Usage:
#
#   ./scripts/prepare-spec-release.sh v<Matrix global version number> <output directory>
#
# Example:
#
#   ./scripts/prepare-spec-release.sh v1.2.3 release/
#
# The released spec files will be available at <output directory>/<Matrix global version number>,
# i.e ./release/v1.2.3/.
#
# This script is used by .buildkite/pipeline as part of building and releasing the spec.

if [ $# -lt 2 ]; then
  echo 1>&2 "$0: not enough arguments"
  exit 2
fi

# Modify the build config to specify a stable release
sed -i.bak -e 's/status = "unstable"/status = "stable"/' config.toml

# Create a release.yaml file which is used to build the changelog entry
tee changelogs/release.yaml <<EOF
  tag: $1
  date: $(date +"%B %d, %Y")
EOF

# Build the spec, and set the baseURL and output directory to the new release version,
# which should match the tag name.
hugo --baseURL "/$1" -d "$2/$1"

# Restore the original config file state
mv config.toml.bak config.toml

echo "Spec release files are available in: $2/$1"