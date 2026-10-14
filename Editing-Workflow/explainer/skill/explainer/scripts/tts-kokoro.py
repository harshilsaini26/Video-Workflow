#!/usr/bin/env python3
"""tts-kokoro.py: the voiceover, line by line with Kokoro-82M (Apache-2.0, runs locally), joined and levelled.

  tts-kokoro.py --script script.json --out voice.wav [--voice ID] [--speed 1.0] [--only l3]
                [--engine kokoro|fake] [--lexicon PATH] [--samples DIR]

Each line goes to lines/<id>.wav (24 kHz mono) next to voice.wav, with the text Kokoro read in lines/<id>.txt, so a
mispronounced line is fixed in lexicon.json or in `say` and regenerated alone with --only. The lines are joined with a
pause by their `break` (comma 0.15 s, sentence 0.35 s, section 0.6 s), then cleaned: high-pass 80 Hz, gentle
compression, two-pass loudnorm to -16 LUFS with the true peak at most -1 dBTP, 48 kHz mono.

It prints {"duration", "lufs", "peak"} and exits 1 when the length is more than 10% off `target_seconds` (gate E2).
--samples DIR writes 10 s of line 0 in three voices for the creator to choose from (Checkpoint A).
The fake engine (tests) writes a 220 Hz tone, 0.32 s a word, with no model and no network.
"""
import argparse, array, json, math, os, re, subprocess, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__))
RATE = 24000
PAUSE = {"comma": 0.15, "sentence": 0.35, "section": 0.6}
SAMPLE_VOICES = ["af_heart", "am_michael", "bf_emma"]
DEFAULT_VOICE = "af_heart"
CLEAN = "highpass=f=80,acompressor=threshold=-18dB:ratio=3:attack=10:release=120"
LOUD = "loudnorm=I=-16:TP=-1:LRA=11"
TOLERANCE = 0.10


sys.path.insert(0, HERE)
from explainer_lib import apply_lexicon, load_lexicon


def write_wav(path, samples):
    """samples: floats in -1..1 at RATE, written as 16-bit mono."""
    pcm = array.array("h", (int(max(-1.0, min(1.0, s)) * 32767) for s in samples))
    if sys.byteorder == "big":
        pcm.byteswap()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())


def fake_engine(text, voice, speed):
    n = int(round(len(text.split()) * 0.32 * RATE))
    return [0.3 * math.sin(2 * math.pi * 220 * i / RATE) for i in range(n)]


_pipes = {}


def kokoro_engine(text, voice, speed):
    try:
        from kokoro import KPipeline
    except ImportError:
        sys.exit("kokoro is not installed: pip install kokoro soundfile (and espeak-ng for unusual words); see the PLAYBOOK, E2")
    lang = "b" if voice.startswith("b") else "a"
    if lang not in _pipes:
        _pipes[lang] = KPipeline(lang_code=lang)
    out = []
    for _, _, audio in _pipes[lang](text, voice=voice, speed=speed):
        a = audio.numpy() if hasattr(audio, "numpy") else audio
        out.extend(float(x) for x in a)
    return out


ENGINES = {"fake": fake_engine, "kokoro": kokoro_engine}


def ffmpeg(*args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-y"] + list(args), capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed: " + r.stderr[-800:])
    return r.stderr


def loudnorm_json(stderr):
    return json.loads(stderr[stderr.rindex("{"):stderr.rindex("}") + 1])


def join(paths, pauses, out):
    """Concatenate the line wavs (all 24 kHz mono 16-bit) with silence between them."""
    with wave.open(out, "wb") as o:
        o.setnchannels(1)
        o.setsampwidth(2)
        o.setframerate(RATE)
        for p, gap in zip(paths, pauses):
            with wave.open(p) as w:
                o.writeframes(w.readframes(w.getnframes()))
            o.writeframes(b"\x00\x00" * int(round(gap * RATE)))


def level(src, out):
    """Clean and level to -16 LUFS / -1 dBTP in two passes; return (lufs, true peak) measured on the result."""
    m = loudnorm_json(ffmpeg("-i", src, "-af", CLEAN + "," + LOUD + ":print_format=json", "-f", "null", "-"))
    second = (LOUD + ":measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}"
              ":offset={target_offset}:linear=true").format(**m)
    ffmpeg("-i", src, "-af", CLEAN + "," + second, "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", out)
    r = loudnorm_json(ffmpeg("-i", out, "-af", LOUD + ":print_format=json", "-f", "null", "-"))
    return float(r["input_i"]), float(r["input_tp"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--only", help="regenerate just this line id, then rebuild voice.wav")
    ap.add_argument("--engine", choices=sorted(ENGINES), default="kokoro")
    ap.add_argument("--lexicon", default=os.path.join(HERE, "..", "lexicon.json"))
    ap.add_argument("--samples", help="write 10 s of line 0 in each sample voice here, then stop")
    a = ap.parse_args()
    with open(a.script) as f:
        S = json.load(f)
    lines = S["lines"]
    if a.only and a.only not in {ln["id"] for ln in lines}:
        sys.exit("--only %s: no such line" % a.only)
    lex = load_lexicon(a.lexicon)
    synth = ENGINES[a.engine]
    voice = a.voice or S.get("voice") or DEFAULT_VOICE

    def say(ln):
        return apply_lexicon(str(ln.get("say") or ln["show"]), lex)

    if a.samples:
        os.makedirs(a.samples, exist_ok=True)
        for v in SAMPLE_VOICES:
            write_wav(os.path.join(a.samples, v + ".wav"), synth(say(lines[0]), v, a.speed)[:10 * RATE])
        print(json.dumps({"samples": [os.path.join(a.samples, v + ".wav") for v in SAMPLE_VOICES]}))
        return

    ldir = os.path.join(os.path.dirname(os.path.abspath(a.out)), "lines")
    paths = []
    for ln in lines:
        p = os.path.join(ldir, ln["id"] + ".wav")
        if a.only is None or ln["id"] == a.only or not os.path.exists(p):
            text = say(ln)
            write_wav(p, synth(text, voice, a.speed))
            with open(os.path.join(ldir, ln["id"] + ".txt"), "w") as f:
                f.write(text + "\n")
        paths.append(p)
    pauses = [PAUSE.get(ln.get("break") or "sentence", PAUSE["sentence"]) for ln in lines[:-1]] + [0.0]
    joined = os.path.join(ldir, "_joined.wav")
    join(paths, pauses, joined)
    lufs, peak = level(joined, a.out)
    os.remove(joined)
    with wave.open(a.out) as w:
        dur = w.getnframes() / w.getframerate()
    print(json.dumps({"duration": round(dur, 3), "lufs": lufs, "peak": peak}))
    target = S.get("target_seconds")
    if target and abs(dur - float(target)) > TOLERANCE * float(target):
        print("E2 FAIL: %.1f s is off target by %.0f%% (target %s s, allowed 10%%)" % (dur, abs(dur - float(target)) / float(target) * 100, target))
        sys.exit(1)


if __name__ == "__main__":
    main()
