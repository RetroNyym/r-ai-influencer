# -*- coding: utf-8 -*-
"""SQLite depolama: personas, posts, schedule, publish_log, ayarlar."""

import json
import sqlite3
import time
from pathlib import Path

KENDI_DOSYA = Path(__file__).resolve().parent.parent
DB_YOL = KENDI_DOSYA / "ai_influencer.db"
URETILEN_KLASOR = KENDI_DOSYA / "uretilen"


def baglanti():
    conn = sqlite3.connect(str(DB_YOL))
    conn.row_factory = sqlite3.Row
    return conn


def kur():
    URETILEN_KLASOR.mkdir(exist_ok=True)
    with baglanti() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            yas INTEGER,
            nis TEXT,
            ten TEXT,
            sac TEXT,
            goz TEXT,
            stil TEXT,
            kisilik TEXT,
            marka_sesi TEXT,
            seed INTEGER,
            anchor_prompt TEXT,
            kanon_gorsel TEXT,
            kaynak TEXT DEFAULT 'ai',
            yuz_meta TEXT,
            olusturma REAL
        );
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_id INTEGER,
            sahne TEXT,
            prompt TEXT,
            gorsel_yol TEXT,
            caption TEXT,
            hashtags TEXT,
            durum TEXT DEFAULT 'taslak',
            olusturma REAL,
            paylasim_zamani REAL,
            FOREIGN KEY(persona_id) REFERENCES personas(id)
        );
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gun INTEGER,
            saat TEXT,
            aktif INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS publish_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            platform TEXT,
            basarili INTEGER,
            mesaj TEXT,
            zamani REAL,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        );
        CREATE TABLE IF NOT EXISTS ayarlar (
            anahtar TEXT PRIMARY KEY,
            deger TEXT
        );
        CREATE TABLE IF NOT EXISTS performans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            platform TEXT,
            goruntulenme INTEGER DEFAULT 0,
            begeni INTEGER DEFAULT 0,
            yorum INTEGER DEFAULT 0,
            paylasim INTEGER DEFAULT 0,
            tarih REAL,
            notlar TEXT,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        );
        CREATE TABLE IF NOT EXISTS toplu_kuyruk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tip TEXT,
            parametre TEXT,
            durum TEXT DEFAULT 'bekliyor',
            hata TEXT,
            olusturma REAL,
            bitis REAL
        );
        """)
        c.commit()


# --- performans ---
def performans_ekle(post_id, platform, goruntulenme=0, begeni=0, yorum=0,
                    paylasim=0, notlar=""):
    with baglanti() as c:
        cur = c.execute(
            """INSERT INTO performans(post_id,platform,goruntulenme,begeni,yorum,
               paylasim,tarih,notlar) VALUES(?,?,?,?,?,?,?,?)""",
            (post_id, platform, goruntulenme, begeni, yorum, paylasim,
             time.time(), notlar))
        c.commit()
        return cur.lastrowid


def performans_listele(limit=100):
    with baglanti() as c:
        return [dict(r) for r in c.execute(
            """SELECT pf.*, p.caption, p.gorsel_yol FROM performans pf
               LEFT JOIN posts p ON p.id=pf.post_id
               ORDER BY pf.tarih DESC LIMIT ?""", (limit,))]


def performans_istatistik():
    with baglanti() as c:
        toplam = c.execute(
            """SELECT COUNT(*) n, COALESCE(SUM(goruntulenme),0) g,
               COALESCE(SUM(begeni),0) b, COALESCE(SUM(yorum),0) y,
               COALESCE(SUM(paylasim),0) p FROM performans""").fetchone()
        en_iyi = c.execute(
            """SELECT pf.*, p.caption FROM performans pf
               LEFT JOIN posts p ON p.id=pf.post_id
               ORDER BY pf.goruntulenme DESC LIMIT 5""").fetchall()
        return {"toplam": dict(toplam), "en_iyi": [dict(r) for r in en_iyi]}


# --- toplu kuyruk ---
def toplu_ekle(tip, parametre):
    with baglanti() as c:
        cur = c.execute(
            "INSERT INTO toplu_kuyruk(tip,parametre,durum,olusturma) VALUES(?,?,?,?)",
            (tip, json.dumps(parametre, ensure_ascii=False), "bekliyor", time.time()))
        c.commit()
        return cur.lastrowid


def toplu_listele():
    with baglanti() as c:
        satirlar = [dict(r) for r in c.execute(
            "SELECT * FROM toplu_kuyruk ORDER BY id")]
        for s in satirlar:
            try:
                s["parametre"] = json.loads(s["parametre"] or "{}")
            except Exception:
                s["parametre"] = {}
        return satirlar


def toplu_durum_guncelle(tid, durum, hata=None):
    with baglanti() as c:
        bitis = time.time() if durum in ("bitti", "hata") else None
        c.execute("UPDATE toplu_kuyruk SET durum=?, hata=?, bitis=? WHERE id=?",
                  (durum, hata, bitis, tid))
        c.commit()


def toplu_temizle():
    with baglanti() as c:
        c.execute("DELETE FROM toplu_kuyruk WHERE durum IN ('bitti')")
        c.commit()


# --- ayarlar ---
def ayar_al(anahtar, varsayilan=None):
    with baglanti() as c:
        r = c.execute("SELECT deger FROM ayarlar WHERE anahtar=?", (anahtar,)).fetchone()
        return r["deger"] if r else varsayilan


def ayar_koy(anahtar, deger):
    with baglanti() as c:
        c.execute("INSERT OR REPLACE INTO ayarlar(anahtar, deger) VALUES(?,?)",
                  (anahtar, str(deger)))
        c.commit()


# --- personas ---
def persona_ekle(p):
    with baglanti() as c:
        cur = c.execute(
            """INSERT INTO personas(ad,yas,nis,ten,sac,goz,stil,kisilik,marka_sesi,
               seed,anchor_prompt,kanon_gorsel,kaynak,yuz_meta,olusturma)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (p["ad"], p.get("yas"), p.get("nis"), p.get("ten"), p.get("sac"),
             p.get("goz"), p.get("stil"), p.get("kisilik"), p.get("marka_sesi"),
             p.get("seed"), p.get("anchor_prompt"), p.get("kanon_gorsel"),
             p.get("kaynak", "ai"), p.get("yuz_meta"), time.time()))
        c.commit()
        return cur.lastrowid


