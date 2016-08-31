with import <nixpkgs> {};

(python.buildEnv.override {
  extraLibs = with pythonPackages;
    [ docutils pyyaml jinja2 pygments ];
}).env
