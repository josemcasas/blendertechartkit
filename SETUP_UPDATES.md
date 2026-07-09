# Auto-updates via GitHub Pages (Blender native)

No custom updater — this uses Blender 4.2+ remote extension repositories.

## One-time setup

### 1. Publish the repo
```powershell
git init && git add . && git commit -m "Initial"
git branch -M main
git remote add origin https://github.com/<user>/blendertechartkit.git
git push -u origin main
```

### 2. Enable GitHub Pages
Repo → Settings → Pages → **Source: Deploy from a branch** → Branch: `main` → Folder: `/docs` → Save.
Pages will serve `https://<user>.github.io/blendertechartkit/`.

### 3. Build + publish the first release
```powershell
powershell -ExecutionPolicy Bypass -File build_release.ps1 -Push
```
This writes `docs/index.json` + `blendertechartkit-<ver>.zip` and pushes them.
Your repo URL is:
```
https://<user>.github.io/blendertechartkit/index.json
```

### 4. Add the repo in Blender (once, on each machine)
Preferences → Get Extensions → ▾ (top-right) → **Add Remote Repository** →
paste the `index.json` URL → tick **Check for Updates on Startup** → OK.
Then find "Blender TechArt Kit" in the list and **Install** it *from there*.

> ⚠️ Install from the remote repo, **not** "Install from Disk". Only repo-installed
> extensions are tracked for updates.

## Releasing an update
1. Bump `version` in `blender_manifest.toml` (e.g. `0.1.0` → `0.1.1`).
2. `powershell -ExecutionPolicy Bypass -File build_release.ps1 -Push`
3. Blender flags the update on next startup (or Get Extensions → **Check for Updates**),
   one click to install.

That's the whole loop: **bump → run → push** on your side, **one click** on Blender's.

## Private instead of public?
GitHub Pages requires a public repo (or Pages on GitHub Pro). If you need it
private, host `docs/` on any HTTPS location (Netlify, S3, a VPS) and point the
remote repository URL there — the build step is identical, just skip `-Push` and
upload `docs/` yourself.
