from demo.demo.settings import WBR_MEDIA

# wbr_media

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Django](https://img.shields.io/badge/django-4.2%2B-green)
![Status](https://img.shields.io/badge/status-active-success)
![Tests](https://github.com/holisticnetworkingnet/wbr_media/actions/workflows/tests.yml/badge.svg)

A small, reusable media app for Django.

`wbr_media` provides a clean way to store, manage, and render media assets without pulling in a full CMS or rebuilding the same patterns in every project.

---

## 📷 Screenshots

### Media Index
A lightweight media library view with previews and metadata.
![Media index](docs/images/wbr_media_index.png)

### Media Detail
Asset inspection with preview, metadata, and image properties.
![Media detail](docs/images/wbr_media_admin.png)

---

## Why WBR Media?

Django handles file uploads well, but it doesn’t provide a consistent,
structured way to manage and render media across content types.

`wbr_media` is a small layer that standardizes:

- how media is stored
- how metadata is handled
- how media is rendered in templates

without introducing a full CMS.

## Why not just use Django FileField directly?

You can—but you'll end up reimplementing:

- metadata extraction
- file cleanup on replacement
- consistent rendering patterns
- image-specific handling

`wbr_media` provides these in a small, reusable layer.

## ✨ Features

- Structured `MediaAsset` model
- Automatic file metadata extraction (name, size, MIME type)
- Image-specific metadata (dimensions, format, etc.)
- Safe file replacement and deletion (no orphaned files)
- Simple, flexible template tag for rendering media

---

## 📸 Example

```django
{% load wbr_media_tags %}

{% render_media asset %}
{% render_media asset display="bare" class_name="card-image" %}
```

---

## 🚀 Installation

```bash
pip install -e .
```

Add to your Django settings:

```python
INSTALLED_APPS = [
    ...
    "wbr_media",
]
```

Configure your media save location. 

__IMPORTANT__: This directory will be appended to the `MEDIA_ROOT` setting.
```python
WBR_MEDIA = [
    "UPLOAD_TO": "wbr_media/%Y/%m/",
]
```

Run migrations:

```bash
python manage.py migrate
```

---

## 🧠 Basic Usage

Upload media via Django admin, then render in templates:

```django
{% load wbr_media_tags %}

{% render_media asset %}
```

### Optional arguments

```django
{% render_media asset size="full" %}
{% render_media asset display="bare" %}
{% render_media asset class_name="my-class" %}
```

### Arguments

| Argument     | Description |
|-------------|------------|
| `size`      | Named size (default: "full" — currently original file) |
| `display`   | Controls markup:<br>• `figure` (default for images)<br>• `bare` (just `<img>`)<br>• `link` (default for non-images) |
| `class_name`| Passed through to the rendered element |

---

## ⚙️ Configuration

Optional settings:

```python
WBR_MEDIA = {
    "UPLOAD_TO": "assets/originals/%Y/%m/",
}
```

---

## 📦 What This Is

- A lightweight media layer for Django projects
- A consistent way to handle files + metadata
- A simple rendering interface for templates

---

## 🚫 What This Is Not

- Not a CMS
- Not a full media library UI
- Not trying to replicate WordPress

This is a focused, infrastructure-level tool.

---

## 🧪 Development

A demo project is included:

```bash
cd demo
python manage.py runserver
```

## Testing

```bash
pytest wbr_media/tests.py
```

Visit:

http://127.0.0.1:8000/media-demo/

---

## 🛣️ Roadmap

Small, practical improvements:

- Size-based image renditions
- Better integration with project-specific design systems
- Optional media usage tracking

No large UI or CMS features are planned.

---

## 📷 Screenshots (optional)

Add a screenshot of:
- Admin media preview
- Demo grid page

---

## 📄 License

All Rights Reserved.
