# QR Platform: Product Scope & Strategy

*Working name: TBD. A free-core, API-extensible QR platform for individuals and businesses, built around three ideas: offline utility, brand-quality design, and plug-and-play integration.*

---

## 1. Vision

QR codes are underused. Most are ugly, untracked, uneditable, and easy to spoof. This platform makes them **beautiful, trustworthy, editable, and connected**, and makes that power usable by a person with no technical skill as well as a developer with an API key.

**Positioning:** Not another generic QR generator (a crowded market). The differentiators are:

1. **Offline-first utility** for individuals (contact, medical, Wi-Fi, emergency cards)
2. **Design and brand studio** with a live scannability score
3. **Trust layer** (authenticity, anti-tamper, link preview)
4. **Hosted, styled landing pages** so anyone can scan-to-something without owning a website
5. **Plug-and-play integrations** for businesses, with an API underneath

---

## 2. How the Idea Evolved

| Stage | Idea | Outcome |
|---|---|---|
| 1 | Free, useful tools for everyday people | Broad brainstorm |
| 2 | Less generic, more clever tech/AI tricks | Narrowed to offline QR + community tip board |
| 3 | Offline QR card + community tip board | Both expanded |
| 4 | QR as a business product | Static vs. dynamic codes, integrations, industry packs |
| 5 | Aesthetics and branding | Styled/artistic codes, personal + business branding |
| 6 | Consolidated scope | Tiers, plug-and-play path, first documentation |
| 7 | Hosted, styled landing pages | Codes lead to a page the platform hosts, so no website is needed (see 4.8) |

**Parked idea:** Community tip-sharing board (shared storage, upvotes, categories: bureaucracy, neighborhood, building, event tips). It can return as a *QR-linked* feature: a QR on a building lobby, venue, or event badge opens that location's tip board. This ties both original ideas together.

---

## 3. Core Concepts

- **Static code:** data is encoded directly (vCard, Wi-Fi, plain text). Works with no internet and no account. Cannot be edited after printing.
- **Dynamic code:** encodes a short link that can be edited, tracked, expired, and routed after printing.
- **Error correction:** QR codes tolerate roughly 7 to 30% damage depending on level. This slack is the design canvas for logos and artistic styling, but too much styling breaks scanning.
- **Scannability score:** a live check of contrast, quiet zone, module size, and logo coverage.
- **Hosted page:** a single mobile-first page, built from blocks and styled during code setup, that the code opens. It gives people without a website a destination, and keeps code, page, and analytics in one place.

---

## 4. Feature Catalog

### 4.1 Free Tier (core, no account for static codes)

The free tier should be genuinely useful, not a crippled trial. It drives adoption and trust.

**Static, offline codes (processed entirely in the browser; nothing uploaded)**
- Contact card (vCard)
- Emergency medical card (allergies, medications, blood type, emergency contact)
- Wi-Fi share card
- "In case of emergency" home card (utility shutoffs, pet info, out-of-town contact)
- URL, text, email, phone, SMS, calendar event

**Basic design**
- Color and background choice
- Basic dot and corner shapes
- Center logo upload
- Simple frames with a call to action ("Scan me")
- **Scannability checker** (always free; it builds trust and prevents bad prints)
- Export: PNG, SVG, printable wallet-card/sticker sheet templates

**Free dynamic (limited)**
- A small number of editable dynamic codes
- Basic scan count
- Platform-branded short link

**Free hosted page (see 4.8)**
- One block-based landing page on a free subdomain
- Core blocks (contact, hours, map, links, socials) and auto-matched brand theme
- Simple open/closed toggle
- Small "made with" badge

### 4.2 Pro Tier (individuals, creators, small businesses; account required)

**Dynamic code management**
- More codes; custom short domain or vanity slug
- Edit destination anytime
- Scan analytics: time, approximate location, device, new vs. returning
- Expiry dates and scan limits (coupons, visitor passes, single-use codes)
- Fallback page if a destination is unavailable
- Password-protected codes

**Smart routing**
- By device (iOS/Android/desktop)
- By language
- By time of day or day of week
- By approximate location

