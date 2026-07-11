from __future__ import annotations

import os
import random
import secrets
import sys
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Tuple

from flask import Flask, abort, render_template, request, session
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from generate_tickets import generate_tickets  # noqa: E402
from pools import build_pools  # noqa: E402
from result_checker import check_ticket_rows, draw_numbers_from_row, load_draw_by_no, load_latest_draw  # noqa: E402
from utils import clean_number_list, load_json, read_csv_dicts  # noqa: E402

APP_VERSION = "v1.0.16-public"
MODE_CHOICES = [
    ("all", "全モード", "迷ったらこれ", "5つのモードをまとめて生成します。比較しながら選べる標準スタートです。"),
    ("balance", "バランス型", "基本", "好きな数字・データ・32以上をバランスよく使います。"),
    ("personal", "好きな数字重視型", "自分の数字", "入力した好きな数字をやや多めに使います。"),
    ("data", "データ重視型", "過去データ", "過去データ側のスコアを強めに使います。"),
    ("cold", "未出現数字重視型", "変化球", "しばらく出ていない数字を変化要素として使います。"),
    ("payout", "高配当意識型", "かぶりにくさ", "32以上を厚めに入れ、誕生日数字偏重を避けます。"),
]
MODE_IDS = {m[0] for m in MODE_CHOICES}


