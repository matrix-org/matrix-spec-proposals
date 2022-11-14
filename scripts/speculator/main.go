// speculator allows you to preview pull requests to the matrix.org specification.
// It serves the following HTTP endpoints:
//  - / lists open pull requests
//  - /spec/123 which renders the spec as html at pull request 123.
//  - /diff/rst/123 which gives a diff of the spec's rst at pull request 123.
//  - /diff/html/123 which gives a diff of the spec's HTML at pull request 123.
// It is currently woefully inefficient, and there is a lot of low hanging fruit for improvement.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"text/template"
	"time"

	"github.com/hashicorp/golang-lru"
)

type PullRequest struct {
	Number  int
	Base    Commit
	Head    Commit
	Title   string
	User    User
	HTMLURL string `json:"html_url"`
}

type Commit struct {
	SHA  string
	Repo RequestRepo
}

type RequestRepo struct {
	CloneURL string `json:"clone_url"`
}

type User struct {
	Login   string
	HTMLURL string `json:"html_url"`
}

var (
	port            = flag.Int("port", 9000, "Port on which to listen for HTTP")
	includesDir     = flag.String("includes_dir", "", "Directory containing include files for styling like matrix.org")
	accessToken     = flag.String("access_token", "", "github.com access token")
	allowedMembers  map[string]bool
	specCache       *lru.Cache // string -> map[string][]byte filename -> contents
	styledSpecCache *lru.Cache // string -> map[string][]byte filename -> contents
)

func (u *User) IsTrusted() bool {
	return allowedMembers[u.Login]
}

const (
	pullsPrefix          = "https://api.github.com/repos/matrix-org/matrix-doc/pulls"
	matrixDocCloneURL    = "https://github.com/matrix-org/matrix-doc.git"
	permissionsOwnerFull = 0700
)

var numericRegex = regexp.MustCompile(`^\d+$`)

func accessTokenQuerystring() string {
	if *accessToken == "" {
		return ""
	}
	return fmt.Sprintf("?access_token=%s", *accessToken)
}

func gitClone(url string, directory string, shared bool) error {
	args := []string{"clone", url, directory}
	if shared {
		args = append(args, "--shared")
	}
	if err := runGitCommand(directory, args); err != nil {
		return err
	}
	return nil
}

func gitCheckout(path, sha string) error {
	return runGitCommand(path, []string{"checkout", sha})
}

func runGitCommand(path string, args []string) error {
	cmd := exec.Command("git", args...)
	cmd.Dir = path
	var b bytes.Buffer
	cmd.Stderr = &b
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("error running %q: %v (stderr: %s)", strings.Join(cmd.Args, " "), err, b.String())
	}
	return nil
}

func lookupPullRequest(prNumber string) (*PullRequest, error) {
	resp, err := http.Get(fmt.Sprintf("%s/%s%s", pullsPrefix, prNumber, accessTokenQuerystring()))
	defer resp.Body.Close()
	if err != nil {
		return nil, fmt.Errorf("error getting pulls: %v", err)
	}
	if resp.StatusCode != 200 {
		body, _ := ioutil.ReadAll(resp.Body)
		return nil, fmt.Errorf("error getting pull request %s: %v", prNumber, string(body))
	}
	dec := json.NewDecoder(resp.Body)
	var pr PullRequest
	if err := dec.Decode(&pr); err != nil {
		return nil, fmt.Errorf("error decoding pulls: %v", err)
	}
	return &pr, nil
}

func (s *server) lookupBranch(branch string) (string, error) {
	err := s.updateBase()
	if err != nil {
		log.Printf("Error fetching: %v, will use cached branches")
	}

	if strings.ToLower(branch) == "head" {
		branch = "master"
	}
	branch = "origin/" + branch
	sha, err := s.getSHAOf(branch)
	if err != nil {
		return "", fmt.Errorf("error getting branch %s: %v", branch, err)
	}
	if sha == "" {
		return "", fmt.Errorf("Unable to get sha for %s", branch)
	}
	return sha, nil
}

