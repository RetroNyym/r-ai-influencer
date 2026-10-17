# -*- coding: utf-8 -*-
"""Persona yönetimi: CRUD, seed kilidi, prompt anchor."""

import random

from core import depolama

# "Çizgi film/AI bebek" görünümünü kırar: kamera, lens, film ve cilt
# doku token'ları Flux'u gerçek fotoğraf yönüne iter.
GERCEKCI_SON = (
    "ultra realistic photo, shot on Sony A7 III, 85mm f/1.4 lens, "
    "shallow depth of field, natural skin pores and texture, fine film grain, "
    "realistic eye reflections, unretouched, candid photojournalism, "
    "adult woman with mature proportionate facial features, natural eye size, "
    "no beauty filter, no doll look, no airbrushing, no illustration, "
    "no CGI, no anime, no painting, no cartoon"
)

# --- Görüntü modları (GUI "Görüntü Modu" seçicisi) ---
# Her mod, prompt'un sonuna eklenen stil token'larıdır. Varsayılan:
# "gercekci" → referanstaki gibi gerçekçi (fotogerçeklik) karakterler.
GORSEL_MODLAR = {
    "gercekci": (
        "Fotogerçek",
        GERCEKCI_SON,
    ),
    "sinematik": (
        "Sinematik",
        "cinematic film still, dramatic lighting, anamorphic lens flare, "
        "rich color grading, 35mm Kodak Portra film look, subtle film grain, "
        "realistic skin texture, natural proportions, photorealistic, "
        "no illustration, no CGI, no anime, no painting, no cartoon",
    ),
    "stüdyo": (
        "Stüdyo Portre",
        "professional studio portrait photography, softbox key light with "
        "fill, seamless dark backdrop, beauty dish catchlights, "
        "85mm lens headshot, natural skin pores, sharp focus on eyes, "
        "photorealistic, high detail, no retouching, no illustration, "
        "no CGI, no anime, no cartoon",
    ),
    "sokak": (
        "Doğaçka Sokak",
        "candid street photography, golden hour sunlight, urban background "
        "with natural bokeh, spontaneous pose, available light, "
        "documentary photojournalism style, realistic skin texture, "
        "photorealistic, unposed, no studio lighting, no illustration, "
        "no CGI, no anime, no cartoon",
    ),
    "moda": (
        "Editoryal Moda",
        "high fashion editorial photography, Vogue magazine style, "
        "elegant pose, designer outfit, crisp studio lighting, "
        "fashion model proportions, detailed fabric texture, "
        "photorealistic, sharp focus, no illustration, no CGI, "
        "no anime, no cartoon",
    ),
}


def gorsel_modu(mod=None):
    """Aktif görüntü modunu döndürür (ayar yoksa fotogerçek)."""
    if not mod:
        try:
            mod = depolama.ayar_al("gorsel_mod", "gercekci")
        except Exception:
            mod = "gercekci"
    if mod not in GORSEL_MODLAR:
        mod = "gercekci"
    return mod



def yeni_kisilik(ad, yas, nis, ten, sac, goz, stil, kisilik_tanimi, marka_sesi):
    """Yeni persona oluşturur; seed rastgele üretilir."""
    seed = random.randint(1, 2**31 - 1)
    anchor = _anchor_yap(ad, yas, ten, sac, goz, stil, kisilik_tanimi)
    pid = depolama.persona_ekle({
        "ad": ad, "yas": yas, "nis": nis, "ten": ten, "sac": sac,
        "goz": goz, "stil": stil, "kisilik": kisilik_tanimi,
        "marka_sesi": marka_sesi, "seed": seed, "anchor_prompt": anchor,
        "kaynak": "ai"
    })
    return pid


def kendi_yuzunden(persona_id, gorsel_yol, yuz_meta, varyasyonlar):
    """Kullanıcının kendi yüzünden dönüştürülmüş sureti persona'ya kaydeder."""
    depolama.persona_guncelle(persona_id, {
        "kaynak": "kendi_yuz",
        "kanon_gorsel": varyasyonlar[0] if varyasyonlar else None,
        "yuz_meta": yuz_meta
    })


def kanon_sec(persona_id, gorsel_yol):
    depolama.persona_guncelle(persona_id, {"kanon_gorsel": gorsel_yol})


def kimlik_kilitle(persona_id, gorsel_yol):
    """Bir suretin ArcFace kimliğini kilitler (stabil karakter için).

    Kilitlenen kimlik, sonraki tüm üretimlerde (post, çizgi film, video)
    aynı kişinin tutarlı çıkmasını sağlar.
    """
    import json
    from core import yuz_degistir
    z = yuz_degistir.kimlik_cikar(gorsel_yol)
    depolama.persona_guncelle(persona_id, {
        "kimlik_embedding": json.dumps(z),
        "kanon_gorsel": gorsel_yol,
    })
    return z


def kimlik_al(persona_id):
    """Kilitli kimlik vektörünü döndürür; yoksa None."""
    import json
    p = depolama.persona_al(persona_id)
    if not p or not p.get("kimlik_embedding"):
        return None
    try:
        return json.loads(p["kimlik_embedding"])
    except Exception:
        return None


def prompt_yap(sahne, persona, mod=None):
    """Sahne + persona anchor'u birleştirir. Anchor her zaman başta.

    mod: GORSEL_MODLAR anahtarı (ör. "gercekci"). None → aktif ayar.
    """
    anchor = persona.get("anchor_prompt", "")
    stil_son = GORSEL_MODLAR[gorsel_modu(mod)][1]
    return f"{anchor}, {sahne}, social media photo, 9:16 aspect ratio, {stil_son}"


def _anchor_yap(ad, yas, ten, sac, goz, stil, kisilik_tanimi):
    parcalar = [
        f"photorealistic portrait of a {yas} year old woman" if "kadın" in (stil or "").lower() or "kadin" in (stil or "").lower()
        else f"photorealistic portrait of a {yas} year old person",
        f"{ten} skin" if ten else "",
        f"{sac} hair" if sac else "",
        f"{goz} eyes" if goz else "",
        f"wearing {stil}" if stil else "",
        f"{kisilik_tanimi} vibe" if kisilik_tanimi else "",
        "same face identity across all images",
        "photorealistic, hyperdetailed, natural proportions",
    ]
    return ", ".join(p for p in parcalar if p)


def persona_listele():
    return depolama.persona_listele()


def persona_al(pid):
    return depolama.persona_al(pid)
