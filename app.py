from __future__ import annotations

import math
import os
import secrets
import sys
import time
from collections import defaultdict, deque
from datetime import date, datetime
from pathlib import Path
from threading import Lock
from typing import Any

from flask import Flask, abort, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from astrology_numbers import JST, parse_birth_date  # noqa: E402
from divination_numbers import TAROT_IMAGE_FILES, calculate_divination_profile, divination_choices, get_divination  # noqa: E402
from product_numbers import MAX_FULL_SIZE, generate_product_rows, get_product, product_choices, product_full_size  # noqa: E402
from settings import DEFAULT_TICKET_COUNT, MAX_TICKET_COUNT  # noqa: E402

APP_VERSION = "v1.17.5-mystic-oracle"
DEFAULT_DIVINATION_ID = "astrology"
DEFAULT_PRODUCT_ID = "loto6"


def is_production_environment() -> bool:
    return (os.environ.get("APP_ENV", "").lower() == "production"
            or os.environ.get("FLASK_ENV", "").lower() == "production"
            or os.environ.get("RENDER", "").lower() == "true")


def resolve_secret_key() -> str:
    key = os.environ.get("SECRET_KEY", "").strip()
    if is_production_environment() and not key:
        raise RuntimeError("本番公開時は環境変数 SECRET_KEY を必ず設定してください。")
    return key or secrets.token_hex(32)


def get_csrf_token() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return str(session["csrf_token"])


def validate_csrf_token() -> None:
    expected = str(session.get("csrf_token", ""))
    submitted = str(request.form.get("csrf_token", ""))
    if not expected or not secrets.compare_digest(expected.encode(), submitted.encode()):
        abort(400, description="フォームの有効期限が切れました。画面を再読み込みして、もう一度お試しください。")