func generate(dir string) error {
	cmd := exec.Command("python", "gendoc.py", "--nodelete")
	cmd.Dir = path.Join(dir, "scripts")
	var b bytes.Buffer
	cmd.Stderr = &b
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("error generating spec: %v\nOutput from gendoc:\n%v", err, b.String())
	}

	// cheekily dump the swagger docs into the gen directory so they can be
	// served by serveSpec
	cmd = exec.Command("python", "dump-swagger.py", "-o", "gen/api-docs.json")
	cmd.Dir = path.Join(dir, "scripts")
	cmd.Stderr = &b
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("error generating api docs: %v\nOutput from dump-swagger:\n%v", err, b.String())
	}

	return nil
}

func writeError(w http.ResponseWriter, code int, err error) {
	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(code)
	io.WriteString(w, fmt.Sprintf("%v\n", err))
}

type server struct {
	mu                sync.Mutex // Must be locked around any git command on matrixDocCloneURL
	matrixDocCloneURL string
}

func (s *server) updateBase() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	return runGitCommand(s.matrixDocCloneURL, []string{"fetch"})
}

// canCheckout returns whether a given sha can currently be checked out from s.matrixDocCloneURL.
func (s *server) canCheckout(sha string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return runGitCommand(s.matrixDocCloneURL, []string{"cat-file", "-e", sha + "^{commit}"}) == nil
}

// generateAt generates spec from repo at sha.
// Returns the path where the generation was done.
func (s *server) generateAt(sha string) (dst string, err error) {
	if !s.canCheckout(sha) {
		err = s.updateBase()
		if err != nil {
			return
		}
	}

	dst, err = makeTempDir()
	if err != nil {
		return
	}
	log.Printf("Generating %s in %s\n", sha, dst)
	s.mu.Lock()
	err = gitClone(s.matrixDocCloneURL, dst, true)
	s.mu.Unlock()
	if err != nil {
		return
	}

	if err = gitCheckout(dst, sha); err != nil {
		return
	}

	err = generate(dst)
	return
}

func (s *server) getSHAOf(ref string) (string, error) {
	cmd := exec.Command("git", "rev-list", ref, "-n1")
	cmd.Dir = path.Join(s.matrixDocCloneURL)
	var b bytes.Buffer
	cmd.Stdout = &b
	s.mu.Lock()
	err := cmd.Run()
	s.mu.Unlock()
	if err != nil {
		return "", fmt.Errorf("error generating spec: %v\nOutput from git:\n%v", err, b.String())
	}
	return strings.TrimSpace(b.String()), nil
}

// extractPRNumber checks that the path begins with the given base, and returns
// the following component.
func extractPRNumber(path, base string) (string, error) {
	if !strings.HasPrefix(path, base+"/") {
		return "", fmt.Errorf("invalid path passed: %q expect %s/123", path, base)
	}
	return strings.Split(path[len(base)+1:], "/")[0], nil
}

// extractPath extracts the file path within the gen directory which should be served for the request.
// Returns one of (file to serve, path to redirect to).
// path is the actual path being requested, e.g. "/spec/head/client_server.html".
// base is the base path of the handler, including a trailing slash, before the PR number, e.g. "/spec/".
func extractPath(path, base string) (string, string) {
	// Assumes exactly one flat directory

	// Count slashes in /spec/head/client_server.html
	// base is /spec/
	// +1 for the PR number - /spec/head
	// +1 for the path-part after the slash after the PR number
	max := strings.Count(base, "/") + 2
	parts := strings.SplitN(path, "/", max)

	if len(parts) < max {
		// Path is base/pr - redirect to base/pr/index.html
		return "", path + "/index.html"
	}
	if parts[max-1] == "" {
		// Path is base/pr/ - serve index.html
		return "index.html", ""
	}

	// Path is base/pr/file.html - serve file
	return parts[max-1], ""
}

