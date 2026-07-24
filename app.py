from __future__ import annotations

import os
import random
import secrets
import sys
import time
from collections import defaultdict, deque
from datetime import date, datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Tuple

from flask import Flask, abort, jsonify, render_template, request, session, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from astrology_numbers import (  # noqa: E402
    JST,
    apply_astrology_scores,
    astrology_numbers_from_profile,
    astrology_pool_from_profile,
    calculate_astrology_profile,
    calculate_birth_sun_sign,
    parse_birth_date,
)
from generate_tickets import generate_tickets  # noqa: E402
from pools import build_pools  # noqa: E402
from result_checker import check_ticket_rows, draw_numbers_from_row, load_draw_by_no, load_latest_draw  # noqa: E402
from utils import load_json, read_csv_dicts  # noqa: E402

APP_VERSION = "v1.5.7-public"
MODE_CHOICES = [
    (
        "astrology",
        "星読み",
        "おすすめ・基本",
        "あなたが生まれた日の星と、今日めぐる七天体から響く数字を中心に結びます。",
    ),
    (
        "balance",
        "バランス",
        "偏りを整える",
        "過去の数字の流れと全体のまとまりを見ながら、偏りすぎない組み合わせへ整えます。",
    ),
    (
        "data",
        "過去データ",
        "数字の記憶",
        "これまでの出現傾向や間隔をいつもより深く読み、流れのある数字を選びます。",
    ),
    (
        "cold",
        "眠っている数字",
        "変化の気配",
        "しばらく姿を見せていない数字にも目を向け、組み合わせへ新しい風を招きます。",
    ),
    (
        "payout",
        "高い数字を含める",
        "32〜43にも注目",
        "誕生日に結びつきやすい数字だけでなく、32〜43の数字にも光を当てます。",
    ),
    (
        "all",
        "五つの導きをすべて試す",
        "じっくり比較",
        "星読み・バランス・過去データ・眠っている数字・高い数字の五つをまとめて試します。",
    ),
]
MODE_IDS = {m[0] for m in MODE_CHOICES}
ASTROLOGY_MODE_ID = "astrology"
BASE_GENERATION_MODE_IDS = [m[0] for m in MODE_CHOICES if m[0] not in {"all", ASTROLOGY_MODE_ID}]
GENERATION_MODE_IDS = [*BASE_GENERATION_MODE_IDS, ASTROLOGY_MODE_ID]

