LURIA: PROJECT MEMORY — THEME-AWARE SVG ASSETS

All SVGs are transparent and automatically switch ink color using
prefers-color-scheme:

  Light theme: #111111
  Dark theme:  #F4F1E8

The SVGs are self-contained: both the logo and Comfortaa wordmark are paths,
so no external font or image files are required.

To set a custom color when embedding the SVG inline, override --luria-ink:

  <svg style="--luria-ink: #123456">...</svg>

For an external SVG loaded through <img>, its internal light/dark media query
runs independently according to the viewer's color-scheme preference.
