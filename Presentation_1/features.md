# Features und Epics – SPL‑Meter (Raspberry Pi Zero 2 W)

Hinweis: Ein Feature entspricht einer konkreten Funktion oder Methode. Die Schätzungen sind Netto-Entwicklungszeiten inkl. Unit-Tests, ohne Hardware-Beschaffung/Einrichtung. Kennzeichnungen REQ-… referenzieren Anforderungen aus W3/Anforderungen.md.

## Übersicht Epics

- **EP-AUD** Audioeingang & Buffer (REQ-FUNC-001, REQ-PERF-001, REQ-PERF-002, REQ-QUAL-001)
- **EP-SIG** Signalverarbeitung (SPL/Weightings/Leq) (REQ-FUNC-002/003/004, REQ-STD-001, REQ-PERF-002)
- **EP-SPC** Spektralanalyse (Oktav/Terz) (REQ-FUNC-005)
- **EP-CAL** Kalibrierung 94 dB @ 1 kHz (REQ-FUNC-008)
- **EP-API** Web-API (HTTP) (REQ-FUNC-006, REQ-INTF-001, REQ-NET-001)
- **EP-UI** Web-GUI (REQ-FUNC-006, REQ-UI-001)
- **EP-EXP** Export & Datenintegrität (REQ-FUNC-007, REQ-DATA-001/002)
- **EP-REC** Audioaufzeichnung (optional) (REQ-FUNC-010)
- **EP-CLI** CLI (optional) (REQ-FUNC-009)

---

## EP-AUD Audioeingang & Buffer

- **FEAT-AUD-001 `init_audio_stream(samplerate, blocksize, dtype, device)`**
  - Beschreibung: Öffnet I2S/USB-Eingang (48 kHz/24 bit), setzt Low-Latency-Parameter.
  - Abhängigkeiten: –
  - Aufwand: 4 h
  - Anforderungen: REQ-FUNC-001, REQ-PERF-001, REQ-PERF-002
  - Bibliotheken: sounddevice, numpy

- **FEAT-AUD-002 `audio_callback(in_data, frames, time, status)`**
  - Beschreibung: Producer-Callback; wandelt 24→32-bit float, schreibt non-blocking in Ringpuffer; zählt Underruns.
  - Abhängigkeiten: FEAT-AUD-003, FEAT-AUD-005
  - Aufwand: 4 h
  - Anforderungen: REQ-FUNC-001, REQ-QUAL-001
  - Bibliotheken: sounddevice, numpy, queue (Stdlib)

- **FEAT-AUD-003 `ring_push(block) / ring_pop()`**
  - Beschreibung: Lock-free Ringpuffer-Methoden (Producer/Consumer entkoppeln).
  - Abhängigkeiten: –
  - Aufwand: 3 h
  - Anforderungen: REQ-FUNC-001
  - Bibliotheken: queue (Stdlib), threading (Stdlib), numpy

- **FEAT-AUD-004 `start_audio_pipeline()` / `stop_audio_pipeline()`**
  - Beschreibung: Start/Stop des Streams, Lebenszyklusverwaltung.
  - Abhängigkeiten: FEAT-AUD-001, FEAT-AUD-002, FEAT-AUD-003
  - Aufwand: 2 h
  - Anforderungen: REQ-FUNC-001
  - Bibliotheken: sounddevice, threading (Stdlib)

- **FEAT-AUD-005 `convert_int24_to_float32(buffer)`**
  - Beschreibung: Korrekte Normierung 24-bit-in-32-bit-Container → float32.
  - Abhängigkeiten: –
  - Aufwand: 2 h
  - Anforderungen: REQ-PERF-002
  - Bibliotheken: numpy

---

## EP-SIG Signalverarbeitung (SPL/Weightings/Leq)

- **FEAT-SIG-001 `compute_rms(block)`**
  - Beschreibung: Vektorisierte RMS-Berechnung je Block.
  - Abhängigkeiten: –
  - Aufwand: 1 h
  - Anforderungen: REQ-FUNC-002
  - Bibliotheken: numpy

- **FEAT-SIG-002 `compute_spl_db(block, cal_factor, ref_pa=20e-6)`**
  - Beschreibung: Rechnet RMS in dB SPL um (inkl. Kalibrierfaktor).
  - Abhängigkeiten: FEAT-SIG-001, FEAT-CAL-004/FEAT-CAL-005
  - Aufwand: 3 h
  - Anforderungen: REQ-FUNC-002
  - Bibliotheken: numpy

