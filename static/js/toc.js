  /*
  Account for id attributes that are in the sidebar nav
  */
  function populateIds() {
    const navItems = document.querySelectorAll(".td-sidebar-nav li");
    return Array.from(navItems).map(item => item.id).filter(id => id != "");
  }

  /*
  Given an ID and an array of IDs, return s version of the original ID that's
  not equal to any of the IDs in the array.
  */
  function uniquifyHeadingId(id, uniqueIDs) {
    const baseId = id;
    let counter = 0;
    while (uniqueIDs.includes(id)) {
      counter = counter + 1;
      id = baseId + "-" + counter.toString();
    }
    return id;
  }

  /*
  Given an array of heading nodes, ensure they all have unique IDs.

  We have to do this mostly because of client-server modules, which are
  rendered separately then glued together with a template.
  Because heading IDs are generated in rendering, this means they can and will
  end up with duplicate IDs.
  */
  function uniquifyHeadingIds(headings) {
    const uniqueIDs = populateIds();
    for (let heading of headings) {
      const uniqueID = uniquifyHeadingId(heading.id, uniqueIDs);
      uniqueIDs.push(uniqueID);
      heading.id = uniqueID;
    }
  }

  /*
  The document contains "normal" headings, and these have corresponding items
  in the ToC.

  The document might also contain H1 headings that act as titles for blocks of
  rendered data, like HTTP APIs or event schemas. Unlike "normal" headings,
  these headings don't appear in the ToC. But they do have anchor IDs to enable
  links to them. When someone follows a link to one of these "rendered data"
  headings we want to scroll the ToC to the item corresponding to the "normal"
  heading preceding the "rendered data" heading we have visited.

  To support this we need to add `data` attributes to ToC items.
  These attributes identify which "rendered data" headings live underneath
  the heading corresponding to that ToC item.
  */
  function setTocItemChildren(toc, headings) {
    let tocEntryForHeading  = null;
    for (const heading of headings) {
      // H1 headings are rendered-data headings
      if (heading.tagName !== "H1") {
        tocEntryForHeading = document.querySelector(`nav li a[href="#${heading.id}"]`);
      } else {
        // on the ToC entry for the parent heading,
        // set a data-* attribute whose name is the child's fragment ID
        tocEntryForHeading.setAttribute(`data-${heading.id}`, "true");
      }
    }
  }

  /*
  Generate a table of contents based on the headings in the document.
  */
  function makeToc() {

    // make the title from the H1
    const h1 = document.body.querySelector("h1");
    const title = document.createElement("a");
    title.id = "toc-title";
    title.setAttribute("href", "#");
    title.textContent = h1.textContent;

    // make the content
    const content = document.body.querySelector(".td-content");
    let headings = [].slice.call(content.querySelectorAll("h2, h3, h4, h5, h6, .rendered-data > details > summary > h1"));

    // exclude headings that don't have IDs.
    headings = headings.filter(heading => heading.id);
    uniquifyHeadingIds(headings);

    // exclude .rendered-data > h1 headings from the ToC
    const tocTargets = headings.filter(heading => heading.tagName !== "H1");

    // we have to adjust heading IDs to ensure that they are unique
    const nav = document.createElement("nav");
    nav.id = "TableOfContents";

    const section = makeTocSection(tocTargets, 0);
    nav.appendChild(section.content);
    // append title and content to the #toc placeholder
    const toc = document.body.querySelector("#toc");
    toc.appendChild(title);
    toc.appendChild(nav);

    // tell ToC items about any rendered-data headings they contain
    setTocItemChildren(section.content, headings);
  }

  // create a single ToC entry
  function makeTocEntry(heading) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.setAttribute("href", `#${heading.id}`);
    a.textContent = heading.textContent;
    li.appendChild(a);
    return li;
  }

  /*
  Each ToC section is an `<ol>` element.
  ToC entries are `<li>` elements and these contain nested ToC sections,
  whenever we go to the next heading level down.
  */
  function makeTocSection(headings, index) {
    const ol = document.createElement("ol");
    let previousHeading = null;
    let previousLi = null;
    let i = index;
    const lis = [];

    for (i; i < headings.length; i++) {
      const thisHeading = headings[i];
      if (previousHeading && (thisHeading.tagName > previousHeading.tagName)) {
        // we are going down a heading level, create a new nested section
        const section = makeTocSection(headings, i);
        previousLi.appendChild(section.content);
        i = section.index -1;
      }
      else if (previousHeading && (previousHeading.tagName > thisHeading.tagName)) {
        // we have come back up a level, so a section is finished
        for (let li of lis) {
          ol.appendChild(li);
        }
        return {
          content: ol,
          index: i
        }
      }
      else {
        // we are still processing this section, so add this heading to the current section
        previousLi = makeTocEntry(thisHeading);
        lis.push(previousLi);
        previousHeading = thisHeading;
      }
    }
    for (let li of lis) {
      ol.appendChild(li);
    }
    return  {
      content: ol,
      index: i
    }
  }

  /*
  Set a new ToC entry.
  Clear any previously highlighted ToC items, set the new one,
  and adjust the ToC scroll position.
  */
  function setTocEntry(newEntry) {
    const activeEntries = document.querySelectorAll("#toc a.active");
    for (const activeEntry of activeEntries) {
      activeEntry.classList.remove('active');
    }

    newEntry.classList.add('active');

    // don't scroll the sidebar nav if the main content is not scrolled
    const nav = document.querySelector("#td-section-nav");
    const content = document.querySelector("html");
    if (content.scrollTop !== 0) {
      nav.scrollTop = newEntry.offsetTop - 100;
    } else {
      nav.scrollTop = 0;
    }
  }

  /*
  Test whether a node is in the viewport
  */
  function isInViewport(node) {
    const rect = node.getBoundingClientRect();

    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
  }

  /*
  The callback we pass to the IntersectionObserver constructor.

  Called when any of our observed nodes starts or stops intersecting
  with the viewport.
  */
  function handleIntersectionUpdate(entries) {

    /*
    Special case: If the current URL hash matches a ToC entry, and
    the corresponding heading is visible in the viewport, then that is
    made the current ToC entry, and we don't even look at the intersection
    observer data.
    This means that if the user has clicked on a ToC entry,
    we won't unselect it through the intersection observer.
    */
    const hash = document.location.hash;
    if (hash) {
      let tocEntryForHash = document.querySelector(`nav li a[href="${hash}"]`);
      // if the hash isn't a direct match for a ToC item, check the data attributes
      if (!tocEntryForHash) {
        const fragment = hash.substring(1);
        tocEntryForHash = document.querySelector(`nav li a[data-${fragment}]`);
      }
      if (tocEntryForHash) {
        const headingForHash = document.querySelector(hash);
        if (headingForHash && isInViewport(headingForHash)) {
          setTocEntry(tocEntryForHash);
          return;
        }
      }
    }

    let newEntry = null;

    for (const entry of entries) {
      if (entry.intersectionRatio > 0) {
        const heading = entry.target;
        /*
        This sidebar nav consists of two sections:
        * at the top, a sitenav containing links to other pages
        * under that, the ToC for the current page

        Since the sidebar scrolls to match the document position,
        the sitenav will tend to scroll off the screen.

        If the user has scrolled up to (or near) the top of the page,
        we want to show the sitenav so.

        So: if the H1 (title) for the current page has started
        intersecting, then always scroll the sidebar back to the top.
        */
        if (heading.tagName === "H1" && heading.parentNode.tagName === "DIV") {
          const nav = document.querySelector("#td-section-nav");
          nav.scrollTop = 0;
          return;
        }
        /*
        Otherwise, get the ToC entry for the first entry that
        entered the viewport, if there was one.
        */
        const id = entry.target.getAttribute('id');
        let tocEntry = document.querySelector(`nav li a[href="#${id}"]`);
        // if the id isn't a direct match for a ToC item,
        // check the ToC entry's `data-*` attributes
        if (!tocEntry) {
          tocEntry = document.querySelector(`nav li a[data-${id}]`);
        }
        if (tocEntry && !newEntry) {
          newEntry = tocEntry;
        }
      }
    }

    if (newEntry) {
      setTocEntry(newEntry);
      return;
    }
  }

  /*
  Track when headings enter the viewport, and use this to update the highlight
  for the corresponding ToC entry.
  */
  window.addEventListener('DOMContentLoaded', () => {

    makeToc();

    const toc = document.querySelector("#toc");
    toc.addEventListener("click", event => {
      if (event.target.tagName === "A") {
        setTocEntry(event.target);
      }
    });

    const observer = new IntersectionObserver(handleIntersectionUpdate);

    document.querySelectorAll("h1, h2, h3, h4, h5, h6").forEach((section) => {
      observer.observe(section);
    });

  });
