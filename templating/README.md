This folder contains the templates and templating system for creating the spec.
We use the templating system Jinja2 in Python. This was chosen over other
systems such as Handlebars.js and Templetor because we already have a Python
dependency on the spec build system, and Jinja provides a rich set of template
operations beyond basic control flow.

Installation
------------
```
 $ pip install Jinja2
```

Running
-------
To build the spec:
```
 $ python build.py
```

This will output ``spec.rst`` which can then be fed into the RST->HTML
converter located in ``matrix-doc/scripts``.
