// continuserv proactively re-generates the spec on filesystem changes, and serves it over HTTP.
// It will always serve the most recent version of the spec, and may block an HTTP request until regeneration is finished.
// It does not currently pre-empt stale generations, but will block until they are complete.
package main

import (
	"bytes"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	fsnotify "gopkg.in/fsnotify.v1"
)

var (
	port = flag.Int("port", 8000, "Port on which to serve HTTP")

	mu      sync.Mutex   // Prevent multiple updates in parallel.
	toServe atomic.Value // Always contains a bytesOrErr. May be stale unless wg is zero.

	wgMu sync.Mutex     // Prevent multiple calls to wg.Wait() or wg.Add(positive number) in parallel.
	wg   sync.WaitGroup // Indicates how many updates are pending.
)

func main() {
	flag.Parse()

	w, err := fsnotify.NewWatcher()
	if err != nil {
		log.Fatalf("Error making watcher: %v", err)
	}

	dir, err := os.Getwd()
	if err != nil {
		log.Fatalf("Error getting wd: %v", err)
	}
	for ; !exists(path.Join(dir, ".git")); dir = path.Dir(dir) {
		if dir == "/" {
			log.Fatalf("Could not find git root")
		}
	}

	walker := makeWalker(dir, w)
	paths := []string{"api", "changelogs", "event-schemas", "scripts",
		"specification", "templating"}

	for _, p := range paths {
		filepath.Walk(path.Join(dir, p), walker)
	}

	wg.Add(1)
	populateOnce(dir)

	ch := make(chan struct{}, 100) // Buffered to ensure we can multiple-increment wg for pending writes
	go doPopulate(ch, dir)

	go watchFS(ch, w)
	fmt.Printf("Listening on port %d\n", *port)
	http.HandleFunc("/", serve)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", *port), nil))

}

func watchFS(ch chan struct{}, w *fsnotify.Watcher) {
	for {
		select {
		case e := <-w.Events:
			if filter(e) {
				fmt.Printf("Noticed change to %s, re-generating spec\n", e.Name)
				ch <- struct{}{}
			}
		}
	}
}

func makeWalker(base string, w *fsnotify.Watcher) filepath.WalkFunc {
	return func(path string, _ os.FileInfo, err error) error {
		if err != nil {
			log.Fatalf("Error walking: %v", err)
		}

		rel, err := filepath.Rel(base, path)
		if err != nil {
			log.Fatalf("Failed to get relative path of %s: %v", path, err)
		}

		// skip a few things that we know don't form part of the spec
		if rel == "api/node_modules" ||
			rel == "scripts/gen" ||
			rel == "scripts/tmp" {
			return filepath.SkipDir
		}

		// log.Printf("Adding watch on %s", path)
		if err := w.Add(path); err != nil {
			log.Fatalf("Failed to add watch on %s: %v", path, err)
		}
		return nil
	}
}

// Return true if event should trigger re-population
func filter(e fsnotify.Event) bool {
	// vim is *really* noisy about how it writes files
	if e.Op != fsnotify.Write {
		return false
	}

	// Avoid some temp files that vim writes
	if strings.HasSuffix(e.Name, "~") || strings.HasSuffix(e.Name, ".swp") || strings.HasPrefix(e.Name, ".") {
		return false
	}

	return true
}

func serve(w http.ResponseWriter, req *http.Request) {
	wgMu.Lock()
	wg.Wait()
	wgMu.Unlock()

	file := req.URL.Path
	if file[0] == '/' {
		file = file[1:]
	}
	if file == "" {
		file = "index.html"
	}
	m := toServe.Load().(bytesOrErr)
	if m.err != nil {
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(m.err.Error()))
		return
	}
	b, ok := m.bytes[file]
	if ok {
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte(b))
		return
	}
	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(404)
	w.Write([]byte("Not found"))
}

func populateOnce(dir string) {
	defer wg.Done()
	mu.Lock()
	defer mu.Unlock()
	cmd := exec.Command("python", "gendoc.py")
	cmd.Dir = path.Join(dir, "scripts")
	var b bytes.Buffer
	cmd.Stderr = &b
	err := cmd.Run()
	if err != nil {
		toServe.Store(bytesOrErr{nil, fmt.Errorf("error generating spec: %v\nOutput from gendoc:\n%v", err, b.String())})
		return
	}

	files := make(map[string][]byte)
	base := path.Join(dir, "scripts", "gen")
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

		bytes, err := ioutil.ReadFile(path)
		if err != nil {
			return err
		}
		files[rel] = bytes
		return nil
	}

	err = filepath.Walk(base, walker)
	if err != nil {
		toServe.Store(bytesOrErr{nil, fmt.Errorf("error reading spec: %v", err)})
		return
	}
	toServe.Store(bytesOrErr{files, nil})
}

func doPopulate(ch chan struct{}, dir string) {
	var pending int
	for {
		select {
		case <-ch:
			if pending == 0 {
				wgMu.Lock()
				wg.Add(1)
				wgMu.Unlock()
			}
			pending++
		case <-time.After(10 * time.Millisecond):
			if pending > 0 {
				pending = 0
				populateOnce(dir)
			}
		}
	}
}

func exists(path string) bool {
	_, err := os.Stat(path)
	return !os.IsNotExist(err)
}

type bytesOrErr struct {
	bytes map[string][]byte // filename -> contents
	err   error
}
