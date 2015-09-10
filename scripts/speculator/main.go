// speculator allows you to preview pull requests to the matrix.org specification.
// It serves two HTTP endpoints:
//  - /spec/123 which renders the spec as html at pull request 123.
//  - /diff/rst/123 which gives a diff of the spec's rst at pull request 123.
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
	"os"
	"os/exec"
	"path"
	"strconv"
	"strings"
	"syscall"
)

type PullRequest struct {
	Base Commit
	Head Commit
	User User
}

type Commit struct {
	SHA  string
	Repo RequestRepo
}

type RequestRepo struct {
	CloneURL string `json:"clone_url"`
}

type User struct {
	Login string
}

var (
	port           = flag.Int("port", 9000, "Port on which to listen for HTTP")
	allowedMembers map[string]bool
)

func gitClone(url string) (string, error) {
	dst := path.Join("/tmp/matrix-doc", strconv.FormatInt(rand.Int63(), 10))
	cmd := exec.Command("git", "clone", url, dst)
	err := cmd.Run()
	if err != nil {
		return "", fmt.Errorf("error cloning repo: %v", err)
	}
	return dst, nil
}

func gitCheckout(path, sha string) error {
	cmd := exec.Command("git", "checkout", sha)
	cmd.Dir = path
	err := cmd.Run()
	if err != nil {
		return fmt.Errorf("error checking out repo: %v", err)
	}
	return nil
}

func lookupPullRequest(prNumber string) (PullRequest, error) {
	resp, _ := http.Get("https://api.github.com/repos/matrix-org/matrix-doc/pulls/" + prNumber)
	defer resp.Body.Close()
	dec := json.NewDecoder(resp.Body)
	var pr PullRequest
	_ = dec.Decode(&pr)
	return pr, nil
}

func generate(dir string) error {
	cmd := exec.Command("python", "gendoc.py", "--nodelete")
	cmd.Dir = path.Join(dir, "scripts")
	var b bytes.Buffer
	cmd.Stderr = &b
	err := cmd.Run()
	if err != nil {
		return fmt.Errorf("error generating spec: %v\nOutput from gendoc:\n%v", err, b.String())
	}
	return nil
}

func writeError(w http.ResponseWriter, err error) {
	w.WriteHeader(500)
	io.WriteString(w, fmt.Sprintf("%v\n", err))
}

// generateAt generates spec from repo at sha.
// Returns the path where the generation was done.
func generateAt(repo, sha string) (dst string, err error) {
	dst, err = gitClone(repo)
	if err != nil {
		return
	}

	if err = gitCheckout(dst, sha); err != nil {
		return
	}

	err = generate(dst)
	return
}

func serveSpec(w http.ResponseWriter, req *http.Request) {
	parts := strings.Split(req.URL.Path, "/")
	if len(parts) != 3 {
		w.WriteHeader(400)
		io.WriteString(w, fmt.Sprintf("Invalid path passed: %v expect /pull/123", req.URL.Path))
		return
	}

	pr, err := lookupPullRequest(parts[2])
	if err != nil {
		writeError(w, err)
		return
	}

	if !allowedMembers[pr.User.Login] {
		w.WriteHeader(403)
		io.WriteString(w, fmt.Sprintf("%q is not a trusted pull requester", pr.User.Login))
		return
	}

	dst, err := generateAt(pr.Head.Repo.CloneURL, pr.Head.SHA)
	defer os.RemoveAll(dst)
	if err != nil {
		writeError(w, err)
		return
	}

	b, err := ioutil.ReadFile(path.Join(dst, "scripts/gen/specification.html"))
	if err != nil {
		writeError(w, fmt.Errorf("Error reading spec: %v", err))
		return
	}
	w.Write(b)
}

func serveRstDiff(w http.ResponseWriter, req *http.Request) {
	parts := strings.Split(req.URL.Path, "/")
	if len(parts) != 4 {
		w.WriteHeader(400)
		io.WriteString(w, fmt.Sprintf("Invalid path passed: %v expect /diff/rst/123", req.URL.Path))
		return
	}

	pr, err := lookupPullRequest(parts[3])
	if err != nil {
		writeError(w, err)
		return
	}

	if !allowedMembers[pr.User.Login] {
		w.WriteHeader(403)
		io.WriteString(w, fmt.Sprintf("%q is not a trusted pull requester", pr.User.Login))
		return
	}

	base, err := generateAt(pr.Base.Repo.CloneURL, pr.Base.SHA)
	defer os.RemoveAll(base)
	if err != nil {
		writeError(w, err)
		return
	}

	head, err := generateAt(pr.Head.Repo.CloneURL, pr.Head.SHA)
	defer os.RemoveAll(head)
	if err != nil {
		writeError(w, err)
		return
	}

	diffCmd := exec.Command("diff", path.Join(base, "scripts", "tmp", "full_spec.rst"), path.Join(head, "scripts", "tmp", "full_spec.rst"))
	var diff bytes.Buffer
	diffCmd.Stdout = &diff
	if err := ignoreExitCodeOne(diffCmd.Run()); err != nil {
		writeError(w, fmt.Errorf("error running diff: %v", err))
		return
	}
	w.Write(diff.Bytes())
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
	// It would be great to read this from github, but there's no convenient way to do so.
	// Most of these memberships are "private", so would require some kind of auth.
	allowedMembers = map[string]bool{
		"dbkr":          true,
		"erikjohnston":  true,
		"illicitonion":  true,
		"Kegsay":        true,
		"NegativeMjark": true,
	}
	http.HandleFunc("/spec/", serveSpec)
	http.HandleFunc("/diff/rst/", serveRstDiff)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", *port), nil))
}
