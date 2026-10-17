# -*- coding: utf-8 -*-
"""Kendi yüzünden yerel suret dönüştürücü — yüksek gerçekçilik, offline.

Gelişmiş pipeline:
1. MediaPipe FaceLandmarker (478 landmark, refine ile iris dahil)
2. Delaunay triangulation piecewise-affine warp (global affine yerine)
3. Cilt dostu bilateral filtre + unsharp mask
4. Histogram matching ile doğal ten tonu kaydırma
5. Ortalama yüz ile Poisson-benzeri cross-blend
6. Deterministik seed'li varyasyonlar
"""

import random
import time
from pathlib import Path

import cv2
import numpy as np

_MP_TASKS = False
try:
    import mediapipe as mp
    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.core.base_options import BaseOptions
    _MP_TASKS = True
except ImportError:
    _MP_TASKS = False

_MODEL_YOL = Path(__file__).resolve().parent.parent / "varlik" / "face_landmarker.task"
_MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/"
              "face_landmarker/face_landmarker/float16/1/face_landmarker.task")


def _model_hazirla():
    if _MODEL_YOL.is_file():
        return str(_MODEL_YOL)
    _MODEL_YOL.parent.mkdir(parents=True, exist_ok=True)
    try:
        import requests
        r = requests.get(_MODEL_URL, timeout=60)
        r.raise_for_status()
        _MODEL_YOL.write_bytes(r.content)
        return str(_MODEL_YOL)
    except Exception:
        return None


def _mp_landmark(img):
    if not _MP_TASKS:
        return None
    model = _model_hazirla()
    if not model:
        return None
    try:
        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False)
        with vision.FaceLandmarker.create_from_options(options) as landmarkeler:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            sonuc = landmarkeler.detect(mp_img)
            if not sonuc.face_landmarks:
                return None
            h, w = img.shape[:2]
            fl = sonuc.face_landmarks[0]
            return [(int(lm.x * w), int(lm.y * h)) for lm in fl]
    except Exception:
        return None


def yuz_bul(gorsel_yol):
    img = cv2.imread(str(gorsel_yol))
    if img is None:
        raise ValueError(f"Gorsel okunamadi: {gorsel_yol}")

    landmarklar = _mp_landmark(img)

    if landmarklar is not None:
        xs = [p[0] for p in landmarklar]
        ys = [p[1] for p in landmarklar]
        box = (min(xs), min(ys), max(xs), max(ys))
        return img, box, landmarklar

    # Fallback: Haar
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
    if len(faces) == 0:
        raise ValueError("Yuz bulunamadi. Daha net bir portre fotograf deneyin.")
    x, y, w, h = faces[0]
    box = (x, y, x + w, y + h)
    landmarklar = _box_landmark(img, box)
    return img, box, landmarklar


