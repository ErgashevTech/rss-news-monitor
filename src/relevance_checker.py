import re
import logging

logger = logging.getLogger(__name__)

# Keywords grouped by language.
# Russian keywords use stems to match inflected forms.
KEYWORDS: dict[str, list[str]] = {
    "en": [
        "visa",
        "migration",
        "migrant",
        "immigrant",
        "immigration",
        "border control",
        "border crossing",
        "border closure",
        "entry ban",
        "exit ban",
        "entry requirement",
        "customs rule",
        "customs regulation",
        "embassy",
        "consulate",
        "consular",
        "travel restriction",
        "travel ban",
        "travel advisory",
        "residence permit",
        "work permit",
        "deportation",
        "deported",
        "asylum",
        "refugee",
        "passport",
        "citizenship",
        "naturalization",
        "overstay",
    ],
    "ru": [
        "виз",            # виза, визовый, визовая, визовое, визовые, визы
        "миграци",        # миграция, миграционный, миграционная
        "мигрант",        # мигрант, мигранты, мигрантов
        "границ",         # граница, границы, границу
        "погранич",       # пограничный, пограничная, пограничном
        "въезд",          # въезд, въезда, въездная
        "выезд",          # выезд, выезда, выездная
        "таможн",         # таможня, таможенный, таможенные
        "посольств",      # посольство, посольства
        "консульств",     # консульство, консульства
        "депортаци",      # депортация, депортации
        "паспорт",        # паспорт, паспорта, паспортный
        "гражданств",     # гражданство, гражданства
        "беженц",         # беженец, беженцы, беженцев
        "беженк",         # беженка, беженки
        "убежищ",         # убежище, убежища
        "вид на жительство",
        "разрешение на работу",
        "пребыван",       # пребывание, пребывания
    ],
    "uz": [
        "viza",
        "migratsiya",
        "migrant",
        "muhojir",
        "muhojirlik",
        "chegara",
        "bojxona",
        "elchixona",
        "konsulxona",
        "deportatsiya",
        "pasport",
        "fuqarolik",
        "ruxsatnoma",
        "qochqin",
        "boshpana",
        "kirish taqiqi",
        "chiqish taqiqi",
        "sayohat cheklovi",
    ],
}

_HTML_TAG_RE = re.compile(r"<[^>]+>")


class RelevanceChecker:
    def __init__(self):
        self._all_keywords: list[str] = []
        for lang_keywords in KEYWORDS.values():
            self._all_keywords.extend(lang_keywords)
        # Sort longest-first so multi-word phrases match before their sub-parts.
        self._all_keywords.sort(key=len, reverse=True)
        logger.info(
            "RelevanceChecker initialized with %d keywords across %d languages",
            len(self._all_keywords),
            len(KEYWORDS),
        )

    def check(self, title: str, summary: str) -> tuple[bool, list[str]]:
        text = f"{title} {summary}"
        text = _HTML_TAG_RE.sub(" ", text)
        text_lower = text.lower()

        matched: list[str] = []
        for kw in self._all_keywords:
            if kw.lower() in text_lower:
                matched.append(kw)

        if matched:
            logger.info(
                "RELEVANT: '%s' — matched: %s",
                title[:80],
                matched[:5],
            )
        else:
            logger.debug("Not relevant: '%s'", title[:80])

        return bool(matched), matched