- **FEAT-SIG-003 `design_a_weighting(fs)`**
  - Beschreibung: Entwurf A-Bewertungsfilter (IEC-konform), stabile IIR-Koeffizienten.
  - Abhängigkeiten: –
  - Aufwand: 4 h
  - Anforderungen: REQ-FUNC-004, REQ-STD-001
  - Bibliotheken: numpy, scipy.signal

- **FEAT-SIG-004 `apply_weighting(block, coeffs)`**
  - Beschreibung: Wendet A- oder Z-Bewertung vektorisiert auf Block an.
  - Abhängigkeiten: FEAT-SIG-003 (für A), Auswahl über FEAT-SIG-007
  - Aufwand: 1 h
  - Anforderungen: REQ-FUNC-004
  - Bibliotheken: numpy, scipy.signal

- **FEAT-SIG-005 `time_weighted_spl_update(state, inst_spl_db, mode)`**
  - Beschreibung: Zeitgewichtungen F/S per Exponentialfilter, Zustandsaktualisierung.
  - Abhängigkeiten: FEAT-SIG-002
  - Aufwand: 4 h
  - Anforderungen: REQ-FUNC-003, REQ-STD-001
  - Bibliotheken: numpy

- **FEAT-SIG-006 `leq_accumulate(state, inst_spl_db, dt)`**
  - Beschreibung: Energieäquivalenter Dauerschallpegel (Leq) über Zeitfenster.
  - Abhängigkeiten: FEAT-SIG-002
  - Aufwand: 3 h
  - Anforderungen: REQ-FUNC-003
  - Bibliotheken: numpy

- **FEAT-SIG-007 `select_weighting(mode)`**
  - Beschreibung: Liefert Koeffizienten für A- oder Z-Bewertung.
  - Abhängigkeiten: FEAT-SIG-003
  - Aufwand: 1 h
  - Anforderungen: REQ-FUNC-004
  - Bibliotheken: scipy.signal

---

## EP-SPC Spektralanalyse (Oktav/Terz)

- **FEAT-SPC-001 `design_octave_filterbank(fs, bands)`**
  - Beschreibung: IIR-Filterbank (Oktav/Terz) gemäß definierter Bandmitten.
  - Abhängigkeiten: –
  - Aufwand: 8 h
  - Anforderungen: REQ-FUNC-005
  - Bibliotheken: numpy, scipy.signal

- **FEAT-SPC-002 `compute_band_levels(block, filters)`**
  - Beschreibung: Bandpegelberechnung (RMS→dB) je Band; optional parallelisiert.
  - Abhängigkeiten: FEAT-SPC-001, FEAT-AUD-005, FEAT-SIG-001
  - Aufwand: 6 h
  - Anforderungen: REQ-FUNC-005
  - Bibliotheken: numpy, scipy.signal

- **FEAT-SPC-003 `downsample_for_bands(block, target_fs)`**
  - Beschreibung: Optionales Downsampling zur Rechenentlastung (nur für Bänder nötig).
  - Abhängigkeiten: –
  - Aufwand: 3 h
  - Anforderungen: REQ-FUNC-005 (leistungsoptimierend)
  - Bibliotheken: numpy, scipy.signal

---

## EP-CAL Kalibrierung 94 dB @ 1 kHz

- **FEAT-CAL-001 `detect_cal_tone_1khz(blocks, fs)`**
  - Beschreibung: Detektiert/validiert 1 kHz-Kalibratorsignal (Fensterung, FFT/Goertzel).
  - Abhängigkeiten: FEAT-AUD-004
  - Aufwand: 4 h
  - Anforderungen: REQ-FUNC-008
  - Bibliotheken: numpy, scipy.signal

- **FEAT-CAL-002 `compute_cal_factor(measured_db, reference_db=94.0)`**
  - Beschreibung: Berechnet Kalibrierfaktor aus gemessenem Pegel.
  - Abhängigkeiten: –
  - Aufwand: 1 h
  - Anforderungen: REQ-FUNC-008
  - Bibliotheken: numpy

- **FEAT-CAL-003 `save_calibration(device_id, factor)`**
  - Beschreibung: Persistiert faktorisiert gerätebezogen (Datei/JSON).
  - Abhängigkeiten: –
  - Aufwand: 1 h
  - Anforderungen: REQ-FUNC-008
  - Bibliotheken: json (Stdlib), pathlib (Stdlib)

- **FEAT-CAL-004 `load_calibration(device_id)`**
  - Beschreibung: Lädt Kalibrierfaktor beim Start.
  - Abhängigkeiten: –
  - Aufwand: 1 h
  - Anforderungen: REQ-FUNC-008
  - Bibliotheken: json (Stdlib), pathlib (Stdlib)

