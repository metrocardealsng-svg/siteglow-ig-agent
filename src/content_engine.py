"""
SiteGlow NG Content Engine
Uses Gemini API + instagram-agent-skill (hooks.json, hookscore.py, humanize.py, caption.py)
to generate viral, zero-slop Instagram Reels & Carousels with quality gates.
"""
import json
import os
import random
import re
from pathlib import Path

from src.ig_skill import caption as cap_lint
from src.ig_skill import hookscore
from src.ig_skill import humanize as hum

ROOT = Path(__file__).resolve().parent.parent
HOOKS_FILE = ROOT / "src" / "ig_skill" / "hooks.json"
VOICE_FILE = ROOT / "voice.md"

TOPIC_PILLARS = [
    {
        "id": "google_invisible",
        "angle": "Why Nigerian businesses lose 70% of ready-to-pay Google buyers every single day by only relying on Instagram DMs",
        "portfolio": "metro_cars.png",
        "niche": "Car Dealerships & Local Businesses",
        "stat_label": "+340% GOOGLE LEADS",
    },
    {
        "id": "ig_ban_risk",
        "angle": "What happens if Instagram suspends or restricts your business page tomorrow? You do not own your IG followers, you own your website.",
        "portfolio": "crownup.png",
        "niche": "E-Commerce & Streetwear Brands",
        "stat_label": "100% OWNED TRAFFIC",
    },
    {
        "id": "dm_price_fatigue",
        "angle": "Stop wasting 4 hours a day replying 'check DM for price' to window shoppers. A ₦150,000 website closes serious buyers while you sleep.",
        "portfolio": "sophy_hairs.png",
        "niche": "Hair, Fashion & Tailoring Vendors",
        "stat_label": "24/7 AUTO ORDERS",
    },
    {
        "id": "trust_high_ticket",
        "angle": "Why big corporate and diaspora clients refuse to transfer ₦1M+ to a business that only has a WhatsApp number and no website",
        "portfolio": "poppycastle.png",
        "niche": "Real Estate, Restaurants & Hospitality",
        "stat_label": "3X CLIENT TRUST",
    },
    {
        "id": "3d_standout",
        "angle": "Boring template websites make your brand look cheap. How interactive 3D-looking websites from SiteGlow NG make small brands look like billion-Naira companies.",
        "portfolio": "agency_hub.png",
        "niche": "Portfolios & Creative Agencies",
        "stat_label": "TOP-CLASS 3D DESIGN",
    },
    {
        "id": "price_objection",
        "angle": "Answering the objection: 'Websites are too expensive.' One single big client found on Google pays back a ₦150,000 website 5 times over.",
        "portfolio": "vytora.png",
        "niche": "Nigerian SMEs & Startups",
        "stat_label": "STARTS AT ₦150,000",
    },
    {
        "id": "competitor_stealing",
        "angle": "Someone in Lagos or Abuja just searched Google for your exact service. Your competitor with a website got the call while your phone stayed silent.",
        "portfolio": "metro_cars.png",
        "niche": "Lagos & Abuja Service Businesses",
        "stat_label": "RANK #1 ON GOOGLE",
    },
    {
        "id": "restaurant_booking",
        "angle": "Restaurants and lounges lose weekend group bookings because customers cannot find a clean menu, location map, or reservation button on Google.",
        "portfolio": "poppycastle.png",
        "niche": "Restaurants, Lounges & Catering",
        "stat_label": "MORE TABLE BOOKINGS",
    },
    {
        "id": "fashion_lookbook",
        "angle": "Tailors and hair vendors: stop sending 25 messy gallery photos on WhatsApp. Send one sleek lookbook link with prices and instant WhatsApp checkout.",
        "portfolio": "sophy_hairs.png",
        "niche": "Tailors, Hair & Beauty Brands",
        "stat_label": "INSTANT CHECKOUT",
    },
    {
        "id": "whatsapp_link_upgrade",
        "angle": "Putting a bare WhatsApp link in your Instagram bio kills half your conversions. Upgrade to a 3D mini-site that pre-sells your brand before they message you.",
        "portfolio": "crownup.png",
        "niche": "Instagram Vendors in Nigeria",
        "stat_label": "2X DM CONVERSION",
    },
]


