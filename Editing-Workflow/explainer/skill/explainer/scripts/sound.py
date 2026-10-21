"""sound.py: the bed under the voice (PLAYBOOK §E3): music or a generated pad, looped to the reel and ducked under the
voice, plus a whoosh on every moving transition and a pop as items land, so the reel never drops to silence.

Everything here is made on this machine and is the same every time: the pad and the sound effects are synthesised in
Python with fixed seeds (no samples, no licences), and FFmpeg only loops, fades and ducks. Music from the creator is a
file next to storyboard.json; its licence goes in SOURCES.md like any other source.
"""
import array, math, os, random, shutil, subprocess, tempfile, wave

RATE = 48000
LEAD = 0.12          # a whoosh starts this long before its scene
SPACE = 0.35         # never two sounds closer than this
PAD_VERSION = 1
# the pad: A minor, F, C, G, four seconds each, crossfaded; every frequency a whole number of cycles in 16 s, so it loops
CHORDS = [(110.0, 220.0, 261.63, 329.63), (87.31, 174.61, 220.0, 261.63), (130.81, 261.63, 329.63, 392.0), (98.0, 196.0, 246.94, 293.66)]
WEIGHTS = (0.42, 0.30, 0.20, 0.16)
LOOP = 16.0


def _write(path, left, right=None, rate=RATE):
    right = left if right is None else right
    data = array.array("h")
    for l, r in zip(left, right):
        data.append(max(-32767, min(32767, int(l * 32767))))
        data.append(max(-32767, min(32767, int(r * 32767))))
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(data.tobytes())
    return path


def make_sfx(folder):
    """whoosh.wav (0.6 s of swept noise, panned left to right), pop.wav (a 0.14 s falling blip) and chime.wav (a soft
    two-tone bell for the key moment): {"whoosh", "pop", "chime": path}."""
    os.makedirs(folder, exist_ok=True)
    rng = random.Random(7)
    n = int(0.6 * RATE)
    lo, left, right = 0.0, [], []
    for i in range(n):
        x = i / float(n)
        cut = 300 + 2700 * math.sin(math.pi * x) ** 2                  # the filter opens and closes: the "whoosh"
        a = 1 - math.exp(-2 * math.pi * cut / RATE)
        lo += a * (rng.uniform(-1, 1) - lo)
        v = lo * 0.9 * math.sin(math.pi * x) ** 2
        left.append(v * math.cos(x * math.pi / 2))
        right.append(v * math.sin(x * math.pi / 2))
    whoosh = _write(os.path.join(folder, "whoosh.wav"), left, right)
    n = int(0.14 * RATE)
    phase, pop = 0.0, []
    for i in range(n):
        t = i / float(RATE)
        phase += 2 * math.pi * (900 - 2800 * t) / RATE                    # 900 Hz falling to about 500 Hz
        pop.append(0.32 * math.sin(phase) * math.exp(-35 * t))
    pop = _write(os.path.join(folder, "pop.wav"), pop)
    n = int(0.9 * RATE)                                                    # chime.wav: a soft two-tone bell, 0.9 s
    chime = [0.16 * (math.sin(2 * math.pi * 1318.5 * i / RATE) + 0.6 * math.sin(2 * math.pi * 1975.5 * i / RATE))
             * min(1.0, i / (0.004 * RATE)) * math.exp(-5.0 * i / RATE) for i in range(n)]
    return {"whoosh": whoosh, "pop": pop, "chime": _write(os.path.join(folder, "chime.wav"), chime)}


def make_pad(path):
    """A 16 s loop of soft chords (A minor, F, C, G) with a slow swell, written to `path`."""
    rate = 24000                     # FFmpeg brings it to 48 kHz; half the samples keeps this quick
    fade = 1.0
    out = []
    chords = [[round(f * LOOP) / LOOP for f in ch] for ch in CHORDS]
    for i in range(int(LOOP * rate)):
        t = i / float(rate)
        v = 0.0
        for k, ch in enumerate(chords):
            start = 4 * k - fade / 2
            d = (t - start) % LOOP                                       # time since this chord began fading in
            if d < fade:
                w = 0.5 - 0.5 * math.cos(math.pi * d / fade)
            elif d < 4:
                w = 1.0
            elif d < 4 + fade:
                w = 0.5 + 0.5 * math.cos(math.pi * (d - 4) / fade)
            else:
                continue
            v += w * sum(a * math.sin(2 * math.pi * f * t) for a, f in zip(WEIGHTS, ch))
        out.append(0.62 * v * (0.85 + 0.15 * math.sin(2 * math.pi * t / 4.0)))
    return _write(path, out, rate=rate)


