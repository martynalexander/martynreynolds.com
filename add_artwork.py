#!/usr/bin/env python3
"""
add_artwork.py — add a new image to the gallery with the full pipeline automated.

For a given source image and its caption it will:
  1. Derive a filename from the caption title (lowercase, underscores,
     accents/punctuation stripped). Repeated titles get _2, _3, ... suffixes.
  2. Archive the original at the repo root under the new name.
  3. Make a web-optimized copy in web/  (max 4480px long edge, quality 92;
     images already <=4480px are just recompressed).
  4. Make a grid thumbnail in thumbs/  (max 2000px long edge, quality 80).
  5. Insert a <!-- cms-item --> block into index.html at the chosen position
     and renumber every data-page sequentially.

Usage examples:
  python3 add_artwork.py photo.jpg \
      --title "Cut Circle" \
      --seg "2025" --seg "heat foil on synthetic velvet" --seg "200 x 150 cm" \
      --link "https://example.com/show" \
      --size tall --after 45

  python3 add_artwork.py photo.jpg --title "Untitled" --end   # append to the end

Notes:
  - Caption segments are shown in order after the title, separated on screen
    by commas (desktop) / new lines (mobile). Put year, medium, dimensions,
    venue etc. as separate --seg values, matching existing captions.
  - --link adds the chain icon + hyperlink, exactly like existing linked pages.
  - Videos are not handled by this script; add those by hand.
"""
import argparse, os, re, shutil, subprocess, sys, unicodedata, html as htmlmod

ROOT   = os.path.dirname(os.path.abspath(__file__))
INDEX  = os.path.join(ROOT, "index.html")
WEB    = os.path.join(ROOT, "web")
THUMBS = os.path.join(ROOT, "thumbs")
WEB_MAX, WEB_Q     = 4480, 92
THUMB_MAX, THUMB_Q = 2000, 80


def slugify(title):
    t = unicodedata.normalize("NFKD", title.strip()).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")
    return t or "untitled"


def max_dimension(path):
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                         capture_output=True, text=True).stdout
    w = int(re.search(r"pixelWidth:\s*(\d+)", out).group(1))
    h = int(re.search(r"pixelHeight:\s*(\d+)", out).group(1))
    return max(w, h)


def unique_name(slug, ext):
    """Return a filename not already used in web/ (checks the served copy)."""
    cand = f"{slug}{ext}"
    if not os.path.exists(os.path.join(WEB, cand)):
        return cand
    n = 2
    while os.path.exists(os.path.join(WEB, f"{slug}_{n}{ext}")):
        n += 1
    return f"{slug}_{n}{ext}"


def build_caption(title, segs, link):
    parts = [title] + list(segs)
    if link:
        parts.append(link)
    return " | ".join(parts)


def build_block(size, newname, caption):
    cls = f' class="{size}"' if size in ("tall", "big") else ""
    alt = htmlmod.escape(caption, quote=True)
    return (
        "<!-- cms-item-start -->\n"
        "            <!-- primary page identifier: data-page -->\n"
        f"            <a{cls} onclick=\"showArtworkPage(this, 'image')\" "
        f"data-file=\"web/{newname}\" data-page=\"0\">\n"
        f"                <img src=\"thumbs/{newname}\" alt=\"{alt}\" loading=\"lazy\">\n"
        "            </a>\n"
        "            <!-- cms-item-end -->\n"
    )


def renumber(doc):
    counter = {"n": 0}
    def repl(m):
        counter["n"] += 1
        return f'data-page="{counter["n"]}"'
    return re.sub(r'data-page="\d+"', repl, doc), counter["n"]


def insert_block(doc, block, after, before, at_end):
    if at_end:
        marker = "<!-- cms-list-end -->"
        idx = doc.index(marker)
        return doc[:idx] + block + "\n" + doc[idx:]
    target = after if after is not None else before
    # locate the cms-item block whose data-page == target
    m = re.search(r'(<!-- cms-item-start -->.*?data-page="%d".*?<!-- cms-item-end -->\n)'
                  % target, doc, re.S)
    if not m:
        sys.exit(f"Could not find page {target} to anchor insertion.")
    if after is not None:
        pos = m.end()
        return doc[:pos] + "\n" + block + doc[pos:]
    else:
        pos = m.start()
        return doc[:pos] + block + "\n" + doc[pos:]


def main():
    ap = argparse.ArgumentParser(description="Add an image to the gallery.")
    ap.add_argument("source", help="path to the source image")
    ap.add_argument("--title", required=True)
    ap.add_argument("--seg", action="append", default=[],
                    help="caption segment after the title (repeatable)")
    ap.add_argument("--link", default=None)
    ap.add_argument("--size", choices=["normal", "tall", "big"], default="normal")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--after", type=int, help="insert after this page number")
    grp.add_argument("--before", type=int, help="insert before this page number")
    grp.add_argument("--end", action="store_true", help="append at the end")
    args = ap.parse_args()

    if not os.path.exists(args.source):
        sys.exit(f"Source not found: {args.source}")

    ext = os.path.splitext(args.source)[1].lower()
    if ext == ".jpeg":
        ext = ".jpeg"
    newname = unique_name(slugify(args.title), ext)
    caption = build_caption(args.title, args.seg, args.link)

    # 1. archive original at root
    shutil.copy2(args.source, os.path.join(ROOT, newname))
    # 2. web-optimized copy
    web_out = os.path.join(WEB, newname)
    if max_dimension(args.source) > WEB_MAX:
        subprocess.run(["sips", "-Z", str(WEB_MAX), "-s", "formatOptions", str(WEB_Q),
                        args.source, "--out", web_out], capture_output=True)
    else:
        subprocess.run(["sips", "-s", "formatOptions", str(WEB_Q),
                        args.source, "--out", web_out], capture_output=True)
    # 3. thumbnail
    subprocess.run(["sips", "-Z", str(THUMB_MAX), "-s", "formatOptions", str(THUMB_Q),
                    args.source, "--out", os.path.join(THUMBS, newname)], capture_output=True)

    # 4. insert + renumber
    doc = open(INDEX).read()
    block = build_block(args.size, newname, caption)
    doc = insert_block(doc, block, args.after, args.before, args.end)
    doc, total = renumber(doc)
    open(INDEX, "w").write(doc)

    # report the new page number
    m = re.search(r'data-file="web/%s" data-page="(\d+)"' % re.escape(newname), doc)
    page = m.group(1) if m else "?"
    web_kb = os.path.getsize(web_out) // 1024
    print(f"Added '{args.title}' as page {page} (of {total})")
    print(f"  file:    {newname}  (web copy {web_kb} KB)")
    print(f"  caption: {caption}")
    print(f"  size:    {args.size}")


if __name__ == "__main__":
    main()
