"use strict";
var nopt = require("nopt");
var parser = require("swagger-parser");
var path = require("path");

var opts = nopt({
    "help": Boolean,
    "schema": path
}, {
    "h": "--help",
    "s": "--schema"
});

if (opts.help) {
    console.log(
        "Use swagger-parser to validate against Swagger 2.0\n"+
        "Usage:\n"+
        "  node validator.js -s <schema_file>"
    );
    process.exit(0);
}
if (!opts.schema) {
    console.error("No [s]chema specified.");
    process.exit(1);
}

parser.parse(opts.schema, function(err, api, metadata) {
    if (!err) {
        console.log("%s is valid.", opts.schema);
        process.exit(0);
        return;
    }
    console.log(metadata);
    console.error(err);
    process.exit(1);
});