def pad_file():
    """The pad, made once per machine and kept in the temp folder."""
    path = os.path.join(tempfile.gettempdir(), "explainer-pad-v%d.wav" % PAD_VERSION)
    if not os.path.exists(path):
        tmp = path + ".%d.tmp" % os.getpid()
        make_pad(tmp)
        os.replace(tmp, path)
    return path


def events(transitions, items, chimes=()):
    """[(seconds, "whoosh"|"pop"|"chime")]: a whoosh LEAD ahead of every transition that moves (not fade or cut), a chime
    on each key moment (the payoff: it always sounds), a pop at each item's time, never a pop within SPACE of another
    sound."""
    out = [(round(max(0.0, t - LEAD), 3), "whoosh") for kind, t in transitions if kind not in ("fade", "cut")]
    out += [(round(t, 3), "chime") for t in chimes]
    for t in sorted(items):
        if all(abs(t - s) >= SPACE for s, _ in out):
            out.append((round(t, 3), "pop"))
    return sorted(out)


def _sfx_track(evs, duration, folder):
    sfx = make_sfx(folder)
    clips = {}
    for k, p in sfx.items():
        with wave.open(p) as w:
            clips[k] = array.array("h", w.readframes(w.getnframes()))
    gain = {"whoosh": 0.55, "pop": 0.6, "chime": 0.5}
    n = int(round(duration * RATE)) * 2
    track = array.array("i", bytes(4 * n))
    for t, kind in evs:
        start = int(round(t * RATE)) * 2
        for j, v in enumerate(clips[kind]):
            if start + j >= n:
                break
            track[start + j] += int(v * gain[kind])
    data = array.array("h", (max(-32767, min(32767, v)) for v in track))
    path = os.path.join(folder, "sfx.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(data.tobytes())
    return path


def mix_bed(voice, music, evs, duration, out, music_db=-22, stems=None):
    """Write the bed to `out` (48 kHz stereo, `duration` long): `music` (a file, or None) looped, faded in and out and
    ducked under `voice` (a file, or None), with the sound effects `evs` on top. Returns `out`. With `stems` (a
    folder), it also writes the two parts the bed is the sum of, for the editor hand-off: music.wav (the ducked music,
    silence without music) and sfx.wav (the sound effects)."""
    folder = tempfile.mkdtemp(prefix="explainer-bed-")
    try:
        sfx = _sfx_track(evs, duration, folder)
        if stems:
            shutil.copy(sfx, os.path.join(stems, "sfx.wav"))
        if not music:
            shutil.copy(sfx, out)
            if stems:
                _write(os.path.join(stems, "music.wav"), [0] * int(round(duration * RATE)))
            return out
        D = "%.3f" % duration
        fmt = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
        graph = ["[0:a]%s,atrim=0:%s,asetpts=N/SR/TB,afade=t=in:d=0.3,afade=t=out:st=%.3f:d=1.5,volume=%sdB[m]"
                 % (fmt, D, max(0.0, duration - 1.5), music_db)]
        cmd = ["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", music, "-i", sfx]
        if voice:
            cmd += ["-i", voice]
            graph.append("[2:a]%s,apad[k]" % fmt)
            graph.append("[m][k]sidechaincompress=threshold=0.05:ratio=4:attack=15:release=350[d]")
            last = "d"
        else:
            last = "m"
        graph.append("[%s]asplit=2[%s1][%s2]" % (last, last, last))
        graph.append("[%s1][1:a]amix=inputs=2:normalize=0:duration=first[o]" % last)
        cmd += ["-filter_complex", ";".join(graph), "-map", "[o]", "-t", D, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", out]
        if stems:
            cmd += ["-map", "[%s2]" % last, "-t", D, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", os.path.join(stems, "music.wav")]
        subprocess.run(cmd, check=True, capture_output=True)
        return out
    finally:
        shutil.rmtree(folder, True)
