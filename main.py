import argparse
import os
import socket

import feedparser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from groq import Groq

from boaboa.config import (
    BLOG_ID,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    MAX_CANDIDATES_PER_FEED,
    MAX_POSTS_PER_RUN,
    PUBLISH_AS_DRAFT,
    REQUIRE_REAL_IMAGE,
    RSS_URLS,
)
from boaboa.extractor import (
    clean_media_name,
    extract_article_details,
    resolve_original_url,
)
from boaboa.history import (
    is_duplicate_story,
    load_history,
    make_history_record,
    save_history,
)
from boaboa.html_formatter import fetch_boaboa_posts_index, format_final_html
from boaboa.image_generator import generate_contextual_illustration
from boaboa.quality_guard import check_editorial_quality
from boaboa.relevance import cluster_candidate_stories, score_candidate
from boaboa.writer import get_best_groq_model, get_groq_model_candidates, rewrite_news

socket.setdefaulttimeout(30)


def get_blogger_service():
    scopes = ["https://www.googleapis.com/auth/blogger"]
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", scopes)

    if creds and creds.expired and creds.refresh_token:
        print("Memperbarui token Blogger...", flush=True)
        creds.refresh(Request())

    if not creds or not creds.valid:
        raise RuntimeError("Token tidak valid. Periksa secret BLOGGER_TOKEN.")

    return build("blogger", "v3", credentials=creds)


def collect_candidates(history: list) -> list[dict]:
    candidates: list[dict] = []
    session_seen: list[dict] = []

    for feed_cfg in RSS_URLS:
        feed_name = feed_cfg["name"]
        rss_url = feed_cfg["url"]
        base_score = feed_cfg["base_score"]
        print(f"\n--- Memindai saluran RSS [{feed_name}] ---", flush=True)
        feed = feedparser.parse(rss_url)

        accepted_from_feed = 0
        for entry in feed.entries:
            if accepted_from_feed >= MAX_CANDIDATES_PER_FEED:
                break

            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            source_media = entry.get("source", {}).get("title", "Media Terkait")
            if not title or not link:
                continue

            is_dup, dup_reason = is_duplicate_story(link, title, history + session_seen)
            if is_dup:
                print(f"Melewati duplikat: {title} ({dup_reason})", flush=True)
                continue

            rel_score, rel_reason = score_candidate(title, source_media, base_score=base_score, url=link)
            if rel_score < 1:
                print(f"Melewati tidak relevan: {title} ({rel_reason})", flush=True)
                continue

            cand = {
                "feed_name": feed_name,
                "title": title,
                "link": link,
                "source_media": source_media,
                "score": rel_score,
                "reason": rel_reason,
            }
            candidates.append(cand)
            session_seen.append({"google_url": link, "title": title})
            accepted_from_feed += 1

    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates


