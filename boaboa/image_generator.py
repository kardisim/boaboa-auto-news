from datetime import datetime, timezone
import io
import os
import re
from urllib.parse import quote

from PIL import Image
import requests

from boaboa.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_MODEL_FALLBACKS,
    GITHUB_REPOSITORY,
)

POLLINATIONS_FLUX_URL_TEMPLATE = (
    "https://image.pollinations.ai/prompt/{prompt}?width=1200&height=675&nologo=true&model=flux"
)


def build_pollinations_url(prompt: str) -> str:
    """Membentuk URL gambar Pollinations Flux dari prompt teks."""
    return POLLINATIONS_FLUX_URL_TEMPLATE.format(prompt=quote(prompt or "", safe=""))


def clean_image_prompt(
    raw_prompt: str = "",
    title: str = "",
    labels: list[str] | None = None,
) -> str:
    """Membersihkan dan menstandarkan prompt visual untuk fallback kompatibilitas."""
    cleaned = (raw_prompt or "").strip().strip("\"'")
    if not cleaned:
        region = "Tapanuli" if labels and "Tapanuli" in labels else "North Sumatra"
        title_hint = title or "editorial news"
        cleaned = f"Editorial documentary photo representing {title_hint} in {region}, photojournalism, realistic lighting"
    return cleaned


def slugify(text: str, max_length: int = 40) -> str:
    """Mengubah teks menjadi slug URL yang bersih dan aman untuk nama berkas gambar."""
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text).strip("-")
    if len(text) > max_length:
        text = text[:max_length].rsplit("-", 1)[0]
    return text or "ilustrasi"


