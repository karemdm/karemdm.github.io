# Demo tools

Scripts used to record and edit the short demo videos for the portfolio projects.

## Files

- `record_demo.py`: records a scripted console demo of a project on a fixed screen region (ffmpeg gdigrab), placing the opened windows on top. Takes a scenario JSON.
- `backdrop.py`: borderless solid-colour window that covers the recording stage behind the demo windows.
- `edit_demo.py`: cuts a raw recording into speed-adjusted segments and exports a web MP4 and a poster image.
- `screencast.py`: high-quality page recording through the Chrome DevTools screencast (JPEG frames with timestamps), for use in Playwright scripts.
- `cursor.js`: injected script that draws a visible cursor on web pages during recording.
- `record_streamlit_ppe.py`: records the PPE Streamlit app in use with Playwright (headless Edge, page video, drawn cursor) and prints time marks for editing.
- `record_nutrilabel_ui.py`: records the NutriLabel web interface in use with Playwright and prints time marks for editing.
- `record_line_counter.py`: screen-records the line-counter desktop flow, checking window focus before each keystroke or click, and prints time marks.
- `probe_streamlit.py`: opens a Streamlit app in Edge, dumps its widgets and saves a screenshot, to plan a recording.
- `seq_merge_site.sh`: merges site pull requests one by one (rebase on main, regenerate pages, push, merge). Stops on conflicts outside generated pages.
- `rerecord_web.sh`: starts the two web apps, runs the web recorders and stops the servers.
- `resolve_additive.py`: resolves git conflicts where both sides only added lines (keeps both, ours first).
- `scenarios/fall.json`, `scenarios/fall-ice2.json`: scenario files read by `record_demo.py`.

## Requirements

- Windows desktop for the screen-recording scripts (`record_demo.py`, `record_line_counter.py`), which use pyautogui, pygetwindow and ffmpeg with the gdigrab input.
- Playwright with an installed Microsoft Edge (`channel="msedge"`) for the web-app recorders (`probe_streamlit.py`, `record_streamlit_ppe.py`, `record_nutrilabel_ui.py`, `screencast.py`).
- imageio-ffmpeg for the ffmpeg binary used by `edit_demo.py`.

## Configuration

Paths at the top of the scripts point to the author's local folders (for example under the user's Desktop, and a fixed repository path in the shell scripts). Adapt them to your own folders before running.
