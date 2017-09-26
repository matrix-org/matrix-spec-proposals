Generating the HTML for the specification
=========================================

Requirements:
 - docutils (for converting RST to HTML)
 - Jinja2 (for templating)
 - PyYAML (for reading YAML files)

Nix[2] users can enter an environment with the appropriate tools and
dependencies available by invoking `nix-shell contrib/shell.nix` in this
directory.

To generate the complete specification along with supporting documentation, run:
    python gendoc.py

The output of this will be inside the "scripts/gen" folder.

Matrix.org only ("gen" folder has matrix.org tweaked pages):
    ./matrix-org-gendoc.sh /path/to/matrix.org/includes/nav.html


Generating the Swagger documentation
====================================
Swagger[1] is a framework for representing RESTful APIs. We use it to generate 
interactive documentation for our APIs.

Swagger UI reads a JSON description of the API. To generate this file from the
YAML files in the `api` folder, run:
    ./dump-swagger.py

By default, `dump-swagger` will write to `scripts/swagger/api-docs.json`.

To make use of the generated file, there are a number of options:
 * It can be uploaded from your filesystem to an online editor/viewer such as
   http://editor.swagger.io/
 * You can run a local HTTP server by running `./swagger-http-server.py`, and
   then view the documentation via an online viewer; for example, at
   http://petstore.swagger.io/?url=http://localhost:8000/api-docs.json
 * You can host the swagger UI yourself:
   * download the latest release from https://github.com/swagger-api/swagger-ui
   * copy the contents of the 'dist' directory alongside `api-docs.json`
   * View the UI via your browser at http://\<hostname>?url=api-docs.json

[1] http://swagger.io/
[2] https://nixos.org/nix/