func (s *server) serveSpec(w http.ResponseWriter, req *http.Request) {
	var sha string

	var styleLikeMatrixDotOrg = req.URL.Query().Get("matrixdotorgstyle") != ""

	if styleLikeMatrixDotOrg && *includesDir == "" {
		writeError(w, 500, fmt.Errorf("Cannot style like matrix.org - no include dir specified"))
		return
	}

	// we use URL.EscapedPath() to get hold of the %-encoded version of the
	// path, so that we can handle branch names with slashes in.
	urlPath := req.URL.EscapedPath()

	if urlPath == "/spec" {
		// special treatment for /spec - redirect to /spec/HEAD/
		s.redirectTo(w, req, "/spec/HEAD/")
		return
	}

	if !strings.HasPrefix(urlPath, "/spec/") {
		writeError(w, 500, fmt.Errorf("invalid path passed: %q expect /spec/...", urlPath))
	}

	splits := strings.SplitN(urlPath[6:], "/", 2)

	if len(splits) == 1 {
		// "/spec/foo" - redirect to "/spec/foo/" (so that relative links from the index work)
		if splits[0] == "" {
			s.redirectTo(w, req, "/spec/HEAD/")
		} else {
			s.redirectTo(w, req, urlPath+"/")
		}
		return
	}

	// now we have:
	//   splits[0] is a PR#, or a branch name
	//   splits[1] is the file to serve

	branchName, _ := url.QueryUnescape(splits[0])
	requestedPath, _ := url.QueryUnescape(splits[1])
	if requestedPath == "" {
		requestedPath = "index.html"
	}

	if numericRegex.MatchString(branchName) {
		// PR number
		pr, err := lookupPullRequest(branchName)
		if err != nil {
			writeError(w, 400, err)
			return
		}

		// We're going to run whatever Python is specified in the pull request, which
		// may do bad things, so only trust people we trust.
		if err := checkAuth(pr); err != nil {
			writeError(w, 403, err)
			return
		}
		sha = pr.Head.SHA
		log.Printf("Serving pr %s (%s)\n", branchName, sha)
	} else if strings.ToLower(branchName) == "head" ||
		branchName == "master" ||
		strings.HasPrefix(branchName, "attic/drafts/") {
		branchSHA, err := s.lookupBranch(branchName)
		if err != nil {
			writeError(w, 400, err)
			return
		}
		sha = branchSHA
		log.Printf("Serving branch %s (%s)\n", branchName, sha)
	} else {
		writeError(w, 404, fmt.Errorf("invalid branch name"))
		return
	}

	var cache = specCache
	if styleLikeMatrixDotOrg {
		cache = styledSpecCache
	}

	var pathToContent map[string][]byte

	if cached, ok := cache.Get(sha); ok {
		pathToContent = cached.(map[string][]byte)
	} else {
		dst, err := s.generateAt(sha)
		defer os.RemoveAll(dst)
		if err != nil {
			writeError(w, 500, err)
			return
		}

		pathToContent = make(map[string][]byte)
		scriptsdir := path.Join(dst, "scripts")
		base := path.Join(scriptsdir, "gen")
		walker := func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			if info.IsDir() {
				return nil
			}

			rel, err := filepath.Rel(base, path)
			if err != nil {
				return fmt.Errorf("Failed to get relative path of %s: %v", path, err)
			}

			if styleLikeMatrixDotOrg {
				cmd := exec.Command("./add-matrix-org-stylings.pl", *includesDir, path)
				cmd.Dir = scriptsdir
				var b bytes.Buffer
				cmd.Stderr = &b
				if err := cmd.Run(); err != nil {
					return fmt.Errorf("error styling spec: %v\nOutput:\n%v", err, b.String())
				}
			}

			bytes, err := ioutil.ReadFile(path)
			if err != nil {
				return fmt.Errorf("Error reading spec: %v", err)
			}
			pathToContent[rel] = bytes
			return nil
		}

		err = filepath.Walk(base, walker)
		if err != nil {
			writeError(w, 500, err)
			return
		}
		cache.Add(sha, pathToContent)
	}

	if requestedPath == "api-docs.json" {
		// allow other swagger UIs access to our swagger
		w.Header().Set("Access-Control-Allow-Origin", "*")
	}

	if b, ok := pathToContent[requestedPath]; ok {
		w.Write(b)
		return
	}
	if requestedPath == "index.html" {
		// Fall back to single-page spec for old PRs
		if b, ok := pathToContent["specification.html"]; ok {
			w.Write(b)
			return
		}
	}
	w.WriteHeader(404)
	w.Write([]byte("Not found"))
}

