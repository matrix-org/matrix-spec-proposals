#!/bin/bash -eu

if [[ $# != 1 || ! -d $1 ]]; then
  echo >&2 "Usage: $0 include_dir"
  exit 1
fi

HEADER="$1/head.html"
NAV_BAR="$1/nav.html"
FOOTER="$1/footer.html"

for f in "$1"/{head,nav,footer}.html; do
  if [[ ! -e "${f}" ]]; then
    echo >&2 "Need ${f} to exist"
    exit 1
  fi
done

files=gen/*.html

perl -MFile::Slurp -pi -e 'BEGIN { $header = read_file("'$HEADER'") } s#<head>#<head>$header
  <link rel="stylesheet" href="//matrix.org/docs/guides/css/docs_overrides.css">
#' ${files}

perl -MFile::Slurp -pi -e 'BEGIN { $nav = read_file("'$NAV_BAR'") } s#<body class="swagger-section">#  <body class=" swagger-section blog et_fixed_nav et_cover_background et_right_sidebar">
   <div id="page-wrapper">
    <div class="page-content" id="page-container">
      $nav
       <div id="main-content">
         <div class="wrapper" id="wrapper">
           <div class="document_foo" id="document">
#' ${files}

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
  </body>#' ${files}
