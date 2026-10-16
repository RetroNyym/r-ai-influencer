# -*- coding: utf-8 -*-
"""Çoklu API yönetimi: key yapıştır → otomatik tanıma → yönlendirme.

Desteklenen API'ler ve key tanıma desenleri:
- OpenAI:        sk-... (uzun, sk- ile başlar)
- Anthropic:     sk-ant-...
- Stability AI:  sk-... (Stability anahtarları genelde 51+ karakter)
- Replicate:     r8_...
- HuggingFace:   hf_...
- Groq:          gsk_...
- Together AI:   ...
- Deepseek:      sk-...
- Pollinations:  pk_... veya sk_... (pollinations özel)
- Mistral:       ...
- Custom:        serbest

Kullanıcı:
1. Listeden API seçer VEYA
2. Key'i yapıştırır → sistem önekten tanır → API adını gösterir
"""

import re
import time
import urllib.parse

import requests

from core import depolama

# (anahtar, gösterilecek ad, key önek/regex deseni, varsayılan uç)
API_TANIMLAR = [
    ("openai", "OpenAI (GPT / DALL·E)",
     r"^(sk-proj-|sk-)[A-Za-z0-9]{20,}",
     "https://api.openai.com/v1"),
    ("anthropic", "Anthropic (Claude)",
     r"^sk-ant-[A-Za-z0-9\-_]{20,}",
     "https://api.anthropic.com/v1"),
    ("stability", "Stability AI (SD3 / SDXL)",
     r"^sk-[A-Za-z0-9]{40,}",
     "https://api.stability.ai/v2beta"),
    ("replicate", "Replicate (FLUX / SD)",
     r"^r8_[A-Za-z0-9]{20,}",
     "https://api.replicate.com/v1"),
    ("huggingface", "HuggingFace Inference",
     r"^hf_[A-Za-z0-9]{20,}",
     "https://api-inference.huggingface.co"),
    ("groq", "Groq (Llama / Mixtral)",
     r"^gsk_[A-Za-z0-9]{20,}",
     "https://api.groq.com/openai/v1"),
    ("together", "Together AI",
     r"^[A-Za-z0-9]{64}$",
     "https://api.together.xyz/v1"),
    ("deepseek", "DeepSeek",
     r"^sk-[A-Za-z0-9]{32,}",
     "https://api.deepseek.com/v1"),
    ("mistral", "Mistral AI",
     r"^[A-Za-z0-9]{32,}",
     "https://api.mistral.ai/v1"),
    ("pollinations", "Pollinations.ai (Ücretsiz)",
     r"^(pk_|sk_)[A-Za-z0-9]{10,}",
     "https://gen.pollinations.ai"),
    ("custom", "Custom / Diğer", None, ""),
]


def key_tanima(key):
    """Yapıştırılan key'den API adını tahmin eder.

    Returns: (api_id, api_adi) veya (None, None)
    """
    if not key or not key.strip():
        return None, None
    key = key.strip()

    # Özel durumlar (önce kontrol et)
    if key.startswith("sk-ant-"):
        return "anthropic", "Anthropic (Claude)"
    if key.startswith("sk-proj-"):
        return "openai", "OpenAI (GPT / DALL·E)"
    if key.startswith("r8_"):
        return "replicate", "Replicate (FLUX / SD)"
    if key.startswith("hf_"):
        return "huggingface", "HuggingFace Inference"
    if key.startswith("gsk_"):
        return "groq", "Groq (Llama / Mixtral)"
    if key.startswith("pk_") or key.startswith("sk_"):
        # Pollinations özel önek
        if len(key) < 60:
            return "pollinations", "Pollinations.ai (Ücretsiz)"

    # Regex desenleri
    for api_id, api_adi, desen, _ in API_TANIMLAR:
        if desen is None:
            continue
        try:
            if re.match(desen, key):
                # Çakışma durumunda daha spesifik olanı tercih et
                if api_id == "openai" and key.startswith("sk-ant-"):
                    continue
                return api_id, api_adi
        except re.error:
            continue

    return "custom", "Custom / Diğer"