def load_hooks():
    return json.loads(HOOKS_FILE.read_text(encoding="utf-8"))["hooks"]


def pick_topic(history: dict) -> dict:
    posted = set(history.get("posted_topics", []))
    remaining = [t for t in TOPIC_PILLARS if t["id"] not in posted]
    if not remaining:
        # Cycle cleanly once all topics have been used
        remaining = TOPIC_PILLARS
    return random.choice(remaining)


def _clean_text(text: str) -> str:
    lex = hum.load_lexicon()
    cleaned, _ = hum.humanize(text, lex)
    return cleaned.strip()


def _fallback_reel(topic: dict) -> dict:
    """High-converting deterministic fallback if GEMINI_API_KEY is unset or quota-limited."""
    spoken_hook = "Stop losing ₦500,000 clients because your business is invisible on Google."
    on_screen = "INVISIBLE ON GOOGLE?"
    beats = [
        {
            "on_screen": on_screen,
            "voice": spoken_hook,
            "card_title": "GOOGLE SEARCH REALITY",
            "card_sub": "Buyers search Google first before trusting any vendor.",
            "badge": "0% VISIBILITY",
            "accent": "red",
        },
        {
            "on_screen": "CHECK THE NUMBERS",
            "voice": "Right now, buyers in Lagos and Abuja are searching Google for what you sell, and calling your competitor instead.",
            "card_title": "ONLINE CLIENT DISCOVERY",
            "card_sub": "Websites capture ready-to-pay search traffic 24/7.",
            "badge": topic["stat_label"],
            "accent": "graph",
        },
        {
            "on_screen": "3D WEB DESIGN",
            "voice": "SiteGlow NG builds fast, 3D-looking websites that turn cold visitors into paying clients automatically.",
            "card_title": topic["niche"].upper(),
            "card_sub": "Custom 3D UI, Google SEO & instant WhatsApp checkout.",
            "badge": "SITEGLOW NG",
            "accent": "portfolio",
        },
        {
            "on_screen": "STARTS AT ₦150K",
            "voice": "Packages start from just 150,000 Naira. Send a DM with the word GLOW and let us get your website live this week.",
            "card_title": "LAUNCH YOUR WEBSITE TODAY",
            "card_sub": "Packages starting from ₦150,000 | Fast delivery",
            "badge": "DM 'GLOW' NOW",
            "accent": "cta",
        },
    ]
    caption_text = (
        "Stop losing ₦500,000 clients because your business is invisible on Google.\n\n"
        f"{topic['angle']}.\n\n"
        "At SiteGlow NG, we build 3D-looking, mobile-ready websites built to rank on Google and close serious buyers for your business.\n\n"
        "Packages start from ₦150,000.\n\n"
        "DM me \"GLOW\" to get your website started this week.\n\n"
        "#SiteGlowNG #WebDesignNigeria #NigerianBusiness #LagosBusiness #AbujaBusiness"
    )
    return {
        "format": "reel",
        "topic_id": topic["id"],
        "portfolio": topic["portfolio"],
        "spoken_hook": _clean_text(spoken_hook),
        "on_screen_hook": on_screen,
        "beats": beats,
        "caption": _clean_text(caption_text),
    }


