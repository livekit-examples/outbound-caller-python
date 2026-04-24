"""
Bulk outbound call dispatcher.

Reads a spreadsheet of leads (Excel .xlsx or CSV) and dispatches outbound
calls to the running LiveKit agent worker. Each row becomes one call,
personalized with the prospect's name from the spreadsheet.

USAGE
-----
    # Dispatch every lead in the file:
    python dispatch_from_excel.py leads.xlsx

    # Validate the file without placing real calls:
    python dispatch_from_excel.py leads.xlsx --dry-run

    # Limit how many calls run in parallel (default 3):
    python dispatch_from_excel.py leads.csv --concurrency 5

    # Only dispatch the first N rows (great for testing):
    python dispatch_from_excel.py leads.xlsx --limit 1

REQUIRED COLUMNS
----------------
    name           Customer first name (used for personalization)
    phone_number   E.164 format, e.g. +15551234567

OPTIONAL COLUMNS
----------------
    transfer_to    Phone number to transfer to (falls back to
                   DEFAULT_TRANSFER_TO env var if absent)

PREREQUISITES
-------------
1. The agent worker must be running in another terminal:
       python agent.py start
2. .env.local must contain LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET.
3. For .xlsx support: pip install pandas openpyxl

OUTPUT
------
Results are appended to call_log.csv in the current directory with the
columns: timestamp, name, phone_number, status, dispatch_id, room, error.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("dispatcher")

# Must match the agent_name registered in agent.py's WorkerOptions.
AGENT_NAME = "outbound-caller"

DEFAULT_CONCURRENCY = 3
# Throttle between dispatches inside one worker slot, to avoid hammering
# the SIP trunk all at once.
DELAY_BETWEEN_DISPATCHES_SEC = 1.0
LOG_FILE = Path("call_log.csv")


def load_leads(path: Path) -> list[dict[str, str]]:
    """Read leads from .xlsx or .csv and normalize the columns."""
    suffix = path.suffix.lower()

    if suffix in (".xlsx", ".xls"):
        try:
            import pandas as pd
        except ImportError:
            raise SystemExit(
                "Reading Excel files requires pandas + openpyxl.\n"
                "Install with:  pip install pandas openpyxl"
            )
        df = pd.read_excel(path, dtype=str).fillna("")
        raw_rows: list[dict[str, Any]] = df.to_dict(orient="records")
    elif suffix == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as f:
            raw_rows = list(csv.DictReader(f))
    else:
        raise SystemExit(
            f"Unsupported file type: {suffix}. Use .xlsx, .xls, or .csv"
        )

    normalized: list[dict[str, str]] = []
    # Start at row 2 because row 1 is the header in user-facing terms.
    for i, row in enumerate(raw_rows, start=2):
        # Case-insensitive column lookup so 'Name', 'NAME', 'name' all work.
        lookup = {
            (k or "").strip().lower(): str(v or "").strip()
            for k, v in row.items()
            if k
        }
        name = lookup.get("name", "")
        phone = (
            lookup.get("phone_number")
            or lookup.get("phone")
            or lookup.get("number")
            or ""
        )
        transfer_to = lookup.get("transfer_to", "")

        if not phone:
            logger.warning(f"Row {i}: missing phone_number, skipping")
            continue

        if not name:
            logger.warning(f"Row {i}: missing name, defaulting to 'there'")
            name = "there"

        # Force E.164: must start with '+'.
        if not phone.startswith("+"):
            cleaned = "".join(c for c in phone if c.isdigit())
            if len(cleaned) == 10:
                # Assume US number.
                phone = "+1" + cleaned
            else:
                phone = "+" + cleaned
            logger.warning(
                f"Row {i}: phone normalized to {phone} "
                "(verify country code is correct)"
            )

        normalized.append(
            {
                "row": str(i),
                "name": name,
                "phone_number": phone,
                "transfer_to": transfer_to,
            }
        )

    return normalized


def append_log(entry: dict[str, str]) -> None:
    """Append a single result row to call_log.csv (creates header if new)."""
    new_file = not LOG_FILE.exists()
    fieldnames = [
        "timestamp",
        "name",
        "phone_number",
        "status",
        "dispatch_id",
        "room",
        "error",
    ]
    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if new_file:
            writer.writeheader()
        writer.writerow(entry)


async def dispatch_one(
    lk: api.LiveKitAPI | None,
    lead: dict[str, str],
    default_transfer: str,
    dry_run: bool,
) -> None:
    """Dispatch one outbound call for a single lead row."""
    transfer_to = lead["transfer_to"] or default_transfer
    metadata = {
        "name": lead["name"],
        "phone_number": lead["phone_number"],
        "transfer_to": transfer_to,
    }
    room_name = (
        f"outbound-{lead['phone_number'].lstrip('+')}-{uuid.uuid4().hex[:6]}"
    )

    log_entry: dict[str, str] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "name": lead["name"],
        "phone_number": lead["phone_number"],
        "status": "",
        "dispatch_id": "",
        "room": room_name,
        "error": "",
    }

    if dry_run or lk is None:
        logger.info(
            f"[DRY RUN] Would call {lead['name']} @ {lead['phone_number']} "
            f"(transfer_to={transfer_to or 'NONE'})"
        )
        log_entry["status"] = "dry_run"
        append_log(log_entry)
        return

    try:
        request = api.CreateAgentDispatchRequest(
            agent_name=AGENT_NAME,
            room=room_name,
            metadata=json.dumps(metadata),
        )
        dispatch = await lk.agent_dispatch.create_dispatch(request)
        logger.info(
            f"Dispatched -> {lead['name']} @ {lead['phone_number']} "
            f"(dispatch_id={dispatch.id})"
        )
        log_entry["status"] = "dispatched"
        log_entry["dispatch_id"] = dispatch.id
    except Exception as e:
        logger.error(
            f"Failed dispatch for {lead['name']} @ {lead['phone_number']}: {e}"
        )
        log_entry["status"] = "error"
        log_entry["error"] = str(e)

    append_log(log_entry)


async def run(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    leads = load_leads(path)
    if not leads:
        raise SystemExit("No valid leads found in file.")

    if args.limit and args.limit > 0:
        leads = leads[: args.limit]
        logger.info(f"--limit applied: only first {len(leads)} leads")

    logger.info(f"Loaded {len(leads)} leads from {path.name}")

    default_transfer = os.getenv("DEFAULT_TRANSFER_TO", "")
    missing_transfer = [l for l in leads if not l["transfer_to"]]
    if missing_transfer and not default_transfer:
        logger.warning(
            f"{len(missing_transfer)} rows have no transfer_to and "
            "DEFAULT_TRANSFER_TO is not set in .env.local — those calls "
            "will not be transferable."
        )

    # Confirm before placing live calls (skip if --yes or --dry-run).
    if not args.dry_run and not args.yes:
        print()
        print(f"About to dispatch {len(leads)} REAL phone calls.")
        print(f"Concurrency: {args.concurrency}")
        print(f"Default transfer: {default_transfer or '(none)'}")
        print()
        answer = input("Type 'yes' to proceed: ").strip().lower()
        if answer != "yes":
            raise SystemExit("Aborted.")

    lk: api.LiveKitAPI | None = None
    if not args.dry_run:
        # LiveKitAPI reads LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
        # from environment (loaded above from .env.local).
        lk = api.LiveKitAPI()

    semaphore = asyncio.Semaphore(args.concurrency)

    async def worker(lead: dict[str, str]) -> None:
        async with semaphore:
            await dispatch_one(lk, lead, default_transfer, args.dry_run)
            await asyncio.sleep(DELAY_BETWEEN_DISPATCHES_SEC)

    try:
        await asyncio.gather(*(worker(lead) for lead in leads))
    finally:
        if lk is not None:
            await lk.aclose()

    logger.info(f"Done. Results written to {LOG_FILE.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bulk dispatch outbound calls from an Excel/CSV file.",
    )
    parser.add_argument("file", help="Path to leads.xlsx or leads.csv")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=(
            f"Max simultaneous calls (default: {DEFAULT_CONCURRENCY}). "
            "Keep low until you trust your trunk capacity."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate the file without placing real calls.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only dispatch the first N rows. 0 = no limit.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation prompt.",
    )
    args = parser.parse_args()

    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
