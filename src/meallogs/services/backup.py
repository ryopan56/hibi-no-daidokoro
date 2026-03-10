import json
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction

from meallogs.constants import TIME_MINUTES_CHOICES
from meallogs.enums import IngredientCategory, TasteLevel
from meallogs.models import MealLog, MealLogIngredient, MealLogPhoto, MealLogTag, Tag

BACKUP_VERSION = 1
LOGS_JSON_PATH = "logs.json"
PHOTOS_DIR = "photos"
VALID_TASTE_LEVEL_CODES = {
    TasteLevel.to_code(value) for value, _ in TasteLevel.choices()
}
INGREDIENT_CATEGORY_CODE_TO_VALUE = {
    category.name: category.value for category in IngredientCategory
}


class BackupValidationError(Exception):
    pass


@dataclass(frozen=True)
class ParsedPhoto:
    path: str
    content: bytes


@dataclass(frozen=True)
class ParsedLog:
    log_date: date
    time_minutes: int | None
    taste_level: int | None
    ingredient_categories: list[int]
    tags: list[dict[str, str]]
    photos: list[ParsedPhoto]


def export_user_backup(user) -> bytes:
    meal_logs = (
        MealLog.objects.filter(user=user)
        .prefetch_related("ingredients", "tags", "photos")
        .order_by("log_date", "id")
    )

    payload_logs = []
    photo_sources: list[tuple[str, str]] = []

    for meal_log in meal_logs:
        log_date_str = meal_log.log_date.isoformat()
        ingredient_values = set(meal_log.ingredients.values_list("category", flat=True))
        photos_payload = []

        for photo in meal_log.photos.all():
            filename = PurePosixPath(photo.image.name).name
            archive_path = f"{PHOTOS_DIR}/{log_date_str}/{filename}"
            photos_payload.append({"path": archive_path})
            photo_sources.append((archive_path, photo.image.name))

        payload_logs.append(
            {
                "log_date": log_date_str,
                "time_minutes": meal_log.time_minutes,
                "taste_level": TasteLevel.to_code(meal_log.taste_level),
                "ingredient_categories": [
                    category.name
                    for category in IngredientCategory
                    if category.value in ingredient_values
                ],
                "tags": [
                    {"kind": tag.kind, "name": tag.name}
                    for tag in meal_log.tags.all().order_by("kind", "name", "id")
                ],
                "photos": photos_payload,
            }
        )

    payload = {
        "version": BACKUP_VERSION,
        "logs": payload_logs,
    }

    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(LOGS_JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2))
        archive.writestr(f"{PHOTOS_DIR}/", b"")
        for archive_path, storage_name in photo_sources:
            with default_storage.open(storage_name, "rb") as photo_file:
                archive.writestr(archive_path, photo_file.read())
    return buffer.getvalue()


def import_user_backup(user, uploaded_file) -> None:
    parsed_logs = _parse_backup(uploaded_file)
    old_file_names = list(
        MealLogPhoto.objects.filter(meal_log__user=user).values_list("image", flat=True)
    )
    created_file_names: list[str] = []

    try:
        with transaction.atomic():
            MealLog.objects.filter(user=user).delete()

            for parsed_log in parsed_logs:
                meal_log = MealLog.objects.create(
                    user=user,
                    log_date=parsed_log.log_date,
                    time_minutes=parsed_log.time_minutes,
                    taste_level=parsed_log.taste_level,
                )

                if parsed_log.ingredient_categories:
                    MealLogIngredient.objects.bulk_create(
                        [
                            MealLogIngredient(meal_log=meal_log, category=category)
                            for category in parsed_log.ingredient_categories
                        ]
                    )

                for tag_payload in parsed_log.tags:
                    tag, _ = Tag.objects.get_or_create(
                        kind=tag_payload["kind"],
                        name=tag_payload["name"],
                    )
                    MealLogTag.objects.get_or_create(meal_log=meal_log, tag=tag)

                for parsed_photo in parsed_log.photos:
                    photo = MealLogPhoto(meal_log=meal_log)
                    photo.image.save(
                        PurePosixPath(parsed_photo.path).name,
                        ContentFile(parsed_photo.content),
                        save=False,
                    )
                    created_file_names.append(photo.image.name)
                    photo.save()

            transaction.on_commit(lambda: _delete_files(old_file_names))
    except Exception:
        for created_file_name in created_file_names:
            default_storage.delete(created_file_name)
        raise