- **FEAT-CAL-005 `apply_calibration(value_pa, factor)`**
  - Beschreibung: Wendet Kalibrierfaktor in der SPL-Kette an.
  - Abhängigkeiten: FEAT-CAL-004
  - Aufwand: 1 h
  - Anforderungen: REQ-FUNC-008
  - Bibliotheken: numpy

- **FEAT-CAL-006 `detect_cal_tone_1khz(window_s)` (API: GET `/detect_cal_1khz`)**
  - Beschreibung: Detektiert 1 kHz‑Kalibratorton aus Pufferfenster, liefert Pegel und Güte.
  - Abhängigkeiten: FEAT-AUD-004
  - Aufwand: 2 h
  - Anforderungen: REQ-FUNC-008
  - Bibliotheken: numpy

- **FEAT-CAL-007 `calibrate_auto(reference_db, window_s, threshold)` (API: POST `/calibrate_auto`)**
  - Beschreibung: Setzt Kalibrier‑Offset automatisch anhand Detektion und Referenzpegel.
  - Abhängigkeiten: FEAT-CAL-006, FEAT-CAL-002/003
  - Aufwand: 2 h
  - Anforderungen: REQ-FUNC-008
  - Bibliotheken: numpy, fastapi

---

---

## EP-API Web-API (HTTP)

- **FEAT-API-001 `start_http_api(host, port)`**
  - Beschreibung: Startet FastAPI/ähnlich; bindet Audio-Pipeline und Metrik-Aggregation ein.
  - Abhängigkeiten: FEAT-AUD-004
  - Aufwand: 4 h
  - Anforderungen: REQ-FUNC-006, REQ-INTF-001, REQ-NET-001
  - Bibliotheken: fastapi, uvicorn, pydantic

- **FEAT-API-002 `api_get_status()`**
  - Beschreibung: Gibt State, Fehler, Konfiguration zurück.
  - Abhängigkeiten: FEAT-AUD-004, FEAT-AUD-002
  - Aufwand: 1 h
  - Anforderungen: REQ-FUNC-006
  - Bibliotheken: fastapi, pydantic

- **FEAT-API-003 `api_get_metrics()`**
  - Beschreibung: Liefert aktuelle Kennwerte (SPL F/S, Leq, optional Bänder) als JSON.
  - Abhängigkeiten: FEAT-SIG-002/005/006, optional FEAT-SPC-002
  - Aufwand: 2 h
  - Anforderungen: REQ-FUNC-006, REQ-FUNC-007
  - Bibliotheken: fastapi, pydantic

- **FEAT-API-004 `api_start_measurement()` / `api_stop_measurement()`**
  - Beschreibung: Steuert Start/Stop der Audio-Pipeline.
  - Abhängigkeiten: FEAT-AUD-004
  - Aufwand: 2 h
  - Anforderungen: REQ-FUNC-006
  - Bibliotheken: fastapi

- **FEAT-API-005 `api_set_config(payload)`**
  - Beschreibung: Setzt Konfiguration (Bewertung, Zeitgewichtung, Kal-Faktor etc.).
  - Abhängigkeiten: FEAT-SIG-007, FEAT-CAL-004/005
  - Aufwand: 3 h
  - Anforderungen: REQ-FUNC-006
  - Bibliotheken: fastapi, pydantic

- **FEAT-API-006 `api_export_session()`**
  - Beschreibung: Triggert Export/Checksumme, liefert Download-Link.
  - Abhängigkeiten: FEAT-EXP-001/002
  - Aufwand: 3 h
  - Anforderungen: REQ-FUNC-007, REQ-DATA-001
  - Bibliotheken: fastapi

- **FEAT-API-007 `api_detect_cal_1khz(window_s)`**
  - Beschreibung: Liefert Ergebnis der 1 kHz-Kalibratordetektion.
  - Abhängigkeiten: FEAT-CAL-006
  - Aufwand: 1 h
  - Anforderungen: REQ-FUNC-008
  - Bibliotheken: fastapi

- **FEAT-API-008 `api_calibrate_auto(payload)`**
  - Beschreibung: Führt automatische Kalibration via Detektion und Referenz durch.
  - Abhängigkeiten: FEAT-CAL-007
  - Aufwand: 1 h
  - Anforderungen: REQ-FUNC-008
  - Bibliotheken: fastapi

---

## EP-UI Web-GUI

- **FEAT-UI-001 `ui_dashboard_page()`**
  - Beschreibung: Live-Anzeige SPL F/S/Leq, Zustandsindikatoren, Warnungen.
  - Abhängigkeiten: FEAT-API-003
  - Aufwand: 6 h
  - Anforderungen: REQ-FUNC-006, REQ-UI-001
  - Bibliotheken: streamlit, requests

