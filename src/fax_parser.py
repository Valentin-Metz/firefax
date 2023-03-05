import re
from pathlib import Path

import pyproj
import pytesseract
from pdf2image import convert_from_path


def transform_coordinates(x: float, y: float) -> (float, float):
    return pyproj.Transformer.from_crs('epsg:5684', 'WGS84').transform(x, y)


def escape_str_markdownv2(s: str) -> str:
    return re.sub(r"([_*\[\],()~`>#+-=|{}.!'])", r"\\\1", s)


class Einsatzort:
    @staticmethod
    def _parse_object(fax: str) -> str:
        match = re.search(r"OBJEKT ?:(.+?)EINSATZPLAN:", fax, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_strasse(fax: str) -> str:
        match = re.search(r"STRAßE:(.+?)ABSCHN[I|L]*?TT:", fax, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_abschnitt(fax: str) -> str:
        match = re.search(r"ABSCHN[I|L]*?TT:(.+?)KREUZUNG:", fax, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_kreuzung(fax: str) -> str:
        match = re.search(r"KREUZUNG:(.+?)ORTSTEIL/ORT:", fax, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_ortsteil(fax: str) -> str:
        match = re.search(r"ORTSTEIL/ORT:(.+?)WACHBEREICH:", fax, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_wachbereich(fax: str) -> str:
        match = re.search(r"WACHBEREICH:(.+?)KOORDINATEN:", fax, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_einsatzplan(fax: str) -> str:
        match = re.search(r"EINSATZPLAN:(.+?)MELDEBILD:", fax, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_koordinaten(fax: str) -> tuple[float, float] | None:
        match = re.search(r"KOORDINATEN:(.+)", fax)
        coordinate_string = match.group(1).strip() if match else ""
        if coordinate_string and len(coordinate_string.split('/')) == 2:
            x_y = coordinate_string.split('/')
            try:
                return transform_coordinates(float(x_y[0]), float(x_y[1]))
            except ValueError:
                return None

    def __init__(self, fax: str):
        self.objekt: str = self._parse_object(fax)

        self.strasse: str = self._parse_strasse(fax)
        self.abschnitt: str = self._parse_abschnitt(fax)
        self.kreuzung: str = self._parse_kreuzung(fax)

        self.ortsteil: str = self._parse_ortsteil(fax)
        self.wachbereich: str = self._parse_wachbereich(fax)

        self.einsatzplan: str = self._parse_einsatzplan(fax)

        self.koordinaten: tuple[float, float] | None = self._parse_koordinaten(fax)

    def __repr__(self):
        representation = ""

        if self.objekt:
            representation += escape_str_markdownv2(self.objekt) + '\n'

        if self.strasse:
            representation += escape_str_markdownv2(self.strasse) + '\n'
        if self.abschnitt:
            representation += escape_str_markdownv2(self.abschnitt) + '\n'
        if self.kreuzung:
            representation += escape_str_markdownv2(self.kreuzung) + '\n'

        if self.ortsteil:
            representation += escape_str_markdownv2(self.ortsteil) + '\n'
        if self.wachbereich:
            representation += escape_str_markdownv2(self.wachbereich) + '\n'

        if self.einsatzplan:
            representation += escape_str_markdownv2(self.einsatzplan) + '\n'

        if self.koordinaten:
            representation += f"[Koordinaten](https://www.google.com/maps/place/" \
                              f"{self.koordinaten[0]},{self.koordinaten[1]})" + '\n'

        return representation


class Fax:
    @staticmethod
    def _parse_einsatzstichwort(fax: str) -> str:
        match = re.search(r"TZSTICHWORT:(.+)", fax)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_meldebild(fax: str) -> str:
        match = re.search(r"MELDEBILD:(.+)", fax)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_hinweis(fax: str) -> str:
        match = re.search(r"HINWEIS:(.+?)EINSATZMITTEL", fax, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _parse_einsatzmittel(fax: str) -> [str]:
        match = re.search(r"EINSATZMITTEL(.+?)\(ALARMSCHREIBEN ENDE\)", fax, re.DOTALL)
        return [line for line in match.group(1).strip().split('\n') if line.strip()] if match else ""

    def __init__(self, fax: str):
        self.einsatzstichwort: str = self._parse_einsatzstichwort(fax)
        self.meldebild: str = self._parse_meldebild(fax)
        self.hinweis: str = self._parse_hinweis(fax)

        self.einsatzort: Einsatzort = Einsatzort(fax)

        self.einsatzmittel: [str] = self._parse_einsatzmittel(fax)

        self.text_raw = fax

    def __repr__(self):
        representation = "*FEUERWEHREINSATZ FFW\\-PELLHEIM*\n"

        representation += escape_str_markdownv2("--------------------\n")

        if self.einsatzstichwort:
            representation += escape_str_markdownv2(self.einsatzstichwort) + '\n'
        if self.meldebild:
            representation += '*' + escape_str_markdownv2(self.meldebild) + '*' + '\n'
        if self.hinweis:
            representation += escape_str_markdownv2(self.hinweis) + '\n'

        representation += escape_str_markdownv2("--------------------\n")

        representation += str(self.einsatzort)

        representation += escape_str_markdownv2("--------------------\n")

        for einsatzmittel in self.einsatzmittel:
            representation += escape_str_markdownv2(einsatzmittel) + '\n'

        return representation


def parse_fax(path: Path) -> Fax | None:
    doc = convert_from_path(path)
    txt = pytesseract.image_to_string(doc[0], lang="deu")
    if 'ALARMSCHREIBEN' in txt:
        return Fax(txt)
    return None
