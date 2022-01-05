# /bin/bash

# Usage: ./generate.sh v1.2 "April 01, 2021"

set -e

MAGIC_STRING="<!-- DO NOT REMOVE OR CHANGE - Release script puts next release here -->"

cd changelogs

# Pre-cleanup just in case it wasn't done on the last run
rm -f rendered.*

# Reversed order so that room versions ends up on the bottom
towncrier --name "Appendices" --dir "./appendices" --config "./pyproject.toml" --yes
towncrier --name "Room Versions" --dir "./room_versions" --config "./pyproject.toml" --yes
towncrier --name "Push Gateway API" --dir "./push_gateway" --config "./pyproject.toml" --yes
towncrier --name "Identity Service API" --dir "./identity_service" --config "./pyproject.toml" --yes
towncrier --name "Application Service API" --dir "./application_service" --config "./pyproject.toml" --yes
towncrier --name "Server-Server API" --dir "./server_server" --config "./pyproject.toml" --yes
towncrier --name "Client-Server API" --dir "./client_server" --config "./pyproject.toml" --yes

# Prepare the header
cp header.md rendered.header.md
sed -i "s/VERSION/$1/g" rendered.header.md
sed -i "s/DATE/$2/g" rendered.header.md
cat rendered.header.md rendered.md > rendered.final.md

# Remove trailing whitespace (such as our intentionally blank RST headings)
sed -i "s/[ ]*$//" rendered.final.md

# Put the changelog in place
mv rendered.final.md ../layouts/partials/changelogs/$1.md
sed -i "s/$MAGIC_STRING/$MAGIC_STRING\n{{% changelog\\/changelog-rendered p=\"changelogs\\/$1.md\" %}}/" ../content/changelog.md

# Cleanup
rm -v rendered.*