class RateLimiter:
    """Per-app, per-process sliding window, shared safely by worker threads."""

    def __init__(self) -> None:
        self.buckets: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()
        self.last_cleanup = 0.0

    def check(self, key: str, limit: int) -> int:
        if limit <= 0:
            return 0
        now = time.monotonic()
        cutoff = now - 60.0
        with self.lock:
            if now - self.last_cleanup >= 60:
                for stale in [k for k, v in self.buckets.items() if not v or v[-1] <= cutoff]:
                    del self.buckets[stale]
                self.last_cleanup = now
            bucket = self.buckets[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return max(1, math.ceil(bucket[0] + 60 - now))
            bucket.append(now)
        return 0


def parse_form_birth(form: Any, today: date | None = None) -> date:
    # Native selects also work with JavaScript disabled. Repeat forms use ISO.
    if any(key in form for key in ("birth_year", "birth_month", "birth_day")):
        try:
            value = date(int(form.get("birth_year", "")), int(form.get("birth_month", "")), int(form.get("birth_day", ""))).isoformat()
        except (ValueError, TypeError) as exc:
            raise ValueError("生年月日の年・月・日を正しく選択してください。") from exc
    else:
        value = str(form.get("birth_date", "")).strip()
    return parse_birth_date(value, today=today)


def parse_generate_form(form: Any, today: date | None = None) -> tuple[str, str, int, int, date]:
    divination = str(form.get("divination", DEFAULT_DIVINATION_ID)).strip()
    product = str(form.get("product", DEFAULT_PRODUCT_ID)).strip()
    get_divination(divination)
    product_info = get_product(product)
    try:
        count = int(str(form.get("count", "")).strip())
    except ValueError as exc:
        raise ValueError(f"受け取る口数を1〜{MAX_TICKET_COUNT}で選んでください。") from exc
    if not 1 <= count <= MAX_TICKET_COUNT:
        raise ValueError(f"受け取る口数は1〜{MAX_TICKET_COUNT}の範囲で選んでください。")
    full_size = product_full_size(product_info)
    # Missing pick_size (older cached forms, or a client that never sent it)
    # falls back to the product's own full size — unchanged past behaviour.
    try:
        raw_size = str(form.get("pick_size", "full")).strip()
        pick_size = full_size if raw_size == "full" else int(raw_size)
    except ValueError as exc:
        raise ValueError(f"欲しい個数を1〜{full_size}で選んでください。") from exc
    if not 1 <= pick_size <= full_size:
        raise ValueError(f"欲しい個数は1〜{full_size}の範囲で選んでください。")
    return divination, product, count, pick_size, parse_form_birth(form, today)


def build_daily_oracle_seed(birth_date_value: date, target_date_value: date, divination_id: str, product_id: str) -> str:
    return "|".join(("lotoscope-daily-v1", birth_date_value.isoformat(), target_date_value.isoformat(), divination_id, product_id))


def wants_json() -> bool:
    return request.accept_mimetypes.best == "application/json"


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=resolve_secret_key(), MAX_CONTENT_LENGTH=256 * 1024,
        PREMIUM_PREVIEW_ENABLED=os.environ.get("PREMIUM_PREVIEW_ENABLED", "1") == "1",
        RATE_LIMIT_PER_MINUTE=int(os.environ.get("RATE_LIMIT_PER_MINUTE", "30")),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=is_production_environment(),
        # Trust only a configured proxy. Direct/local deployments ignore XFF.
        TRUSTED_PROXY_HOPS=int(os.environ.get("TRUSTED_PROXY_HOPS", "1" if os.environ.get("RENDER", "").lower() == "true" else "0")),
    )
    if test_config:
        app.config.update(test_config)
    hops = int(app.config["TRUSTED_PROXY_HOPS"])
    if not 0 <= hops <= 5:
        raise ValueError("TRUSTED_PROXY_HOPS は0〜5で指定してください。")
    if hops:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=0, x_host=0, x_port=0, x_prefix=0)
    limiter = RateLimiter()
    app.extensions["rate_limiter"] = limiter

    @app.before_request
    def protect_request():
        g.today = datetime.now(JST).date()
        if request.method == "POST":
            # Do not read user-supplied forwarding headers here.
            retry = limiter.check(request.remote_addr or "unknown", int(app.config["RATE_LIMIT_PER_MINUTE"]))
            if retry:
                g.retry_after = retry
                abort(429, description=f"短時間に操作が集中しています。{retry}秒ほど待ってからお試しください。")
            validate_csrf_token()

    def has_premium_access() -> bool:
        # Temporary open access, explicitly requested for preview. No billing.
        return bool(app.config["PREMIUM_PREVIEW_ENABLED"] or
                    (app.testing and app.config.get("TEST_PREMIUM_ACCESS", False)))

    def require_method_access(method: str) -> None:
        if method != "astrology" and not has_premium_access():
            abort(403, description="この占術は月額プランの対象です。現在は購入受付の準備中です。西洋占星術は無料でご利用いただけます。")

    def tarot_card_image(filename: str) -> str:
        # Resolve at render time so installing artwork requires no logic changes.
        if filename in TAROT_IMAGE_FILES and (Path(app.static_folder) / filename).is_file():
            return filename
        return "img/oracle-tarot.webp"

    @app.context_processor
    def common():
        today = getattr(g, "today", datetime.now(JST).date())
        return dict(app_version=APP_VERSION, divination_choices=divination_choices(), product_choices=product_choices(),
                    csrf_token=get_csrf_token, default_ticket_count=DEFAULT_TICKET_COUNT, max_ticket_count=MAX_TICKET_COUNT,
                    max_full_size=MAX_FULL_SIZE, premium_access=has_premium_access(),
                    premium_preview=app.config["PREMIUM_PREVIEW_ENABLED"], tarot_card_image=tarot_card_image,
                    operator_name=os.environ.get("OPERATOR_NAME", "下地 恵雄"),
                    support_email=os.environ.get("SUPPORT_EMAIL", "keiyuu1975@yahoo.co.jp"),
                    business_address=os.environ.get("BUSINESS_ADDRESS", "未設定（公開準備中）"),
                    business_phone=os.environ.get("BUSINESS_PHONE", "未設定（公開準備中）"),
                    today_date=today.isoformat(), current_year=today.year, today_label=f"{today.year}.{today.month:02d}.{today.day:02d}")

    @app.after_request
    def security_headers(response):
        response.headers.update({
            "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; connect-src 'self'; form-action 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'",
        })
        if response.mimetype in {"text/html", "application/json"}:
            response.headers["Cache-Control"] = "no-store"
        if response.status_code == 429:
            response.headers["Retry-After"] = str(getattr(g, "retry_after", 60))
        return response

    @app.get("/")
    def index():
        return render_template("index.html", values={}, error="")

    @app.get("/generate")
    def generate_home():
        return redirect(url_for("index"))

    @app.post("/divination-preview")
    def divination_preview():
        try:
            method = str(request.form.get("divination", DEFAULT_DIVINATION_ID)).strip()
            get_divination(method)
            require_method_access(method)
            birth = parse_form_birth(request.form, g.today)
            profile = calculate_divination_profile(method, birth, g.today)
            return jsonify(method_id=profile["method_id"], summary_items=profile["summary_items"])
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

    @app.post("/generate")
    def generate():
        try:
            method, product, count, pick_size, birth = parse_generate_form(request.form, g.today)
            require_method_access(method)
            profile = calculate_divination_profile(method, birth, g.today)
            seed = build_daily_oracle_seed(birth, g.today, method, product)
            rows = generate_product_rows(product, count, profile, seed=seed, pick_size=pick_size)
            html = render_template("result.html", rows=rows, product=get_product(product), product_id=product, count=count,
                                   pick_size=pick_size,
                                   divination=get_divination(method), divination_id=method, divination_profile=profile)
            return jsonify(html=html) if wants_json() else html
        except (ValueError, RuntimeError) as exc:
            if wants_json():
                return jsonify(error=str(exc)), 400
            return render_template("index.html", values=dict(request.form), error=str(exc)), 400
        except HTTPException:
            raise
        except Exception:
            app.logger.exception("Unexpected generation error")
            abort(500)

    @app.get("/plans")
    def plans():
        return render_template("plans.html")

    @app.get("/privacy")
    def privacy():
        return render_template("privacy.html")

    @app.get("/terms")
    def terms():
        return render_template("terms.html")

    @app.get("/support")
    def support():
        return render_template("support.html")

    @app.get("/commerce")
    def commerce():
        return render_template("commerce.html")

    @app.get("/health")
    def health():
        return "OK"

    @app.errorhandler(HTTPException)
    def http_error(err):
        messages = {404: "ページが見つかりません。", 405: "この操作は入力画面から行ってください。",
                    413: "送信データが大きすぎます。画面を開き直してお試しください。",
                    500: "数字を導けませんでした。少し時間をおいてお試しください。"}
        message = messages.get(err.code, err.description)
        if wants_json() or request.path == "/divination-preview":
            return jsonify(error=message), err.code
        return render_template("error.html", message=message), err.code

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8786")), debug=False)
