# Code-Style Arbeitsanweisung

## 1. Ziel

Dieses Dokument beschreibt die Code-Style-Regeln für das SPL-Meter-Projekt.

Das Ziel ist, dass der Code im gesamten Projekt einheitlich, lesbar, wartbar und testbar bleibt. Da das Projekt Echtzeit-Audiosignalverarbeitung auf einem Raspberry Pi Zero 2 W verwendet, sind neben allgemeinen Python-Regeln auch Performance-Regeln wichtig.

---

## 2. Allgemeine Python-Regeln

Der Python-Code soll sich an PEP 8 orientieren.

Wichtige Regeln:

- Funktionsnamen werden in `snake_case` geschrieben.
- Klassennamen werden in `PascalCase` geschrieben.
- Konstanten werden in `UPPER_CASE` geschrieben.
- Variablennamen sollen aussagekräftig sein.
- Funktionen sollen kurz und verständlich bleiben.
- Komplexe Berechnungen müssen kommentiert werden.
- Duplizierter Code soll vermieden werden.

## 3.

- In zeitkritischen Signalverarbeitungsfunktionen dürfen keine Python-Loops über einzelne Samples verwendet werden.

- Für wichtige Funktionen sollen Type Hints verwendet werden.

- Automatische Tools
black、ruff、pytest

- Definition of Done