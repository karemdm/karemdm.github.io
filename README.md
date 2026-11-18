# karemdm.github.io

Bilingual portfolio of Karem Daiane Marcomini, Ph.D., published with GitHub Pages: English at `/` and Brazilian
Portuguese at `/pt/`.

Sections: about, skills, experience, projects (with detailed pages under `projects/`), publications, education and
contact. Static HTML with shared styles in `assets/site.css` and `assets/project.css`, IBM Plex fonts, a light/dark
theme switch and a layout that works down to phone width.

## Project pages

Each project page (EN and PT) is generated from a content file:

```bash
python _build/build_projects.py
```

- `_build/projects/NN_<slug>.py`: texts, stats, pipeline and state diagrams, tables and commands for one project.
- `_build/data/`: data behind the charts (for example a feature trace CSV).
- `assets/projects/<slug>/`: demo videos, posters and frames.

`_build/` is not published by GitHub Pages.

Prepared with AI assistance.