def _fallback_carousel(topic: dict) -> dict:
    slides = [
        {
            "tag": "NIGERIAN BUSINESS TRUTH",
            "headline": "STOP LOSING ₦500K CLIENTS ON GOOGLE",
            "body": "Why relying only on Instagram DMs is quietly costing your brand serious buyers every week.",
            "style": "cover",
        },
        {
            "tag": "01 / THE PROBLEM",
            "headline": "BUYERS SEARCH GOOGLE FIRST",
            "body": "When high-ticket clients need a vendor in Lagos or Abuja, they check Google. If you do not show up, they pay your competitor.",
            "style": "problem",
        },
        {
            "tag": "02 / THE GROWTH GAP",
            "headline": "WEBSITE VS. DM-ONLY PAGE",
            "body": "Businesses with a fast Google-indexed website capture 3x more inbound leads and close buyers even at 2 AM.",
            "style": "graph",
        },
        {
            "tag": "03 / REAL PROOF",
            "headline": "BUILT TO LOOK TOP-CLASS",
            "body": "SiteGlow NG builds interactive 3D-looking websites for dealerships, restaurants, fashion brands, and portfolios.",
            "style": "portfolio",
        },
        {
            "tag": "04 / GET STARTED",
            "headline": "PACKAGES START FROM ₦150,000",
            "body": "Mobile-ready, Google SEO setup, and instant WhatsApp order buttons. DM me 'GLOW' right now to claim your build slot.",
            "style": "cta",
        },
    ]
    caption_text = (
        "Stop losing ₦500,000 clients because your business has no website.\n\n"
        f"{topic['angle']}.\n\n"
        "Swipe through to see how a 3D-looking SiteGlow NG website turns Google searchers into paying customers starting from ₦150,000.\n\n"
        "DM me \"GLOW\" to get your website built this week.\n\n"
        "#SiteGlowNG #WebDesignNigeria #LagosBusiness #AbujaBusiness #SmallBusinessNigeria"
    )
    return {
        "format": "carousel",
        "topic_id": topic["id"],
        "portfolio": topic["portfolio"],
        "slides": slides,
        "caption": _clean_text(caption_text),
    }


def _call_gemini(prompt: str) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json", "temperature": 0.85},
        )
        return resp.text
    except Exception as exc:
        print(f"[content_engine] Gemini call failed ({exc}); falling back to built-in template.")
        return None