func (s *server) redirectTo(w http.ResponseWriter, req *http.Request, path string) {
	u := *req.URL
	u.Scheme = "http"
	u.Host = req.Host
	u.Path = path
	w.Header().Set("Location", u.String())
	w.WriteHeader(302)
}

func checkAuth(pr *PullRequest) error {
	if !pr.User.IsTrusted() {
		return fmt.Errorf("%q is not a trusted pull requester", pr.User.Login)
	}
	return nil
}

func (s *server) serveRSTDiff(w http.ResponseWriter, req *http.Request) {
	prNumber, err := extractPRNumber(req.URL.Path, "/diff/rst")
	if err != nil {
		writeError(w, 400, err)
		return
	}
	pr, err := lookupPullRequest(prNumber)
	if err != nil {
		writeError(w, 400, err)
		return
	}

	// We're going to run whatever Python is specified in the pull request, which
	// may do bad things, so only trust people we trust.
	if err := checkAuth(pr); err != nil {
		writeError(w, 403, err)
		return
	}

	base, err := s.generateAt(pr.Base.SHA)
	defer os.RemoveAll(base)
	if err != nil {
		writeError(w, 500, err)
		return
	}

	head, err := s.generateAt(pr.Head.SHA)
	defer os.RemoveAll(head)
	if err != nil {
		writeError(w, 500, err)
		return
	}

	diffCmd := exec.Command("diff", "-r", "-u", path.Join(base, "scripts", "tmp"), path.Join(head, "scripts", "tmp"))
	var diff bytes.Buffer
	diffCmd.Stdout = &diff
	if err := ignoreExitCodeOne(diffCmd.Run()); err != nil {
		writeError(w, 500, fmt.Errorf("error running diff: %v", err))
		return
	}
	w.Write(diff.Bytes())
}

func (s *server) serveHTMLDiff(w http.ResponseWriter, req *http.Request) {
	prNumber, err := extractPRNumber(req.URL.Path, "/diff/html")
	if err != nil {
		writeError(w, 400, err)
		return
	}
	pr, err := lookupPullRequest(prNumber)
	if err != nil {
		writeError(w, 400, err)
		return
	}

	// We're going to run whatever Python is specified in the pull request, which
	// may do bad things, so only trust people we trust.
	if err := checkAuth(pr); err != nil {
		writeError(w, 403, err)
		return
	}

	base, err := s.generateAt(pr.Base.SHA)
	defer os.RemoveAll(base)
	if err != nil {
		writeError(w, 500, err)
		return
	}

	head, err := s.generateAt(pr.Head.SHA)
	defer os.RemoveAll(head)
	if err != nil {
		writeError(w, 500, err)
		return
	}

	htmlDiffer, err := findHTMLDiffer()
	if err != nil {
		writeError(w, 500, fmt.Errorf("could not find HTML differ"))
		return
	}

	requestedPath, redirect := extractPath(req.URL.Path, "/diff/spec/")
	if redirect != "" {
		s.redirectTo(w, req, redirect)
		return
	}
	cmd := exec.Command(htmlDiffer, path.Join(base, "scripts", "gen", requestedPath), path.Join(head, "scripts", "gen", requestedPath))
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		writeError(w, 500, fmt.Errorf("error running HTML differ: %v\nOutput:\n%v", err, stderr.String()))
		return
	}
	w.Write(stdout.Bytes())
}

