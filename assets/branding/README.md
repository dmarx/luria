# Luria — Theme-conditional SVG set

Each SVG is self-contained and switches automatically via:

```css
@media (prefers-color-scheme: dark) { ... }
```

## Palette

- Light-scheme foreground: `#111111`
- Dark-scheme foreground: `#f0ede8`
- Adaptive tile assets invert those values for the background and mark.

## Assets

### Symbols
- `01-symbol/luria-a3-symbol-theme.svg` — primary mark
- `01-symbol/luria-a3-symbol-micro-theme.svg` — optical micro mark for 16–24 px

### Lockups
- `02-lockups/luria-a3-wordmark-theme.svg`
- `02-lockups/luria-a3-lockup-horizontal-theme.svg`
- `02-lockups/luria-a3-lockup-compact-theme.svg`
- `02-lockups/luria-a3-lockup-stacked-theme.svg`

### Icons
- `03-icons/luria-a3-favicon-theme.svg` — adaptive rounded tile
- `03-icons/luria-a3-favicon-transparent-theme.svg` — transparent micro mark
- `03-icons/luria-a3-app-icon-theme.svg` — 512 px adaptive tile
- `03-icons/luria-a3-avatar-circle-theme.svg` — adaptive circular avatar

All lettering is outlined. No external fonts, raster images, scripts, or dependencies.
