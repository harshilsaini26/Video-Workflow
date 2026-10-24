#!/usr/bin/env python3
"""filmcraft.py: the hand-off's FCP 7 XML and captions made into a native filmcraft project (.fcproj) with
filmcraft-cli (github.com/storytold/filmcraft, MIT OR Apache-2.0), and read back for the checks.

  find_cli()                                   -> path of filmcraft-cli ($FILMCRAFT_CLI, else the PATH) or None
  to_project(xml, srt, out_fcproj)             -> {"offlineMedia": [...], "captions": n, "sequences": [...], "report": [...]}
  inspect(fcproj)                              -> {"sequence": {...}, "captions": [...], "media": [...]}

Get filmcraft-cli from a filmcraft release, or build it: `cargo build --release -p filmcraft-cli` in a checkout.
"""
import json, os, shutil, subprocess


class FilmcraftError(Exception):
    pass


def find_cli():
    env = os.environ.get("FILMCRAFT_CLI")
    if env and os.path.isfile(env):
        return env
    return shutil.which("filmcraft-cli")


def _cli():
    cli = find_cli()
    if not cli:
        raise FilmcraftError("filmcraft-cli not found: set FILMCRAFT_CLI or put it on the PATH")
    return cli


def _run(args, stdin=None):
    r = subprocess.run([_cli(), "--compact"] + args, input=stdin, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout, r.stderr


def to_project(xml, srt, out_fcproj):
    lines = [{"id": "file.import", "params": {"paths": [os.path.abspath(xml)]}}]
    if srt:
        lines.append({"id": "captions.import", "params": {"path": os.path.abspath(srt)}})
    code, out, err = _run(["--save-as", os.path.abspath(out_fcproj), "run", "-"], "\n".join(json.dumps(l) for l in lines) + "\n")
    results = []
    for line in out.splitlines():
        try:
            results.append(json.loads(line))
        except ValueError:
            continue
    bad = [r for r in results if not r.get("ok")]
    if code != 0 or bad or not results:
        why = (bad[0].get("error") if bad else None) or err.strip() or out.strip() or "no result"
        raise FilmcraftError("filmcraft-cli could not import %s: %s" % (os.path.basename(xml), why))
    imp = results[0]["result"]
    docs = imp.get("documents") or []
    if imp.get("errors") or not docs:
        raise FilmcraftError("filmcraft-cli could not import %s: %s" % (os.path.basename(xml), imp.get("errors") or "no sequence in it"))
    return {"offlineMedia": [m for d in docs for m in d.get("offlineMedia", [])], "sequences": imp.get("sequences", []),
            "report": [x for d in docs for x in d.get("report", [])],
            "captions": results[1]["result"].get("captions", 0) if len(results) > 1 else 0}


def _json(args):
    code, out, err = _run(args)
    if code != 0:
        raise FilmcraftError("filmcraft-cli %s: %s" % (" ".join(args[2:]), err.strip() or out.strip()))
    return json.loads(out)


def inspect(fcproj):
    p = ["--project", os.path.abspath(fcproj)]
    caps = _json(p + ["exec", "captions.list"])
    return {"sequence": _json(p + ["inspect", "sequence"]),
            "captions": [c for t in caps.get("tracks", []) for c in t.get("captions", [])],
            "media": _json(p + ["exec", "media.status"])}
