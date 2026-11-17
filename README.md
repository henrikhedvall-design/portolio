# henrikhedvall.com

Henrik Hedvall's portfolio, served by GitHub Pages from the `docs/` folder.

The site is password protected: page content, images and films in `docs/` are encrypted, and the unencrypted source is kept elsewhere.

## Source backup

`source.enc` is an encrypted archive of the site's source (pages, CSS, JS, assets, fonts, build scripts). It is not served by GitHub Pages. Restore with the site password:

    openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -in source.enc -out site-src.tar.gz
    mkdir site && tar xzf site-src.tar.gz -C site
    cd site && python3 build.py

Regenerate the archive after every change to the source.
