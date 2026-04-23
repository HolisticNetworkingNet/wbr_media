# WBR Media Manager

A reusable, content-aware media system for Django projects.

This is not just file uploads.  
This is an attempt to treat media as a first-class part of structured content.

---

## What This Is

`wbr_media` is a standalone Django app that provides:

- A central **MediaAsset model**
- A growing **media library system**
- The foundation for **image renditions and optimization**
- A path toward **usage tracking across content**

It is designed to be installed into multiple projects (e.g., portfolio, WBR) without modification.

---

## What This Is Not

- Not a full CMS
- Not a drop-in WordPress clone
- Not a UI-first system

This is an **infrastructure layer**, not a product.

---

## Core Philosophy

Media should be:

- **Structured** – not scattered across models
- **Reusable** – one asset, many contexts
- **Traceable** – where is this used?
- **Deterministic** – predictable paths, predictable outputs
- **Optimized** – no runtime guessing

If content is structured, media must be too.

---

## Current Capabilities (v0.1)

- Upload and store media assets
- Basic admin interface
- Thumbnail preview in Django admin
- Configurable upload paths via settings

---

## Planned Features

- Automatic width/height extraction
- Pre-generated image renditions (thumb, hero, etc.)
- Media usage tracking across models
- Custom media library UI (beyond Django admin)
- API endpoints for media access
- Orphan detection and cleanup

---

## Installation (Local Development)

From the repo root:

```bash
pip install -e .