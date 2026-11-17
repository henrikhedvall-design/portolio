# henrikhedvall.com

Portfolio site for Henrik Hedvall, freelance product designer.

- `docs/` is the published site, served by GitHub Pages at https://henrikhedvall.com.
- `site/` is the source: pages, CSS, JavaScript, images, fonts and the build scripts.

## Build

    cd site
    python3 build.py

This writes the site to `site/docs/`. Copy that folder over `docs/` in the repository root and push to `main` to publish.

The build needs Python 3 with Pillow. It creates smaller WebP versions of the images in `site/_variants/` (a cache, not committed).

## Password protection

The site can be published behind a password again: put the password, a salt and the iteration count in `site/.secret.json` (never committed), set `PROTECT = True` in `build.py` and rebuild.