func findHTMLDiffer() (string, error) {
	wd, err := os.Getwd()
	if err != nil {
		return "", err
	}
	differ := path.Join(wd, "htmldiff.pl")
	if _, err := os.Stat(differ); err == nil {
		return differ, nil
	}
	return "", fmt.Errorf("unable to find htmldiff.pl")
}

func getPulls() ([]PullRequest, error) {
	resp, err := http.Get(fmt.Sprintf("%s%s", pullsPrefix, accessTokenQuerystring()))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		body, _ := ioutil.ReadAll(resp.Body)
		return nil, fmt.Errorf("error getting pull requests: %v", string(body))
	}
	dec := json.NewDecoder(resp.Body)
	var pulls []PullRequest
	err = dec.Decode(&pulls)
	return pulls, err
}

// getBranches returns a list of the upstream branch names.
// It attempts to `git fetch` before doing so.
func (s *server) getBranches() ([]string, error) {
	err := s.updateBase()
	if err != nil {
		log.Printf("Error fetching: %v, will use cached branches")
	}

	cmd := exec.Command("git", "branch", "-r")
	cmd.Dir = path.Join(s.matrixDocCloneURL)
	var b bytes.Buffer
	cmd.Stdout = &b
	s.mu.Lock()
	err = cmd.Run()
	s.mu.Unlock()
	if err != nil {
		return nil, fmt.Errorf("Error reading branch names: %v. Output from git:\n%v", err, b.String())
	}
	branches := []string{}
	for _, b := range strings.Split(b.String(), "\n") {
		b = strings.TrimSpace(b)
		if strings.HasPrefix(b, "origin/") {
			branches = append(branches, b[7:])
		}
	}
	return branches, nil
}

func (srv *server) makeIndex(w http.ResponseWriter, req *http.Request) {
	pulls, err := getPulls()
	if err != nil {
		writeError(w, 500, err)
		return
	}

	branches, err := srv.getBranches()
	if err != nil {
		writeError(w, 500, err)
		return
	}

	// write our stuff into a buffer so that we can change our minds
	// and write a 500 if it all goes wrong.
	var b bytes.Buffer
	b.Write([]byte(`
<head>
<script>
function redirectToApiDocs(relativePath) {
    var url = new URL(window.location);
    url.pathname += relativePath;
    var newLoc = "http://matrix.org/docs/api/client-server/?url=" + encodeURIComponent(url);
    window.location = newLoc;
}
</script>
</head>
<body><ul>
`))

	tmpl, err := template.New("pr entry").Parse(`
<li>{{.Number}}:
 <a href="{{.User.HTMLURL}}">{{.User.Login}}</a>:
 <a href="{{.HTMLURL}}">{{.Title}}</a>:
 <a href="spec/{{.Number}}/">spec</a>
 <a href="#" onclick="redirectToApiDocs('spec/{{.Number}}/api-docs.json')">api docs</a>
 <a href="diff/html/{{.Number}}/">spec diff</a>
 <a href="diff/rst/{{.Number}}/">rst diff</a>
</li>
`)
	if err != nil {
		log.Fatal(err)
	}

	for _, pull := range pulls {
		err = tmpl.Execute(&b, pull)
		if err != nil {
			writeError(w, 500, err)
			return
		}
	}
	b.Write([]byte(`
</ul>
<div>View the spec at:<ul>
`))
	branchNames := []string{}
	for _, branch := range branches {
		if strings.HasPrefix(branch, "drafts/") {
			branchNames = append(branchNames, branch)
		}
	}
	branchNames = append(branchNames, "HEAD")
	for _, branch := range branchNames {
		href := "spec/" + url.QueryEscape(branch) + "/"
		fmt.Fprintf(&b, "<li><a href=\"%s\">%s</a></li>\n", href, branch)
		if *includesDir != "" {
			fmt.Fprintf(&b, "<li><a href=\"%s?matrixdotorgstyle=1\">%s, styled like matrix.org</a></li>\n",
				href, branch)
		}
	}
	b.Write([]byte("</ul></div>\n\n"))

	b.Write([]byte("<div>View the API docs at:<ul>"))
	for _, branch := range branchNames {
		fmt.Fprintf(&b,
			"<li><a href=\"#\" onclick=\"redirectToApiDocs('spec/%s/api-docs.json')\">%s</a></li>\n",
			url.QueryEscape(branch), branch)
	}
	b.Write([]byte("</ul></div>"))

	b.Write([]byte("</body>"))
	b.WriteTo(w)
}