def create_app() -> Flask:
    app = Flask(__name__)
    secret_key = resolve_secret_key()
    app.config["SECRET_KEY"] = secret_key
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    app.config["TICKET_TOKEN_MAX_AGE_SECONDS"] = int(os.environ.get("TICKET_TOKEN_MAX_AGE_SECONDS", "86400"))
    app.config["RATE_LIMIT_PER_MINUTE"] = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "30"))
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = is_production_environment()

    @app.context_processor
    def inject_common() -> Dict[str, Any]:
        return {
            "app_version": APP_VERSION,
            "mode_choices": MODE_CHOICES,
            "csrf_token": get_csrf_token,
            "data_status": data_status(),
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
        return response

    @app.get("/")
    def index():
        return render_template("index.html", values={}, error="")

    @app.post("/generate")
    def generate():
        try:
            favorite_numbers, avoided_numbers, mode, count = parse_generate_form(request.form)
            rows = generate_ticket_rows(favorite_numbers, avoided_numbers, mode, count)
            token = sign_payload({"rows": rows})
            return render_template(
                "result.html",
                rows=rows,
                token=token,
                favorite_numbers=favorite_numbers,
                avoided_numbers=avoided_numbers,
                mode=mode,
                count=count,
            )
        except Exception as exc:
            values = dict(request.form.items())
            return render_template("index.html", values=values, error=str(exc)), 400

    @app.post("/check")
    def check_form():
        try:
            rows = rows_from_token(request.form.get("ticket_token", ""))
            latest = load_latest_draw()
            main_numbers, bonus = draw_numbers_from_row(latest)
            draw_values = {f"main_{idx}": str(n) for idx, n in enumerate(main_numbers, start=1)}
            draw_values["bonus"] = str(bonus)
            return render_template(
                "check.html",
                ticket_token=request.form.get("ticket_token", ""),
                latest=latest,
                draw_values=draw_values,
                use_draw_no=True,
                error="",
            )
        except Exception as exc:
            return render_template("error.html", message=str(exc)), 400

    @app.post("/check-result")
    def check_result():
        try:
            ticket_token = request.form.get("ticket_token", "")
            rows = rows_from_token(ticket_token)
            use_draw_no = request.form.get("use_draw_no") == "on"
            if use_draw_no:
                draw_no_text = request.form.get("draw_no", "").strip()
                draw_row = load_draw_by_no(int(draw_no_text)) if draw_no_text else load_latest_draw()
                main_numbers, bonus = draw_numbers_from_row(draw_row)
                draw_no = str(draw_row.get("draw_no", ""))
                draw_date = str(draw_row.get("draw_date", ""))
            else:
                main_numbers = [int(request.form.get(f"main_{i}", "")) for i in range(1, 7)]
                bonus = int(request.form.get("bonus", ""))
                draw_no = ""
                draw_date = "手入力"
            checked_rows = check_ticket_rows(rows, main_numbers, bonus, draw_no=draw_no, draw_date=draw_date)
            return render_template("checked.html", rows=checked_rows)
        except Exception as exc:
            latest = safe_latest_draw()
            return render_template(
                "check.html",
                ticket_token=request.form.get("ticket_token", ""),
                latest=latest,
                draw_values=dict(request.form.items()),
                use_draw_no=request.form.get("use_draw_no") == "on",
                error=str(exc),
            ), 400

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

    @app.errorhandler(429)
    def too_many_requests(err):
        message = getattr(err, "description", "短時間に操作が集中しています。少し時間をおいてからお試しください。")
        return render_template("error.html", message=message), 429

    @app.errorhandler(500)
    def server_error(_err):
        return render_template("error.html", message="内部エラーが発生しました。時間をおいて再度お試しください。"), 500

    return app


def parse_generate_form(form: Any) -> Tuple[List[int], List[int], str, int]:
    favorite_numbers = read_box_numbers(form, "favorite", 5)
    avoided_numbers = read_box_numbers(form, "avoid", 5)
    avoided_set = set(avoided_numbers)
    favorite_numbers = [n for n in favorite_numbers if n not in avoided_set]

    mode = str(form.get("mode", "all"))
    if mode not in MODE_IDS:
        mode = "all"

    try:
        count = int(form.get("count", 5))
    except Exception:
        count = 5
    settings = load_json("config/app_settings.json")
    max_count = int(settings.get("max_ticket_count", 10))
    count = max(1, min(count, max_count))

    seed = str(form.get("seed", "")).strip()
    if seed:
        try:
            random.seed(int(seed))
        except ValueError:
            random.seed(seed)

    return favorite_numbers, avoided_numbers, mode, count


def read_box_numbers(form: Any, prefix: str, max_count: int) -> List[int]:
    values: List[str] = []
    for idx in range(1, max_count + 1):
        values.append(str(form.get(f"{prefix}_{idx}", "")).strip())
    return clean_number_list(",".join(v for v in values if v))[:max_count]


def load_number_stats() -> List[Dict[str, Any]]:
    settings = load_json("config/app_settings.json")
    rows = read_csv_dicts(settings.get("number_stats_path", "data/processed/number_stats.csv"))
    if not rows:
        raise RuntimeError("number_stats.csv が空です。")
    return rows


def generate_ticket_rows(
    favorite_numbers: List[int],
    avoided_numbers: List[int],
    mode: str,
    count: int,
) -> List[Dict[str, Any]]:
    mode_rules = load_json("config/mode_rules.json")
    balance_rules = load_json("config/balance_rules.json")
    number_stats = load_number_stats()
    pools = build_pools(number_stats, favorite_numbers, avoided_numbers)
    modes = list(mode_rules.keys()) if mode == "all" else [mode]

    tickets: List[Dict[str, Any]] = []
    for mode_id in modes:
        tickets.extend(
            generate_tickets(
                mode_id=mode_id,
                ticket_count=count,
                pools=pools,
                number_stats=number_stats,
                mode_rules=mode_rules,
                balance_rules=balance_rules,
                favorite_numbers=favorite_numbers,
            )
        )

    if not tickets:
        raise RuntimeError("買い目を生成できませんでした。避けたい数字を減らすか、口数を少なくしてください。")
    return flatten_tickets(tickets, favorite_numbers, avoided_numbers)


def flatten_tickets(
    tickets: List[Dict[str, Any]],
    user_numbers: List[int],
    avoided_numbers: List[int],
) -> List[Dict[str, Any]]:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows: List[Dict[str, Any]] = []
    for idx, ticket in enumerate(tickets, start=1):
        nums = [int(n) for n in ticket["numbers"]]
        row = {
            "ticket_id": f"web_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx:03d}",
            "generated_at": generated_at,
            "mode_id": ticket.get("mode_id", ""),
            "mode_name": ticket.get("mode_name", ""),
            "mode_name_ja": ticket.get("mode_name_ja", ""),
            "user_numbers": ",".join(str(n) for n in user_numbers),
            "avoided_numbers": ",".join(str(n) for n in avoided_numbers),
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
            "personal_hit_count": ticket.get("personal_hit_count", ""),
            "data_score_avg": ticket.get("data_score_avg", ""),
            "balance_fit_score": ticket.get("balance_fit_score", ""),
            "personal_fit_score": ticket.get("personal_fit_score", ""),
            "uniqueness_score": ticket.get("uniqueness_score", ""),
            "ticket_score": ticket.get("ticket_score", ""),
            "reason": ticket.get("reason", ""),
        }
        rows.append(row)
    return rows


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


def enforce_rate_limit(app: Flask) -> None:
    limit = int(app.config.get("RATE_LIMIT_PER_MINUTE", 30))
    if limit <= 0:
        return
    key = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    now = time.time()
    window_start = now - 60
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