**Brand Studio**
- Brand kit: upload a logo, auto-extract colors, generate a code style guide
- Custom module shapes and custom finder eyes
- Gradients and duotones
- Saved style presets applied across all codes
- **Seasonal skins:** restyle without changing the destination
- **Campaign variants:** same style, different color per channel, tracked separately
- Bulk generation from a spreadsheet (CSV upload)
- Hosted landing pages: multiple pages, no badge, per-block analytics, scheduling, AI setup, text-to-update (see 4.8)

**Personal branding**
- Signature code used across business card, email signature, LinkedIn banner, and badge
- Portrait/avatar-blended codes
- Digital business card page (a landing page the code opens)
- Creator kit: templates for overlays, merch, podcast art

### 4.3 Business Tier (teams, multi-location; adds collaboration and governance)

- Team workspaces, roles, and approval workflows for changing live codes
- Multi-location management (one template, many locations, per-location analytics)
- Custom domains and white-labeling
- Audit log (who changed which destination and when)
- Brand guardrails: locked colors and styles so staff cannot create off-brand or unscannable codes
- Wallet passes (Apple/Google Wallet): loyalty cards, tickets, coupons
- Integrations (see 4.5) included without needing the API
- Hosted pages: custom domains, multi-location page templates, approval workflow for page edits (see 4.8)

### 4.4 API / Platform Tier (usage-based)

For developers and companies that want to embed QR capability inside their own products.

| Endpoint group | What it does |
|---|---|
| **Codes** | Create, update, delete, list static and dynamic codes |
| **Render** | Generate styled images (PNG/SVG/PDF) from a style preset, with scannability score returned |
| **Routing rules** | Programmatically set device, geo, time, and language rules |
| **Analytics** | Query scans by code, campaign, time range; export |
| **Webhooks** | Fire on scan, expiry, limit reached, or tamper alert |
| **Bulk** | Batch create thousands of unique codes (serialized products, tickets) |
| **Verify** | Validate signed codes for authenticity |
| **Wallet** | Issue and update wallet passes |
| **Embed SDK** | Drop-in widget so a customer's own users can design and generate codes in-app |
| **Pages** | Create and update hosted pages and blocks from JSON, apply themes, publish, and push content updates (e.g. "sold out" flags) via webhook |

Pricing model: free monthly quota, then per-render and per-scan usage tiers.

### 4.5 Integrations (no-code, available in Business; exposed via API too)

- **POS/commerce:** Square, Stripe, Shopify (table-specific order/pay codes, product pages)
- **CRM:** HubSpot, Salesforce (a scan creates or updates a lead, tagged by source)
- **Automation:** Zapier, Make, Google Sheets (scan adds a row, sends a Slack alert or email)
- **Calendar/booking:** Google Calendar, Calendly-style booking
- **Wallet:** Apple Wallet, Google Wallet
- **Email/marketing:** Mailchimp and similar (scan subscribes)

### 4.6 Trust & Safety Layer (differentiator; tiered)

| Feature | Tier |
|---|---|
| Link safety preview (show destination before opening) | Free |
| Scannability and print-readiness checks | Free |
| Brand-verified visual signature (consistent look that customers learn to trust) | Pro |
| Signed codes for product authenticity | Business/API |
| Anti-tamper detection (alerts when a sticker is placed over a legitimate code, using scan anomalies and reports) | Business/API |
| Malicious-destination monitoring on customer links | Business |

### 4.7 Artistic and Physical Codes (add-on packs)

- **Image-blended codes:** code woven into a photo, illustration, or product shot
- **AI-generated scene codes:** skyline, forest, storefront
- **Animated codes** for signage and video
- **Materials guide and export profiles:** laser-etched wood, embossed leather, embroidery, latte art, stamps, packaging print. Each profile adjusts module size and contrast for that medium.
- **Packaging mode:** code as artwork with print-safe specs

Note: these are the highest-risk for scan failure. Always gate export behind the scannability score with a "test with real devices" prompt.

### 4.8 Hosted Landing Pages ("No Website Needed")

**The problem:** many small businesses and most individuals have no landing page, so a QR code has nowhere good to send people. Hosting the destination removes that barrier and makes the code, page, and analytics one product.

**Scope discipline:** this is **one mobile-first page assembled from blocks**, not a website builder. Constrained design keeps setup fast, pages light, and moderation manageable.

