"use strict";
var fs = require("fs");
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
        "  node validator.js -s <schema_file_or_folder>"
    );
    process.exit(0);
}
if (!opts.schema) {
    console.error("No [s]chema specified.");
    process.exit(1);
}


var errFn = function(err, api) {
    if (!err) {
        return;
    }
    console.error(err);
    process.exit(1);
};

/**
 * @brief Produce a handler for parser.validate().
 * Recommended usage: `parser.validate(filename, makeHandler(filename));`
 * or `parser.validate(schema, makeHandler());`.
 * @param scope - usually a filename, this will be used to denote
 *                an (in)valid schema in console output; "Schema" if undefined
 * @returns {function} the handler that can be passed to parser.validate
 */
function makeHandler(scope) {
    if (!scope)
        scope = "Schema";
    return function(err, api, metadata) {
        if (err) {
            console.error("%s is not valid.", scope || "Schema");
            errFn(err, api, metadata); // Won't return
        }

        Object.keys(api.paths).forEach(function (endpoint) {
            var operationsMap = api.paths[endpoint];
            Object.keys(operationsMap).forEach(function (verb) {
                if (!operationsMap[verb]["operationId"]) {
                    console.error("%s is not valid", scope);
                    errFn("operationId is missing in " + endpoint + ", verb " + verb, api);
                }
            })
        });

        console.log("%s is valid.", scope);
    }
}

var isDir = fs.lstatSync(opts.schema).isDirectory();
if (isDir) {
    console.log("Checking directory %s for .yaml files...", opts.schema);
    fs.readdir(opts.schema, function(err, files) {
        if (err) {
            errFn(err); // Won't return
        }
        files.forEach(function(f) {
            var suffix = ".yaml";
            if (f.indexOf(suffix, f.length - suffix.length) > 0) {
                parser.validate(path.join(opts.schema, f), makeHandler(f));
            }
        });
    });
}
else{
    parser.validate(opts.schema, makeHandler(opts.schema));
}