def run_automation(dry_run: bool = False) -> None:
    if not GROQ_API_KEY and not GEMINI_API_KEY:
        raise RuntimeError("Environment variable GEMINI_API_KEY atau GROQ_API_KEY belum diatur.")

    print("Memulai pembacaan riwayat BoaBoa...", flush=True)
    history = load_history()

    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    model_candidates = get_groq_model_candidates(groq_client) if groq_client else []
    active_model = model_candidates[0] if model_candidates else "llama-3.3-70b-versatile"
    ai_engine = f"Gemini ({GEMINI_MODEL})" if GEMINI_API_KEY else f"Groq ({active_model})"
    print(f"Mesin AI Utama: {ai_engine}", flush=True)

    service = None if dry_run else get_blogger_service()
    posts_index = fetch_boaboa_posts_index(max_results=250)
    print(f"Indeks internal linking boaboa.bataktive.com: {len(posts_index)} artikel dimuat.", flush=True)

    raw_candidates = collect_candidates(history)
    print(f"\nTotal kandidat sebelum clustering: {len(raw_candidates)}")
    candidates = cluster_candidate_stories(raw_candidates, similarity_threshold=0.55)
    print(f"Total kandidat setelah clustering peristiwa: {len(candidates)} (maks {MAX_POSTS_PER_RUN} draf/run)", flush=True)

    published_count = 0
    for cand in candidates:
        if published_count >= MAX_POSTS_PER_RUN:
            break

        source_media = clean_media_name(cand["source_media"])
        print(
            f"\n[{published_count + 1}/{MAX_POSTS_PER_RUN}] Memproses ({source_media}, {cand['reason']}): {cand['title']}",
            flush=True,
        )

        try:
            real_url = resolve_original_url(cand["link"])
            print(f"Situs asli: {real_url}", flush=True)

            if "news.google.com" in real_url:
                print(
                    f"Melewati berita karena URL Google News gagal didekode ke situs penerbit asli: {cand['title']}",
                    flush=True,
                )
                continue

            is_dup_real, dup_reason = is_duplicate_story(cand["link"], cand["title"], history, real_url=real_url)
            if is_dup_real:
                print(f"Melewati duplikat situs asli: {dup_reason}", flush=True)
                continue

            details = extract_article_details(real_url)
            total_photos = len(details.get("images", []))
            print(
                f"Ekstraksi [{details['extraction_method']}]: {details['char_count']} karakter, "
                f"{details['sentence_count']} kalimat, foto={total_photos} foto liputan",
                flush=True,
            )

            if details["char_count"] == 0:
                print(
                    f"Melewati berita karena konten gagal diakses/diblokir server sumber: {cand['title']}",
                    flush=True,
                )
                continue

            full_source_text = details["text"]
            clustered = cand.get("clustered_sources", [])
            if clustered:
                print(f"Menggabungkan {len(clustered)} sumber liputan untuk peristiwa yang sama...", flush=True)
                extra_texts = []
                for cl_item in clustered[:2]:
                    try:
                        cl_url = resolve_original_url(cl_item["link"])
                        cl_details = extract_article_details(cl_url)
                        if cl_details["char_count"] > 100:
                            extra_texts.append(
                                f"\n--- Tambahan Fakta dari {cl_item['source_media']} ---\n{cl_details['text']}"
                            )
                    except Exception:
                        pass
                if extra_texts:
                    full_source_text = full_source_text + "\n" + "\n".join(extra_texts)

            main_image_url = details.get("image_url")
            image_status = f"Foto Sumber ({source_media})" if main_image_url else ""
            if not main_image_url:
                if REQUIRE_REAL_IMAGE:
                    print(
                        f"Melewati berita karena REQUIRE_REAL_IMAGE aktif dan naskah tanpa foto liputan: {cand['title']}",
                        flush=True,
                    )
                    continue
                else:
                    print(
                        f"Foto liputan asli tidak ditemukan pada sumber. Menghasilkan ilustrasi AI editorial kontekstual untuk: {cand['title']}",
                        flush=True,
                    )
                    illustration = generate_contextual_illustration(
                        title=cand["title"],
                        content=full_source_text[:300],
                    )
                    main_image_url = illustration["url"]
                    image_status = illustration.get("status", "Ilustrasi AI Gemini")

            article_data = rewrite_news(
                groq_client=groq_client,
                model_name=model_candidates,
                title=cand["title"],
                full_text_content=full_source_text,
                source_media=source_media,
                source_url=real_url,
                published_date=details.get("published_date"),
                author=details.get("author"),
                gemini_api_key=GEMINI_API_KEY,
                gemini_model=GEMINI_MODEL,
            )

            quality_report = check_editorial_quality(
                article_data=article_data,
                source_text=full_source_text,
                image_url=main_image_url,
                image_status=image_status,
            )
            print(f"Editorial Checklist: {quality_report['checklist']}", flush=True)

            extra_images = details.get("images", [])[1:] if details.get("images") else []
            final_content = format_final_html(
                article_data=article_data,
                image_url=main_image_url,
                source_media_name=source_media,
                real_url=real_url,
                posts_index=posts_index,
                image_width=details.get("image_width"),
                image_height=details.get("image_height"),
                additional_images=extra_images,
                image_status=image_status,
                quality_report=quality_report,
                is_draft=PUBLISH_AS_DRAFT,
            )

            body = {
                "kind": "blogger#post",
                "blog": {"id": BLOG_ID},
                "title": article_data["title"],
                "content": final_content,
                "labels": article_data["labels"],
            }
            meta_desc = article_data.get("meta_description", "")

            if dry_run:
                print(
                    f"[DRY-RUN] Siap unggah draf: {article_data['title']} ({len(article_data['title'])} kar.) "
                    f"| labels={article_data['labels']} | meta_desc={meta_desc} ({len(meta_desc)} kar.)",
                    flush=True,
                )
            else:
                service.posts().insert(blogId=BLOG_ID, body=body, isDraft=True).execute()
                print(
                    f"Berhasil diunggah ke Draf: {article_data['title']} ({len(article_data['title'])} kar.) "
                    f"| labels={article_data['labels']} | Deskripsi Penelusuran: {meta_desc}",
                    flush=True,
                )
                history.append(make_history_record(cand["link"], real_url, cand["title"], source_media))
                for cl_item in cand.get("clustered_sources", []):
                    history.append(make_history_record(cl_item["link"], "", cl_item["title"], cl_item["source_media"]))
                save_history(history)

            published_count += 1
        except Exception as e:
            print(f"Dilewati/gagal memproses berita: {e}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BoaBoa Auto News Generator (boaboa.bataktive.com)")
    parser.add_argument("--dry-run", action="store_true", help="Jalankan tanpa mengunggah ke Blogger")
    args = parser.parse_args()
    run_automation(dry_run=args.dry_run or os.environ.get("DRY_RUN") == "1")