**Styling during code setup**
- Page theme auto-generated from the same logo and brand kit as the code, so page and code match
- A handful of layouts per goal (menu page, contact card, event page, product page, help page)
- Font, color, and button style presets; light and dark modes
- Free subdomain (e.g. `yourname.platform.link`), custom domain on higher tiers

**Blocks**
- Contact and click-to-call, WhatsApp, SMS
- Hours, map and directions, "open now" status
- Menu or price list, service list, gallery
- Links and socials
- Wi-Fi join, emergency/medical info, vCard save (ties back to the offline cards)
- Booking, payment, tip, and review buttons (as **link-outs** to Stripe, Calendly, PayPal, Google, not built in)
- Announcement banner, FAQ, feedback form, newsletter signup
- Location tip board (from the parked community tip idea)

**Feasibility by effort**

| Effort | Feature |
|---|---|
| **Easy (weeks)** | Block editor and themes; free subdomain; brand-matched styling; click-to-call/WhatsApp; open/closed and "back in 10 minutes" toggles; per-block analytics; auto-translation |
| **Medium (a few months)** | **Photo-to-page** (snap a paper menu, price list, or flyer; AI digitizes it); **auto-fill** from an Instagram, Facebook, or Google Business link; schedule-aware content (breakfast/dinner menus, holiday hours); custom domains; link-out booking and payments; offline-cached page (PWA); **text-to-update** (text "sold out of croissants" and the page changes); accessibility auto-checks |
| **Hard (defer)** | Built-in ordering, checkout, or POS; inventory or scheduling engines; full website and SEO tooling |

**Smart page behavior (builds on existing platform features)**
- Routing rules apply to pages too: language, device, time of day, location
- Seasonal skins restyle the page and code together
- Campaign variants: same page, different offer per flyer or location
- Expiring pages for events, coupons, and visitor passes
- Verified-business badge pairs with the trust layer

**Guardrails**
- Constrained blocks (no arbitrary scripts or embeds) to limit phishing and scam pages
- Moderation pipeline, report-abuse link on every page, rate limits on new accounts
- Speed budget: page loads in under a second on weak signal; images auto-compressed
- Review handling: offer a plain "leave a review" button and a private feedback option side by side; do **not** route only happy customers to public review sites, which violates Google's policies

**Tier mapping**

| Tier | Hosted page offering |
|---|---|
| Free | 1 page, subdomain, core blocks, brand-matched theme, open/closed toggle, platform badge |
| Pro | Multiple pages, no badge, per-block analytics, scheduling, AI setup (photo-to-page, auto-fill), text-to-update, translation |
| Business | Custom domains, multi-location templates, approvals and audit log, brand guardrails on pages |
| API | Programmatic page and block management, theming, webhooks for content updates |

---

## 5. Who Uses It and How

### 5.1 Individuals

| Persona | Uses |
|---|---|
| **Everyday person** | Wi-Fi card for guests, fridge emergency card, wallet medical card |
| **Parent / caregiver** | Kid backpack tag, elderly parent's medical info readable with a locked phone |
| **Job seeker / professional** | Signature code on resume, business card, LinkedIn; digital card page |
| **Creator / freelancer** | Branded code on merch, video overlays, portfolio, tip jar |
| **Event attendee / organizer** | Badge contact swap, session feedback, venue tip board |
| **Renter / homeowner** | Building tip board, appliance manuals, home info card |

### 5.2 Businesses (Industry Packs)

Each pack is a **preconfigured bundle**: templates, code types, integrations, and a setup wizard.

| Industry | Pack contents |
|---|---|
| **Restaurants and cafes** | Table ordering, live menu, allergen info, tip and split-bill, loyalty wallet card, latte-art/branded code |
| **Retail** | Product page with reviews and size guides, warranty registration on item, authenticity check |
| **Healthcare** | Patient check-in, intake forms, medication info on packaging, medical ID cards |
| **Real estate** | Yard-sign codes with tours and agent contact, per-sign analytics, open-house check-in |
| **Facilities / manufacturing** | Equipment codes linking to manuals, maintenance logs, "report a problem" form |
| **Events** | Ticketing, check-in, feedback, badge networking, venue tip board |
| **Logistics** | Tracking, proof-of-delivery, returns |
| **Hospitality** | Wi-Fi codes, room service, local guide, digital check-in |
| **Marketing agencies** | Multi-client workspaces, campaign variants, white-label reports |

