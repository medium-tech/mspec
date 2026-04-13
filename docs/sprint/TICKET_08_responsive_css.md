# Ticket 08 — Responsive CSS: Mobile and Desktop Support

**Branch:** `improve-sosh-net-ui`

## Overview

Ensure the sosh-net frontend renders correctly on both mobile (small screens) and desktop (large screens). The current stylesheet (`browser2/js/src/style.css`) has a fixed `max-width: 1000px` on `body` but no responsive breakpoints, making it unusable on narrow viewports.

## Background

The JS browser2 renderer uses `browser2/js/src/style.css` for all page rendering. The current CSS:
- Sets `body { max-width: 1000px; margin: 20px; }` — fine on desktop, but does not adapt to narrow screens
- Uses fixed pixel widths on form inputs (`width: 233px`) — these overflow on small screens
- Tables have no horizontal scrolling or stacking — they clip on mobile
- No viewport meta tag is enforced in the renderer HTML (if not already present)

## Implementation

### 1. Viewport meta tag

Ensure `browser2/js/src/index.html` (or wherever the page shell lives) includes:

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

### 2. Responsive body / layout (`browser2/js/src/style.css`)

```css
/* replace fixed max-width body rule with a fluid layout */
body {
    font-family: Verdana, sans-serif;
    font-size: 12px;
    margin: 0;
    padding: 16px;
    background-color: white;
    box-sizing: border-box;
    max-width: 1000px;
    /* centre on wide screens */
    margin-left: auto;
    margin-right: auto;
}

/* fluid inputs — never overflow their container */
input[type="text"],
input[type="password"],
input[type="email"],
select,
textarea {
    width: 100%;
    max-width: 400px;
    box-sizing: border-box;
}
```

### 3. Mobile breakpoint (≤ 600 px)

Add a `@media` block targeting phones:

```css
@media (max-width: 600px) {
    body {
        padding: 8px;
        font-size: 13px;   /* slightly larger for readability */
    }

    h1 { font-size: 24px; }
    h2 { font-size: 20px; }
    h3 { font-size: 18px; }
    h4 { font-size: 16px; }

    /* make tables horizontally scrollable on small screens */
    .table-scroll-wrapper {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    /* stack form tables vertically */
    .form-table td {
        display: block;
        width: 100%;
    }

    /* full-width buttons on mobile */
    button {
        width: 100%;
        margin: 4px 0;
    }

    /* full-width inputs on mobile */
    input[type="text"],
    input[type="password"],
    input[type="email"],
    select,
    textarea {
        max-width: 100%;
        width: 100%;
    }

    /* lingo container — remove side borders on tiny screens */
    .lingo-container {
        padding: 10px;
        border-width: 2px;
    }

    /* popup — full width on mobile */
    .popup-content {
        width: 90%;
        left: 5%;
        top: 10%;
    }
}
```

### 4. Tablet breakpoint (601 px – 900 px) — optional

```css
@media (min-width: 601px) and (max-width: 900px) {
    body { padding: 12px; }
    input[type="text"],
    input[type="password"] {
        max-width: 300px;
    }
}
```

### 5. Table scroll wrapper

The JS renderer (`browser2/js/src/markup.js`) wraps rendered `<table>` elements in a `<div class="table-scroll-wrapper">` so they scroll horizontally on mobile instead of clipping:

```javascript
// in the table render function, wrap output:
const wrapper = document.createElement('div');
wrapper.className = 'table-scroll-wrapper';
wrapper.appendChild(tableEl);
parent.appendChild(wrapper);
```

### 6. Navigation / breadcrumb wrapping

Ensure the nav block in `sosh-network-page.yaml` and all breadcrumb blocks use `flex-wrap: wrap` so links wrap gracefully on narrow screens:

```css
.breadcrumb {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}
```

## Scope

| File | Change |
|------|--------|
| `browser2/js/src/index.html` | Add viewport meta tag |
| `browser2/js/src/style.css` | Fluid layout, mobile breakpoint, tablet breakpoint |
| `browser2/js/src/markup.js` | Wrap tables in scroll container |

The sosh-net specific pages (profiles, account, forum, chatter from Tickets 04–07) should be authored with mobile-first layout in mind — prefer stacked block elements over side-by-side columns, and avoid hardcoded pixel dimensions in lingo page YAML.

## Tests

- Playwright viewport tests (`templates/sosh-net/tests/`) — add a test fixture or config entry that runs key pages at a mobile viewport size (e.g. 390 × 844 for iPhone 14):
  ```javascript
  test.use({ viewport: { width: 390, height: 844 } });
  ```
  - Verify no horizontal overflow (use `document.body.scrollWidth <= window.innerWidth`)
  - Verify the nav links wrap rather than clip
  - Verify tables are scrollable (not clipped)
  - Verify form inputs are visible and tappable
- Run existing Playwright tests at the default (desktop) viewport to confirm no regressions

## Documentation

- Add a comment block at the top of `browser2/js/src/style.css` noting the mobile-first breakpoints
- Update `browser2/js/TODO.MD` or any relevant UI documentation to mark responsive CSS as done

## References

- `browser2/js/src/style.css` — current styles
- `browser2/js/src/index.html` — page shell (viewport meta tag)
- `browser2/js/src/markup.js` — JS renderer (table wrapping)
- Tickets 04–07 — custom pages that must render correctly on mobile
