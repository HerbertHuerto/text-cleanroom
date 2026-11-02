"""Preserve immutable spans locally; placeholders are not a watermark technique."""

import hashlib
import re

RESERVED = "[[TCI:"
TOKEN = re.compile(r"\[\[TCI:[0-9a-f]{12}:\d+\]\]")
MAX_PROTECTED_MATCHES = 10000


def protected_spans(text, phrases):
    """Union all occurrences, including overlapping/nested protected phrases."""
    spans = []
    for phrase in dict.fromkeys(phrases):
        if not isinstance(phrase, str) or not phrase:
            raise ValueError("protected strings must be nonempty")
        start = text.find(phrase)
        while start >= 0:
            if len(spans) >= MAX_PROTECTED_MATCHES:
                raise ValueError("more than 10,000 protected matches; select a smaller passage")
            spans.append((start, start + len(phrase)))
            start = text.find(phrase, start + 1)
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def freeze(original, phrases):
    if RESERVED in original:
        raise ValueError("input contains the reserved immutable-island marker")
    nonce = hashlib.sha256(original.encode("utf-8")).hexdigest()[:12]
    return [{"placeholder": f"{RESERVED}{nonce}:{index}]]", "text": original[start:end]}
            for index, (start, end) in enumerate(protected_spans(original, phrases))]


def restore(text, islands, require_all=False):
    """One pass: original fragments never become executable replacement templates."""
    values = {item["placeholder"]: item["text"] for item in islands}
    found = TOKEN.findall(text)
    if any(token not in values for token in found):
        raise ValueError("unknown immutable-island marker")
    if require_all and (len(found) != len(values) or set(found) != set(values)):
        raise ValueError("every immutable island must occur exactly once")
    unmarked = TOKEN.sub("", text)
    if RESERVED in unmarked:
        raise ValueError("malformed immutable-island marker")
    return TOKEN.sub(lambda match: values[match[0]], text)


def restore_result(candidate, mapping, islands):
    candidate = restore(candidate, islands, require_all=True)
    mapping = [{**item, "candidate_quote": restore(item["candidate_quote"], islands)} for item in mapping]
    if any(item["candidate_quote"] not in candidate for item in mapping):
        raise ValueError("restored fact-map locator is absent from candidate")
    return candidate, mapping