**Recommendation:** Launch with **one or two packs** (suggested: restaurants and facilities/maintenance) rather than all at once. Depth in a niche beats breadth against generic competitors.

### 5.3 The "No Website" Segment

Hosted pages open a segment that generic QR tools miss entirely: people and businesses with no digital presence beyond a phone.

| Who | What the page + code becomes |
|---|---|
| Food truck, market stall, street vendor | Menu, "where we are today," payment link |
| Salon, barber, tutor, cleaner, tradesperson | Services, prices, booking link, WhatsApp button, photo gallery |
| Landlord, property manager | Building info, maintenance request, emergency contacts |
| Community group, place of worship, club | Schedule, announcements, donation link, contact |
| Individual (job seeker, freelancer, artist) | Digital business card, portfolio, one link for everything |
| Pop-up or seasonal seller | Expiring page with a dated offer |

These users convert well to paid because the platform *is* their web presence: switching costs are real and the value is obvious.

---

## 6. Design Path: Plug-and-Play for Non-Technical Users

The goal: a user should go from "I need a QR code" to "it's live and connected" in under five minutes, with no code, and be able to grow into more power without switching products.

### 6.1 Three Lanes, One Product

| Lane | User | Experience |
|---|---|---|
| **1. Guided (no-code)** | Individuals, small business owners | Answer plain-language questions; wizard builds everything |
| **2. Connect (low-code)** | Marketers, ops managers | Point-and-click integrations, templates, Zapier |
| **3. Build (API)** | Developers, platform companies | REST API, SDKs, webhooks, embed widget |

All three lanes share the same underlying objects (codes, styles, rules, analytics), so a code made in Lane 1 can later be automated in Lane 3.

### 6.2 Guided Onboarding Flow (Lane 1)

1. **"What do you want people to do when they scan?"** Options: see my menu, save my contact, join Wi-Fi, pay, book, leave feedback, get help, something else.
2. **Fill in the essentials** (a short form specific to that goal; no jargon such as "vCard" or "URL").
3. **Pick a look.** Upload a logo, and the brand kit auto-suggests colors and styles. Pick from previews.
4. **Live scannability check** with a green/yellow/red indicator in plain language ("Easy to scan," "May struggle on older phones").
5. **Choose where it will live:** table tent, window sticker, business card, flyer, packaging, screen. The tool applies the right size and print profile.
6. **Download or order.** Print-ready file, printable sheet, or (later) ordered physical products.
7. **Next step prompt:** "Want to see who scans it?" This upgrades the code to dynamic.

**Branch at step 1 for people with no website:** if the destination is "show my info/menu/services," the wizard offers **"We'll build your page for you."** It then asks for a photo of a menu or flyer, or a link to an Instagram/Facebook/Google Business profile, drafts the page with AI, and shows a live phone preview. The user edits blocks, picks a theme (pre-matched to the code style), and publishes page and code together in one step.

### 6.3 Connect Experience (Lane 2)

- **"Connect an app" gallery** with logos, one-click OAuth, and plain-language recipes:
  - "When someone scans, add them to my HubSpot"
  - "Send me a Slack message when the VIP code is scanned"
  - "Add each scan to a Google Sheet"
- **Template library** organized by goal and industry, each showing a preview of the result.
- **Rules builder** with sentence-style UI: *If the phone is an iPhone → go to App Store; otherwise → Google Play.*
- **Test mode:** scan or preview without polluting analytics.

### 6.4 Build Experience (Lane 3)

- OpenAPI spec, interactive docs, and copy-paste quickstarts (curl, JS, Python)
- Sandbox keys with generous free quota
- Webhooks with retry and signature verification
- **Embed SDK:** a few lines of code puts the QR designer inside a customer's own app, themed to their brand
- Low-friction upgrade: start from a code made in the UI and "view as API call"

### 6.5 Design Principles

- **Plain language everywhere.** Say "who scanned" not "UTM parameters."
- **Templates first, blank canvas second.**
- **Safe defaults.** Error correction, contrast, and quiet zone are set automatically; advanced controls are hidden behind "Customize."
- **Progressive disclosure.** Free static codes need no account; accounts appear only when the user wants tracking or editing.
- **Never break a printed code.** Destination changes are safe; the code image itself is stable. Warn before any change that would alter the printed pattern.
- **Undo and version history** for every live change.
- **Accessibility:** color-blind-safe checks, high-contrast alternatives, and a text fallback URL printed with the code.

