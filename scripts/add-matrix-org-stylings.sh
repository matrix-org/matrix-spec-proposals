#!/bin/bash -eu

if [[ $# == 0 || ! -d $1 ]]; then
  echo >&2 "Usage: $0 include_dir file_to_replace..."
  exit 1
fi

include_dir="$1"
shift

HEADER="${include_dir}/head.html"
NAV_BAR="${include_dir}/nav.html"
FOOTER="${include_dir}/footer.html"

for f in "${include_dir}"/{head,nav,footer}.html; do
  if [[ ! -e "${f}" ]]; then
    echo >&2 "Need ${f} to exist"
    exit 1
  fi
done

perl -MFile::Slurp -pi -e 'BEGIN { $header = read_file("'$HEADER'") } s#<head>#<head>$header
  <link rel="stylesheet" href="/docs/guides/css/docs_overrides.css">
#' "$@"

perl -MFile::Slurp -pi -e 'BEGIN { $nav = read_file("'$NAV_BAR'") } s#<body>#  <body class="blog et_fixed_nav et_cover_background et_right_sidebar">
   <div id="page-wrapper">
    <div class="page-content" id="page-container">
      $nav
       <div id="main-content">
         <div class="wrapper" id="wrapper">
           <div class="document_foo" id="document">
#' "$@"

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
  </body>#' "$@"
