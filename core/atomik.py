# -*- coding: utf-8 -*-
"""Atomik dosya yazımı: önce .part, sonra rename (çökme dayanıklı)."""

import json
import os
from pathlib import Path


def atomik_yaz(yol, veri, binary=False):
    """Dosyayı .part'a yazıp atomik olarak yeniden adlandırır."""
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    part = yol.with_suffix(yol.suffix + ".part")
    if binary:
        with open(part, "wb") as f:
            f.write(veri)
    else:
        with open(part, "w", encoding="utf-8") as f:
            f.write(veri)
    os.replace(part, yol)
    return yol


def atomik_json_yaz(yol, veri):
    return atomik_yaz(yol, json.dumps(veri, ensure_ascii=False, indent=2))


def json_oku(yol, varsayilan=None):
    try:
        with open(yol, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return varsayilan
