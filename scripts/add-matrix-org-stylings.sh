#! /bin/bash

if [ -z "$1" ]; then
    echo "Expected /includes/head.html file as 1st arg."
    exit 1
fi

if [ -z "$2" ]; then
    echo "Expected /includes/nav.html file as 2nd arg."
    exit 1
fi

if [ -z "$3" ]; then
    echo "Expected /includes/footer.html file as 3rd arg."
    exit 1
fi


HEADER=$1
NAV_BAR=$2
FOOTER=$3

if [ ! -f $HEADER ]; then
    echo $HEADER " does not exist"
    exit 1
fi

if [ ! -f $NAV_BAR ]; then
    echo $NAV_BAR " does not exist"
    exit 1
fi

if [ ! -f $FOOTER ]; then
    echo $FOOTER " does not exist"
    exit 1
fi

perl -MFile::Slurp -pi -e 'BEGIN { $header = read_file("'$HEADER'") } s#<head>#<head>$header
  <link rel="stylesheet" href="//matrix.org/docs/guides/css/docs_overrides.css">
#' gen/specification.html gen/howtos.html

perl -MFile::Slurp -pi -e 'BEGIN { $nav = read_file("'$NAV_BAR'") } s#<body>#  <body class="blog et_fixed_nav et_cover_background et_right_sidebar">
   <div id="page-wrapper">
    <div class="page-content" id="page-container">
      $nav
       <div id="main-content">
         <div class="wrapper" id="wrapper">
           <div class="document_foo" id="document">
#' gen/specification.html gen/howtos.html

perl -MFile::Slurp -pi -e 'BEGIN { $footer = read_file("'$FOOTER'") } s#</body>#
            </div>
          </div>
          <div class="push">
          </div>
        </div>
      </div>
        $footer
      </div>
    </div>
  </body>#' gen/specification.html gen/howtos.html
