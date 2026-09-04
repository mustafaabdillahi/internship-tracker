from app.models.database_models import EmailRecord
from typing import Any
import html
import re
import string

HTML_CLEANER = re.compile("<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});", re.IGNORECASE)
STRUCTURAL_TAGS_CLEANER = re.compile( r"<\s*/?\s*(?:p|div|br)\b[^>]*>", re.IGNORECASE)
TEXT_CLEANER = re.compile(r"\s+")
MARKDOWN_LINK_CLEANER = re.compile(r"\[([^\]]+)\]\([^)]+\)")
MARKDOWN_BOLD_CLEANER = re.compile(r"\*\*(.*?)\*\*")
MARKDOWN_ITALIC_CLEANER = re.compile(r"(?<!\*)\*(?!\*)(.*?)\*(?!\*)")
URL_CLEANER = re.compile(r"https?://\S+")

SENTENCE_SPLITTER = re.compile(r"(?<=[.!?])\s+") # Used to split sentences on .!?
TRANSLATION_TABLE = str.maketrans("", "", string.punctuation) # Used to remove puncutation

POSITIVE_TERMS = [
    "application",
    "applied",
    "applying",
    "assessment",
    "assessments",
    "interview",
    "interviews",
    "offer",
    "rejected",
    "unsuccessful",
    "successful",
    "unfortunately",
    "next stage",
    "next stages",
    "next step",
    "next steps",
    "progress",
    "proceed",
    "needs",
    "candidate",
    "candidates",
    "recruitment",
    "complete",
    "submit",
    "schedule",
    "confirm",
    "deadline",
    "respond",
    "book",
    "attend",
]

NEGATIVE_TERMS = [
    "unsubscribe",
    "privacy policy",
    "terms and conditions",
    "cookie",
    "manage preferences",
    "regards"
]

BOILERPLATE_MARKERS = [
    "manage your preferences",
    "privacy policy",
    "terms and conditions",
    "view this email in your browser",
]


def phrase_exists(phrase: str, sentence: str) -> bool:
    """Determines whether a phrase is included in a sentence (excluding wrapping)."""
    pattern = rf"\b{re.escape(phrase)}\b"
    return bool(re.search(pattern, sentence))


def relevant_sentence(sentence: str) -> bool:
    """Determines whether a sentence in an email is revelant."""
    if any(phrase_exists(term, sentence) for term in NEGATIVE_TERMS):
        return False

    return any(phrase_exists(term, sentence) for term in POSITIVE_TERMS)


def contains_boilerplate(sentence: str) -> bool:
    """Determines whether a sentence containes a boilerplate marker."""
    return any(phrase_exists(marker, sentence) for marker in BOILERPLATE_MARKERS)


def prune_sentences(sentences: list[str]) -> list[str]:
    """Prunes sentences based on whether they are near a relevant sentence."""
    keep = set()

    for i, sentence in enumerate(sentences):
        s = sentence.lower().translate(TRANSLATION_TABLE)

        # Immediately stop if a sentence contains boilerplate words typically found at the end of an e-mail
        if contains_boilerplate(s):
            keep.discard(i)
            break

        # If relevant, add the sentence and the ones immediately before/after it
        if relevant_sentence(s):
            keep.add(i)
            if i > 0:
                keep.add(i-1)
            if i < len(sentences) - 1:
                keep.add(i+1)

    return [sentences[i] for i in sorted(keep)]


def prune_emails(emails: list[EmailRecord]) -> dict[int, dict[str, str]]:
    """Prunes emails to remove unnecessary information and HTML noise."""
    pruned = {}

    for email in emails:
        
        # Extract text from text/html field
        if email.raw_text is not None:
            text = html.unescape(email.raw_text)
        else:
            text = html.unescape(re.sub(
                HTML_CLEANER, " ",
                re.sub(STRUCTURAL_TAGS_CLEANER, "\n", email.raw_html) # type: ignore
            ).strip())

        # Use regex rules to clean text
        text = re.sub(TEXT_CLEANER, " ", html.unescape(text))
        text = re.sub(MARKDOWN_LINK_CLEANER, r"\1", text)
        text = re.sub(MARKDOWN_BOLD_CLEANER, r"\1", text)
        text = re.sub(MARKDOWN_ITALIC_CLEANER, r"\1", text)
        text = re.sub(URL_CLEANER, "", text).strip()

        # Remove duplicate headers
        while text.startswith(email.subject): # type: ignore
            text = text[len(email.subject):].lstrip() # type: ignore

        # Prune sentences semantically, then join together the remaining ones
        text = " ".join(prune_sentences(SENTENCE_SPLITTER.split(text))).strip()

        pruned[email.id] =  {
            "subject": email.subject,
            "text": text
        }

    return pruned