func ignoreExitCodeOne(err error) error {
	if err == nil {
		return err
	}

	if exiterr, ok := err.(*exec.ExitError); ok {
		if status, ok := exiterr.Sys().(syscall.WaitStatus); ok {
			if status.ExitStatus() == 1 {
				return nil
			}
		}
	}
	return err
}

func main() {
	flag.Parse()
	// It would be great to read this from github
	// cf https://github.com/matrix-org/matrix-doc/issues/1384
	allowedMembers = map[string]bool{
		"dbkr":          true,
		"erikjohnston":  true,
		"illicitonion":  true,
		"Kegsay":        true,
		"NegativeMjark": true,
		"richvdh":       true,
		"ara4n":         true,
		"leonerd":       true,
		"rxl881":        true,
		"uhoreg":        true,
		"turt2live":     true,
		"Half-Shot":     true,
		"anoadragon453": true,
		"mujx":          true,
		"benparsons":    true,
		"KitsuneRal":    true,
	}
	if err := initCache(); err != nil {
		log.Fatal(err)
	}
	rand.Seed(time.Now().Unix())
	masterCloneDir, err := makeTempDir()
	if err != nil {
		log.Fatal(err)
	}
	log.Printf("Creating master clone dir %s\n", masterCloneDir)
	if err = gitClone(matrixDocCloneURL, masterCloneDir, false); err != nil {
		log.Fatal(err)
	}
	s := server{matrixDocCloneURL: masterCloneDir}
	http.HandleFunc("/spec/", forceHTML(s.serveSpec))
	http.HandleFunc("/diff/rst/", s.serveRSTDiff)
	http.HandleFunc("/diff/html/", forceHTML(s.serveHTMLDiff))
	http.HandleFunc("/healthz", serveText("ok"))
	http.HandleFunc("/", forceHTML(s.makeIndex))

	fmt.Printf("Listening on port %d\n", *port)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", *port), nil))
}

func forceHTML(h func(w http.ResponseWriter, req *http.Request)) func(w http.ResponseWriter, req *http.Request) {
	return func(w http.ResponseWriter, req *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		h(w, req)
	}
}

func serveText(s string) func(http.ResponseWriter, *http.Request) {
	return func(w http.ResponseWriter, req *http.Request) {
		io.WriteString(w, s)
	}
}

func initCache() error {
	c1, err := lru.New(50) // Evict after 50 entries (i.e. 50 sha1s)
	specCache = c1

	c2, err := lru.New(50) // Evict after 50 entries (i.e. 50 sha1s)
	styledSpecCache = c2
	return err
}

func makeTempDir() (string, error) {
	directory := path.Join("/tmp/matrix-doc", strconv.FormatInt(rand.Int63(), 10))
	if err := os.MkdirAll(directory, permissionsOwnerFull); err != nil {
		return "", fmt.Errorf("error making directory %s: %v", directory, err)
	}
	return directory, nil
}