def translate_to_safe_visual_prompt(
    title: str,
    content: str = "",
    labels: list[str] | None = None,
    gemini_api_key: str = "",
) -> str:
    """Menerjemahkan judul/isi berita menjadi prompt visual fotografi jurnalistik editorial 16:9 yang aman.

    Untuk berita peristiwa/kriminal/hukum/kecelakaan:
    Wajib diubah menjadi penggambaran jurnalistik netral, simbolis, atau suasana lingkungan (environmental storytelling)
    TANPA kekerasan, darah, senjata, perjudian, maupun teks/tulisan di dalam gambar.
    """
    key = gemini_api_key or GEMINI_API_KEY
    region_hint = "North Sumatra, Indonesia"
    for lbl in labels or []:
        if lbl in ("Tapanuli", "Wisata & Kuliner", "Berita Sumut", "Olahraga", "Ekobis", "Budaya & Hata", "Ototekno", "Hukrimpol"):
            region_hint = f"{lbl}, North Sumatra, Indonesia"
            break

    # 1. Coba gunakan Gemini API teks untuk menerjemahkan ke visual prompt yang aman
    if key:
        try:
            from google import genai

            client = genai.Client(api_key=key)
            instruction = (
                "You are an editorial photo editor for an Indonesian news portal (boaboa.bataktive.com). "
                "Convert the given Indonesian news headline into a single, concise English photo prompt (20-35 words) "
                "for generating an editorial photojournalism documentary picture (16:9 aspect ratio). "
                "CRITICAL SAFETY GUIDELINES:\n"
                "- If the news is about crime, police arrests, drug busts, gambling, trials, or traffic accidents: "
                "DO NOT depict any violence, blood, injuries, handcuffs, suspects' faces, firearms, narcotics, gambling paraphernalia, or wrecked cars. "
                "Instead, depict a safe, atmospheric, symbolic journalistic scene: e.g. a misty Trans-Sumatran highway road at dawn, "
                "a clean wooden office desk with legal file folders and a gavel, an exterior shot of a local government or justice building, "
                "or a serene landscape of Lake Toba / North Sumatra hills with dramatic daylight.\n"
                "- STRICTLY NO TEXT, NO LETTERS, NO NUMBERS, NO WATERMARKS, NO SIGNS inside the image.\n"
                "- Style: Realistic editorial documentary photography, natural daylight, 35mm lens, 16:9 wide composition."
            )
            models_to_try = [GEMINI_MODEL] + [m for m in GEMINI_MODEL_FALLBACKS if m != GEMINI_MODEL]
            for target_model in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=target_model,
                        contents=f"{instruction}\n\nNews Title: {title}\nLocation context: {region_hint}\nNews summary snippet: {content[:300]}",
                    )
                    text_result = (response.text or "").strip()
                    clean_result = re.sub(r'["\'`\r\n]+', " ", text_result).strip()
                    if len(clean_result) > 15:
                        return clean_result
                except Exception:
                    continue
        except Exception:
            pass

    # 2. Heuristik aman lokal (rule-based safety transformation jika offline / tanpa API key)
    title_lower = title.lower()
    if any(k in title_lower for k in ("polisi", "polres", "polda", "tangkap", "narkoba", "sabu", "ganja", "judi", "curat", "curas", "begal", "tersangka", "kasus", "kejari", "sidang", "vonis")):
        return (
            f"Editorial documentary photograph of a formal legal case folder on a polished wooden desk, "
            f"gavel in soft morning sunlight, courtroom interior in {region_hint}, photojournalism, no text"
        )
    if any(k in title_lower for k in ("kecelakaan", "tabrakan", "laka", "jalan", "lalu lintas", "macet")):
        return (
            f"Atmospheric documentary photography of a winding Trans-Sumatran highway through misty tropical pine forests "
            f"in {region_hint}, early morning fog, realistic journalistic lighting, 16:9, no text"
        )
    if any(k in title_lower for k in ("bencana", "banjir", "longsor", "cuaca", "hujan", "angin")):
        return (
            f"Documentary landscape photo of dramatic weather over mountain hills in {region_hint}, "
            f"lush green valley, natural daylight, wide angle 16:9, no text"
        )
    if any(k in title_lower for k in ("danau toba", "wisata", "pariwisata", "pantai", "samosir", "kaldera")):
        return (
            f"Stunning editorial travel photography of Lake Toba panoramic view with calm blue water and green volcanic hills "
            f"in {region_hint}, golden hour sunlight, ultra realistic, 16:9, no text"
        )
    if any(k in title_lower for k in ("budaya", "adat", "ulos", "tradisi", "marga", "tarombo", "gondang", "hata")):
        return (
            f"Editorial photojournalism of traditional Batak woven Ulos textile details displayed in a heritage wooden Batak house "
            f"in {region_hint}, warm natural lighting, high cultural detail, 16:9, no text"
        )
    if any(k in title_lower for k in ("kuliner", "makanan", "andaliman", "arsik", "kopi", "durian")):
        return (
            f"Editorial documentary still life of fresh Indonesian regional culinary ingredients and spices on a rustic table "
            f"in North Sumatra, warm daylight, food journalism, 16:9, no text"
        )
    if any(k in title_lower for k in ("psms", "sepak bola", "stadion", "atlet", "pon", "olahraga")):
        return (
            f"Dynamic editorial documentary photo of a soccer stadium grass field in North Sumatra, "
            f"dramatic afternoon sunlight, sports photojournalism, 16:9, no text"
        )
    if any(k in title_lower for k in ("ekonomi", "bisnis", "sawit", "pasar", "inflasi", "umkm")):
        return (
            f"Documentary photo of lush green oil palm plantation and local commerce activity in North Sumatra, "
            f"natural daylight, economic photojournalism, 16:9, no text"
        )

    clean_t = re.sub(r"[^\w\s-]", "", title).strip()
    return f"Editorial documentary photography representing {clean_t} in {region_hint}, realistic photojournalism, natural lighting, 16:9 aspect ratio, no text"


