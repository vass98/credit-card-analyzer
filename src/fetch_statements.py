import base64
from pathlib import Path

from auth import get_gmail_service
from config import ACCOUNT_STATEMENTS_DIR, BANK_ACCOUNTS, BANKS, STATEMENTS_DIR


def _download_pdf_attachments(service, message_id: str, bank: str, out_dir: Path) -> list[Path]:
    msg = service.users().messages().get(userId="me", id=message_id).execute()
    parts = msg.get("payload", {}).get("parts", []) or []
    saved = []

    for part in parts:
        filename = part.get("filename", "")
        if not filename.lower().endswith(".pdf"):
            continue

        attachment_id = part["body"].get("attachmentId")
        if not attachment_id:
            continue

        attachment = (
            service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )
        data = base64.urlsafe_b64decode(attachment["data"])

        out_path = out_dir / bank / f"{message_id}_{filename}"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if not out_path.exists():
            out_path.write_bytes(data)
        saved.append(out_path)

    return saved


def _fetch(bank_config: dict, out_dir: Path) -> dict[str, list[Path]]:
    service = get_gmail_service()
    results: dict[str, list[Path]] = {}

    for bank, cfg in bank_config.items():
        response = service.users().messages().list(userId="me", q=cfg["query"]).execute()
        message_ids = [m["id"] for m in response.get("messages", [])]

        saved_paths = []
        for message_id in message_ids:
            saved_paths.extend(_download_pdf_attachments(service, message_id, bank, out_dir))

        results[bank] = saved_paths
        print(f"[{bank}] found {len(message_ids)} emails, saved {len(saved_paths)} PDF(s)")

    return results


def fetch_all_statements() -> dict[str, list[Path]]:
    return _fetch(BANKS, STATEMENTS_DIR)


def fetch_all_account_statements() -> dict[str, list[Path]]:
    return _fetch(BANK_ACCOUNTS, ACCOUNT_STATEMENTS_DIR)


if __name__ == "__main__":
    fetch_all_statements()