- **FEAT-UI-002 `ui_controls_page()`**
  - Beschreibung: Start/Stop, Bewertung/Timeweighting, Kalibrier-Trigger.
  - Abhängigkeiten: FEAT-API-004/005
  - Aufwand: 4 h
  - Anforderungen: REQ-FUNC-006
  - Bibliotheken: streamlit, requests

- **FEAT-UI-003 `ui_config_page()`**
  - Beschreibung: Geräteeinstellungen, Export/Download, Storage-Status.
  - Abhängigkeiten: FEAT-API-005/006
  - Aufwand: 4 h
  - Anforderungen: REQ-FUNC-006
  - Bibliotheken: streamlit, requests

---

## EP-EXP Export & Datenintegrität

- **FEAT-EXP-001 `export_session_json(session, path)`**
  - Beschreibung: Exportiert Mess-/Metadaten als JSON gemäß Schema.
  - Abhängigkeiten: FEAT-API-003
  - Aufwand: 4 h
  - Anforderungen: REQ-FUNC-007
  - Bibliotheken: json (Stdlib), pathlib (Stdlib)

- **FEAT-EXP-002 `write_sha256(file_path)`**
  - Beschreibung: Erzeugt .sha256-Datei für Export.
  - Abhängigkeiten: FEAT-EXP-001
  - Aufwand: 1 h
  - Anforderungen: REQ-DATA-001
  - Bibliotheken: hashlib (Stdlib), pathlib (Stdlib)

- **FEAT-EXP-003 `prune_old_exports(max_bytes)`**
  - Beschreibung: Einfache Speicherstrategie (Aufräumen nach Schwelle).
  - Abhängigkeiten: –
  - Aufwand: 3 h
  - Anforderungen: REQ-DATA-002
  - Bibliotheken: pathlib (Stdlib), os (Stdlib)

---

## EP-REC Audioaufzeichnung (optional)

- **FEAT-REC-001 `start_recording_wav(path)`**
  - Beschreibung: Initialisiert WAV-Header, startet Schreibvorgang.
  - Abhängigkeiten: FEAT-AUD-003
  - Aufwand: 4 h
  - Anforderungen: REQ-FUNC-010
  - Bibliotheken: soundfile, numpy, threading (Stdlib)

- **FEAT-REC-002 `recording_consumer()`**
  - Beschreibung: Consumer-Thread liest Ringpuffer und schreibt streaming-fähig.
  - Abhängigkeiten: FEAT-AUD-003
  - Aufwand: 6 h
  - Anforderungen: REQ-FUNC-010
  - Bibliotheken: soundfile, numpy, threading (Stdlib), queue (Stdlib)

- **FEAT-REC-003 `stop_recording()`**
  - Beschreibung: Finalisiert WAV-Header, schließt Datei robust.
  - Abhängigkeiten: FEAT-REC-001/002
  - Aufwand: 2 h
  - Anforderungen: REQ-FUNC-010
  - Bibliotheken: soundfile

- **FEAT-REC-004 API Recording Steuerung (POST `/record/start`, `/record/stop`)**
  - Beschreibung: API-Endpunkte zum Start/Stop der WAV-Aufnahme.
  - Abhängigkeiten: FEAT-REC-001/002/003, FEAT-API-001
  - Aufwand: 1 h
  - Anforderungen: REQ-FUNC-010, REQ-INTF-001
  - Bibliotheken: fastapi


---

## EP-CLI CLI (optional)

- **FEAT-CLI-001 `cli_main()`**
  - Beschreibung: Dünner CLI-Client (Typer/Click) gegen HTTP-API (Start/Stop/Status/Export).
  - Abhängigkeiten: FEAT-API-002/003/004/006
  - Aufwand: 6 h
  - Anforderungen: REQ-FUNC-009
  - Bibliotheken: typer, requests

---

## Hinweise zur Reihenfolge (empfohlen)

- **Phase 1 (Fundament)**: EP-AUD, EP-SIG (bis FEAT-SIG-006)
- **Phase 2 (Benutzerschnittstellen)**: EP-API, EP-UI, EP-EXP
- **Phase 3 (Erweiterungen/Leistung)**: EP-SPC, EP-CAL, EP-REC
- **Phase 4 (Optionales)**: EP-CLI

Gesamtschätzung Muss-Umfang (ohne optionale Epics): ca. 70–90 h. Mit optionalen Epics: ca. 110–140 h.