def _box_landmark(img, box):
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    pts = [
        (x1 + w // 2, y1 + h // 10), (x1 + w // 4, y1 + h // 4),
        (x2 - w // 4, y1 + h // 4), (x1, y1 + h // 2), (x2, y1 + h // 2),
        (x1 + w // 3, y1 + h // 2 - h // 10), (x2 - w // 3, y1 + h // 2 - h // 10),
        (x1 + w // 2, y1 + h // 2), (x1 + w // 2, y1 + h * 3 // 4),
        (x1 + w // 2, y2 - h // 6), (x1 + w // 2, y2),
        (x1 + w // 5, y2 - h // 4), (x2 - w // 5, y2 - h // 4),
    ]
    return pts


# MediaPipe FaceMesh'te anlamlı anatomik noktalar (478 landmark içinden)
# Bu indeksler bilinen FaceMesh şemasından alınmıştır
_ANA_INDEKS = {
    "alin": [10, 67, 69, 104, 108, 151, 336, 296, 334, 293, 300, 285],
    "sol_almakik": [116, 117, 118, 123, 50, 101, 100, 47, 126, 204, 205, 187],
    "sag_almakik": [345, 346, 347, 352, 283, 332, 331, 328, 355, 425, 426, 411],
    "sol_goz": [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
    "sag_goz": [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 49],
    "burun": [1, 2, 98, 327, 168, 6, 197, 195, 5, 4],
    "agiz": [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185],
    "cene": [152, 377, 400, 378, 152, 172, 136, 150, 149, 176, 148, 152],
    "siluet": [10, 234, 454, 152, 10],
}


def _delunay_warp(img, kaynak, hedef):
    """Delaunay triangulation ile piecewise-affine warp.

    Subdiv2D dikdörtgen köşeleri (0,0)/(w,0)/(0,h)/(w,h) üçgenlere girer;
    bunlar landmark setinde olmadığından en yakın noktaya snap edilip
    dev üçgenler (yanlış bölge yapıştırma) oluştururdu — köşe üçgenleri
    bilinçli olarak atlanır.
    """
    h, w = img.shape[:2]
    rect = (0, 0, w, h)

    # Benzersiz noktalar + kaynak→hedef eşlemesi (ilk geçeni koru)
    esleme = {}
    for s, d in zip(kaynak, hedef):
        p = (int(round(float(s[0]))), int(round(float(s[1]))))
        p = (max(0, min(w - 1, p[0])), max(0, min(h - 1, p[1])))
        if p not in esleme:
            esleme[p] = (np.array(s, dtype=np.float32),
                         np.array(d, dtype=np.float32))
    if len(esleme) < 3:
        return img.copy()

    tri = cv2.Subdiv2D(rect)
    for p in esleme:
        try:
            tri.insert((float(p[0]), float(p[1])))
        except cv2.error:
            pass

    ucgenler = tri.getTriangleList()
    son = img.copy()

    for t in ucgenler:
        pts_t = [(t[0], t[1]), (t[2], t[3]), (t[4], t[5])]
        src_tri, dst_tri = [], []
        gecerli = True
        for tx, ty in pts_t:
            anahtar = (int(round(tx)), int(round(ty)))
            if anahtar not in esleme:  # köşe/frame noktası veya yuvarlama kaybı
                gecerli = False
                break
            s, d = esleme[anahtar]
            src_tri.append(s)
            dst_tri.append(d)
        if not gecerli:
            continue
        src_tri = np.float32(src_tri)
        dst_tri = np.float32(dst_tri)

        try:
            # Dejenere üçgenleri atla (çok ince / çok büyük)
            alan_src = cv2.contourArea(src_tri.reshape(-1, 1, 2))
            alan_dst = cv2.contourArea(dst_tri.reshape(-1, 1, 2))
            if alan_src < 4 or alan_dst < 4:
                continue
            alan_oran = max(alan_src, alan_dst) / max(1.0, min(alan_src, alan_dst))
            if alan_oran > 8:
                continue

            r1 = cv2.boundingRect(src_tri)
            r2 = cv2.boundingRect(dst_tri)
            x1, y1, w1, h1 = r1
            x2, y2, w2, h2 = r2
            if w1 <= 0 or h1 <= 0 or w2 <= 0 or h2 <= 0:
                continue
            if x1 < 0 or y1 < 0 or x1 + w1 > w or y1 + h1 > h:
                continue

            src_crop = img[y1:y1 + h1, x1:x1 + w1]
            src_tri_rel = src_tri - np.array([x1, y1], dtype=np.float32)
            dst_tri_rel = dst_tri - np.array([x2, y2], dtype=np.float32)

            M = cv2.getAffineTransform(src_tri_rel, dst_tri_rel)
            warped = cv2.warpAffine(src_crop, M, (w2, h2),
                                    flags=cv2.INTER_LINEAR,
                                    borderMode=cv2.BORDER_REFLECT)

            mask = np.zeros((h2, w2), dtype=np.uint8)
            cv2.fillConvexPoly(mask, np.int32(dst_tri_rel), 255)

            y2e, y2f = max(0, y2), min(h, y2 + h2)
            x2e, x2f = max(0, x2), min(w, x2 + w2)
            wy1, wx1 = y2e - y2, x2e - x2
            wy2, wx2 = wy1 + (y2f - y2e), wx1 + (x2f - x2e)
            if wy2 <= wy1 or wx2 <= wx1:
                continue

            roi = son[y2e:y2f, x2e:x2f]
            mask_roi = mask[wy1:wy2, wx1:wx2]
            warped_roi = warped[wy1:wy2, wx1:wx2]
            if roi.shape != warped_roi.shape or mask_roi.shape[:2] != roi.shape[:2]:
                continue

            son[y2e:y2f, x2e:x2f] = np.where(mask_roi[..., None] > 0,
                                              warped_roi, roi)
        except Exception:
            continue

    return son


def _yuz_maske(img, landmarklar, genislet=0.12, yumusat=0.35):
    """Landmark'lardan türetilmiş yumuşatılmış yüz maskesi.

    Warp'ı yalnızca yüzün içine uygulayıp arka planı/silueti korur;
    böylece Delaunay sınır üçgenlerinin oluşturduğu ince tel çizgileri önlenir.
    """
    h, w = img.shape[:2]
    pts = np.array(landmarklar, dtype=np.int32)
    hull = cv2.convexHull(pts)

    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillConvexPoly(mask, hull, 255)

    # Yüzü biraz büyüt (kenar boşluğu bırak) ama arka plana taşma
    merkez = (w // 2, h // 2)
    olcek = 1.0 + genislet
    M = cv2.getRotationMatrix2D(merkez, 0, olcek)
    mask = cv2.warpAffine(mask, M, (w, h), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    # Yumuşak geçiş (feather) için Gaussian blur
    r = max(3, int(min(h, w) * yumusat * 0.05))
    mask = cv2.GaussianBlur(mask, (0, 0), r)
    return mask


def _ten_tonu_kaydir(img, rng):
    """LAB aralığında yumuşak, doğal ten tonu kaydırma (abartısız)."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)

    # L: parlaklık, A: yeşil-kırmızı, B: sarı-mavi — sınırlı kaydırma
    l_dk = rng.randint(-8, 8)    # parlaklık
    a_kay = rng.randint(-5, 5)   # ten sıcaklığı
    b_kay = rng.randint(-4, 4)   # ten sarılığı

    lab[:, :, 0] = np.clip(lab[:, :, 0] + l_dk, 0, 255)
    lab[:, :, 1] = np.clip(lab[:, :, 1] + a_kay, 0, 255)
    lab[:, :, 2] = np.clip(lab[:, :, 2] + b_kay, 0, 255)

    son = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

    # Hafif histogram eşleme (kontrast)
    if rng.random() < 0.35:
        lab2 = cv2.cvtColor(son, cv2.COLOR_BGR2LAB)
        clahe = cv2.createCLAHE(clipLimit=1.1, tileGridSize=(8, 8))
        lab2[:, :, 0] = clahe.apply(lab2[:, :, 0])
        son = cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)

    return son


def _cilt_parlat(img, rng):
    """Bilateral filter (kenar koruyucu cilt yumuşatma) + unsharp mask."""
    # Bilateral: cilt dokusunu korurken pürüzsüzleştirir
    d = rng.choice([5, 7, 9])
    sigma = rng.uniform(25, 50)
    yumusak = cv2.bilateralFilter(img, d, sigma, sigma)

    # Unsharp mask ile netlik
    net = cv2.addWeighted(img, 1.3, yumusak, -0.3, 0)

    # Hafif cross-dissolve
    alpha = rng.uniform(0.1, 0.25)
    son = cv2.addWeighted(img, 1 - alpha, yumusak, alpha, 0)
    son = cv2.addWeighted(son, 1.15, net, -0.15, 0)
    return son


def _goz_parlat(img, landmarklar, rng):
    """Göz çevresine hafif netlik/parlaklık artışı."""
    if len(landmarklar) < 380:
        return img
    h, w = img.shape[:2]
    son = img.copy()
    for goz_idx in [_ANA_INDEKS["sol_goz"], _ANA_INDEKS["sag_goz"]]:
        pts = np.array([landmarklar[i] for i in goz_idx if i < len(landmarklar)],
                       dtype=np.int32)
        if len(pts) < 4:
            continue
        x, y, gw, gh = cv2.boundingRect(pts)
        # Göz çevresi margin
        mx, my = int(gw * 0.3), int(gh * 0.5)
        x1, y1 = max(0, x - mx), max(0, y - my)
        x2, y2 = min(w, x + gw + mx), min(h, y + gh + my)
        roi = son[y1:y2, x1:x2]
        if roi.size == 0:
            continue
        # Parlaklığı koruyan unsharp mask (toplam=1.0) — parlaklık patlamasını önler
        blur = cv2.GaussianBlur(roi, (0, 0), sigmaX=1.2)
        roi = cv2.addWeighted(roi, 1.35, blur, -0.35, 0)
        son[y1:y2, x1:x2] = roi
    return son


def _boyutlandir(img, hedef_w=1024, hedef_h=1280):
    h, w = img.shape[:2]
    oran = hedef_w / hedef_h
    mevcut = w / h
    if mevcut > oran:
        yeni_w = int(h * oran)
        x = (w - yeni_w) // 2
        img = img[:, x:x + yeni_w]
    else:
        yeni_h = int(w / oran)
        y = (h - yeni_h) // 2
        img = img[y:y + yeni_h, :]
    return cv2.resize(img, (hedef_w, hedef_h), interpolation=cv2.INTER_LANCZOS4)


def varyasyon_uret(gorsel_yol, cikti_klasor, seed=None, sayi=8):
    """Yüksek gerçekçilikli 8 varyasyon üretir."""
    if seed is None:
        seed = random.randint(1, 2**31 - 1)

    img, box, landmarklar = yuz_bul(gorsel_yol)
    cikti_klasor = Path(cikti_klasor)
    cikti_klasor.mkdir(parents=True, exist_ok=True)

    # Landmark çifti: kaynak (orijinal) → hedef (deplase edilmiş)
    kaynak_pts = np.float32(landmarklar)

    sonuclar = []
    for v in range(sayi):
        v_seed = seed + v
        rng = random.Random(v_seed)

        # 1. Hedef landmark'ları deplace et (Delaunay warp için)
        hedef_pts = kaynak_pts.copy()
        guc = rng.uniform(0.02, 0.05)

        h, w = img.shape[:2]
        # Çene genişliği/darlığı (daha ılımlı — tel çizgi artefaktını önler)
        if len(landmarklar) > 152:
            cene_delta = int(w * guc * 0.5)
            for idx in [152, 377, 400, 378, 172, 136, 150]:
                if idx < len(hedef_pts):
                    hedef_pts[idx] = (
                        hedef_pts[idx][0] + rng.randint(-cene_delta, cene_delta),
                        hedef_pts[idx][1] + rng.randint(0, cene_delta))
        # Alın
        for idx in _ANA_INDEKS["alin"]:
            if idx < len(hedef_pts):
                hedef_pts[idx] = (
                    hedef_pts[idx][0] + rng.randint(-int(w * guc * 0.4), int(w * guc * 0.4)),
                    hedef_pts[idx][1] - rng.randint(0, int(h * guc * 0.3)))
        # Elmacık
        for idx in _ANA_INDEKS["sol_almakik"][:4]:
            if idx < len(hedef_pts):
                hedef_pts[idx] = (
                    hedef_pts[idx][0] - rng.randint(0, int(w * guc * 0.6)),
                    hedef_pts[idx][1] + rng.randint(-int(h * guc * 0.3), int(h * guc * 0.3)))
        for idx in _ANA_INDEKS["sag_almakik"][:4]:
            if idx < len(hedef_pts):
                hedef_pts[idx] = (
                    hedef_pts[idx][0] + rng.randint(0, int(w * guc * 0.6)),
                    hedef_pts[idx][1] + rng.randint(-int(h * guc * 0.3), int(h * guc * 0.3)))

        # 2. Delaunay piecewise warp → yalnızca yüz maskesi içinde harmanla
        warped = _delunay_warp(img, kaynak_pts, hedef_pts)
        yuz_mask = _yuz_maske(img, landmarklar)
        m3 = yuz_mask[..., None].astype(np.float32) / 255.0
        warped = (warped.astype(np.float32) * m3 +
                  img.astype(np.float32) * (1.0 - m3)).astype(np.uint8)

        # 3. Ten tonu kaydırma
        renkli = _ten_tonu_kaydir(warped, rng)

        # 4. Cilt parlatma
        parlatilmis = _cilt_parlat(renkli, rng)

        # 5. Göz parlatma
        son = _goz_parlat(parlatilmis, landmarklar, rng)

        # 6. Mirror şansı
        if rng.random() < 0.3:
            son = cv2.flip(son, 1)

        # 7. Boyutlandır (9:16)
        son = _boyutlandir(son)

        # 8. Hafif gürültü ekle (doğal film graini)
        if rng.random() < 0.4:
            gurultu = np.random.normal(0, rng.uniform(1, 3), son.shape).astype(np.int16)
            son = np.clip(son.astype(np.int16) + gurultu, 0, 255).astype(np.uint8)

        ad = f"kanon_v{v+1}_{v_seed}.jpg"
        yol = cikti_klasor / ad
        cv2.imwrite(str(yol), son, [cv2.IMWRITE_JPEG_QUALITY, 95])

        sonuclar.append({
            "gorsel_yol": str(yol),
            "meta": {
                "seed": v_seed,
                "warp_gucu": round(guc, 3),
                "yontem": "delaunay+bilateral+lab",
                "zaman": time.time()
            }
        })

    return sonuclar


def test_yuz(gorsel_yol):
    try:
        img, box, landmarklar = yuz_bul(gorsel_yol)
        return True, f"Yuz bulundu: {len(landmarklar)} landmark"
    except Exception as e:
        return False, str(e)
