# -*- coding: utf-8 -*-
"""Niş bazlı sahne şablonları."""

SAHNELER = {
    "lifestyle": [
        "walking through a sunny city street with coffee in hand",
        "sitting in a cozy cafe reading a book by the window",
        "relaxing in a modern apartment with plants and warm light",
        "enjoying a sunset on a rooftop terrace",
        "exploring a weekend farmers market with a tote bag",
        "having a picnic in a green park with friends",
        "working on a laptop in a stylish co-working space",
        "cooking a healthy meal in a bright kitchen",
    ],
    "moda": [
        "posing in a trendy oversized blazer on a minimalist backdrop",
        "street style outfit with sneakers and layered accessories",
        "elegant evening dress under soft city lights",
        "casual denim look with a statement handbag",
        "monochrome outfit against an industrial concrete wall",
        "summer linen outfit on a Mediterranean balcony",
        "athleisure set during a morning walk",
        "vintage inspired outfit with bold makeup",
    ],
    "fitness": [
        "stretching in a sunlit yoga studio",
        "post-workout smile holding a water bottle",
        "morning run along a scenic waterfront trail",
        "meditation pose in a peaceful living room",
        "lifting light dumbbells in a home gym",
        "hiking on a mountain trail with a backpack",
        "cycling through the countryside at golden hour",
        "healthy smoothie bowl prep after training",
    ],
    "tech": [
        "unboxing a new gadget on a clean desk setup",
        "using VR headset in a futuristic lit room",
        "coding on a laptop with multiple monitors glowing",
        "reviewing a smartphone with ring light setup",
        "podcast recording setup with professional microphone",
        "smart home devices arranged aesthetically on a shelf",
        "drone photography session at a scenic overlook",
        "gear layout flatlay of everyday tech carry",
    ],
    "yemek": [
        "presenting a beautifully plated homemade pasta dish",
        "baking fresh cookies in a rustic kitchen",
        "tasting street food at a vibrant night market",
        "arranging a charcuterie board with wine",
        "pouring latte art in a ceramic mug close-up",
        "harvesting fresh herbs from a garden box",
        "sharing a dessert with a friend at a bakery",
        "filming a cooking tutorial with ingredients prepped",
    ],
    "seyahat": [
        "standing at a scenic overlook with ocean view",
        "exploring cobblestone streets of an old town",
        "posing with luggage at a train station platform",
        "beach day with turquoise water and white sand",
        "mountain cabin morning coffee with pine forest view",
        "night market stroll with lanterns overhead",
        "airport departure board with travel outfit",
        "sunset silhouette on a famous city bridge",
    ],
    "guzellik": [
        "skincare routine close-up with dewy glowing skin",
        "applying lipstick with soft glam makeup",
        "hair care moment with silky flowing hair",
        "spa day with face mask and cucumber water",
        "perfume bottle flatlay with fresh flowers",
        "before and after makeup transformation pose",
        "nail art showcase with elegant hand pose",
        "self care sunday morning in a robe with tea",
    ],
}


def sahne_sec(nis, seed=None):
    """Verilen nişten rastgele bir sahne seçer. Seed verilirse deterministik."""
    import random
    havuz = SAHNELER.get(nis, SAHNELER["lifestyle"])
    rng = random.Random(seed)
    return rng.choice(havuz)


def sahne_listesi(nis):
    return SAHNELER.get(nis, SAHNELER["lifestyle"])


def nisler():
    return list(SAHNELER.keys())
