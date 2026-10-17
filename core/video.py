# -*- coding: utf-8 -*-
"""Video kurulumu: görsel slayt + ses + isteğe bağlı altyazı (ffmpeg).

Çıktı .part dosyasına yazılır, bitince yeniden adlandırılır (çökme dayanıklı).
Ses varsa final karışım -16 LUFS'a normalize edilir (YouTube uyumlu).
"""

import json
import os
import subprocess
from pathlib import Path

KLASIK_ORANLAR = {
    "9:16": (1080, 1920),   # Shorts / Reels / TikTok
    "16:9": (1920, 1080),   # YouTube uzun
    "1:1": (1080, 1080),    # IG feed
}


def ffprobe_sure(dosya):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(dosya)],
            capture_output=True, text=True, timeout=30)
        return float(json.loads(r.stdout or "{}").get("format", {}).get("duration", 0))
    except Exception:
        return 0.0


def ffmpeg_var_mi():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=15)
        return True
    except Exception:
        return False


def srt_yaz(satirlar, hedef):
    """[{baslangicSn, sureSn, metin}] → SRT dosyası (atomik)."""
    def _ts(sn):
        sn = max(0.0, sn)
        sa = int(sn // 3600)
        dk = int((sn % 3600) // 60)
        sn_i = int(sn % 60)
        ms = int(round((sn - int(sn)) * 1000))
        return f"{sa:02d}:{dk:02d}:{sn_i:02d},{ms:03d}"

    sat = []
    for i, s in enumerate(satirlar, 1):
        bitis = s["baslangicSn"] + s["sureSn"]
        sat.append(f"{i}\n{_ts(s['baslangicSn'])} --> {_ts(bitis)}\n{s['metin']}\n")
    hedef = Path(hedef)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    part = hedef.with_suffix(hedef.suffix + ".part")
    with open(part, "w", encoding="utf-8") as f:
        f.write("\n".join(sat))
    os.replace(part, hedef)
    return hedef


def _girdi_hazirla(liste, ses_sure):
    """Her görsel kare_sure kadar döner; ses varsa kareler ses süresine bölünür."""
    girdi = []
    if ses_sure and ses_sure > 0:
        kare = ses_sure / max(1, len(liste))
        for yol, _ in liste:
            girdi += ["-loop", "1", "-t", f"{kare:.3f}", "-i", yol]
        return girdi, kare * len(liste), kare
    toplam = 0.0
    for yol, sure in liste:
        girdi += ["-loop", "1", "-t", f"{sure:.3f}", "-i", yol]
        toplam += sure
    return girdi, toplam, None


def video_kur(gorseller, cikti_yol, ses_yol=None, srt_yol=None,
              oran="9:16", kare_sure=4.0):
    """Görsel listesinden MP4 kurar.

    gorseller: [(gorsel_yol, sure_sn)] veya [gorsel_yol]
    ses_yol: isteğe bağlı mp3 (yoksa sessiz video)
    srt_yol: isteğe bağlı altyazı (yanar)
    """
    if not ffmpeg_var_mi():
        raise RuntimeError("ffmpeg bulunamadı. Kurun: winget install ffmpeg")

    cikti_yol = Path(cikti_yol)
    cikti_yol.parent.mkdir(parents=True, exist_ok=True)
    genislik, yukseklik = KLASIK_ORANLAR.get(oran, KLASIK_ORANLAR["9:16"])

    liste = []
    for g in gorseller:
        if isinstance(g, (tuple, list)):
            liste.append((str(g[0]), float(g[1])))
        else:
            liste.append((str(g), kare_sure))
    if not liste:
        raise ValueError("Görsel listesi boş")
    for yol, _ in liste:
        if not os.path.isfile(yol):
            raise FileNotFoundError(f"Görsel yok: {yol}")

    ses_var = bool(ses_yol and os.path.isfile(ses_yol))
    ses_sure = ffprobe_sure(ses_yol) if ses_var else 0.0
    girdi, toplam, _kare = _girdi_hazirla(liste, ses_sure)
    n = len(liste)
    srt_var = bool(srt_yol and os.path.isfile(srt_yol))
    srt_win = ""
    if srt_var:
        srt_win = str(Path(srt_yol).resolve()).replace("\\", "/").replace(":", "\\:")

    olcek = (f"scale={genislik}:{yukseklik}:force_original_aspect_ratio=increase,"
             f"crop={genislik}:{yukseklik},fps=30")
    if srt_var:
        olcek += f",subtitles='{srt_win}'"
    olcek += ",format=yuv420p"

    if n == 1:
        vf = olcek
        harita = ["-map", "0:v"]
        filtre = None
    else:
        # her kare ölçeklenir, concat ile birleşir
        parcalar = "".join(
            f"[{i}:v]{olcek if not srt_var else f'scale={genislik}:{yukseklik}:force_original_aspect_ratio=increase,crop={genislik}:{yukseklik},fps=30'}[v{i}];"
            for i in range(n))
        birlesim = "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vcat]"
        if srt_var:
            filtre = parcalar + birlesim + f";[vcat]subtitles='{srt_win}',format=yuv420p[vout]"
        else:
            filtre = parcalar + birlesim + ";[vcat]format=yuv420p[vout]"
        vf = None
        harita = ["-map", "[vout]"]

    komut = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + girdi
    if ses_var:
        komut += ["-i", str(ses_yol)]
    if filtre:
        komut += ["-filter_complex", filtre]
    else:
        komut += ["-vf", vf]
    komut += harita
    if ses_var:
        komut += ["-map", f"{n}:a",
                  "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                  "-c:a", "aac", "-b:a", "192k"]
    komut += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
              "-movflags", "+faststart", "-t", f"{toplam:.3f}"]

    part = cikti_yol.with_suffix(cikti_yol.suffix + ".part")
    komut += ["-f", "mp4", str(part)]
    r = subprocess.run(komut, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0 or not part.is_file() or part.stat().st_size < 1000:
        hata = (r.stderr or "")[-800:]
        try:
            part.unlink()
        except OSError:
            pass
        raise RuntimeError(f"ffmpeg render hatası: {hata}")

    boyut = part.stat().st_size
    os.replace(part, cikti_yol)
    return {"cikti": str(cikti_yol), "sureSn": round(ffprobe_sure(cikti_yol), 2),
            "boyut_mb": round(boyut / 1e6, 2)}