def api_listesi():
    """GUI combobox için (gösterilecek_ad, api_id) listesi."""
    return [(adi, aid) for aid, adi, _, _ in API_TANIMLAR]


def api_kaydet(api_id, key, api_adi=None):
    """API anahtarını kaydeder. api_id='custom' ise serbest ad da kaydedilir."""
    if api_adi is None:
        for aid, adi, _, _ in API_TANIMLAR:
            if aid == api_id:
                api_adi = adi
                break
    depolama.ayar_koy(f"api_{api_id}_key", key.strip())
    depolama.ayar_koy(f"api_{api_id}_ad", api_adi or api_id)
    # Son kullanılan API olarak işaretle
    depolama.ayar_koy("aktif_api", api_id)
    return True


def aktif_api():
    """Aktif API bilgisini döner: {id, ad, key, uc}"""
    api_id = depolama.ayar_al("aktif_api")
    if not api_id:
        return None
    key = depolama.ayar_al(f"api_{api_id}_key", "")
    ad = depolama.ayar_al(f"api_{api_id}_ad", api_id)
    uc = ""
    for aid, _, _, u in API_TANIMLAR:
        if aid == api_id:
            uc = u
            break
    return {"id": api_id, "ad": ad, "key": key, "uc": uc}


def kayitli_api_listesi():
    """Kaydedilmiş tüm API anahtarlarını listeler (key maskeli)."""
    sonuclar = []
    for api_id, api_adi, _, _ in API_TANIMLAR:
        key = depolama.ayar_al(f"api_{api_id}_key")
        if key:
            maskeli = key[:6] + "..." + key[-4:] if len(key) > 12 else "***"
            sonuclar.append({
                "id": api_id, "ad": api_adi,
                "key_maskeli": maskeli,
                "aktif": depolama.ayar_al("aktif_api") == api_id
            })
    return sonuclar


def api_sil(api_id):
    depolama.ayar_koy(f"api_{api_id}_key", "")
    if depolama.ayar_al("aktif_api") == api_id:
        depolama.ayar_koy("aktif_api", "")


def baglanti_testi(api_id, key):
    """Seçili API'nin gerçek uç noktasına basit bir test isteği atar.

    Returns: (basarili: bool, mesaj: str)
    """
    import requests

    uc = ""
    for aid, _, _, u in API_TANIMLAR:
        if aid == api_id:
            uc = u
            break

    if not uc:
        return True, "Custom API — test atlanıyor (uç noktası bilinmiyor)"

    try:
        if api_id == "openai":
            r = requests.get(f"{uc}/models",
                             headers={"Authorization": f"Bearer {key}"},
                             timeout=15)
        elif api_id == "anthropic":
            r = requests.get(f"{uc}/models",
                             headers={"x-api-key": key,
                                      "anthropic-version": "2023-06-01"},
                             timeout=15)
        elif api_id == "replicate":
            r = requests.get(f"{uc}/models",
                             headers={"Authorization": f"Bearer {key}"},
                             timeout=15)
        elif api_id == "huggingface":
            r = requests.get(f"{uc}/models",
                             headers={"Authorization": f"Bearer {key}"},
                             timeout=15)
        elif api_id == "groq":
            r = requests.get(f"{uc}/models",
                             headers={"Authorization": f"Bearer {key}"},
                             timeout=15)
        elif api_id == "pollinations":
            # Pollinations key'siz de çalışır; key varsa test et
            r = requests.get(f"{uc}/v1/models",
                             headers={"Authorization": f"Bearer {key}"},
                             timeout=15)
        else:
            # Genel HEAD/GET testi
            r = requests.get(uc, timeout=10)

        if r.status_code == 200:
            return True, f"✓ Bağlantı başarılı (HTTP 200)"
        elif r.status_code == 401:
            return False, "✗ Geçersiz anahtar (401)"
        elif r.status_code == 403:
            return False, "✗ Yetki reddedildi (403)"
        else:
            return False, f"HTTP {r.status_code}: {r.text[:100]}"

    except requests.exceptions.Timeout:
        return False, "Zaman aşımı (timeout)"
    except requests.exceptions.ConnectionError:
        return False, "Bağlantı hatası"
    except Exception as e:
        return False, str(e)


