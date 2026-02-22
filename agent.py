"""
Release Note Agent — CLI entry point.

Usage:
    python agent.py [--poll N]

The main thread runs an async Claude SDK conversational loop.
A background daemon thread polls SQLite every N seconds, detects
RESOLVED→OPEN transitions, and removes those rows from the live .docx.
"""
import asyncio
import threading
import argparse
import sys
import re

from dotenv import load_dotenv
load_dotenv()

import anthropic
import db
import doc_generator

# ---------------------------------------------------------------------------
# Shared state (thread-safe via lock / Event)
# ---------------------------------------------------------------------------
shutdown_event = threading.Event()
doc_lock = threading.Lock()
active_label: str | None = None
status_cache: dict[int, str] = {}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are a Release Note Assistant. You help users generate and manage release notes.

When the user asks you to generate release notes for a specific label or version
(e.g. "generate release notes for v1.0"), include the token ACTION:GENERATE:<label>
on its own line somewhere in your response (replace <label> with the actual value,
e.g. ACTION:GENERATE:v1.0).

When the user asks to exit, quit, or shut down, include the token ACTION:SHUTDOWN
on its own line in your response.

Always give a brief, helpful conversational reply in addition to any action token.
"""

# ---------------------------------------------------------------------------
# Background polling thread
# ---------------------------------------------------------------------------
def poll_loop(interval: int) -> None:
    global status_cache, active_label

    while not shutdown_event.wait(interval):
        try:
            current = {d['id']: d['status'] for d in db.get_all_defects()}

            for defect_id, old_status in list(status_cache.items()):
                new_status = current.get(defect_id)
                if old_status == 'RESOLVED' and new_status == 'OPEN':
                    label = active_label
                    if label:
                        print(
                            f"\n[POLL] Defect {defect_id} reverted to OPEN — "
                            f"removing from '{label}' release notes...",
                            flush=True,
                        )
                        with doc_lock:
                            doc_generator.remove_row(label, defect_id)
                        print(
                            f"[POLL] Defect {defect_id} removed. "
                            f"Regenerating release notes for '{label}'...",
                            flush=True,
                        )
                        with doc_lock:
                            path = doc_generator.create_doc(label)
                        print(f"[POLL] Regenerated → {path}", flush=True)

            status_cache.update(current)
        except Exception as exc:
            print(f"\n[POLL ERROR] {exc}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _read_line(prompt: str = "> ") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: input(prompt))


def _handle_actions(assistant_text: str) -> None:
    global active_label

    # ACTION:GENERATE:<label>
    match = re.search(r'ACTION:GENERATE:(\S+)', assistant_text)
    if match:
        label = match.group(1)
        active_label = label
        print(f"\n[ACTION] Generating release notes for '{label}'...", flush=True)
        with doc_lock:
            try:
                path = doc_generator.create_doc(label)
                print(f"[ACTION] Saved → {path}", flush=True)
            except Exception as exc:
                print(f"[ACTION ERROR] {exc}", file=sys.stderr, flush=True)

    # ACTION:SHUTDOWN
    if 'ACTION:SHUTDOWN' in assistant_text:
        shutdown_event.set()


# ---------------------------------------------------------------------------
# Main async loop
# ---------------------------------------------------------------------------
async def main(poll_interval: int) -> None:
    # Initialise DB and seed status cache (no transitions on startup)
    db.init_db()
    global status_cache
    status_cache = {d['id']: d['status'] for d in db.get_all_defects()}

    # Start background polling thread
    threading.Thread(
        target=poll_loop,
        args=(poll_interval,),
        daemon=True,
        name="poll-thread",
    ).start()

    client = anthropic.AsyncAnthropic()
    messages: list[dict] = []

    print("Release Note Agent ready. Type a message to get started.")
    print("Example: 'Generate release notes for v1.0'")
    print("Type 'shutdown' or 'exit' to quit.\n")

    while not shutdown_event.is_set():
        # Read user input (non-blocking via executor)
        try:
            user_input = await _read_line("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nInterrupted — shutting down.", flush=True)
            shutdown_event.set()
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        # Stream response from Claude
        try:
            async with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                print("\nAssistant: ", end="", flush=True)
                async for chunk in stream.text_stream:
                    print(chunk, end="", flush=True)
                print("\n", flush=True)

                final = await stream.get_final_message()
                assistant_text = "".join(
                    block.text for block in final.content if block.type == "text"
                )

        except anthropic.APIError as exc:
            print(f"\n[API ERROR] {exc}", file=sys.stderr, flush=True)
            messages.pop()  # remove failed user turn
            continue

        messages.append({"role": "assistant", "content": assistant_text})
        _handle_actions(assistant_text)

    print("Agent shut down.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Release Note Agent")
    parser.add_argument(
        "--poll",
        type=int,
        default=10,
        metavar="N",
        help="Poll interval in seconds (default: 10)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.poll))