---

## 7. Free vs. Paid Summary

| Capability | Free | Pro | Business | API |
|---|---|---|---|---|
| Static/offline codes (contact, medical, Wi-Fi, etc.) | ✅ | ✅ | ✅ | ✅ |
| Basic styling and logo | ✅ | ✅ | ✅ | ✅ |
| Scannability checker | ✅ | ✅ | ✅ | ✅ |
| Link safety preview | ✅ | ✅ | ✅ | ✅ |
| Editable dynamic codes | Few | Many | Unlimited | Metered |
| Scan analytics | Basic count | Full | Full + team reports | Query API |
| Smart routing | ❌ | ✅ | ✅ | ✅ |
| Expiry / scan limits | ❌ | ✅ | ✅ | ✅ |
| Brand Studio (kits, custom shapes, skins) | ❌ | ✅ | ✅ (with guardrails) | ✅ |
| Bulk generation | ❌ | CSV | CSV + workflows | ✅ |
| Team roles and approvals | ❌ | ❌ | ✅ | ✅ |
| Custom domain / white-label | ❌ | Vanity slug | ✅ | ✅ |
| Integrations (CRM, POS, Sheets) | ❌ | Limited | ✅ | ✅ |
| Hosted landing page (block-based) | 1 page, badge | Multiple, no badge | Unlimited, multi-location | Full API |
| AI page setup (photo-to-page, auto-fill from social link) | Limited | ✅ | ✅ | ✅ |
| Open/closed toggle | ✅ | ✅ | ✅ | ✅ |
| Scheduling, text-to-update, translation | ❌ | ✅ | ✅ | ✅ |
| Per-block page analytics | ❌ | ✅ | ✅ | ✅ |
| Custom domain for page | ❌ | ❌ | ✅ | ✅ |
| Wallet passes | ❌ | ❌ | ✅ | ✅ |
| Signed/authenticity codes and anti-tamper | ❌ | ❌ | ✅ | ✅ |
| Webhooks, embed SDK | ❌ | ❌ | Limited | ✅ |

**Principle:** Anything that protects the user or is a basic utility stays free. Anything that scales, automates, or requires infrastructure we operate is paid.

---

## 8. Technical Architecture (High Level)

- **Client-side generator:** browser-based QR encoding and styling so static codes never touch a server (privacy and offline story).
- **Redirect service:** fast, globally distributed short-link resolver with low latency, since it sits in every scan path. Needs high availability and a fallback mode.
- **Rules engine:** evaluates device, geo, time, and language at redirect time.
- **Analytics pipeline:** event ingestion, aggregation, and privacy controls (see Risks).
- **Style engine:** shared rendering library used by the UI, API, and embed SDK so output is identical everywhere.
- **Scannability engine:** simulated decoding across blur, angle, and contrast, plus contrast/quiet-zone math.
- **Signing service:** cryptographic signatures for authenticity codes; public verification endpoint.
- **Integration layer:** OAuth connectors and webhook dispatcher.
- **Page renderer:** static-first, edge-cached rendering of block pages with a strict speed budget, plus offline caching (PWA) for repeat visitors.
- **AI ingestion service:** vision and text models that turn menu photos, flyers, and social profile links into draft pages; always shown for human review before publishing.
- **Moderation pipeline:** automated screening of page content and destinations, abuse reports, and account rate limits.
- **Update channels:** text-message and webhook endpoints that change page content (e.g. "sold out") without opening the editor.
- **Storage:** codes, styles, rules, pages and blocks, workspaces, and audit logs.

---

## 9. Roadmap

**Phase 1: Free Foundation (weeks 0 to 8)**
- Static offline generators (contact, medical, Wi-Fi, home emergency)
- Styler with logo, colors, shapes
- Scannability checker
- Printable card templates

**Phase 2: Dynamic + Analytics (weeks 8 to 16)**
- Accounts, dynamic codes, redirect service
- Basic analytics, expiry, scan limits
- Device-based routing
- **Hosted page builder v1:** blocks, themes matched to the code style, free subdomain, open/closed toggle