def uretim_yonlendir(prompt, seed=42, genislik=1024, yukseklik=1280,
                     api_zorla=None):
    """Aktif API'ye göre görsel üretir.

    api_zorla: belirli bir api_id kullan (test için).
    Returns: bytes (görsel) veya None
    """
    import requests
    import urllib.parse

    api = None
    if api_zorla:
        key = depolama.ayar_al(f"api_{api_zorla}_key", "")
        uc = ""
        for aid, _, _, u in API_TANIMLAR:
            if aid == api_zorla:
                uc = u
                break
        api = {"id": api_zorla, "key": key, "uc": uc}
    else:
        api = aktif_api()

    # API yoksa veya Pollinations ise ücretsiz uç
    if not api or api["id"] == "pollinations" or not api.get("key"):
        return _pollinations_uret(prompt, seed, genislik, yukseklik)

    key = api["key"]
    api_id = api["id"]

    try:
        if api_id == "openai":
            return _openai_uret(key, prompt, seed, genislik, yukseklik)
        elif api_id == "stability":
            return _stability_uret(key, prompt, genislik, yukseklik)
        elif api_id == "replicate":
            return _replicate_uret(key, prompt, genislik, yukseklik)
        elif api_id == "huggingface":
            return _hf_uret(key, prompt, genislik, yukseklik)
        else:
            # Bilinmeyen API → Pollinations fallback
            return _pollinations_uret(prompt, seed, genislik, yukseklik)
    except Exception:
        # Hata durumunda Pollinations'a düş
        return _pollinations_uret(prompt, seed, genislik, yukseklik)


# --- Üretim uçları ---

def _pollinations_uret(prompt, seed, w, h):
    enc = urllib.parse.quote(prompt)
    url = (f"https://image.pollinations.ai/prompt/{enc}"
           f"?width={w}&height={h}&seed={seed}&model=flux&private=true&nologo=true")
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    return r.content


def _openai_uret(key, prompt, seed, w, h):
    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1792" if h > w else "1024x1024",
            "quality": "standard",
        },
        timeout=120)
    r.raise_for_status()
    import base64
    b64 = r.json()["data"][0].get("b64_json")
    if b64:
        return base64.b64decode(b64)
    img_url = r.json()["data"][0]["url"]
    r2 = requests.get(img_url, timeout=60)
    r2.raise_for_status()
    return r2.content


def _stability_uret(key, prompt, w, h):
    r = requests.post(
        "https://api.stability.ai/v2beta/stable-image/generate/core",
        headers={"Authorization": f"Bearer {key}", "Accept": "image/*"},
        files={"none": ""},
        data={"prompt": prompt, "output_format": "jpeg",
              "aspect_ratio": "9:16" if h > w else "1:1"},
        timeout=120)
    r.raise_for_status()
    return r.content


def _replicate_uret(key, prompt, w, h):
    r = requests.post(
        "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions",
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        json={"input": {"prompt": prompt, "aspect_ratio": "9:16",
                        "num_outputs": 1}},
        timeout=120)
    r.raise_for_status()
    pred = r.json()
    # Async bekle
    import time as _t
    for _ in range(30):
        _t.sleep(2)
        r2 = requests.get(pred["urls"]["get"],
                          headers={"Authorization": f"Bearer {key}"}, timeout=30)
        pred = r2.json()
        if pred.get("status") == "succeeded":
            output = pred["output"]
            url = output[0] if isinstance(output, list) else output
            r3 = requests.get(url, timeout=60)
            return r3.content
        if pred.get("status") == "failed":
            raise RuntimeError("Replicate prediction failed")
    raise RuntimeError("Replicate timeout")


def _hf_uret(key, prompt, w, h):
    r = requests.post(
        "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
        headers={"Authorization": f"Bearer {key}"},
        json={"inputs": prompt},
        timeout=120)
    r.raise_for_status()
    return r.content