def _parse_backup(uploaded_file) -> list[ParsedLog]:
    try:
        with ZipFile(uploaded_file) as archive:
            normalized_names: set[str] = set()
            photo_contents: dict[str, bytes] = {}
            logs_json_bytes = None
            has_photos_dir = False

            for info in archive.infolist():
                normalized_path = _normalize_archive_path(info.filename)
                if normalized_path in normalized_names:
                    raise BackupValidationError("ZIP 内に重複したパスがあります。")
                normalized_names.add(normalized_path)

                if normalized_path == LOGS_JSON_PATH:
                    if info.is_dir():
                        raise BackupValidationError("logs.json の構造が不正です。")
                    logs_json_bytes = archive.read(info)
                    continue

                if normalized_path == PHOTOS_DIR:
                    if not info.is_dir():
                        raise BackupValidationError("photos ディレクトリの構造が不正です。")
                    has_photos_dir = True
                    continue

                if info.is_dir():
                    raise BackupValidationError("ZIP 内のディレクトリ構造が不正です。")

                if normalized_path.startswith(f"{PHOTOS_DIR}/"):
                    has_photos_dir = True
                    photo_contents[normalized_path] = archive.read(info)
                    continue

                raise BackupValidationError("ZIP 内に想定外のファイルがあります。")
    except BadZipFile as exc:
        raise BackupValidationError("ZIP ファイルを解凍できませんでした。") from exc

    if logs_json_bytes is None:
        raise BackupValidationError("logs.json が見つかりません。")
    if not has_photos_dir:
        raise BackupValidationError("photos ディレクトリが見つかりません。")

    try:
        payload = json.loads(logs_json_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackupValidationError("logs.json を読み取れませんでした。") from exc

    return _validate_payload(payload, photo_contents)


def _normalize_archive_path(path: str) -> str:
    if "\\" in path:
        raise BackupValidationError("ZIP 内のパス形式が不正です。")

    raw_path = path.rstrip("/")
    if not raw_path:
        raise BackupValidationError("ZIP 内のパス形式が不正です。")

    pure_path = PurePosixPath(raw_path)
    if pure_path.is_absolute() or any(part in (".", "..") for part in pure_path.parts):
        raise BackupValidationError("ZIP 内のパスが不正です。")

    normalized_path = pure_path.as_posix()
    if normalized_path in {LOGS_JSON_PATH, PHOTOS_DIR}:
        return normalized_path

    parts = pure_path.parts
    if len(parts) == 1:
        return normalized_path

    if len(parts) == 3 and parts[0] == PHOTOS_DIR and parts[1] and parts[2]:
        try:
            date.fromisoformat(parts[1])
        except ValueError as exc:
            raise BackupValidationError("photos 配下のパスが不正です。") from exc
        return normalized_path

    raise BackupValidationError("ZIP 内の構造が不正です。")


def _validate_payload(payload, photo_contents: dict[str, bytes]) -> list[ParsedLog]:
    if not isinstance(payload, dict):
        raise BackupValidationError("logs.json の形式が不正です。")
    if set(payload.keys()) != {"version", "logs"}:
        raise BackupValidationError("logs.json に想定外の項目があります。")
    if payload["version"] != BACKUP_VERSION:
        raise BackupValidationError("対応していないバックアップ形式です。")
    if not isinstance(payload["logs"], list):
        raise BackupValidationError("logs が不正です。")

    parsed_logs: list[ParsedLog] = []
    seen_dates: set[date] = set()
    referenced_photo_paths: set[str] = set()

    for log_payload in payload["logs"]:
        if not isinstance(log_payload, dict):
            raise BackupValidationError("ログ項目の形式が不正です。")
        if set(log_payload.keys()) != {
            "log_date",
            "time_minutes",
            "taste_level",
            "ingredient_categories",
            "tags",
            "photos",
        }:
            raise BackupValidationError("ログ項目に想定外の項目があります。")

        try:
            log_date = date.fromisoformat(log_payload["log_date"])
        except (TypeError, ValueError) as exc:
            raise BackupValidationError("log_date が不正です。") from exc
        if log_date in seen_dates:
            raise BackupValidationError("同じ日付のログが重複しています。")
        seen_dates.add(log_date)

        time_minutes = log_payload["time_minutes"]
        if time_minutes is not None and time_minutes not in TIME_MINUTES_CHOICES:
            raise BackupValidationError("time_minutes が不正です。")

        taste_level_code = log_payload["taste_level"]
        if taste_level_code is None:
            taste_level = None
        else:
            if (
                not isinstance(taste_level_code, str)
                or taste_level_code not in VALID_TASTE_LEVEL_CODES
            ):
                raise BackupValidationError("taste_level が不正です。")
            taste_level = TasteLevel.from_code(taste_level_code)

        ingredient_payload = log_payload["ingredient_categories"]
        if not isinstance(ingredient_payload, list):
            raise BackupValidationError("ingredient_categories が不正です。")
        if len(set(ingredient_payload)) != len(ingredient_payload):
            raise BackupValidationError("ingredient_categories が重複しています。")
        try:
            ingredient_categories = [
                INGREDIENT_CATEGORY_CODE_TO_VALUE[code] for code in ingredient_payload
            ]
        except KeyError as exc:
            raise BackupValidationError("ingredient_categories に不正な値があります。") from exc

        tags_payload = log_payload["tags"]
        if not isinstance(tags_payload, list):
            raise BackupValidationError("tags が不正です。")
        parsed_tags = []
        for tag_payload in tags_payload:
            if not isinstance(tag_payload, dict) or set(tag_payload.keys()) != {"kind", "name"}:
                raise BackupValidationError("tag の形式が不正です。")
            kind = tag_payload["kind"]
            name = tag_payload["name"]
            if (
                not isinstance(kind, str)
                or not isinstance(name, str)
                or not kind
                or not name
                or len(kind) > 32
                or len(name) > 64
            ):
                raise BackupValidationError("tag の値が不正です。")
            parsed_tags.append({"kind": kind, "name": name})

        photos_payload = log_payload["photos"]
        if not isinstance(photos_payload, list):
            raise BackupValidationError("photos が不正です。")
        parsed_photos = []
        for photo_payload in photos_payload:
            if not isinstance(photo_payload, dict) or set(photo_payload.keys()) != {"path"}:
                raise BackupValidationError("photo の形式が不正です。")
            photo_path = photo_payload["path"]
            if not isinstance(photo_path, str):
                raise BackupValidationError("photo path が不正です。")
            normalized_photo_path = _normalize_archive_path(photo_path)
            if not normalized_photo_path.startswith(f"{PHOTOS_DIR}/{log_date.isoformat()}/"):
                raise BackupValidationError("photo path と log_date が一致しません。")
            if normalized_photo_path not in photo_contents:
                raise BackupValidationError("ZIP 内に不足している写真があります。")
            if normalized_photo_path in referenced_photo_paths:
                raise BackupValidationError("photo path が重複しています。")
            referenced_photo_paths.add(normalized_photo_path)
            parsed_photos.append(
                ParsedPhoto(
                    path=normalized_photo_path,
                    content=photo_contents[normalized_photo_path],
                )
            )

        parsed_logs.append(
            ParsedLog(
                log_date=log_date,
                time_minutes=time_minutes,
                taste_level=taste_level,
                ingredient_categories=ingredient_categories,
                tags=parsed_tags,
                photos=parsed_photos,
            )
        )

    if referenced_photo_paths != set(photo_contents.keys()):
        raise BackupValidationError("ZIP 内に参照されていない写真があります。")

    return parsed_logs


def _delete_files(file_names: list[str]) -> None:
    for file_name in file_names:
        default_storage.delete(file_name)
