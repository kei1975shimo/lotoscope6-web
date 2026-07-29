from __future__ import annotations

import os
import secrets
import sys
import time
from collections import defaultdict, deque
from datetime import date, datetime
from pathlib import Path
from typing import Any, Deque, Dict, Tuple

from flask import Flask, abort, jsonify, render_template, request, session, url_for

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from astrology_numbers import (  # noqa: E402
    JST,
    calculate_astrology_profile,
    calculate_birth_sun_sign,
    parse_birth_date,
)
from product_numbers import (  # noqa: E402
    generate_product_rows,
    get_product,
    product_choices,
)
from utils import load_json  # noqa: E402

APP_VERSION = "v1.7.9-repeat-button-contrast"
DEFAULT_PRODUCT_ID = "loto6"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = resolve_secret_key()
    app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
    app.config["RATE_LIMIT_PER_MINUTE"] = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "30"))
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = is_production_environment()

    @app.context_processor
    def inject_common() -> Dict[str, Any]:
        settings = load_json("config/app_settings.json")
        return {
            "app_version": APP_VERSION,
            "product_choices": product_choices(),
            "csrf_token": get_csrf_token,
            "default_ticket_count": int(settings.get("default_ticket_count", 2)),
            "max_ticket_count": int(settings.get("max_ticket_count", 10)),
            "today_date": datetime.now(JST).date().isoformat(),
            "current_year": datetime.now(JST).year,
        }

    @app.before_request
    def protect_post_requests():
        if request.method != "POST":
            return None
        enforce_rate_limit(app)
        validate_csrf_token()
        return None

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; font-src 'self' data:; form-action 'self'; base-uri 'self'; frame-ancestors 'none'",
        )
        if response.mimetype == "text/html":
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    @app.get("/")
    def index():
        values = dict(request.args.items())
        return render_template("index.html", values=values, error="")

    @app.get("/zodiac-preview")
    def zodiac_preview():
        try:
            birth_date_value = parse_birth_date(request.args.get("birth_date", ""))
            return jsonify(calculate_birth_sun_sign(birth_date_value))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.post("/generate")
    def generate():
        try:
            product_id, count, seed, birth_date_value = parse_generate_form(request.form)
            product = get_product(product_id)
            astrology_profile = calculate_astrology_profile(birth_date_value)
            rows = generate_product_rows(product_id, count, astrology_profile, seed=seed)
            edit_url = build_edit_url(product_id, count, seed, birth_date_value)
            return render_template(
                "result.html",
                rows=rows,
                product=product,
                product_id=product_id,
                count=count,
                seed=seed,
                edit_url=edit_url,
                astrology_profile=astrology_profile,
            )
        except (ValueError, RuntimeError) as exc:
            values = dict(request.form.items())
            return render_template("index.html", values=values, error=str(exc)), 400
        except Exception:
            app.logger.exception("Unexpected generation error")
            values = dict(request.form.items())
            return render_template(
                "index.html",
                values=values,
                error="数字を導けませんでした。入力内容を確認して、もう一度お試しください。",
            ), 500

    @app.get("/health")
    def health():
        return "OK"

    @app.errorhandler(400)
    def bad_request(err):
        message = getattr(err, "description", "入力内容を確認してください。")
        return render_template("error.html", message=message), 400

    @app.errorhandler(404)
    def not_found(_err):
        return render_template("error.html", message="ページが見つかりません。"), 404

    @app.errorhandler(413)
    def request_too_large(_err):
        return render_template("error.html", message="送信データが大きすぎます。口数を減らして、もう一度お試しください。"), 413

    @app.errorhandler(429)
    def too_many_requests(err):
        message = getattr(err, "description", "短時間に操作が集中しています。少し時間をおいてからお試しください。")
        return render_template("error.html", message=message), 429

    @app.errorhandler(500)
    def server_error(_err):
        return render_template("error.html", message="内部エラーが発生しました。時間をおいて再度お試しください。"), 500

    return app


def parse_generate_form(form: Any) -> Tuple[str, int, str, date]:
    product_id = str(form.get("product", DEFAULT_PRODUCT_ID)).strip()
    get_product(product_id)

    settings = load_json("config/app_settings.json")
    max_count = int(settings.get("max_ticket_count", 10))
    try:
        count = int(str(form.get("count", "")).strip())
    except Exception as exc:
        raise ValueError(f"受け取る口数を1〜{max_count}で選んでください。") from exc
    if not 1 <= count <= max_count:
        raise ValueError(f"受け取る口数は1〜{max_count}の範囲で選んでください。")

    seed = str(form.get("seed", "")).strip()
    if len(seed) > 80:
        raise ValueError("星読みの合言葉は80文字以内で入力してください。")

    birth_date_value = parse_birth_date(str(form.get("birth_date", "")).strip())
    return product_id, count, seed, birth_date_value


def build_edit_url(product_id: str, count: int, seed: str, birth_date_value: date) -> str:
    params: Dict[str, Any] = {
        "product": product_id,
        "count": count,
        "birth_date": birth_date_value.isoformat(),
    }
    if seed:
        params["seed"] = seed
    return url_for("index", **params)


def is_production_environment() -> bool:
    app_env = os.environ.get("APP_ENV", "").strip().lower()
    flask_env = os.environ.get("FLASK_ENV", "").strip().lower()
    return app_env == "production" or flask_env == "production"


def resolve_secret_key() -> str:
    secret_key = os.environ.get("SECRET_KEY", "").strip()
    if is_production_environment() and not secret_key:
        raise RuntimeError("本番公開時は環境変数 SECRET_KEY を必ず設定してください。")
    return secret_key or "dev-only-change-this-secret"


def get_csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return str(token)


def validate_csrf_token() -> None:
    expected = session.get("csrf_token")
    submitted = request.form.get("csrf_token", "")
    if not expected or not secrets.compare_digest(str(expected), str(submitted)):
        abort(400, description="フォームの有効期限が切れました。画面を再読み込みして、もう一度お試しください。")


_RATE_LIMIT_BUCKETS: Dict[str, Deque[float]] = defaultdict(deque)
_RATE_LIMIT_LAST_CLEANUP = 0.0


def enforce_rate_limit(app: Flask) -> None:
    global _RATE_LIMIT_LAST_CLEANUP
    limit = int(app.config.get("RATE_LIMIT_PER_MINUTE", 30))
    if limit <= 0:
        return
    key = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    now = time.time()
    window_start = now - 60

    if now - _RATE_LIMIT_LAST_CLEANUP > 300:
        stale_keys = [bucket_key for bucket_key, bucket in _RATE_LIMIT_BUCKETS.items() if not bucket or bucket[-1] < window_start]
        for bucket_key in stale_keys:
            _RATE_LIMIT_BUCKETS.pop(bucket_key, None)
        _RATE_LIMIT_LAST_CLEANUP = now

    bucket = _RATE_LIMIT_BUCKETS[key]
    while bucket and bucket[0] < window_start:
        bucket.popleft()
    if len(bucket) >= limit:
        abort(429, description="短時間に操作が集中しています。少し時間をおいてからお試しください。")
    bucket.append(now)



app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8786"))
    app.run(host="0.0.0.0", port=port, debug=False)