**Phase 3: Brand Studio + First Industry Pack (weeks 16 to 28)**
- Brand kit extraction, presets, seasonal skins
- Restaurant pack (or facilities pack) with POS/Sheets integrations
- Guided onboarding wizard with "build my page for me" branch
- **AI page setup:** photo-to-page and auto-fill from social profile links
- Schedule-aware page content, translation, per-block analytics

**Phase 4: Business + Trust (weeks 28 to 40)**
- Teams, approvals, audit log, multi-location
- Signed codes, anti-tamper alerts
- Wallet passes, CRM integrations
- Custom domains for pages, multi-location page templates, page approvals
- Link-out booking and payment blocks

**Phase 5: Platform (weeks 40+)**
- Public API, webhooks, bulk endpoints
- Embed SDK
- Additional industry packs, artistic/AI code add-ons
- QR-linked community tip boards (as a page block)
- Text-to-update, offline-cached pages, pages API

---

## 10. Risks and Open Questions

| Risk | Mitigation |
|---|---|
| **Crowded market** of generators | Niche packs, trust layer, and design quality as wedge |
| **Redirect service is a single point of failure** (dead service means dead printed codes) | High availability, fallback modes, export-to-static escape hatch, clear continuity policy so customers trust printing on our links |
| **Privacy of scan analytics** | Aggregate by default, no personal identifiers, region-level location, clear disclosure, compliance review (GDPR/CCPA) |
| **Artistic codes fail to scan** | Mandatory scannability gate, device testing prompts, conservative defaults |
| **Abuse: phishing and malicious redirects** | Destination scanning, reporting flow, rate limits, link preview |
| **Medical data on codes** | Clear warnings that static codes are readable by anyone who scans; recommend minimal data; no claims of medical-grade security |
| **Vendor lock-in concerns** | Offer export of all codes and static fallbacks; allow custom domains |
| **Anti-tamper claims overpromise** | Position as detection and alerting, not prevention |
| **Scope creep into a website builder** | One page, fixed block set, no custom code; anything bigger is a link-out |
| **Hosting phishing/scam pages** | Constrained blocks, moderation, abuse reporting, new-account limits, verified-business badge |
| **AI mistakes in photo-to-page** (wrong prices, missed allergens) | Mandatory human review before publish; highlight low-confidence fields; disclaimers on allergen data |
| **Review-policy violations** | Neutral review and private-feedback options shown together, never selective gating |
| **Slow pages on weak signal** | Speed budget, image compression, edge caching, offline cache |
| **Support load from non-technical users** | Templates, AI setup, and guided flows over open-ended design freedom |

**Open questions**
1. Which first industry pack: restaurants (crowded, fast sales) or facilities (less crowded, stickier)?
2. Pricing: per seat, per code, or per scan?
3. Do we sell physical products (stickers, table tents, etched items) or partner with printers?
4. Is the community tip board a separate product or a feature of location-linked codes?
5. Custom-domain requirement: bundled in Pro or Business only?
6. Hosted pages: how strict should the block set be at launch, and do we ever allow custom HTML?
7. Is the free page badge enough incentive to upgrade, or do we also cap views or blocks?
8. Which AI setup input do we build first: menu photo or social-profile link?

---

## 11. Success Metrics

- **Adoption:** free static codes generated; conversion from static to dynamic
- **Quality:** percentage of exported codes scoring "easy to scan"; scan failure reports
- **Engagement:** scans per code; codes edited after printing (proves dynamic value)
- **Business:** free-to-paid conversion; integrations connected per business; API calls per active developer
- **Trust:** flagged-malicious links caught; tamper alerts resolved
- **Onboarding:** median time from signup to first live code (target: under 5 minutes)
- **Hosted pages:** pages published; share of new users who use "build my page for me"; page load time; edits per page after launch; free-to-paid conversion for page users

---

## 12. Suggested Next Builds (Prototypes)

1. **Offline Card Generator** (contact, medical, Wi-Fi, home emergency) with printable layouts
2. **Brand Styler** with logo upload, shape presets, and live scannability score
3. **Guided Wizard demo** showing the "what should happen when someone scans?" flow
4. **Industry pack mockup** (restaurant table-order flow) showing integrations end to end
5. **Hosted Page Builder** with live phone preview, brand-matched theme, and open/closed toggle (recommended first, since it demonstrates the "no website needed" value most clearly)
