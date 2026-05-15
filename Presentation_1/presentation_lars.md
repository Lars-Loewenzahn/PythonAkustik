---
marp: true
theme: default
paginate: true
style: |
  section {
    font-size: 1em;
  }
  h1 { font-size: 3em; }
  h2 { font-size: 2.4em; }
  h3 { font-size: 2em; }
  table { font-size: 1.8em; }
  code, pre { font-size: 1em; }
---

# SPL‑Meter – Anforderungen & Umsetzung

Anforderungen aus `W3/Anforderungen.md`, Pläne aus `W4/Vorschläge_anforderungen.ipynb`.

Legende: 🙂 leicht · 😐 mittel · 😓 anspruchsvoll · 😵 kritisch

---

| Anforderung | Unser Plan | S |
|---|---|---|
| REQ-FUNC-001 Digitaler Audioeingang (USB/I2S) | INMP441 via I2S; Kernel-Overlay aktivieren; ALSA `hw:0,0` / sounddevice testen | 😐 |
| REQ-FUNC-002 Echtzeit-SPL-Berechnung | Blockweise RMS/SPL; Verarbeitungs-Thread von GUI entkoppeln (Queue) | 😐 |
| REQ-FUNC-003 Zeitbewertungen F/S & Leq | Vektorisierte Filter (NumPy/SciPy); ggf. Cython/Numba; bei Bedarf Pi Zero 2 | 😓 |
| REQ-FUNC-004 Frequenzbewertungen A/Z | IIR-Filter mit verifizierten Koeffizienten implementieren | 😐 |
| REQ-FUNC-005 Oktav-/Terzbandanalyse | Filterbank; ggf. reduzierte Bänder oder Downsampling | 😵 |
| REQ-FUNC-006 Web-GUI | Streamlit-Minimal-UI: Live-Werte, Start/Stop, Konfiguration | 🙂 |

---

| Anforderung | Unser Plan | S |
|---|---|---|
| REQ-FUNC-007 JSON-Export | Dataclass-Schema + Export; gegen JSON-Schema validieren | 🙂 |
| REQ-FUNC-008 Kalibrierung 94 dB @ 1 kHz | Kalibrier-Workflow in GUI; Faktor speichern; Button + LED optional | 😐 |
| REQ-FUNC-009 CLI/TUI-Steuerung | HTTP-API + schlanker CLI-Client (SSH/seriell) | 🙂 |
| REQ-FUNC-010 Audioaufzeichnung | Ringpuffer + Schreib-Thread; WAV-Streaming | 😐 |
| REQ-FUNC-011 Integration „tapy“ | Bibliothek klären; Minimal-API definieren; PoC erstellen | 😐 |

---

| Anforderung | Unser Plan | S |
|---|---|---|
| REQ-PERF-001 Unterstützte Abtastraten | Blockgröße 2048–4096; NumPy vektorisiert; Audio-Prozess priorisieren; GUI entkoppeln | 😐 |
| REQ-PERF-002 Wortbreite/Datenpfad | 24‑bit in; intern float32 (2^31 Normierung); keine Überläufe | 🙂 |
| REQ-QUAL-001 Keine automatische Pegelregelung (AGC) | Fester Gain; Review/Tests sichern, dass keine AGC aktiv ist | 🙂 |
| REQ-INTF-001 Kommunikationsschnittstellen | WiFi/SSH + USB CDC; Steuerung via HTTP‑API | 🙂 |
| REQ-NET-001 Nutzung des WiFi-Chips | Pi Zero 2W WLAN für GUI/SSH nutzen | 🙂 |
| REQ-DATA-001 Checksummen für Datenintegrität | Sidecar .sha256 erzeugen; Prüfsummen‑CLI bereitstellen | 🙂 |

---


| Anforderung | Unser Plan | S |
|---|---|---|
| REQ-DATA-002 Speicherbedarf/-strategie | 12h SPL bei 10 Hz < 50 MB; optional Delta‑Encoding/Kompression | 🙂 |
| REQ-PWR-001 Energieversorgung | USB‑Betrieb; Option Powerbank ≥12 h | 🙂 |
| REQ-MECH-001 Gehäuse | Einfaches 3D‑Druck‑Gehäuse (Schutz, Anschlüsse frei) | 🙂 |
| REQ-UI-001 Kein lokales Display | Nur Web‑GUI; headless Start | 🙂 |
| REQ-MIC-001 Mikrofon | Single‑Channel ohne Richtkompensation | 🙂 |
| REQ-STD-001 Zeitgewichtungen gemäß IEC 61672‑2 | Prüfungen gemäß IEC 61672‑2; Toleranzen verifizieren | 😓 |

---

| Anforderung | Unser Plan | S |
|---|---|---|
| REQ-ARCH-001 Zustandsmaschine | transitions‑Lib; PlantUML‑Diagramm; robuste Übergänge | 🙂 |
| REQ-DIAG-001 Diagnosejobs pro Substate | Substate‑spezifische Selbsttests (Audio, Latenz, Storage) | 😐 |
| REQ-ERR-001 Fehlerbehandlung | Fehlerklassen + Recovery (Retry, Idle, Logs) | 😐 |
| REQ-VAL-001 Vergleich gegen Referenzgerät | Tests gegen NTi XL2; Ziel ≤ ±1 dB | 😐 |
| REQ-PROC-001 Lieferzyklen | 2‑wöchige Sprints, Reviews, Inkremente | 🙂 |
| REQ-LIC-001 Lizenzmodell | Vorschlag: MIT; finale Entscheidung dokumentieren | 🙂 |

