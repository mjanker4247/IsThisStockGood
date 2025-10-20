"""Internationalization helpers and translations for the IsThisStockGood web UI."""

from __future__ import annotations

"""Internationalization helpers and translations for the web UI."""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Language:
    """Information about a supported language."""

    code: str
    label: str
    locale: str


SUPPORTED_LANGUAGES: Dict[str, Language] = {
    "en": Language(code="en", label="English", locale="en-US"),
    "de": Language(code="de", label="Deutsch", locale="de-DE"),
}

TRANSLATIONS: Dict[str, Dict[str, object]] = {
    "en": {
        "meta": {"lang_code": "en", "locale": "en-US"},
        "global": {
            "page_title": "Is This Stock Good?",
            "skip_to_main": "Skip to main content",
            "language_label": "Language",
            "language_switcher_aria": "Select application language",
            "loading": "Loading",
            "language_prompt": "Choose language",
            "language_confirmation": "Use this language",
        },
        "search": {
            "heading": "Analyze a Ticker",
            "helper": "Enter a valid ticker symbol (letters and optional dot or hyphen).",
            "label": "Ticker symbol",
            "placeholder": "e.g. AAPL",
            "button": "Analyze",
            "button_aria": "Analyze ticker",
            "helper_detail": "Up to five letters with an optional dot or hyphen suffix.",
        },
        "sections": {
            "meaning": {
                "title": "Meaning",
                "tooltip": (
                    "The first 'M' in Rule #1 investing is 'meaning'. For more information, read "
                    "chapter 3 from Rule #1 'Buy a Business; Not a Stock'. The goal of this step is "
                    "to determine if you'd want to own the entire business, if you could. And also if "
                    "you understand it enough that you'd be comfortable owning the entire business."
                ),
            },
            "moat": {
                "title": "Moat",
                "tooltip": (
                    "The second 'M' in Rule #1 investing is 'moat'. For more information, read chapter "
                    "4 from Rule #1 'Buying a Wonderful Business'. The goal of this step is to "
                    "determine if the company has a durable competitive advantage that protects it "
                    "from competitors."
                ),
                "tables": {
                    "roic": "ROIC (%)",
                    "equity": "Equity/BVPS Growth Rate (%)",
                    "eps": "EPS Growth Rate (%)",
                    "sales": "Sales/Revenue Growth Rate (%)",
                    "cash": "Free Cash Flow Growth Rate (%)",
                    "max": "Max",
                    "five_year": "5 year",
                    "three_year": "3 year",
                    "one_year": "1 year",
                },
            },
            "financial": {
                "heading": "Financial Trends Overview",
                "description": "Track how key financial metrics evolve across one, three, five year, and maximum time horizons.",
                "summary_prompt": "Enter a ticker to visualize trends for EPS, sales, equity, cash flow, and ROIC growth rates.",
            },
            "management": {
                "title": "Management",
                "tooltip": (
                    "The third 'M' in Rule #1 investing is 'management'. For more information, read "
                    "chapter 6 from Rule #1 'The Big Five Numbers'. The goal of this step is to "
                    "evaluate whether management is acting in the shareholders' best interest and to "
                    "understand how they are managing the company's resources."
                ),
                "tables": {
                    "cash_flow_caption": "Cash flow and debt metrics",
                    "long_term_debt": "Long term debt",
                    "free_cash_flow": "Free cash flow",
                    "years_to_pay": "Years to pay off debt",
                    "de_ratio_caption": "Debt to equity ratio",
                    "de_ratio": "Debt-to-Equity Ratio (Most recent quarter)",
                },
            },
            "margin_of_safety": {
                "title": "Margin of Safety",
                "tooltip": (
                    "The fourth 'M' in Rule #1 investing is 'margin of safety'. For more information, read "
                    "chapter 9 from Rule #1 'Stick to the Fundamentals'. The goal of this step is to "
                    "estimate the company's intrinsic value and compare it with the current market price."
                ),
                "tables": {
                    "sticker_caption": "Sticker price estimation",
                    "sticker": "Sticker Price",
                    "mos_caption": "Margin of safety valuation",
                    "mos_price": "Margin of Safety price",
                    "current_price_caption": "Current market price",
                    "current_price": "Current Price",
                },
            },
            "payback_time": {
                "title": "Payback Time",
                "tooltip": (
                    "Payback time estimates how long it would take for your investment to return its "
                    "initial cost through earnings."
                ),
                "tables": {
                    "caption": "Payback time results",
                    "header": "Payback Time (years)",
                },
            },
            "ten_cap": {
                "title": "10 Cap",
                "tooltip": (
                    "The 10 cap price estimates a fair purchase price based on free cash flow relative to "
                    "the company's market capitalization."
                ),
                "tables": {
                    "caption": "10 cap price estimation",
                    "header": "10 Cap Price",
                },
            },
            "market_cap": {
                "title": "Market Cap",
                "tooltip": (
                    "Market capitalization and trading volume help assess whether the company is large "
                    "enough and liquid enough for your portfolio."
                ),
                "tables": {
                    "average_volume_caption": "Average trading volume",
                    "average_volume": "Average Volume",
                    "shares_caption": "Maximum number of shares to hold",
                    "shares": "Max Shares to Hold",
                },
            },
        },
        "footer": {
            "disclaimer_heading": "Disclaimer",
            "disclaimer_text": (
                "This site is intended for personal investing use and should be used at your own discretion. "
                "There are never any guarantees in investing, so please use your best judgement when researching "
                "stocks to invest in. This site is simply one tool that may help you in your investment decisions. "
                "The calculations on this site are derived from the {rule_one_link} investing book by Phil Town. I highly "
                "recommend reading that book before interpreting any of the metrics calculated on this site. Also, "
                "for the sake of transparency, this entire site is open source on GitHub. Feel free to dig into the "
                "code yourself if you have any questions regarding the exact calculations used."
            ),
            "disclaimer_link_text": "Rule #1",
        },
        "js": {
            "chart_labels": ["1 Year", "3 Year", "5 Year", "Max"],
            "chart_dataset_labels": {
                "eps": "EPS Growth",
                "sales": "Sales Growth",
                "equity": "Equity Growth",
                "cash": "Cash Flow Growth",
                "roic": "ROIC",
            },
            "chart_axis": "Growth (%)",
            "chart_tooltip_no_data": "No data",
            "summary_prompt": "Financial trend data will appear here after a successful search.",
            "summary_unavailable": "Financial trend data is unavailable for this company.",
            "summary_prefix": "1-year growth snapshot:",
            "summary_metric_labels": {
                "eps": "EPS",
                "sales": "Sales",
                "equity": "Equity",
                "cash": "Cash Flow",
                "roic": "ROIC",
            },
            "summary_one_year_suffix": " (1Y)",
            "errors": {
                "ticker_required": "Ticker is required.",
                "ticker_invalid": "Please enter a valid ticker (letters with optional dot or hyphen).",
                "response_unprocessable": "We were unable to process the response. Please try again.",
                "unexpected": "There was an unexpected error. Please try again.",
                "network": "Network connection lost. Check your internet connection and try again.",
                "status_code": "There was an error (code {status}). Please try again shortly.",
            },
            "loading": "Loading",
            "analyzing": "Analyzing {ticker}",
            "negative_cash_flow": "Negative Cash Flow",
            "undefined": "Undefined",
            "not_available": "N/A",
        },
        "api": {
            "invalid_ticker": "Invalid ticker symbol",
        },
    },
    "de": {
        "meta": {"lang_code": "de", "locale": "de-DE"},
        "global": {
            "page_title": "Ist diese Aktie gut?",
            "skip_to_main": "Zum Hauptinhalt springen",
            "language_label": "Sprache",
            "language_switcher_aria": "Anwendungssprache auswählen",
            "loading": "Laden",
            "language_prompt": "Sprache auswählen",
            "language_confirmation": "Diese Sprache verwenden",
        },
        "search": {
            "heading": "Ticker analysieren",
            "helper": "Geben Sie ein gültiges Tickersymbol ein (Buchstaben und optionaler Punkt oder Bindestrich).",
            "label": "Tickersymbol",
            "placeholder": "z. B. AAPL",
            "button": "Analysieren",
            "button_aria": "Ticker analysieren",
            "helper_detail": "Bis zu fünf Buchstaben mit optionalem Punkt- oder Bindestrich-Suffix.",
        },
        "sections": {
            "meaning": {
                "title": "Bedeutung",
                "tooltip": (
                    "Das erste \"M\" beim Rule-#1-Investieren steht für \"Meaning\" (Bedeutung). Mehr dazu finden Sie in Kapitel 3 "
                    "von Rule #1 \"Buy a Business; Not a Stock\". Ziel dieses Schrittes ist es festzustellen, ob Sie das gesamte "
                    "Unternehmen besitzen möchten, wenn Sie könnten, und ob Sie es gut genug verstehen, um sich damit wohlzufühlen."
                ),
            },
            "moat": {
                "title": "Burggraben",
                "tooltip": (
                    "Das zweite \"M\" beim Rule-#1-Investieren steht für \"Moat\" (Burggraben). Mehr dazu finden Sie in Kapitel 4 "
                    "von Rule #1 \"Buying a Wonderful Business\". Ziel dieses Schrittes ist es festzustellen, ob das Unternehmen "
                    "einen dauerhaften Wettbewerbsvorteil besitzt, der es vor Konkurrenten schützt."
                ),
                "tables": {
                    "roic": "ROIC (%)",
                    "equity": "Eigenkapital/BVPS-Wachstumsrate (%)",
                    "eps": "EPS-Wachstumsrate (%)",
                    "sales": "Umsatz-/Erlöswachstumsrate (%)",
                    "cash": "Free-Cashflow-Wachstumsrate (%)",
                    "max": "Max",
                    "five_year": "5 Jahre",
                    "three_year": "3 Jahre",
                    "one_year": "1 Jahr",
                },
            },
            "financial": {
                "heading": "Überblick über finanzielle Trends",
                "description": "Verfolgen Sie, wie sich wichtige Finanzkennzahlen über ein, drei, fünf Jahre und den gesamten Zeitraum entwickeln.",
                "summary_prompt": "Geben Sie einen Ticker ein, um Trends für EPS-, Umsatz-, Eigenkapital-, Cashflow- und ROIC-Wachstumsraten zu visualisieren.",
            },
            "management": {
                "title": "Management",
                "tooltip": (
                    "Das dritte \"M\" beim Rule-#1-Investieren steht für \"Management\". Mehr dazu finden Sie in Kapitel 6 von Rule #1 "
                    "\"The Big Five Numbers\". Ziel dieses Schrittes ist es zu bewerten, ob das Management im Sinne der Aktionäre handelt "
                    "und wie es die Ressourcen des Unternehmens steuert."
                ),
                "tables": {
                    "cash_flow_caption": "Cashflow- und Schuldenkennzahlen",
                    "long_term_debt": "Langfristige Schulden",
                    "free_cash_flow": "Freier Cashflow",
                    "years_to_pay": "Jahre zur Schuldentilgung",
                    "de_ratio_caption": "Verschuldungsgrad",
                    "de_ratio": "Verschuldungsgrad (letztes Quartal)",
                },
            },
            "margin_of_safety": {
                "title": "Sicherheitsmarge",
                "tooltip": (
                    "Das vierte \"M\" beim Rule-#1-Investieren steht für \"Margin of Safety\" (Sicherheitsmarge). Mehr dazu finden Sie in Kapitel 9 "
                    "von Rule #1 \"Stick to the Fundamentals\". Ziel dieses Schrittes ist es, den inneren Wert des Unternehmens zu schätzen "
                    "und ihn mit dem aktuellen Marktpreis zu vergleichen."
                ),
                "tables": {
                    "sticker_caption": "Schätzung des Stickerpreises",
                    "sticker": "Stickerpreis",
                    "mos_caption": "Bewertung der Sicherheitsmarge",
                    "mos_price": "Preis der Sicherheitsmarge",
                    "current_price_caption": "Aktueller Marktpreis",
                    "current_price": "Aktueller Preis",
                },
            },
            "payback_time": {
                "title": "Amortisationszeit",
                "tooltip": (
                    "Die Amortisationszeit schätzt, wie lange es dauert, bis Ihre Investition die anfänglichen Kosten durch Gewinne zurückverdient hat."
                ),
                "tables": {
                    "caption": "Ergebnisse der Amortisationszeit",
                    "header": "Amortisationszeit (Jahre)",
                },
            },
            "ten_cap": {
                "title": "10 Cap",
                "tooltip": (
                    "Der 10-Cap-Preis schätzt einen fairen Kaufpreis auf Grundlage des freien Cashflows im Verhältnis zur Marktkapitalisierung des Unternehmens."
                ),
                "tables": {
                    "caption": "Schätzung des 10-Cap-Preises",
                    "header": "10-Cap-Preis",
                },
            },
            "market_cap": {
                "title": "Marktkapitalisierung",
                "tooltip": (
                    "Marktkapitalisierung und Handelsvolumen helfen einzuschätzen, ob das Unternehmen groß und liquide genug für Ihr Portfolio ist."
                ),
                "tables": {
                    "average_volume_caption": "Durchschnittliches Handelsvolumen",
                    "average_volume": "Durchschnittsvolumen",
                    "shares_caption": "Maximale Anzahl zu haltender Aktien",
                    "shares": "Max. zu haltende Aktien",
                },
            },
        },
        "footer": {
            "disclaimer_heading": "Haftungsausschluss",
            "disclaimer_text": (
                "Diese Website ist für den persönlichen Gebrauch beim Investieren gedacht und sollte nach eigenem Ermessen genutzt werden. "
                "Beim Investieren gibt es niemals Garantien. Bitte wenden Sie Ihr bestmögliches Urteilsvermögen an, wenn Sie Aktien für Ihre "
                "Investitionen recherchieren. Diese Website ist lediglich ein Werkzeug, das Sie bei Ihren Entscheidungen unterstützen kann. "
                "Die Berechnungen auf dieser Website basieren auf dem {rule_one_link} von Phil Town. Ich empfehle dringend, dieses Buch "
                "zu lesen, bevor Sie die auf dieser Website berechneten Kennzahlen interpretieren. Außerdem ist diese Website der Transparenz halber "
                "komplett Open Source auf GitHub. Sie können sich den Code gern selbst ansehen, wenn Sie Fragen zu den verwendeten Berechnungen haben."
            ),
            "disclaimer_link_text": "Rule #1",
        },
        "js": {
            "chart_labels": ["1 Jahr", "3 Jahre", "5 Jahre", "Max"],
            "chart_dataset_labels": {
                "eps": "EPS-Wachstum",
                "sales": "Umsatzwachstum",
                "equity": "Eigenkapitalwachstum",
                "cash": "Cashflow-Wachstum",
                "roic": "ROIC",
            },
            "chart_axis": "Wachstum (%)",
            "chart_tooltip_no_data": "Keine Daten",
            "summary_prompt": "Nach einer erfolgreichen Suche werden hier Finanztrends angezeigt.",
            "summary_unavailable": "Für dieses Unternehmen sind keine Finanztrends verfügbar.",
            "summary_prefix": "Überblick über das Wachstum im 1. Jahr:",
            "summary_metric_labels": {
                "eps": "EPS",
                "sales": "Umsatz",
                "equity": "Eigenkapital",
                "cash": "Cashflow",
                "roic": "ROIC",
            },
            "summary_one_year_suffix": " (1J)",
            "errors": {
                "ticker_required": "Ein Ticker wird benötigt.",
                "ticker_invalid": "Bitte geben Sie einen gültigen Ticker ein (Buchstaben mit optionalem Punkt oder Bindestrich).",
                "response_unprocessable": "Die Antwort konnte nicht verarbeitet werden. Bitte versuchen Sie es erneut.",
                "unexpected": "Es ist ein unerwarteter Fehler aufgetreten. Bitte versuchen Sie es erneut.",
                "network": "Netzwerkverbindung verloren. Prüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.",
                "status_code": "Es ist ein Fehler aufgetreten (Code {status}). Bitte versuchen Sie es in Kürze erneut.",
            },
            "loading": "Laden",
            "analyzing": "Analysiere {ticker}",
            "negative_cash_flow": "Negativer Cashflow",
            "undefined": "Nicht definiert",
            "not_available": "Nicht verfügbar",
        },
        "api": {
            "invalid_ticker": "Ungültiges Tickersymbol",
        },
    },
}


def get_language(language_code: str) -> Language:
    """Return metadata for the requested language, defaulting to English."""

    return SUPPORTED_LANGUAGES.get(language_code, SUPPORTED_LANGUAGES["en"])


def get_translations(language_code: str) -> Dict[str, object]:
    """Return translated strings for the requested language."""

    return TRANSLATIONS.get(language_code, TRANSLATIONS["en"])


__all__ = [
    "Language",
    "SUPPORTED_LANGUAGES",
    "TRANSLATIONS",
    "get_language",
    "get_translations",
]
