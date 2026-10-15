"""Read diary emotion fields against content/emotion_vocabulary.json.

Diaries keep up to three emotions in the order chosen, joined by "、"; the first is the main
emotion and the only one the intensity refers to. A word the participant typed is stored as
"词（类名）" with the category they picked, so statistics can count it in that category. Older
single-word records parse the same way. Categories follow emotion_annotation_ontology.json.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from database import load_content_json

SEPARATOR = "、"
_CUSTOM_PATTERN = re.compile(r"^(?P<word>[^（）]+)（(?P<label>[^（）]+)）$")
_FORBIDDEN_IN_WORD = re.compile(r"[、（）()：:\s]")


@dataclass(frozen=True)
class EmotionEntry:
    word: str
    code: str
    label: str
    custom: bool


class EmotionVocabulary:
    def __init__(self, payload: dict) -> None:
        self.max_selected = int(payload.get("max_selected") or 3)
        self.custom_word_max_length = int(payload.get("custom_word_max_length") or 8)
        unknown = payload.get("unknown") or {}
        self.unknown_code = str(unknown.get("code") or "unknown")
        self.unknown_label = str(unknown.get("label") or "说不清")
        self._labels: dict[str, str] = {self.unknown_code: self.unknown_label}
        self._words: dict[str, dict[str, str]] = {"parent": {}, "child": {}}
        for category in payload.get("categories", []):
            code, label = str(category["code"]), str(category["label"])
            self._labels[code] = label
            for role in ("parent", "child"):
                for word in category.get(f"{role}_words", []):
                    self._words[role][str(word)] = code
        for word in [*unknown.get("child_words", []), *unknown.get("aliases", [])]:
            for role in ("parent", "child"):
                self._words[role].setdefault(str(word), self.unknown_code)
        self._codes_by_label = {label: code for code, label in self._labels.items()}

    def label(self, code: str) -> str:
        return self._labels.get(code, self.unknown_label)

    def _code_for_word(self, word: str, role: str) -> str | None:
        other = "child" if role == "parent" else "parent"
        return self._words[role].get(word) or self._words[other].get(word)

    def parse(self, stored, role: str = "parent") -> list[EmotionEntry]:
        entries: list[EmotionEntry] = []
        seen: set[str] = set()
        for token in str(stored or "").split(SEPARATOR):
            token = token.strip()
            if not token:
                continue
            custom = _CUSTOM_PATTERN.match(token)
            if custom and custom.group("label") in self._codes_by_label:
                word = custom.group("word").strip()
                code = self._codes_by_label[custom.group("label")]
                entry = EmotionEntry(word, code, self.label(code), True)
            else:
                code = self._code_for_word(token, role)
                entry = EmotionEntry(token, code or self.unknown_code, self.label(code or self.unknown_code), code is None)
            if entry.word not in seen:
                seen.add(entry.word)
                entries.append(entry)
        return entries

    def primary_label(self, stored, role: str = "parent") -> str:
        """Category label of the main (first) emotion; empty when nothing was recorded."""

        entries = self.parse(stored, role)
        return entries[0].label if entries else ""

    def labels(self, stored, role: str = "parent") -> list[str]:
        result: list[str] = []
        for entry in self.parse(stored, role):
            if entry.label not in result:
                result.append(entry.label)
        return result

    def display(self, stored, role: str = "parent") -> str:
        """The chosen words without the stored category suffix, for participant-facing text."""

        return SEPARATOR.join(entry.word for entry in self.parse(stored, role))

    def count_words(self, values, role: str = "parent") -> Counter[str]:
        """Count every chosen word across records, e.g. for "本周常见"."""

        counts: Counter[str] = Counter()
        for stored in values:
            counts.update(entry.word for entry in self.parse(stored, role))
        return counts

    def validation_error(self, stored, role: str = "parent") -> str | None:
        tokens = [token.strip() for token in str(stored or "").split(SEPARATOR) if token.strip()]
        if len(tokens) > self.max_selected:
            return f"情绪最多选 {self.max_selected} 个"
        for token in tokens:
            custom = _CUSTOM_PATTERN.match(token)
            if custom is None:
                continue
            word = custom.group("word").strip()
            if custom.group("label") not in self._codes_by_label:
                return "自己填写的情绪需要选一个最接近的类别"
            if not word or len(word) > self.custom_word_max_length or _FORBIDDEN_IN_WORD.search(word):
                return f"自己填写的情绪词最多 {self.custom_word_max_length} 个字，不能包含标点或空格"
        return None


def load_emotion_vocabulary() -> EmotionVocabulary:
    return EmotionVocabulary(load_content_json("emotion_vocabulary.json"))
