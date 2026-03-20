# -*- coding: utf-8 -*-
# SearchBoost: AI-Powered Semantic Search & Reliability Engine
# Copyright (C) 2026 Nikolaos Alexandrakis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# ---------------------------------------------------------------------
# COMMERCIAL USE NOTICE:
# For licensing outside the scope of AGPLv3, contact: nikolasalexandrakis.work@gmail.com
# ---------------------------------------------------------------------

import re
from dataclasses import dataclass, field

@dataclass
class PIIMatch:
    pattern_name: str
    matched_value: str

@dataclass
class PIIDetectionResult:
    contains_pii: bool
    matches: list[PIIMatch] = field(default_factory=list)

    def __bool__(self):
        return self.contains_pii


# ---------------------------------------------------------------------------
# PII pattern registry
# Each tuple is (human-readable name, compiled regex)
# Add new patterns here as needed — the detector picks them up automatically.
# ---------------------------------------------------------------------------
_PII_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "credit_card",
        # Visa, Mastercard, Amex, etc. — with or without dashes/spaces
        re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b")
    ),
    (
        "debit_card",
        # Visa, Mastercard, Amex, etc. — with or without dashes/spaces
        re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b")
    ),
    (
        "ssn",
        # US Social Security Number: 123-45-6789
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    ),
    (
        "iban",
        # International Bank Account Number: GB29NWBK60161331926819
        re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b")
    ),
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
    ),
    (
        "phone_number",
        # Matches +1 (555) 555-5555, 555-555-5555, 5555555555, etc.
        re.compile(r"\b(?:\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}\b")
    ),
    (
        "ipv4_address",
        # Private or public IPs can be PII in certain contexts
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    ),
    (
        "passport",
        # US passport numbers: 1-2 letters followed by 7 digits
        re.compile(r"\b[A-Z]{1,2}\d{7}\b")
    ),
    (
        "date_of_birth",
        # Common DOB patterns: DD/MM/YYYY, MM-DD-YYYY, YYYY.MM.DD, etc.
        re.compile(r"\b(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})\b")
    ),
]


class PIIDetector:
    """
    Scans text for common PII patterns before committing data to a shared cache.
    Acts as a hard gate: if ANY pattern matches, the text is considered unsafe to cache.

    Usage:
        detector = PIIDetector(logger=logger)
        result = detector.scan("Some text with 4111-1111-1111-1111 in it")
        if result.contains_pii:
            # skip cache
    """

    def __init__(self, logger=None):
        self.logger = logger

    def scan(self, text: str) -> PIIDetectionResult:
        """
        Scan `text` against all registered PII patterns.
        Returns a PIIDetectionResult describing every match found.
        Errs on the side of caution: a false positive skips the cache;
        a false negative would be a data leak.
        """
        if not text or not isinstance(text, str):
            return PIIDetectionResult(contains_pii=False)

        matches: list[PIIMatch] = []

        for name, pattern in _PII_PATTERNS:
            found = pattern.findall(text)
            for value in found:
                matches.append(PIIMatch(pattern_name=name, matched_value=value))

        result = PIIDetectionResult(contains_pii=bool(matches), matches=matches)

        if result.contains_pii and self.logger:
            detected_types = list({m.pattern_name for m in matches})
            self.logger.warning(
                f"PIIDetector: PII detected in text — types: {detected_types}. "
                f"Cache write BLOCKED for safety."
            )
        elif self.logger:
            self.logger.debug("PIIDetector: No PII detected. Text is safe to cache.")

        return result