def generate_content(fmt: str, history: dict) -> dict:
    topic = pick_topic(history)
    hooks = load_hooks()
    chosen_hooks = random.sample(hooks, 4)
    voice_doc = VOICE_FILE.read_text(encoding="utf-8")

    hook_menu = "\n".join(
        f"- {h['name']}: {h['template']} (Example: {h['example']})" for h in chosen_hooks
    )

    if fmt == "reel":
        prompt = f"""
You are the Instagram content strategist for SiteGlow NG. Follow this brand voice strictly:
{voice_doc}

Today's topic angle: {topic['angle']}
Target niche highlight: {topic['niche']}
Key stat badge: {topic['stat_label']}

Pick the sharpest hook from these proven formulas:
{hook_menu}

Return ONLY valid JSON matching this exact schema:
{{
  "spoken_hook": "A punchy 6-12 word spoken opening line with a concrete number/Naira figure or real stake, addressing 'you'. No greetings, no emojis, no hashtags.",
  "on_screen_hook": "3 to 5 bold ALL-CAPS words for the very first frame",
  "beats": [
    {{
      "on_screen": "3-5 ALL-CAPS words",
      "voice": "1-2 short punchy spoken sentences (max 18 words) for this 4-second beat",
      "card_title": "Short card title (max 28 chars)",
      "card_sub": "Short supporting proof line (max 56 chars)",
      "badge": "Short pill tag (max 18 chars)",
      "accent": "red"
    }},
    {{ "on_screen": "...", "voice": "...", "card_title": "...", "card_sub": "...", "badge": "{topic['stat_label']}", "accent": "graph" }},
    {{ "on_screen": "...", "voice": "...", "card_title": "...", "card_sub": "...", "badge": "SITEGLOW NG", "accent": "portfolio" }},
    {{ "on_screen": "STARTS AT ₦150K", "voice": "End mentioning packages start from 150,000 Naira and ask them to DM the word GLOW today.", "card_title": "GET YOUR WEBSITE LIVE", "card_sub": "Starts at ₦150,000 | Google SEO + 3D Design", "badge": "DM 'GLOW' NOW", "accent": "cta" }}
  ],
  "caption": "Instagram caption under 900 chars. First line under 115 chars with a concrete number or stake. No em-dashes, no URLs, ZERO generic hashtags (#viral/#fyp forbidden). Include ONE single ask: DM me \\"GLOW\\" to get started. End with 4-5 niche hashtags like #SiteGlowNG #WebDesignNigeria #LagosBusiness #AbujaBusiness."
}}
"""
        raw = _call_gemini(prompt)
        data = None
        if raw:
            try:
                parsed = json.loads(raw)
                if "beats" in parsed and len(parsed["beats"]) == 4 and "caption" in parsed:
                    data = {
                        "format": "reel",
                        "topic_id": topic["id"],
                        "portfolio": topic["portfolio"],
                        "spoken_hook": _clean_text(parsed["spoken_hook"]),
                        "on_screen_hook": parsed["on_screen_hook"].upper()[:36],
                        "beats": parsed["beats"],
                        "caption": _clean_text(parsed["caption"]),
                    }
                    # Clean every spoken beat
                    for b in data["beats"]:
                        b["voice"] = _clean_text(b["voice"])
            except Exception as exc:
                print(f"[content_engine] Failed parsing Gemini Reel JSON: {exc}")
        if not data:
            data = _fallback_reel(topic)

        # Quality Gate 1: Score the spoken hook with instagram-agent-skill hookscore.py
        _, score, verdict, flags = hookscore.run(data["spoken_hook"])
        print(f"[quality_gate] Hook score: {score:.1f}/100 ({verdict}) -> {data['spoken_hook']}")
        if flags:
            print(f"[quality_gate] Hook flags: {flags}")
        data["hook_score"] = round(score, 1)

    else:
        prompt = f"""
You are the Instagram content strategist for SiteGlow NG. Follow this brand voice strictly:
{voice_doc}

Today's carousel topic angle: {topic['angle']}
Target niche: {topic['niche']}

Return ONLY valid JSON matching this exact schema (exactly 5 slides):
{{
  "slides": [
    {{"tag": "NIGERIAN BUSINESS TRUTH", "headline": "Punchy 5-8 word cover headline with a number or stake", "body": "1 short subline under 95 chars", "style": "cover"}},
    {{"tag": "01 / THE COST", "headline": "Short headline", "body": "2 crisp sentences max (under 140 chars) explaining the business mistake", "style": "problem"}},
    {{"tag": "02 / THE DATA", "headline": "Short headline", "body": "Why businesses with a website win Google search traffic 24/7", "style": "graph"}},
    {{"tag": "03 / REAL WORK", "headline": "Short headline", "body": "Showcase SiteGlow NG 3D-looking websites for Nigerian brands", "style": "portfolio"}},
    {{"tag": "04 / LAUNCH TODAY", "headline": "PACKAGES START FROM ₦150,000", "body": "Mobile-ready, Google SEO & WhatsApp checkout. DM me 'GLOW' right now.", "style": "cta"}}
  ],
  "caption": "Instagram caption under 900 chars. First line under 115 chars with a concrete number or stake. No em-dashes, no URLs, ZERO generic hashtags (#viral/#fyp forbidden). Include ONE single ask: DM me \\"GLOW\\" to get your website started. End with 4-5 niche hashtags (#SiteGlowNG #WebDesignNigeria #LagosBusiness #AbujaBusiness)."
}}
"""
        raw = _call_gemini(prompt)
        data = None
        if raw:
            try:
                parsed = json.loads(raw)
                if "slides" in parsed and len(parsed["slides"]) == 5 and "caption" in parsed:
                    for s in parsed["slides"]:
                        s["headline"] = _clean_text(s["headline"]).upper()
                        s["body"] = _clean_text(s["body"])
                    data = {
                        "format": "carousel",
                        "topic_id": topic["id"],
                        "portfolio": topic["portfolio"],
                        "slides": parsed["slides"],
                        "caption": _clean_text(parsed["caption"]),
                    }
            except Exception as exc:
                print(f"[content_engine] Failed parsing Gemini Carousel JSON: {exc}")
        if not data:
            data = _fallback_carousel(topic)

    # Quality Gate 2: Lint caption with instagram-agent-skill caption.py
    cap_report = cap_lint.analyse(
        data["caption"],
        keywords=["website", "SiteGlow", "150,000"],
    )
    print(f"[quality_gate] Caption lint verdict: {cap_report['verdict']} ({cap_report['characters']} chars, {len(cap_report['hashtags'])} tags)")
    # Auto-trim hashtags if > 5 just in case
    if len(cap_report["hashtags"]) > 5:
        extra = cap_report["hashtags"][5:]
        for t in extra:
            data["caption"] = re.sub(r"\s*" + re.escape(t) + r"\b", "", data["caption"]).strip()
    data["caption_verdict"] = cap_report["verdict"]
    return data
