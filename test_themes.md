Love the brief: #1 clarity, #2 cozy. I looked at your current materials and PyCon TW pages to ground this (talks/schedule/tickets) and pulled a few evidence-based rules to keep things legible and accessible.

## 1) Information-First (default)

* **Feel:** neutral, airy, understated.
* **Typography:** a single, highly legible sans (e.g., IBM Plex Sans) with a disciplined type scale (display/headline/title/body/label). Plex is open-source and built for UI; Material’s type roles keep hierarchy consistent. ([GitHub][2], [Material Design][3])
* **Grid & rhythm:** target **50–75 characters/line** for body, \~1.4–1.6 line height. This maximizes readability across devices. ([Baymard Institute][4], [Wikipedia][5])
* **Color:** soft warm gray background (#F8F7F5), dark ink text (#1B1B1B), one brand accent for actions. Meet **WCAG 2.2** contrast (≥4.5:1 text; ≥3:1 UI) — aim AAA 7:1 for body when possible. ([W3C][6], [webaim.org][7], [Make Things Accessible][8])
* **Components:**

  * Hero with one sentence (“What / When / Where / CTA”).
  * “Now / Next” sticky bar on schedule pages; filters by **day / track / level / language**.
  * Talk card = Time • Room • Title • Speaker • Tags — nothing else.

## 2) Editorial Cozy

* **Feel:** conference magazine.
* **Typography:** Plex Sans + Plex Serif (serif only for talk abstracts & blog posts). Keep type scale consistent via Material style tokens. ([GitHub][2], [Material Design][9])
* **Color:** oatmeal background, charcoal text, muted accent set (sage, clay, midnight) for tracks.
* **Micro-UI:** larger line height on abstracts, wider margins, card corners 14–16px radius.

## 3) Playful Tech (restrained)

* **Feel:** friendly but focused; accents carry the energy, not the layout.
* **Typography:** single sans with **labels** for metadata (room/level) and **titles** for talk names per Material roles. ([Material Design][3])
* **Color:** light canvas, one vivid accent (e.g., cyan) + desaturated track colors; animated hover only on CTAs.

---

Awesome—here are **five theme presets** you can hand to another AI. They’re compact, implementation-ready, and all target:

* **Readability:** \~**50–75 CPL** line length for body/abstracts. ([Baymard Institute][1], [UXPin][2])
* **Accessibility:** **WCAG 2.2** contrast (≥4.5:1 small text; aim 7:1 for body); link/element checks with WebAIM; **44×44pt** mobile hit targets; motion reduced via `prefers-reduced-motion`. ([W3C][3], [webaim.org][4], [Apple Developer][5], [MDN Web Docs][6])
* **Type roles:** Material 3’s display/headline/title/body/label. ([Material Design][7])
* **Fonts:** IBM Plex (Sans/Serif/Mono), open-source. ([GitHub][8], [Google Fonts][9], [IBM][10])

> **How to use:** Paste one JSON block into your generator. Each includes palette, typography, spacing, component options, and schedule/talk-card rules.

The following all enforce: **\~50–75 CPL** body text, **WCAG 2.2** contrast (≥4.5:1 small text; aim **7:1** for body), **Material 3 type roles** (display/headline/title/body/label), **reduce motion** via `prefers-reduced-motion`, and **≥44×44pt** touch targets. ([UXPin][1], [Baymard Institute][2], [W3C][3], [Material Design][4], [MDN Web Docs][5], [Apple Developer][6])

> Tip for the generator: Use WAI-ARIA APG patterns for any interactive widgets (filters, accordions, dialogs). Validate color pairs with WebAIM’s checker. ([W3C][7], [webaim.org][8])

---

### 1) Info-First Neutral (default)

```json
{
  "name": "Info-First Neutral",
  "meta": { "version": "2025-08", "goal": ["clarity", "cozy"] },
  "brand": { "name": "PyConTW 2025", "accent": "#006CFF" },
  "palette": {
    "bg": "#F8F7F5",
    "surface": "#FFFFFF",
    "ink": "#1B1B1B",
    "muted": "#6B6B6B",
    "ui": "#EAE8E3",
    "accent": "#006CFF",
    "success": "#1A7F37",
    "warning": "#B06A00",
    "error": "#B3261E",
    "border": "#E6E2DA",
    "focus": "#1B1B1B",
    "trackColors": ["#0E7490", "#6D28D9", "#059669", "#EA580C"],
    "states": {
      "hover": { "surface": "#FDFDFC", "accent": "#0056CC" },
      "active": { "surface": "#F7F6F2", "accent": "#0047AA" },
      "disabledOpacity": 0.5
    }
  },
  "typography": {
    "fontSans": "\"IBM Plex Sans\",\"Noto Sans TC\",system-ui,Segoe UI,Roboto,Arial",
    "fontSerif": "\"IBM Plex Serif\",\"Noto Serif TC\",serif",
    "fontMono": "\"IBM Plex Mono\",ui-monospace,monospace",
    "rolesPx": { "display": 56, "headline": 32, "title": 20, "body": 16, "label": 12 },
    "rolesRem": { "display": 3.5, "headline": 2, "title": 1.25, "body": 1, "label": 0.75 },
    "weights": { "display": 600, "headline": 600, "title": 600, "body": 400, "label": 600 },
    "lineHeights": { "display": 1.15, "headline": 1.25, "title": 1.3, "body": 1.55, "label": 1.2 },
    "letterSpacing": { "label": 0.02, "caps": true },
    "measureCh": 65
  },
  "layout": {
    "gridUnit": 8,
    "radius": 16,
    "shadow": "0 2px 8px rgba(0,0,0,.08)",
    "contentMaxPx": 1200,
    "containerBodyMaxCh": 75,
    "gaps": { "xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32 }
  },
  "breakpoints": {
    "sm": 480,
    "md": 768,
    "lg": 1024,
    "xl": 1280
  },
  "motion": {
    "durationMs": { "fast": 120, "base": 160, "slow": 220 },
    "easing": "cubic-bezier(.2,.7,.2,1)",
    "reduceOnPrefersReducedMotion": true
  },
  "a11y": {
    "contrast": { "body": ">=7:1", "smallTextMin": ">=4.5:1", "ui": ">=3:1" },
    "hitTargetPt": { "min": [44, 44] },
    "focusRing": { "widthPx": 2, "offsetPx": 2, "color": "#1B1B1B" },
    "ariaPatterns": ["dialog", "listbox", "tabs", "combobox"]
  },
  "icons": { "style": "line", "stroke": 1.75 },
  "components": {
    "header": { "sticky": true, "elevated": true, "heightPx": 64 },
    "nav": { "activeUnderline": true, "gap": 16 },
    "button": { "kinds": ["filled","tonal","ghost"], "size": "lg", "radius": 12 },
    "input": { "radius": 12, "heightPx": 44, "paddingX": 12 },
    "chip": { "radius": 999, "size": "sm", "style": "outline" },
    "card": { "padding": 20, "radius": 16, "divider": false, "border": "1px solid #E6E2DA" },
    "table": { "rowDensity": "comfortable", "stripe": true }
  },
  "pages": {
    "homeHero": { "show": ["what","when","where","primaryCTA"], "kpis": ["date","venue","city"] },
    "talkCard": {
      "density": "comfortable",
      "slots": ["time","room","title","speakers","tags"],
      "titleRole": "headline",
      "metaRole": "label",
      "abstractPreviewLines": 2,
      "showSave": true
    },
    "talkDetail": {
      "aboveFold": ["title","speakers","timeRoom","primaryCTA"],
      "sideMeta": ["duration","level","language"],
      "leadParagraphSerif": false
    },
    "schedule": {
      "mobileNowNext": true,
      "stickyFilters": true,
      "timeSlotMin": 30,
      "trackColorLegend": true,
      "expandOnTap": true
    }
  }
}
```

---

### 2) Editorial Cozy

```json
{
  "name": "Editorial Cozy",
  "meta": { "version": "2025-08", "goal": ["clarity", "cozy", "editorial"] },
  "brand": { "accent": "#2D6A4F" },
  "palette": {
    "bg": "#FAF7F2",
    "surface": "#FFFFFF",
    "ink": "#222222",
    "muted": "#6C6C6C",
    "ui": "#EDE8E1",
    "accent": "#2D6A4F",
    "border": "#E7E0D6",
    "trackColors": ["#6B705C", "#0A9396", "#9A6D38", "#3D5A80"],
    "states": {
      "hover": { "surface": "#FFFBF5", "accent": "#285C45" },
      "active": { "surface": "#F6EFE6", "accent": "#234F3B" }
    }
  },
  "typography": {
    "fontSans": "\"IBM Plex Sans\",\"Noto Sans TC\",system-ui",
    "fontSerif": "\"IBM Plex Serif\",\"Noto Serif TC\",serif",
    "useSerifFor": ["abstract","blog","longform"],
    "rolesPx": { "display": 48, "headline": 28, "title": 20, "body": 17, "label": 12 },
    "rolesRem": { "display": 3, "headline": 1.75, "title": 1.25, "body": 1.0625, "label": 0.75 },
    "weights": { "display": 600, "headline": 600, "title": 600, "body": 400, "label": 600 },
    "lineHeights": { "display": 1.15, "headline": 1.3, "title": 1.35, "body": 1.6, "label": 1.2 },
    "measureCh": 66
  },
  "layout": {
    "gridUnit": 8,
    "radius": 18,
    "shadow": "0 6px 24px rgba(0,0,0,.06)",
    "contentMaxPx": 1100,
    "containerBodyMaxCh": 75,
    "gaps": { "md": 16, "lg": 24, "xl": 32 }
  },
  "breakpoints": { "sm": 480, "md": 768, "lg": 1024, "xl": 1280 },
  "motion": { "durationMs": { "base": 180 }, "easing": "ease-out", "reduceOnPrefersReducedMotion": true },
  "a11y": {
    "contrast": { "body": ">=7:1", "smallTextMin": ">=4.5:1", "ui": ">=3:1" },
    "hitTargetPt": { "min": [44, 44] },
    "focusRing": { "widthPx": 2, "offsetPx": 3, "color": "#2D6A4F" },
    "ariaPatterns": ["disclosure","accordion","dialog","tabs"]
  },
  "components": {
    "sectionIntro": { "eyebrowLabel": true, "eyebrowRole": "label" },
    "card": { "padding": 24, "radius": 18, "divider": true, "border": "1px solid #E7E0D6" },
    "tag": { "style": "soft", "upper": true, "radius": 999 },
    "button": { "style": "filled|tonal|ghost", "radius": 14 },
    "input": { "heightPx": 46, "radius": 14, "paddingX": 14 }
  },
  "pages": {
    "talkCard": { "titleRole": "headline", "metaRole": "label", "showSave": true, "tagLimit": 3 },
    "talkDetail": { "leadParagraphSerif": true, "sideMeta": ["duration","level","language"] },
    "schedule": { "gridDensity": "comfortable", "expandOnTap": true }
  }
}
```

---

### 3) Minimal Monochrome (ultra-clear)

```json
{
  "name": "Minimal Monochrome",
  "meta": { "version": "2025-08", "goal": ["clarity", "speed"] },
  "brand": { "accent": "#005AC2" },
  "palette": {
    "bg": "#FFFFFF",
    "surface": "#FFFFFF",
    "ink": "#111111",
    "muted": "#555555",
    "ui": "#E9E9E9",
    "accent": "#005AC2",
    "border": "#E9E9E9",
    "trackColors": ["#0F766E", "#7C3AED", "#2563EB", "#B45309"],
    "states": {
      "hover": { "surface": "#FAFAFA", "accent": "#004CA3" },
      "active": { "surface": "#F5F5F5", "accent": "#003F87" }
    }
  },
  "typography": {
    "fontSans": "\"IBM Plex Sans\",\"Noto Sans TC\",system-ui",
    "rolesPx": { "display": 44, "headline": 28, "title": 18, "body": 16, "label": 12 },
    "rolesRem": { "display": 2.75, "headline": 1.75, "title": 1.125, "body": 1, "label": 0.75 },
    "weights": { "display": 600, "headline": 600, "title": 600, "body": 400, "label": 600 },
    "lineHeights": { "display": 1.2, "headline": 1.3, "title": 1.35, "body": 1.55, "label": 1.2 },
    "measureCh": 62
  },
  "layout": {
    "gridUnit": 8,
    "radius": 12,
    "shadow": "none",
    "borders": "1px solid #E9E9E9",
    "contentMaxPx": 1160,
    "containerBodyMaxCh": 72
  },
  "breakpoints": { "sm": 480, "md": 768, "lg": 1024, "xl": 1280 },
  "motion": { "durationMs": { "base": 120 }, "easing": "linear", "reduceOnPrefersReducedMotion": true },
  "a11y": {
    "contrast": { "body": ">=7:1", "smallTextMin": ">=4.5:1", "ui": ">=3:1" },
    "hitTargetPt": { "min": [44, 44] },
    "focusRing": { "widthPx": 2, "offsetPx": 2, "color": "#005AC2" },
    "ariaPatterns": ["listbox","menu","dialog"]
  },
  "components": {
    "nav": { "underlineActive": true, "focusRing": "2px auto", "gap": 12 },
    "buttons": { "style": "ghost|filled", "corner": "slight", "radius": 10 },
    "chips": { "style": "outline", "radius": 999, "size": "sm" },
    "input": { "heightPx": 44, "radius": 10, "paddingX": 12 },
    "card": { "padding": 16, "radius": 12, "border": "1px solid #E9E9E9" }
  },
  "pages": {
    "homeHero": { "compact": true, "secondaryCTA": "View schedule" },
    "talkCard": { "density": "compact", "showTags": false, "twoLineTitle": true },
    "schedule": { "gridDensity": "dense", "timeColumnWidthPx": 88 }
  }
}
```

---

### 4) Playful Pastel Tech (friendly but focused)

```json
{
  "name": "Playful Pastel Tech",
  "meta": { "version": "2025-08", "goal": ["clarity", "friendly"] },
  "brand": { "accent": "#00B8D9" },
  "palette": {
    "bg": "#FBFDFF",
    "surface": "#FFFFFF",
    "ink": "#1A1F2C",
    "muted": "#5B6472",
    "ui": "#E6EEF6",
    "accent": "#00B8D9",
    "border": "#D9E6F2",
    "trackColors": ["#82C0FF", "#B9A6FF", "#7EE3C1", "#FFC69E"],
    "states": {
      "hover": { "surface": "#F4F9FF", "accent": "#00A4C3" },
      "active": { "surface": "#EDF5FD", "accent": "#008FAA" }
    }
  },
  "typography": {
    "fontSans": "\"IBM Plex Sans\",\"Noto Sans TC\",system-ui",
    "rolesPx": { "display": 52, "headline": 30, "title": 18, "body": 16, "label": 12 },
    "rolesRem": { "display": 3.25, "headline": 1.875, "title": 1.125, "body": 1, "label": 0.75 },
    "weights": { "display": 600, "headline": 600, "title": 600, "body": 400, "label": 600 },
    "lineHeights": { "display": 1.1, "headline": 1.25, "title": 1.35, "body": 1.55, "label": 1.2 },
    "measureCh": 64
  },
  "layout": {
    "gridUnit": 8,
    "radius": 20,
    "shadow": "0 8px 28px rgba(10,31,44,.08)",
    "contentMaxPx": 1200,
    "containerBodyMaxCh": 74
  },
  "breakpoints": { "sm": 480, "md": 768, "lg": 1024, "xl": 1280 },
  "motion": {
    "durationMs": { "base": 180, "hover": 120 },
    "easing": "cubic-bezier(.16,1,.3,1)",
    "hoverOnly": true,
    "reduceOnPrefersReducedMotion": true
  },
  "a11y": {
    "contrast": { "body": ">=7:1", "smallTextMin": ">=4.5:1", "ui": ">=3:1" },
    "hitTargetPt": { "min": [44, 44] },
    "focusRing": { "widthPx": 2, "offsetPx": 2, "color": "#00B8D9" },
    "ariaPatterns": ["radiogroup","tabs","combobox","dialog"]
  },
  "icons": { "style": "line", "stroke": 1.75 },
  "components": {
    "cta": { "style": "filled-tonal", "radius": 16 },
    "pillFilters": { "segmented": true, "size": "md", "radius": 999 },
    "input": { "heightPx": 46, "radius": 14, "paddingX": 14 },
    "card": { "padding": 20, "radius": 20, "border": "1px solid #D9E6F2" }
  },
  "pages": {
    "talkCard": { "titleRole": "title", "metaRole": "label", "showTags": true, "tagLimit": 3 },
    "schedule": { "mobileNowNext": true, "stickyFilters": true, "expandOnTap": true }
  }
}
```

---

### 5) Warm Civic Sans (clear + cozy)

```json
{
  "name": "Warm Civic Sans",
  "meta": { "version": "2025-08", "goal": ["clarity", "cozy", "civic"] },
  "brand": { "accent": "#0F7B99" },
  "palette": {
    "bg": "#FFFDF9",
    "surface": "#FFFFFF",
    "ink": "#151515",
    "muted": "#5D605F",
    "ui": "#EDE7DD",
    "accent": "#0F7B99",
    "border": "#E7DFD0",
    "focus": "#0F7B99",
    "success": "#1F7A3F",
    "warning": "#9C6A00",
    "error": "#B3261E",
    "trackColors": ["#2E7D8C", "#7A5EA8", "#3A8F6A", "#C9742A"],
    "states": {
      "hover": { "surface": "#FFFBF3", "accent": "#0D6C87" },
      "active": { "surface": "#FBF4E6", "accent": "#0B5E74" },
      "disabledOpacity": 0.5
    }
  },
  "typography": {
    "fontSans": "\"IBM Plex Sans\",\"Noto Sans TC\",system-ui,Segoe UI,Roboto,Arial",
    "fontSerif": "\"IBM Plex Serif\",\"Noto Serif TC\",serif",
    "fontMono": "\"IBM Plex Mono\",ui-monospace,monospace",
    "rolesPx": { "display": 50, "headline": 30, "title": 19, "body": 16, "label": 12 },
    "rolesRem": { "display": 3.125, "headline": 1.875, "title": 1.1875, "body": 1, "label": 0.75 },
    "weights": { "display": 600, "headline": 600, "title": 600, "body": 400, "label": 600 },
    "lineHeights": { "display": 1.14, "headline": 1.28, "title": 1.34, "body": 1.58, "label": 1.2 },
    "letterSpacing": { "label": 0.02, "caps": true },
    "measureCh": 64
  },
  "layout": {
    "gridUnit": 8,
    "radius": 14,
    "shadow": "0 4px 18px rgba(0,0,0,.06)",
    "borders": "1px solid #E7DFD0",
    "contentMaxPx": 1160,
    "containerBodyMaxCh": 74,
    "gaps": { "xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32 }
  },
  "breakpoints": { "sm": 480, "md": 768, "lg": 1024, "xl": 1280 },
  "motion": {
    "durationMs": { "fast": 120, "base": 160, "slow": 220 },
    "easing": "ease-in-out",
    "hoverOnly": true,
    "reduceOnPrefersReducedMotion": true
  },
  "a11y": {
    "contrast": { "body": ">=7:1", "smallTextMin": ">=4.5:1", "ui": ">=3:1" },
    "hitTarget": { "iosPt": [44, 44], "androidDp": [48, 48] },
    "focusRing": { "widthPx": 2, "offsetPx": 2, "color": "#0F7B99" },
    "ariaPatterns": ["tabs","radiogroup","combobox","dialog","accordion"]
  },
  "icons": { "style": "line", "stroke": 1.75 },
  "components": {
    "header": { "sticky": true, "elevated": true, "heightPx": 64, "border": true },
    "announcementBar": { "enabled": true, "bg": "#FFFAEE", "ink": "#5A4B1F", "icon": "info" },
    "nav": { "activeUnderline": true, "gap": 16, "breadcrumb": true },
    "button": { "kinds": ["filled","tonal","ghost"], "size": "lg", "radius": 12 },
    "input": { "heightPx": 46, "radius": 12, "paddingX": 14 },
    "chip": { "radius": 999, "size": "sm", "style": "soft" },
    "tag": { "style": "soft", "upper": true, "radius": 999 },
    "card": { "padding": 20, "radius": 14, "border": "1px solid #E7DFD0", "divider": true },
    "table": { "rowDensity": "comfortable", "stripe": true, "headerSticky": true }
  },
  "pages": {
    "homeHero": {
      "show": ["what","when","where","primaryCTA"],
      "kpis": ["date","venue","city"],
      "subtext": "One-line value prop"
    },
    "talkCard": {
      "density": "comfortable",
      "slots": ["time","room","title","speakers","tags"],
      "titleRole": "headline",
      "metaRole": "label",
      "abstractPreviewLines": 2,
      "showSave": true,
      "timeBadge": { "shape": "pill", "upper": true }
    },
    "talkDetail": {
      "aboveFold": ["title","speakers","timeRoom","primaryCTA"],
      "sideMeta": ["duration","level","language"],
      "leadParagraphSerif": false,
      "shareActions": true
    },
    "schedule": {
      "mobileNowNext": true,
      "stickyFilters": true,
      "timeSlotMin": 30,
      "trackColorLegend": true,
      "daySwitcherPersistent": true,
      "expandOnTap": true,
      "timeColumnWidthPx": 92
    },
    "tickets": {
      "recommendedIndex": 1,
      "priceTableRows": 4,
      "benefitsChecklist": true
    }
  }
}
```

---

#### Notes for your generator

* Keep **body text** within the specified `measureCh` (≈65 CPL) for abstracts and long descriptions. ([Baymard Institute][1], [UXPin][2])
* Validate color pairs with **WebAIM Contrast Checker** and meet **WCAG 2.2** thresholds. ([webaim.org][4], [W3C][3])
* Use **Material 3 roles** to map font sizes consistently across pages (display/headline/title/body/label). ([Material Design][7])
* Respect `prefers-reduced-motion` in CSS for all motion tokens. ([W3C][11], [MDN Web Docs][6])
* For interactive widgets (filters, accordions, dialogs), follow **WAI-ARIA APG** patterns. ([W3C][12])
* Touch targets on mobile: **≥44×44pt**. ([Apple Developer][5])

If you want, tell me which one you’re leaning toward and I’ll turn that preset into a drop-in Tailwind/React theme with a talks card and schedule grid.

[1]: https://baymard.com/blog/line-length-readability?utm_source=chatgpt.com "Readability: The Optimal Line Length"
[2]: https://www.uxpin.com/studio/blog/optimal-line-length-for-readability/?utm_source=chatgpt.com "Optimal Line Length for Readability"
[3]: https://www.w3.org/TR/WCAG22/?utm_source=chatgpt.com "Web Content Accessibility Guidelines (WCAG) 2.2"
[4]: https://webaim.org/resources/contrastchecker/?utm_source=chatgpt.com "Contrast Checker"
[5]: https://developer.apple.com/design/tips/?utm_source=chatgpt.com "UI Design Dos and Don'ts"
[6]: https://developer.mozilla.org/en-US/docs/Web/CSS/%40media/prefers-reduced-motion?utm_source=chatgpt.com "prefers-reduced-motion - CSS - MDN Web Docs"
[7]: https://m3.material.io/styles/typography/applying-type?utm_source=chatgpt.com "Typography – Material Design 3"
[8]: https://github.com/IBM/plex?utm_source=chatgpt.com "The package of IBM's typeface, IBM Plex."
[9]: https://fonts.google.com/specimen/IBM%2BPlex%2BSans?utm_source=chatgpt.com "IBM Plex Sans"
[10]: https://www.ibm.com/plex/?utm_source=chatgpt.com "Introduction | IBM Plex"
[11]: https://www.w3.org/WAI/WCAG22/Techniques/css/C39?utm_source=chatgpt.com "C39: Using the CSS reduce-motion query to prevent motion"
[12]: https://www.w3.org/WAI/ARIA/apg/?utm_source=chatgpt.com "ARIA Authoring Practices Guide | APG | WAI"
