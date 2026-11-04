"""Long conversations stay light (spec 026, R-AG-M3).

Before each request, the tool results of turns older than the last two questions are replaced by
their one-line summary. No model call; the stored history stays complete, only what is sent
shrinks. The model keeps its own earlier answers, which already quote the figures that mattered."""

from dataclasses import replace

from app.modules.agent.engine.messages import Message

KEEP_QUESTIONS = 2
EARLIER = "[earlier result, summarised] "


def compact(history: list[Message], keep: int = KEEP_QUESTIONS) -> list[Message]:
    questions = [i for i, m in enumerate(history) if _is_question(m)]
    if len(questions) <= keep:
        return history
    cut = questions[-keep]
    return [_shrink(m) if i < cut else m for i, m in enumerate(history)]


def _is_question(message: Message) -> bool:
    return message.role == "user" and any(b.kind == "text" for b in message.blocks)


def _shrink(message: Message) -> Message:
    if not any(b.kind == "tool_result" for b in message.blocks):
        return message
    blocks = []
    for block in message.blocks:
        summary = (block.meta or {}).get("summary") if block.kind == "tool_result" else None
        if summary and len(block.text) > len(EARLIER) + len(summary):
            block = replace(block, text=EARLIER + summary)
        blocks.append(block)
    return Message(message.role, blocks)
