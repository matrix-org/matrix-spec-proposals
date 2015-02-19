#! /bin/bash

if [ -z "$1" ]; then
    echo "Expected /includes/nav.html file as arg."
    exit 1
fi

NAV_BAR=$1

if [ ! -f $NAV_BAR ]; then
    echo $NAV_BAR " does not exist"
    exit 1
fi

python gendoc.py

perl -pi -e 's#<head>#<head><link rel="stylesheet" href="/site.css">#' gen/specification.html gen/howtos.html

perl -MFile::Slurp -pi -e 'BEGIN { $nav = read_file("'$NAV_BAR'") } s#<body>#<body><div id="header"><div id="headerContent">$nav</div></div><div id="page"><div id="wrapper"><div style="text-align: center; padding: 40px;"><a href="/"><img src="/matrix.png" width="305" height="130" alt="[matrix]"/></a></div>#' gen/specification.html gen/howtos.html

perl -pi -e 's#</body>#</div></div><div id="footer"><div id="footerContent">&copy 2014-2015 Matrix.org</div></div></body>#' gen/specification.html gen/howtos.html
