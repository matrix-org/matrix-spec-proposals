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

	fsnotify "gopkg.in/fsnotify.v1"
)

var (
	port = flag.Int("port", 8000, "Port on which to serve HTTP")

	toServe atomic.Value   // Always contains valid []byte to serve. May be stale unless wg is zero.
	wg      sync.WaitGroup // Indicates how many updates are pending.
	mu      sync.Mutex     // Prevent multiple updates in parallel.
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

	filepath.Walk(dir, makeWalker(w))

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
				wg.Add(1)
				fmt.Printf("Noticed change to %s, re-generating spec\n", e.Name)
				ch <- struct{}{}
			}
		}
	}
}

func makeWalker(w *fsnotify.Watcher) filepath.WalkFunc {
	return func(path string, _ os.FileInfo, err error) error {
		if err != nil {
			log.Fatalf("Error walking: %v", err)
		}
		if err := w.Add(path); err != nil {
			log.Fatalf("Failed to add watch: %v", err)
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

	// Avoid infinite cycles being caused by writing actual output
	if strings.Contains(e.Name, "/tmp/") || strings.Contains(e.Name, "/gen/") {
		return false
	}
	return true
}

func serve(w http.ResponseWriter, req *http.Request) {
	wg.Wait()
	b := toServe.Load().([]byte)
	w.Write(b)
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
		toServe.Store([]byte(fmt.Errorf("error generating spec: %v\nOutput from gendoc:\n%v", err, b.String()).Error()))
		return
	}
	specBytes, err := ioutil.ReadFile(path.Join(dir, "scripts", "gen", "specification.html"))
	if err != nil {
		toServe.Store([]byte(fmt.Errorf("error reading spec: %v", err).Error()))
		return
	}
	toServe.Store(specBytes)
}

func doPopulate(ch chan struct{}, dir string) {
	for _ = range ch {
		populateOnce(dir)
	}
}

func exists(path string) bool {
	_, err := os.Stat(path)
	return !os.IsNotExist(err)
}
