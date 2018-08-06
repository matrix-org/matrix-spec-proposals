This folder contains the templates and a home-brewed templating system called
Batesian for creating the spec. Batesian uses the templating system Jinja2 in
Python.

Installation
------------
```
 $ pip install Jinja2
```

Running
-------
To pass arbitrary files (not limited to RST) through the templating system:
```
 $ python build.py -i matrix_templates /random/file/path/here.rst
```

The template output can be found at ``out/here.rst``. For a full list of
options, type ``python build.py --help``.

Developing
----------

### Sections and Units
Batesian is built around the concept of Sections and Units. Sections are strings
which will be inserted into the provided document. Every section has a unique
key name which is the template variable that it represents. Units are arbitrary
python data. They are also represented by unique key names.

### Adding template variables
If you want to add a new template variable e.g. `{{foo_bar}}` which is replaced
with the text `foobar`, you need to add a new Section:

 - Open `matrix_templates/sections.py`.
 - Add a new function to `MatrixSections` called `render_foo_bar`. The function
   name after `render_` determines the template variable name, and the return
   value of this function determines what will be inserted.

   ```python
   def render_foo_bar(self):
       return "foobar"
   ```
 - Run `build.py` with a file which has `{{foo_bar}}` in it, and it will be
   replaced with `foobar`.

### Adding data for template variables
If you want to expose arbitrary data which can be used by `MatrixSections`, you
need to add a new Unit:

 - Open `matrix_templates/units.py`.
 - Add a new function to `MatrixUnits` called `load_some_data`. Similar to
   sections, the function name after `load_` determines the unit name, and the
   return value of this function determines the value of the unit.

   ```python
   def load_some_data(self):
       return {
          "data": "this could be JSON from file from json.loads()",
          "processed_data": "this data may have helper keys added",
          "types": "it doesn't even need to be a dict. Whatever you want!"
       }
   ```
 - In `MatrixSections`, you can now call `self.units.get("some_data")` to
   retrieve the value you returned.
   
### Using Jinja templates
Sections can use Jinja templates to return text. Batesian will attempt to load
all templates from `matrix_templates/templates/`. These can be accessed in
Section code via `template = self.env.get_template("name_of_template.tmpl")`. At
this point, the `template` is just a standard `jinja2.Template`. In fact,
`self.env` is just a `jinja2.Environment`.

### Debugging
If you don't know why your template isn't behaving as you'd expect, or you just
want to add some informative logging, use `self.log` in either the Sections
class or Units class. You'll need to add `-v` to `build.py` for these lines to
show.

About
-----

Batesian was designed to be extremely simple and just use Python as its language
rather than another intermediary language like some other templating systems.
This provides a **lot** of flexibility since you aren't contrained by a
templating language. Batesian provides a thin abstraction over Jinja which is
very useful when you want to do random bits of processing then dump the output
into a Jinja template. Its name is derived from Batesian mimicry due to how the
templating system uses Python as its language, but in a harmless way.