def persona_listele():
    with baglanti() as c:
        return [dict(r) for r in c.execute("SELECT * FROM personas ORDER BY olusturma DESC")]


def persona_al(pid):
    with baglanti() as c:
        r = c.execute("SELECT * FROM personas WHERE id=?", (pid,)).fetchone()
        return dict(r) if r else None


def persona_guncelle(pid, alanlar):
    pairs = ", ".join(f"{k}=?" for k in alanlar)
    with baglanti() as c:
        c.execute(f"UPDATE personas SET {pairs} WHERE id=?",
                  (*alanlar.values(), pid))
        c.commit()


# --- posts ---
def post_ekle(p):
    with baglanti() as c:
        cur = c.execute(
            """INSERT INTO posts(persona_id,sahne,prompt,gorsel_yol,caption,hashtags,
               durum,olusturma,paylasim_zamani)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (p.get("persona_id"), p.get("sahne"), p.get("prompt"), p.get("gorsel_yol"),
             p.get("caption"), p.get("hashtags"), p.get("durum", "taslak"),
             time.time(), p.get("paylasim_zamani")))
        c.commit()
        return cur.lastrowid


def post_listele(durum=None):
    with baglanti() as c:
        if durum:
            return [dict(r) for r in c.execute(
                "SELECT * FROM posts WHERE durum=? ORDER BY olusturma DESC", (durum,))]
        return [dict(r) for r in c.execute("SELECT * FROM posts ORDER BY olusturma DESC")]


def post_al(pid):
    with baglanti() as c:
        r = c.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()
        return dict(r) if r else None


def post_durum(pid, durum):
    with baglanti() as c:
        c.execute("UPDATE posts SET durum=? WHERE id=?", (durum, pid))
        c.commit()


# --- schedule ---
def schedule_ekle(gun, saat):
    with baglanti() as c:
        cur = c.execute("INSERT INTO schedule(gun,saat,aktif) VALUES(?,?,1)",
                        (gun, saat))
        c.commit()
        return cur.lastrowid


def schedule_listele():
    with baglanti() as c:
        return [dict(r) for r in c.execute("SELECT * FROM schedule ORDER BY gun, saat")]


def schedule_sil(sid):
    with baglanti() as c:
        c.execute("DELETE FROM schedule WHERE id=?", (sid,))
        c.commit()


# --- publish_log ---
def log_ekle(post_id, platform, basarili, mesaj):
    with baglanti() as c:
        c.execute("INSERT INTO publish_log(post_id,platform,basarili,mesaj,zamani) VALUES(?,?,?,?,?)",
                  (post_id, platform, int(basarili), mesaj, time.time()))
        c.commit()


def log_listele(limit=50):
    with baglanti() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM publish_log ORDER BY zamani DESC LIMIT ?", (limit,))]


kur()
