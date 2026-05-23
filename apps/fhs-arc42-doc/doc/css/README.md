# CSS Modules

Modular CSS architecture for FHS arc42 documentation.

## Structure

```
doc/css/
├── modules/
│   ├── base.css          # Core styles (1,063 lines, ~22 KB)
│   └── canvas.css        # Canvas-specific layouts (602 lines, ~14 KB)
├── arc42-custom.css      # Full CSS (generated)
├── arc42-docs.css        # Documentation CSS (generated, no canvas)
└── arc42-canvas.css      # Canvas CSS (generated)
```

## Modules

### `base.css`
Core styles used by all documentation pages:
- CSS variables and design tokens
- Typography and fonts
- Layout and spacing
- Tables, code blocks, admonitions
- TOC sidebar
- Responsive design
- Dark mode support
- C4 model colors

**Used by:** All HTML pages

### `canvas.css`
Canvas-specific layout styles:
- Architecture Inception Canvas (AIC)
- Architecture Communication Canvas (ACC)
- Grid-based canvas layouts
- Canvas header formatting
- Canvas-specific responsive rules

**Used by:** Canvas pages only (`architecture-inception-canvas.html`, `architecture-communication-canvas.html`)

## Build Process

CSS is built and optimized automatically during documentation generation:

```bash
# Manual CSS build + optimization
cd apps/fhs-arc42-doc
python3 pipeline/build_css.py .      # Build from modules
python3 pipeline/purge_css.py .      # Remove unused CSS

# Full docs build (includes CSS build + purge)
cd /
export JUPYTER_TOKEN="token"
./cicd/run-cicd.sh docs
```

### Build Pipeline

1. **CSS Module Concatenation** (`build_css.py`)
   - Combines modules into full CSS files
   - Adds auto-generation headers

2. **Documentation Generation** (DocToolchain)
   - Generates HTML from AsciiDoc
   - Embeds CSS based on `:stylesheet:` attribute

3. **CSS Purging** (`purge_css.py`)
   - Analyzes generated HTML
   - Removes unused selectors
   - Generates `.min.css` files

### Build Outputs

| File | Modules | Size | Purged | Use Case |
|------|---------|------|--------|----------|
| `arc42-docs.css` | base | 22 KB | No | Documentation (intermediate) |
| `arc42-docs.min.css` | base | **20 KB** | Yes | **Documentation (production)** ✅ |
| `arc42-canvas.css` | base + canvas | 36 KB | No | Canvas (intermediate) |
| `arc42-canvas.min.css` | base + canvas | **31 KB** | Yes | **Canvas (production)** ✅ |
| `arc42-custom.css` | base + canvas | 36 KB | No | Compatibility (legacy) |

**Optimizations achieved:**
- Main docs: 36 KB → 20 KB (**44% reduction**)
- Canvas: 36 KB → 31 KB (**14% reduction**)
- Total savings: ~19 KB across all pages

## Editing CSS

**Do NOT edit generated files directly!**

1. Edit source modules in `doc/css/modules/`
2. Run CSS build: `python3 pipeline/build_css.py .`
3. Rebuild documentation: `./cicd/run-cicd.sh docs`

## Future Optimizations

### Phase 4: CSS Minification (Optional)
Add whitespace removal and compression:
- Remove comments (except license headers)
- Minify property values
- Compress color codes
- Target: Additional 10-15% reduction

### Phase 5: Asset Pipeline (Optional)
- Add content hashing for cache busting
- Generate source maps for debugging
- Implement CSS splitting for above-the-fold content

## Performance Metrics

**Before optimization:**
- All pages: 36 KB CSS (monolithic)

**After Phase 2 + Phase 3:**
- Main docs: 20 KB CSS (44% reduction) ✅
- Canvas pages: 31 KB CSS (14% reduction) ✅
- Average: 43% reduction for typical page loads

## Migration Notes

**v1.0.0 → v2.0.0 (Modular CSS)**
- CSS source split into modules
- Generated files have auto-gen header
- Build integrated into docs pipeline
- No breaking changes for consumers

**v2.0.0 → v2.1.0 (Conditional Loading + PurgeCSS)**
- Page-specific CSS files (`.min.css`)
- Automatic unused CSS removal
- AsciiDoc files updated to use optimized CSS
- 44% smaller CSS for documentation pages
- Canvas layout fix preserved in all outputs
