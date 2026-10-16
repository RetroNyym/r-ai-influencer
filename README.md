# R+ AI Influencer Otomasyonu

> **Ücretsiz, open-source AI influencer üretim ve paylaşım otomasyonu.**
> Kendi sanal influencer'ını yarat, günlük içerik üret, Instagram & TikTok'a otomatik paylaş — hepsi tek masaüstü uygulamasında, $0 maliyetle.

[English](#english) | [Özellikler](#özellikler) | [Kurulum](#kurulum) | [Kullanım](#kullanım) | [API Bağlantıları](#api-bağlantıları)

---

## Neden R+ AI Influencer?

Piyasadaki premium sanal influencer platformları **$19–99/ay** tutarında:

| Platform | Aylık Ücret |
|---|---|
| The Influencer AI | $19–99/ay |
| APOB AI | $19–99/ay |
| Influverse | $19–99/ay |
| InfluencerBuild | SaaS ücretli |

**R+ AI Influencer** bu özelliklerin tamamını **ücretsiz** sunar:

- ✅ Tutarlı sanal karakter üretimi (seed-kilitli yüz)
- ✅ Kendi yüzünden 8 farklı suret (tamamen offline, API'siz)
- ✅ AI görsel + caption + hashtag üretimi (ücretsiz API)
- ✅ Zamanlanmış otomatik paylaşım (Instagram + TikTok)
- ✅ Çoklu API desteği (OpenAI, Replicate, Stability, HuggingFace...)
- ✅ Masaüstü GUI (Türkçe arayüz, retro+ tasarım)
- ✅ Tamamen self-hosted, veriler senin bilgisayarında

---

## Özellikler

### 🎭 Karakter Yönetimi
- Ad, yaş, niş, ten, saç, göz, stil, kişilik tanımla
- Seed-kilitli tutarlı yüz: her post'ta aynı kişi
- 7 niş × 8 sahne şablonu: lifestyle, moda, fitness, tech, yemek, seyahat, güzellik

### 📸 Kendi Yüzünden Suret (Offline)
Kendi fotoğrafını yükle; program **tamamen internetsiz** 8 farklı varyasyon üretir:
- MediaPipe FaceLandmarker (478 landmark)
- Delaunay triangulation piecewise-affine warp
- Cilt dostu bilateral filtre + LAB renk kaydırma
- Göz parlatma + film graini
- Deterministik seed ile tekrar üretilebilir

### 🤖 AI İçerik Üretimi
- Pollinations.ai Flux ile fotorealistik görsel (ücretsiz, API anahtarsız)
- Pollinations text ile caption + hashtag üretimi
- Toplu üretim: tek tıkla 1–10 sahne

### 📅 Zamanlama & Paylaşım
- Gün/saat bazlı paylaşım takvimi
- Instagram Graph API (Content Publishing)
- TikTok Content Posting API (taslak/SELF_ONLY/direct)
- Manuel mod: klasöre dışa aktar + caption panoya kopyala

### 🔌 Çoklu API Desteği
Key'i yapıştır — sistem otomatik tanır:
- OpenAI (DALL·E 3)
- Anthropic (Claude)
- Stability AI (SD3/SDXL)
- Replicate (FLUX)
- HuggingFace Inference
- Groq, Together, DeepSeek, Mistral
- Pollinations.ai (ücretsiz)

API yoksa otomatik olarak ücretsiz Pollinations.ai kullanılır.

---

## Kurulum

### Gereksinimler
- Python 3.10+
- Windows / macOS / Linux

### Kurulum

```bash
git clone https://github.com/KULLANICI_ADI/r-ai-influencer.git
cd r-ai-influencer
pip install -r requirements.txt
```

### Çalıştırma

```bash
python baslat.py
```

veya Windows'ta:
```cmd
baslat.bat
```

### PyInstaller ile .exe paketleme

```bash
pip install pyinstaller
pyinstaller ai_influencer.spec
# Çıktı: dist/R-AIInfluencer.exe
```

---

## Kullanım

### 1. Karakter Oluştur
**Karakter** sekmesinden:
- Formu doldur → "Karakteri Oluştur (AI Yüz)" (Pollinations'tan canon yüz üretir)
- VEYA "Fotoğraf Seç" → izin onayı → "8 Varyasyon Üret" (offline kendi yüzünden)

### 2. İçerik Üret
**Üretim & Onay** sekmesinden:
- Karakter + sahne sayısı seç → "Üretimi Başlat"
- Görsel + caption + hashtag otomatik üretilir
- Onayla / Reddet / Panoya Kopyala

### 3. Zamanla & Paylaş
**Takvim** sekmesinden:
- Gün + saat ekle → "Zamanlayıcı Başlat"
- Onaylı postlar saati gelince otomatik paylaşılır

### 4. API Bağla (Opsiyonel)
**API & Bağlantılar** sekmesinden:
- Kendi API anahtarını yapıştır → otomatik tanır
- VEYA listeden seç → anahtarı gir → "Kaydet ve Aktif Yap"
- Bağlantı testi ile doğrula

---

## Teknoloji Stack

| Katman | Teknoloji |
|---|---|
| Arayüz | Python tkinter + ttk (retro+ teması) |
| Yerel görüntü | OpenCV + MediaPipe FaceLandmarker |
| AI üretim | Pollinations.ai (ücretsiz), OpenAI, Replicate, Stability |
| Depolama | SQLite |
| Zamanlama | Python threading |
| Paylaşım | Instagram Graph API, TikTok Content Posting API |
| Paketleme | PyInstaller |

---

## SEO Anahtar Kelimeler

AI influencer, sanal influencer, virtual influencer generator, AI influencer automation, ücretsiz AI influencer, open source virtual influencer, AI content creator, otomatik Instagram paylaşım, TikTok otomasyon, self-hosted influencer, consistent AI character, face transform offline, MediaPipe face landmark, Pollinations AI, stable diffusion free, AI avatar creator, dijital influencer, yapay zeka influencer, otomasyon botu, retro+ AI

---

## Lisans

MIT License — özgürce kullan, değiştir, dağıt.

---

## English

**R+ AI Influencer Automation** — Free, open-source virtual influencer generation and auto-posting.

Create a consistent AI influencer persona, generate daily photo content with captions/hashtags, and auto-schedule posts to Instagram & TikTok — all from a desktop app, at $0 cost.

**Key features:**
- Seed-locked consistent face identity
- Upload your own photo → 8 offline face variations (MediaPipe + Delaunay warp, no internet needed)
- Free AI image + caption generation (Pollinations.ai)
- Multi-API support (OpenAI, Replicate, Stability, HuggingFace, Groq...) with auto-detection
- Instagram Graph API + TikTok Content Posting API
- Turkish desktop GUI with retro+ design

```bash
git clone https://github.com/KULLANICI_ADI/r-ai-influencer.git
cd r-ai-influencer
pip install -r requirements.txt
python baslat.py
```