def generate_editorial_image(
    safe_prompt: str,
    title: str = "",
    gemini_api_key: str = "",
    output_dir: str = "generated_images",
    github_repo: str = "",
) -> tuple[str, str, str]:
    """Menghasilkan gambar ilustrasi editorial 16:9 menggunakan Gemini API (SDK google-genai / Imagen)
    atau fallback Pollinations Flux, mengompresnya dengan Pillow ke format .jpg di folder generated_images/,
    dan mengembalikan tuple: (cdn_url, local_file_path, status_label).
    """
    key = gemini_api_key or GEMINI_API_KEY
    img_bytes = None
    status_label = "Ilustrasi AI Gemini"

    # 1. Coba panggil model pembuat gambar Gemini (Imagen 3) jika API Key tersedia
    if key:
        try:
            from google import genai

            client = genai.Client(api_key=key)
            result = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=safe_prompt,
                config=dict(
                    number_of_images=1,
                    aspect_ratio="16:9",
                    output_mime_type="image/jpeg",
                ),
            )
            if result.generated_images:
                img_bytes = result.generated_images[0].image.image_bytes
                status_label = "Ilustrasi AI Gemini (Imagen 3)"
        except Exception:
            pass

    # 2. Fallback tangguh ke Pollinations Flux jika Imagen 3 tidak aktif/mengalami limit
    if not img_bytes:
        try:
            pollinations_url = POLLINATIONS_FLUX_URL_TEMPLATE.format(prompt=quote(safe_prompt, safe=""))
            resp = requests.get(pollinations_url, timeout=15)
            if resp.status_code == 200 and resp.content:
                img_bytes = resp.content
                status_label = "Ilustrasi AI Gemini (Flux Editorial)"
        except Exception:
            pass

    # 3. Fallback jika seluruh request jaringan gagal: buat gambar kanvas editorial lokal dengan Pillow
    if not img_bytes:
        im_fallback = Image.new("RGB", (1200, 675), color=(30, 41, 59))
        buf = io.BytesIO()
        im_fallback.save(buf, format="JPEG", quality=85)
        img_bytes = buf.getvalue()
        status_label = "Ilustrasi Redaksi BoaBoa"

    # 4. Simpan ke folder generated_images/ dengan kompresi Pillow
    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    slug = slugify(title or safe_prompt[:30])
    filename = f"{today_str}-{slug}.jpg"
    local_path = os.path.join(output_dir, filename)

    try:
        im = Image.open(io.BytesIO(img_bytes))
        im = im.convert("RGB")
        if im.size != (1200, 675):
            im = im.resize((1200, 675), Image.Resampling.LANCZOS)
        im.save(local_path, format="JPEG", quality=82, optimize=True)
    except Exception:
        with open(local_path, "wb") as f:
            f.write(img_bytes)

    # 5. Bentuk URL publik CDN jsdelivr
    repo = github_repo or GITHUB_REPOSITORY or "kardisim/boaboa-auto-news"
    cdn_url = f"https://cdn.jsdelivr.net/gh/{repo}@main/generated_images/{filename}"

    return cdn_url, local_path, status_label


def generate_contextual_illustration(
    image_prompt: str = "",
    title: str = "",
    labels: list[str] | None = None,
    verify_remote: bool = False,
    timeout: int = 5,
    content: str = "",
    gemini_api_key: str = "",
    github_repo: str = "",
) -> dict:
    """Fungsi utama untuk menghasilkan ilustrasi AI kontekstual dan meng-host-nya ke repo GitHub."""
    safe_prompt = translate_to_safe_visual_prompt(
        title=title,
        content=content,
        labels=labels,
        gemini_api_key=gemini_api_key,
    )
    cdn_url, local_path, status_label = generate_editorial_image(
        safe_prompt=safe_prompt,
        title=title,
        gemini_api_key=gemini_api_key,
        github_repo=github_repo,
    )
    return {
        "url": cdn_url,
        "local_path": local_path,
        "caption": "Ilustrasi: Dokumentasi Konseptual Redaksi BoaBoa",
        "is_ai": True,
        "status": status_label,
        "safe_prompt": safe_prompt,
    }
