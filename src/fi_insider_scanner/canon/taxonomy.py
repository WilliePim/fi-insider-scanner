"""Tassonomie del registro: Karaktär, Handelsplats, Befattning, Instrumenttyp.

Tutti i valori osservati devono mappare (test snapshot). Un valore sconosciuto
diventa UNMAPPED e non può mai essere segnale.
"""

from __future__ import annotations

import re
from enum import StrEnum


def _norm(s: str | None) -> str:
    s = (s or "").replace("–", "-").replace("—", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip().casefold()


class TxnKind(StrEnum):
    ACQ_PURCHASE = "acq_purchase"
    DISP_SALE = "disp_sale"
    SUBSCRIPTION = "subscription"
    GRANT = "grant"
    EXERCISE_IN = "exercise_in"
    EXERCISE_OUT = "exercise_out"
    GIFT_IN = "gift_in"
    GIFT_OUT = "gift_out"
    LOAN_OUT = "loan_out"
    LOAN_IN = "loan_in"
    LOAN_RETURN_IN = "loan_return_in"
    LOAN_RETURN_OUT = "loan_return_out"
    EXCHANGE_IN = "exchange_in"
    EXCHANGE_OUT = "exchange_out"
    CONVERSION_IN = "conversion_in"
    CONVERSION_OUT = "conversion_out"
    DIVIDEND_IN = "dividend_in"
    DIVIDEND_OUT = "dividend_out"
    REDEMPTION = "redemption"
    ISSUANCE = "issuance"
    PLEDGE = "pledge"
    PLEDGE_RELEASE = "pledge_release"
    MERGER_IN = "merger_in"
    MERGER_OUT = "merger_out"
    DEMERGER_IN = "demerger_in"
    DEMERGER_OUT = "demerger_out"
    INTERNAL_IN = "internal_in"
    INTERNAL_OUT = "internal_out"
    INHERITANCE_IN = "inheritance_in"
    INHERITANCE_OUT = "inheritance_out"
    DIVISION_IN = "division_in"
    DIVISION_OUT = "division_out"
    SHORT = "short"
    UNMAPPED = "unmapped"


K = TxnKind
KARAKTAR_MAP: dict[str, TxnKind] = {
    _norm(k): v
    for k, v in {
        "Förvärv": K.ACQ_PURCHASE,
        "Avyttring": K.DISP_SALE,
        "Teckning": K.SUBSCRIPTION,
        "Tilldelning": K.GRANT,
        "Lösen ökning": K.EXERCISE_IN,
        "Lösen minskning": K.EXERCISE_OUT,
        "Gåva mottagen": K.GIFT_IN,
        "Gåva lämnad": K.GIFT_OUT,
        "Lån utlåning": K.LOAN_OUT,
        "Lån mottaget": K.LOAN_IN,
        "Lån återgång ökning": K.LOAN_RETURN_IN,
        "Lån återgång minskning": K.LOAN_RETURN_OUT,
        "Utbyte ökning": K.EXCHANGE_IN,
        "Utbyte minskning": K.EXCHANGE_OUT,
        "Konvertering ökning": K.CONVERSION_IN,
        "Konvertering minskning": K.CONVERSION_OUT,
        "Utdelning mottagen": K.DIVIDEND_IN,
        "Utdelning lämnad": K.DIVIDEND_OUT,
        "Inlösen egenutfärdat instrument": K.REDEMPTION,
        "Utfärdande av instrument": K.ISSUANCE,
        "Pantsättning": K.PLEDGE,
        "Pantsättning åter": K.PLEDGE_RELEASE,
        "Fusion ökning": K.MERGER_IN,
        "Fusion minskning": K.MERGER_OUT,
        "Fission ökning": K.DEMERGER_IN,
        "Fission minskning": K.DEMERGER_OUT,
        "Interntransaktion - Förvärv": K.INTERNAL_IN,
        "Interntransaktion - Avyttring": K.INTERNAL_OUT,
        "Koncernintern överföring ökning": K.INTERNAL_IN,
        "Koncernintern överföring förvärv": K.INTERNAL_IN,
        "Koncernintern överföring minskning": K.INTERNAL_OUT,
        "Koncernintern överföring avyttring": K.INTERNAL_OUT,
        "Arv mottagen": K.INHERITANCE_IN,
        "Arv ökning": K.INHERITANCE_IN,
        "Arv lämnad": K.INHERITANCE_OUT,
        "Arv minskning": K.INHERITANCE_OUT,
        "Bodelning ökning": K.DIVISION_IN,
        "Bodelning förvärv": K.DIVISION_IN,
        "Bodelning minskning": K.DIVISION_OUT,
        "Bodelning avyttring": K.DIVISION_OUT,
        "Blankning": K.SHORT,
        # export en-GB
        "Acquisition": K.ACQ_PURCHASE,
        "Disposal": K.DISP_SALE,
        "Subscription": K.SUBSCRIPTION,
        "Allotment": K.GRANT,
    }.items()
}

_PLUS = {
    K.ACQ_PURCHASE, K.SUBSCRIPTION, K.GRANT, K.EXERCISE_IN, K.GIFT_IN, K.LOAN_IN, K.LOAN_RETURN_IN,
    K.EXCHANGE_IN, K.CONVERSION_IN, K.DIVIDEND_IN, K.MERGER_IN, K.DEMERGER_IN, K.INTERNAL_IN,
    K.INHERITANCE_IN, K.DIVISION_IN,
}
_MINUS = {
    K.DISP_SALE, K.EXERCISE_OUT, K.GIFT_OUT, K.LOAN_OUT, K.LOAN_RETURN_OUT, K.EXCHANGE_OUT,
    K.CONVERSION_OUT, K.DIVIDEND_OUT, K.MERGER_OUT, K.DEMERGER_OUT, K.INTERNAL_OUT,
    K.INHERITANCE_OUT, K.DIVISION_OUT, K.REDEMPTION, K.SHORT,
}

EXCLUSION_BY_KIND: dict[TxnKind, str] = {
    K.DISP_SALE: "sale",
    K.SUBSCRIPTION: "subscription",
    K.GRANT: "grant",
    K.EXERCISE_IN: "exercise",
    K.EXERCISE_OUT: "exercise",
    K.GIFT_IN: "gift",
    K.GIFT_OUT: "gift",
    K.EXCHANGE_IN: "conversion_exchange",
    K.EXCHANGE_OUT: "conversion_exchange",
    K.CONVERSION_IN: "conversion_exchange",
    K.CONVERSION_OUT: "conversion_exchange",
    K.INHERITANCE_IN: "inheritance_division",
    K.INHERITANCE_OUT: "inheritance_division",
    K.DIVISION_IN: "inheritance_division",
    K.DIVISION_OUT: "inheritance_division",
    K.MERGER_IN: "corporate_action",
    K.MERGER_OUT: "corporate_action",
    K.DEMERGER_IN: "corporate_action",
    K.DEMERGER_OUT: "corporate_action",
    K.DIVIDEND_IN: "corporate_action",
    K.DIVIDEND_OUT: "corporate_action",
    K.REDEMPTION: "corporate_action",
    K.ISSUANCE: "corporate_action",
    K.LOAN_OUT: "loan_pledge",
    K.LOAN_IN: "loan_pledge",
    K.LOAN_RETURN_IN: "loan_pledge",
    K.LOAN_RETURN_OUT: "loan_pledge",
    K.PLEDGE: "loan_pledge",
    K.PLEDGE_RELEASE: "loan_pledge",
    K.INTERNAL_IN: "internal_transfer",
    K.INTERNAL_OUT: "internal_transfer",
    K.SHORT: "short",
    K.UNMAPPED: "unmapped",
}


def txn_kind(raw: str | None) -> TxnKind:
    return KARAKTAR_MAP.get(_norm(raw), K.UNMAPPED)


def direction(kind: TxnKind) -> int:
    return 1 if kind in _PLUS else -1 if kind in _MINUS else 0


class VenueClass(StrEnum):
    XSTO = "xsto"
    FNSE = "fnse"
    SPOTLIGHT = "spotlight"
    NGM = "ngm"
    MTF_SI = "mtf_si"
    FOREIGN_EXCHANGE = "foreign_exchange"
    OTHER_VENUE = "other_venue"
    OFF_VENUE = "off_venue"
    UNKNOWN = "unknown"


_MTF_SI_RE = re.compile(
    r"SYSTEMATIC INTERNALI|\bSI\b|\bMTF\b|CBOE|AQUIS|TURQUOISE|DARK|BLOOMBERG|INTERACTIVE BROKERS|\bATS\b|"
    r"SEB ENSKILDA|HANDELSBANKEN|SWEDBANK|NORDEA|DANSKE|CARNEGIE|POSIT|EQUIDUCT|LIQUIDNET|\bUBS\b|GOLDMAN|"
    r"MORGAN|CITI|BARCLAYS|VIRTU|JANE STREET|\bXTX\b|OPTIVER|SUSQUEHANNA|BATS|CHI-X|INSTINET|KEPLER|"
    r"SIGMA X|FIDELITY|CROSSSTREAM|TOWER RESEARCH|DEUTSCHE BANK|CREDIT SUISSE|NASDAQ OMX EUROPE|INTERNET DIRECT-ACCESS"
)
_FOREIGN_RE = re.compile(
    r"TORONTO|\bTSX|OSLO|HELSINKI|COPENHAGEN|KØBENHAVN|LONDON|NEW YORK|NYSE|XETRA|FRANKFURT|EURONEXT|"
    r"\bSIX\b|WARSAW|ICELAND|TALLINN|RIGA|VILNIUS|\bOTC|ASX|AUSTRALIAN|BÖRSE|BORSE|BOERSE|BORSA|MADRID|VIENNA|"
    r"CANADIAN|\bCSE\b|VENTURE|TRADEGATE|MERKUR|NASDAQ CAPITAL MARKET|NORWEGIAN OVER THE COUNTER"
)
_OFF_RE = re.compile(r"UTANFÖR|OUTSIDE|OFF-EXCHANGE|NO MARKET|UNLISTED")


def venue_class(raw: str | None) -> VenueClass:
    u = (raw or "").replace(" ", " ").strip().upper()
    if not u:
        return VenueClass.UNKNOWN
    if _OFF_RE.search(u):
        return VenueClass.OFF_VENUE
    if "FIRST NORTH" in u:
        return VenueClass.FNSE
    if "SPOTLIGHT" in u or "AKTIETORGET" in u:
        return VenueClass.SPOTLIGHT
    if "NORDIC GROWTH MARKET" in u or "NORDIC SME" in u or "NORDIC MTF" in u or re.search(r"\bNGM\b", u):
        return VenueClass.NGM
    if "STOCKHOLM" in u and ("NASDAQ" in u or "OMX" in u):
        return VenueClass.XSTO
    if _MTF_SI_RE.search(u):
        return VenueClass.MTF_SI
    if _FOREIGN_RE.search(u):
        return VenueClass.FOREIGN_EXCHANGE
    return VenueClass.OTHER_VENUE


def is_on_venue(vc: VenueClass) -> bool:
    return vc not in (VenueClass.OFF_VENUE, VenueClass.UNKNOWN)


# --- Befattning -> ruoli --------------------------------------------------------------

_ROLE_RULES: list[tuple[str, re.Pattern]] = [
    ("employee_rep", re.compile(r"arbetstagarrepresentant|arbetstagarsuppleant|employee representative")),
    ("other_admin_body", re.compile(r"annan medlem i bolagets administrations")),
    ("deputy_ceo", re.compile(r"\b(vice|deputy|ställföreträdande|biträdande)\s*(vd|verkställande|ceo|managing director|chief executive)")),
    ("ceo", re.compile(r"verkställande direktör|\bvd\b|\bceo\b|managing director|chief executive")),
    ("cfo", re.compile(r"ekonomichef|finanschef|finansdirektör|\bcfo\b|chief financial|ekonomi\s*/|ekonomidirektör")),
    ("chair", re.compile(r"(?<!vice )(styrelse)?ordförande|chairman|\bchair\b")),
    ("deputy_board", re.compile(r"suppleant|board deputy|deputy board|alternate")),
    ("board", re.compile(
        r"styrelseledamot|styrelsemedlem|\bledamot\b|board member|member of the board|board of directors|"
        r"\bdirector\b|\bstyrelse\b|vice ordförande|adjungerad"
    )),
    ("other_exec", re.compile(
        r"annan ledande befattningshavare|koncernledning|ledningsgrupp|\bchef\b|chef\b|\bhead\b|\bcoo\b|\bcto\b|"
        r"\bcmo\b|\bcio\b|\bcco\b|\bcso\b|\bcpo\b|\bcdo\b|\bchro\b|general counsel|chefsjurist|affärsområde|"
        r"business area|president|\bvp\b|\bsvp\b|\bevp\b|direktör|officer|manager|controller|ec member|"
        r"management team|verkställande ledning|redovisningsansvarig"
    )),
    ("owner_keyword", re.compile(r"ägare|\bowner\b|grundare|founder|aktieägare|shareholder|10\s*\+?\s*%")),
]


def roles(raw: str | None) -> frozenset[str]:
    text = _norm(raw)
    found: set[str] = set()
    remaining = text
    for name, rx in _ROLE_RULES:
        if rx.search(remaining):
            found.add(name)
            if name in ("deputy_ceo", "employee_rep", "other_admin_body"):
                remaining = rx.sub(" ", remaining)
    if "employee_rep" in found:
        found.discard("board")
        found.discard("deputy_board")
    if found & {"ceo", "cfo", "deputy_ceo"}:
        found.discard("other_exec")
    return frozenset(found)


# --- Instrumenttyp ------------------------------------------------------------------------


class InstrumentType(StrEnum):
    SHARE = "share"
    WARRANT_SUB = "subscription_warrant"
    BTA = "bta"
    BTU = "btu"
    SUB_RIGHT = "subscription_right"
    OPTION = "option"
    WARRANT = "warrant"
    BOND = "bond"
    CONVERTIBLE = "convertible"
    DERIVATIVE_OTHER = "derivative_other"
    REDEMPTION_SHARE = "redemption_share"
    REDEMPTION_RIGHT = "redemption_right"
    INTERIM_SHARE = "interim_share"
    CAPITAL_CERT = "capital_certificate"
    DEPOSITARY = "depositary_receipt"
    EMISSION = "emission_allowance"


INSTRUMENT_MAP: dict[str, InstrumentType] = {
    _norm(k): v
    for k, v in {
        "Aktie": InstrumentType.SHARE,
        "Share": InstrumentType.SHARE,
        "Teckningsoption": InstrumentType.WARRANT_SUB,
        "BTA (betald tecknad aktie)": InstrumentType.BTA,
        "BTU (betald tecknad unit)": InstrumentType.BTU,
        "Teckningsrätt/Uniträtt": InstrumentType.SUB_RIGHT,
        "Teckningsrätt": InstrumentType.SUB_RIGHT,
        "Option": InstrumentType.OPTION,
        "Köpoption": InstrumentType.OPTION,
        "Säljoption": InstrumentType.OPTION,
        "Syntetisk option": InstrumentType.OPTION,
        "Warrant": InstrumentType.WARRANT,
        "Obligation": InstrumentType.BOND,
        "Företagscertifikat": InstrumentType.BOND,
        "Konvertibel": InstrumentType.CONVERTIBLE,
        "Övriga derivatkontrakt": InstrumentType.DERIVATIVE_OTHER,
        "Swap": InstrumentType.DERIVATIVE_OTHER,
        "Terminer": InstrumentType.DERIVATIVE_OTHER,
        "Finansiella kontrakt avseende prisdifferenser (CFD)": InstrumentType.DERIVATIVE_OTHER,
        "Inlösenaktie": InstrumentType.REDEMPTION_SHARE,
        "Inlösenrätt": InstrumentType.REDEMPTION_RIGHT,
        "Interimsaktie": InstrumentType.INTERIM_SHARE,
        "Kapitalandelsbevis": InstrumentType.CAPITAL_CERT,
        "Depåbevis": InstrumentType.DEPOSITARY,
        "Utsläppsrätt": InstrumentType.EMISSION,
        "Auktionerad produkt baserad på en utsläppsrätt": InstrumentType.EMISSION,
    }.items()
}

# Strumenti che segnalano un'emissione in corso (dilution veto / strutturale).
ISSUE_INSTRUMENTS = frozenset({InstrumentType.BTA, InstrumentType.BTU, InstrumentType.SUB_RIGHT, InstrumentType.INTERIM_SHARE})


def instrument_type(raw: str | None) -> InstrumentType | None:
    """None se vuoto; KeyError-safe: un valore sconosciuto non vuoto resta None (contato a parte)."""
    return INSTRUMENT_MAP.get(_norm(raw))


_NAME_RULES: list[tuple[InstrumentType, re.Pattern]] = [
    (InstrumentType.BTA, re.compile(r"\bbta\b|betald tecknad aktie")),
    (InstrumentType.BTU, re.compile(r"\bbtu\b|betald tecknad unit")),
    (InstrumentType.WARRANT_SUB, re.compile(r"teckningsoption|\bto\s?\d|\bto\b|\bwarrants? (series|serie)|optionsrätt")),
    (InstrumentType.SUB_RIGHT, re.compile(r"teckningsrätt|uniträtt|\btr\b|\bur\b|subscription right")),
    (InstrumentType.INTERIM_SHARE, re.compile(r"interimsaktie|\bia\b")),
    (InstrumentType.CONVERTIBLE, re.compile(r"konvertib|\bkv\b|convertible")),
    (InstrumentType.BOND, re.compile(r"obligation|\bbond\b|\bfrn\b|certifikat|\bnote\b")),
    (InstrumentType.REDEMPTION_SHARE, re.compile(r"inlösenaktie|\bia\b|\bir\b")),
    (InstrumentType.OPTION, re.compile(r"option|köpopt|säljopt|\bcall\b|\bput\b|\blti\b|aktiesparprogram|personaloption")),
    (InstrumentType.WARRANT, re.compile(r"warrant")),
    (InstrumentType.DEPOSITARY, re.compile(r"depåbevis|\bsdb\b|\bsdr\b")),
]


def instrument_type_from_name(name: str | None) -> InstrumentType | None:
    text = _norm(name)
    if not text:
        return None
    for itype, rx in _NAME_RULES:
        if rx.search(text):
            return itype
    return None
