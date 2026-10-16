# -*- coding: utf-8 -*-
"""AI Influencer Otomasyonu — giriş noktası."""

import sys
from pathlib import Path

# Proje kökünü path'e ekle
KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK))


def main():
    from core import depolama
    depolama.kur()

    from gui.ana_pencere import calistir
    calistir()


if __name__ == "__main__":
    main()
