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

var isDir = fs.lstatSync(opts.schema).isDirectory()
if (isDir) {
    console.log("Checking directory %s for .yaml files...", opts.schema);
    fs.readdir(opts.schema, function(err, files) {
        if (err) {
            console.error(err);
            process.exit(1);
        }
        files.forEach(function(f) {
            var suffix = ".yaml";
            if (f.indexOf(suffix, f.length - suffix.length) > 0) {
                parser.validate(path.join(opts.schema, f), function(err, api, metadata) {
                    if (!err) {
                        console.log("%s is valid.", f);
                    }
                    else {
                        console.error("%s is not valid.", f);
                        errFn(err, api, metadata);
                    }
                });
            } 
        });
    });
}
else{
    parser.validate(opts.schema, function(err, api) {
        if (!err) {
            console.log("%s is valid", opts.schema);
        }
        else {
            errFn(err, api);
        }
    });
};