# v1.5.5 hotfix:
# GitHubのWebアップロードなどで config/mode_rules.json だけが古い状態に残っても、
# 画面側が送る astrology モードを必ず解決できるよう、アプリ側にも安全な既定値を持たせます。
ASTROLOGY_MODE_RULE_FALLBACK: Dict[str, Any] = {
    "mode_id": ASTROLOGY_MODE_ID,
    "mode_name": "Astrology",
    "mode_name_ja": "星読み",
    "description": "あなたが生まれた日の星と、今日めぐる七天体から響く数字を中心に結びます。",
    "astrology_core_min": 2,
    "astrology_core_max": 3,
    "astrology_min": 1,
    "astrology_max": 2,
    "data_min": 1,
    "data_max": 2,
    "cold_min": 0,
    "cold_max": 1,
    "over31_min": 1,
    "over31_max": 2,
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = resolve_secret_key()
    app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
    app.config["TICKET_TOKEN_MAX_AGE_SECONDS"] = int(os.environ.get("TICKET_TOKEN_MAX_AGE_SECONDS", "86400"))
    app.config["RATE_LIMIT_PER_MINUTE"] = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "30"))
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = is_production_environment()

    @app.context_processor
    def inject_common() -> Dict[str, Any]:
        settings = load_json("config/app_settings.json")
        return {
            "app_version": APP_VERSION,
            "mode_choices": MODE_CHOICES,
            "csrf_token": get_csrf_token,
            "data_status": data_status(),
            "default_ticket_count": int(settings.get("default_ticket_count", 2)),
            "max_ticket_count": int(settings.get("max_ticket_count", 10)),
            "generation_mode_count": len(BASE_GENERATION_MODE_IDS),
            "generation_mode_count_with_astrology": len(GENERATION_MODE_IDS),
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
            mode, count, seed, birth_date_value = parse_generate_form(request.form)
            astrology_profile = calculate_astrology_profile(birth_date_value) if birth_date_value else None
            rows = generate_ticket_rows(
                mode,
                count,
                seed,
                astrology_profile=astrology_profile,
            )
            token = sign_payload({"rows": rows})
            edit_url = build_edit_url(
                mode,
                count,
                seed,
                birth_date_value,
            )
            active_mode_count = len(BASE_GENERATION_MODE_IDS) + (1 if astrology_profile else 0) if mode == "all" else 1
            return render_template(
                "result.html",
                rows=rows,
                token=token,
                mode=mode,
                count=count,
                seed=seed,
                edit_url=edit_url,
                astrology_profile=astrology_profile,
                active_mode_count=active_mode_count,
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
                error="買い目を生成できませんでした。入力内容を確認して、もう一度お試しください。",
            ), 500

    @app.post("/check")
    def check_form():
        try:
            ticket_token = request.form.get("ticket_token", "")
            rows_from_token(ticket_token)
            latest = load_latest_draw()
            incoming = dict(request.form.items())
            check_method = incoming.get("check_method", "draw")
            if check_method not in {"draw", "manual"}:
                check_method = "draw"
            draw_values = {
                f"main_{idx}": incoming.get(f"main_{idx}", "") for idx in range(1, 7)
            }
            draw_values["bonus"] = incoming.get("bonus", "")
            draw_no_value = incoming.get("draw_no", "") or str(latest.get("draw_no", ""))
            return render_template(
                "check.html",
                ticket_token=ticket_token,
                latest=latest,
                draw_values=draw_values,
                draw_no_value=draw_no_value,
                check_method=check_method,
                error="",
            )
        except (ValueError, RuntimeError) as exc:
            return render_template("error.html", message=str(exc)), 400
        except Exception:
            app.logger.exception("Unexpected check form error")
            return render_template("error.html", message="照合画面を開けませんでした。もう一度買い目を生成してください。"), 500

    @app.post("/check-result")
    def check_result():
        ticket_token = request.form.get("ticket_token", "")
        check_values = dict(request.form.items())
        try:
            rows = rows_from_token(ticket_token)
            check_method = request.form.get("check_method", "draw")
            if check_method == "draw":
                draw_no = parse_draw_no(request.form.get("draw_no", ""))
                draw_row = load_draw_by_no(draw_no)
                main_numbers, bonus = draw_numbers_from_row(draw_row)
                checked_draw_no = str(draw_row.get("draw_no", ""))
                checked_draw_date = str(draw_row.get("draw_date", ""))
            elif check_method == "manual":
                main_numbers, bonus = parse_manual_draw(request.form)
                checked_draw_no = ""
                checked_draw_date = "手入力"
            else:
                raise ValueError("照合方法を選択してください。")

            checked_rows = check_ticket_rows(
                rows,
                main_numbers,
                bonus,
                draw_no=checked_draw_no,
                draw_date=checked_draw_date,
            )
            return render_template(
                "checked.html",
                rows=checked_rows,
                ticket_token=ticket_token,
                check_values=check_values,
            )
        except (ValueError, RuntimeError) as exc:
            latest = safe_latest_draw()
            return render_template(
                "check.html",
                ticket_token=ticket_token,
                latest=latest,
                draw_values=check_values,
                draw_no_value=check_values.get("draw_no", str(latest.get("draw_no", ""))),
                check_method=check_values.get("check_method", "draw"),
                error=str(exc),
            ), 400
        except Exception:
            app.logger.exception("Unexpected result check error")
            latest = safe_latest_draw()
            return render_template(
                "check.html",
                ticket_token=ticket_token,
                latest=latest,
                draw_values=check_values,
                draw_no_value=check_values.get("draw_no", str(latest.get("draw_no", ""))),
                check_method=check_values.get("check_method", "draw"),
                error="照合処理でエラーが発生しました。入力内容を確認して、もう一度お試しください。",
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


def parse_generate_form(form: Any) -> Tuple[str, int, str, date | None]:
    mode = str(form.get("mode", "astrology")).strip()
    if mode not in MODE_IDS:
        raise ValueError("生成モードを選択してください。")

    settings = load_json("config/app_settings.json")
    max_count = int(settings.get("max_ticket_count", 10))
    try:
        count = int(str(form.get("count", "")).strip())
    except Exception as exc:
        raise ValueError(f"それぞれの導きから受け取る口数を1〜{max_count}で選んでください。") from exc
    if not 1 <= count <= max_count:
        raise ValueError(f"それぞれの導きから受け取る口数は1〜{max_count}の範囲で選んでください。")

    seed = str(form.get("seed", "")).strip()
    if len(seed) > 80:
        raise ValueError("再現用キーワードは80文字以内で入力してください。")

    birth_date_text = str(form.get("birth_date", "")).strip()
    # v1.5.7: 誕生日入力をすべての導きの共通入口に統一します。
    # 星読みを画面上の別スイッチにせず、どの方法でも誕生日と今日の天体を土台にします。
    birth_date_value = parse_birth_date(birth_date_text)

    return mode, count, seed, birth_date_value

def parse_draw_no(value: Any) -> int:
    text = str(value or "").strip()
    if not text:
        raise ValueError("抽せん回を入力してください。")
    try:
        draw_no = int(text)
    except ValueError as exc:
        raise ValueError("抽せん回は数字で入力してください。") from exc
    if draw_no <= 0:
        raise ValueError("抽せん回は1以上で入力してください。")
    return draw_no


def parse_manual_draw(form: Any) -> Tuple[List[int], int]:
    main_numbers: List[int] = []
    for idx in range(1, 7):
        raw = str(form.get(f"main_{idx}", "")).strip()
        if not raw:
            raise ValueError("本数字を6個すべて入力してください。")
        try:
            number = int(raw)
        except ValueError as exc:
            raise ValueError("本数字は1〜43の整数で入力してください。") from exc
        if not 1 <= number <= 43:
            raise ValueError("本数字は1〜43の範囲で入力してください。")
        if number in main_numbers:
            raise ValueError(f"本数字に同じ数字が重複しています: {number}")
        main_numbers.append(number)

    bonus_raw = str(form.get("bonus", "")).strip()
    if not bonus_raw:
        raise ValueError("ボーナス数字を入力してください。")
    try:
        bonus = int(bonus_raw)
    except ValueError as exc:
        raise ValueError("ボーナス数字は1〜43の整数で入力してください。") from exc
    if not 1 <= bonus <= 43:
        raise ValueError("ボーナス数字は1〜43の範囲で入力してください。")
    if bonus in main_numbers:
        raise ValueError("ボーナス数字は本数字と異なる数字を入力してください。")

    return sorted(main_numbers), bonus


def load_number_stats() -> List[Dict[str, Any]]:
    settings = load_json("config/app_settings.json")
    rows = read_csv_dicts(settings.get("number_stats_path", "data/processed/number_stats.csv"))
    if not rows:
        raise RuntimeError("数字別の集計データを読み込めませんでした。管理者にデータ更新を依頼してください。")
    return rows


def load_generation_mode_rules() -> Dict[str, Any]:
    """Load generation rules and repair a stale/missing astrology rule safely."""
    configured = load_json("config/mode_rules.json")
    if not isinstance(configured, dict):
        raise RuntimeError("生成モード設定を読み込めませんでした。")

    mode_rules: Dict[str, Any] = {
        mode_id: dict(rule)
        for mode_id, rule in configured.items()
        if isinstance(rule, dict)
    }

    # A stale deployment can contain the new UI/app.py but an older JSON file.
    # Merge the built-in fallback so mode_id=astrology never becomes unknown.
    astrology_rule = dict(ASTROLOGY_MODE_RULE_FALLBACK)
    deployed_rule = mode_rules.get(ASTROLOGY_MODE_ID)
    if isinstance(deployed_rule, dict):
        astrology_rule.update(deployed_rule)
    mode_rules[ASTROLOGY_MODE_ID] = astrology_rule

    return mode_rules


def generate_ticket_rows(
    mode: str,
    count: int,
    seed: str = "",
    astrology_profile: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    mode_rules = load_generation_mode_rules()
    balance_rules = load_json("config/balance_rules.json")
    astrology_numbers = astrology_numbers_from_profile(astrology_profile)
    astrology_pool = astrology_pool_from_profile(astrology_profile)
    number_stats = apply_astrology_scores(load_number_stats(), astrology_profile)
    pools = build_pools(
        number_stats,
        astrology_numbers=astrology_numbers,
        astrology_pool=astrology_pool,
    )
    if mode == "all":
        modes = [*BASE_GENERATION_MODE_IDS, *([ASTROLOGY_MODE_ID] if astrology_profile else [])]
    else:
        modes = [mode]
    if ASTROLOGY_MODE_ID in modes and not astrology_profile:
        raise ValueError("誕生星のラッキー型を受け取るには、生年月日を西暦で教えてください。")
    rng: random.Random | random.SystemRandom
    rng = random.Random(seed) if seed else random.SystemRandom()

    tickets: List[Dict[str, Any]] = []
    shared_seen: set[tuple[int, ...]] = set()
    for mode_id in modes:
        generated = generate_tickets(
            mode_id=mode_id,
            ticket_count=count,
            pools=pools,
            number_stats=number_stats,
            mode_rules=mode_rules,
            balance_rules=balance_rules,
            astrology_numbers=astrology_numbers,
            rng=rng,
            seen=shared_seen,
        )
        if len(generated) < count:
            raise RuntimeError(
                f"{mode_rules.get(mode_id, {}).get('mode_name_ja', mode_id)}で指定口数を生成できませんでした。"
                "各モードの口数を少なくして、もう一度お試しください。"
            )
        tickets.extend(generated)

    if not tickets:
        raise RuntimeError("買い目を生成できませんでした。各モードの口数を少なくして、もう一度お試しください。")
    return flatten_tickets(tickets, astrology_profile)


def flatten_tickets(
    tickets: List[Dict[str, Any]],
    astrology_profile: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    id_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    astrology_numbers = astrology_numbers_from_profile(astrology_profile)
    rows: List[Dict[str, Any]] = []
    for idx, ticket in enumerate(tickets, start=1):
        nums = [int(n) for n in ticket["numbers"]]
        row = {
            "ticket_id": f"web_{id_stamp}_{idx:03d}",
            "generated_at": generated_at,
            "mode_id": ticket.get("mode_id", ""),
            "mode_name": ticket.get("mode_name", ""),
            "mode_name_ja": ticket.get("mode_name_ja", ""),
            "astrology_numbers": ",".join(str(n) for n in astrology_numbers),
            "n1": nums[0],
            "n2": nums[1],
            "n3": nums[2],
            "n4": nums[3],
            "n5": nums[4],
            "n6": nums[5],
            "set_sum": ticket.get("set_sum", ""),
            "odd_count": ticket.get("odd_count", ""),
            "even_count": ticket.get("even_count", ""),
            "low_count": ticket.get("low_count", ""),
            "mid_count": ticket.get("mid_count", ""),
            "high_count": ticket.get("high_count", ""),
            "over31_count": ticket.get("over31_count", ""),
            "consecutive_count": ticket.get("consecutive_count", ""),
            "data_score_avg": ticket.get("data_score_avg", ""),
            "balance_fit_score": ticket.get("balance_fit_score", ""),
            "astrology_hit_count": ticket.get("astrology_hit_count", 0),
            "astrology_fit_score": ticket.get("astrology_fit_score", ""),
            "score_has_astrology": ticket.get("score_has_astrology", False),
            "score_weights": ticket.get("score_weights", {}),
            "uniqueness_score": ticket.get("uniqueness_score", ""),
            "ticket_score": ticket.get("ticket_score", ""),
            "reason": ticket.get("reason", ""),
        }
        rows.append(row)
    return rows


def build_edit_url(
    mode: str,
    count: int,
    seed: str,
    birth_date_value: date | None = None,
) -> str:
    params: Dict[str, Any] = {"mode": mode, "count": count}
    if seed:
        params["seed"] = seed
    if birth_date_value:
        params["birth_date"] = birth_date_value.isoformat()
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


def get_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(resolve_secret_key(), salt="lotoscope6-ticket-v1")


def sign_payload(payload: Dict[str, Any]) -> str:
    return get_serializer().dumps(payload)


def rows_from_token(token: str) -> List[Dict[str, Any]]:
    if not token:
        raise ValueError("照合する買い目データがありません。先に買い目を生成してください。")
    try:
        payload = get_serializer().loads(token, max_age=current_token_max_age())
    except SignatureExpired as exc:
        raise ValueError("買い目データの有効期限が切れました。もう一度生成してください。") from exc
    except BadSignature as exc:
        raise ValueError("買い目データを確認できません。もう一度生成してください。") from exc
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("買い目データが空です。もう一度生成してください。")
    return rows


def current_token_max_age() -> int:
    try:
        return int(os.environ.get("TICKET_TOKEN_MAX_AGE_SECONDS", "86400"))
    except Exception:
        return 86400


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


def data_status() -> Dict[str, Any]:
    latest = safe_latest_draw()
    status: Dict[str, Any] = {
        "latest_draw_no": latest.get("draw_no", ""),
        "latest_draw_date": latest.get("draw_date", ""),
        "is_stale": False,
        "stale_days": 0,
    }
    try:
        latest_date = datetime.strptime(str(latest.get("draw_date", "")), "%Y-%m-%d").date()
        stale_days = (datetime.now().date() - latest_date).days
        status["stale_days"] = stale_days
        status["is_stale"] = stale_days >= 14
    except Exception:
        status["is_stale"] = True
    return status


def safe_latest_draw() -> Dict[str, Any]:
    try:
        return load_latest_draw()
    except Exception:
        return {}


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8786"))
    app.run(host="0.0.0.0", port=port, debug=False)
