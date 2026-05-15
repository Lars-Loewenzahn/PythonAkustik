# Zeitplan – SPL‑Meter Projekt

Stand: 15.05.2026

- **Heute**: 15.05.2026
- **Abgabefrist**: 04.07.2026, 00:01 (vgl. W5/termine_und_daten.md)
- **Verbleibende Zeit**: 50 Tage ≈ 7 Wochen + 1 Tag
- **Annahme**: Die Zustandsmaschine (State Machine) ist bereits erledigt und muss nicht mehr eingeplant werden.

## Sprintplan (7 Sprints + Puffer)

- **Sprint 1**: 15.05.2026 – 21.05.2026 (Zwischenbericht #1 am 18.05.)
- **Sprint 2**: 22.05.2026 – 28.05.2026
- **Sprint 3**: 29.05.2026 – 04.06.2026 (Review #2 am 01.06.)
- **Sprint 4**: 05.06.2026 – 11.06.2026
- **Sprint 5**: 12.06.2026 – 18.06.2026 (Review #3 am 15.06.)
- **Sprint 6**: 19.06.2026 – 25.06.2026
- **Sprint 7**: 26.06.2026 – 02.07.2026 (Review #4 am 29.06.)
- **Release‑Puffer**: 03.07.2026 – 04.07.2026, 00:01 (Finalisierung, Polishing, Release v1.0)

## Abhängigkeiten & Parallelisierungsannahmen

- **Audioeingang/Buffer (EP‑AUD)** vor Signalverarbeitung (EP‑SIG), API/GUI stützt sich auf lauffähige Pipeline.
- **Kalibrierung (EP‑CAL)** setzt SPL‑Berechnung und API‑Grundgerüst voraus.
- **Spektralanalyse (EP‑SPC)** ist nach stabiler Pipeline sinnvoll, kann parallel zu UI/API‑Erweiterungen laufen.
- **Export (EP‑EXP)** benötigt Messdaten/Session‑Struktur; späte Sprints.
- **Optionale Epics (REC/CLI)** nur bei Zeitpuffer (Sprint 7).
- **Tests/Doku** laufen flankierend; Reviews setzen jeweils präsentierbare Zwischenstände voraus.

---

## Aufgabenplanung mit frühestem Start (ES) und spätestem Ende (LE)

Format: `TASK_CODE – Titel – ES → LE – Hinweise`

### EP‑AUD Audioeingang & Buffer
- FEAT‑AUD‑001 – init_audio_stream – 15.05.2026 → 21.05.2026 – Basis I2S/USB; Voraussetzung für SIG/API.
- FEAT‑AUD‑002 – audio_callback – 15.05.2026 → 21.05.2026 – Inkl. Statushandling; parallel zu AUD‑001.
- FEAT‑AUD‑003 – ring_push/pop – 15.05.2026 → 21.05.2026 – Thread‑sicher; parallel zu AUD‑001/002.
- FEAT‑AUD‑004 – start/stop_audio_pipeline – 22.05.2026 → 28.05.2026 – Lifecycle auf Basis AUD‑001..003.
- FEAT‑AUD‑005 – convert_int24_to_float32 – 22.05.2026 → 28.05.2026 – Für 24‑bit Pfad nötig.

### EP‑SIG Signalverarbeitung (SPL/Weightings/Leq)
- FEAT‑SIG‑001 – compute_rms – 22.05.2026 → 28.05.2026 – Benötigt Rohdatenpfad.
- FEAT‑SIG‑002 – compute_spl_db – 22.05.2026 → 28.05.2026 – Auf RMS aufbauend.
- FEAT‑SIG‑003 – design_a_weighting – 29.05.2026 → 04.06.2026 – IEC‑konformer Entwurf.
- FEAT‑SIG‑004 – apply_weighting – 29.05.2026 → 04.06.2026 – Auf SIG‑003 basierend.
- FEAT‑SIG‑005 – time_weighted_spl_update – 05.06.2026 → 11.06.2026 – F/S Zeitgewichtungen.
- FEAT‑SIG‑006 – leq_accumulate – 05.06.2026 → 11.06.2026 – Leq‑Integration.
- FEAT‑SIG‑007 – select_weighting – 05.06.2026 → 11.06.2026 – A/Z Umschaltung.

### EP‑SPC Spektralanalyse (Oktav/Terz)
- FEAT‑SPC‑001 – design_octave_filterbank – 12.06.2026 → 18.06.2026 – Nach stabiler Pipeline.
- FEAT‑SPC‑002 – compute_band_levels – 19.06.2026 → 25.06.2026 – Auf SPC‑001 basierend.
- FEAT‑SPC‑003 – downsample_for_bands – 19.06.2026 → 25.06.2026 – Performance‑Optimierung.

### EP‑CAL Kalibrierung 94 dB @ 1 kHz
- FEAT‑CAL‑001 – detect_cal_tone_1khz(blocks, fs) – 05.06.2026 → 11.06.2026 – Benötigt SIG/FFT‑Pfad.
- FEAT‑CAL‑002 – compute_cal_factor – 12.06.2026 → 18.06.2026 – Auf CAL‑001 basierend.
- FEAT‑CAL‑003 – save_calibration – 12.06.2026 → 18.06.2026 – Persistenz.
- FEAT‑CAL‑004 – load_calibration – 12.06.2026 → 18.06.2026 – Fallback/Validierung.
- FEAT‑CAL‑005 – apply_calibration – 12.06.2026 → 18.06.2026 – In SPL‑Pfad integrieren.
- FEAT‑CAL‑006 – detect_cal_tone_1khz(window_s) (API‑gestützt) – 12.06.2026 → 18.06.2026 – Binding vorbereiten.
- FEAT‑CAL‑007 – calibrate_auto – 19.06.2026 → 25.06.2026 – End‑to‑End Auto‑Kalibrierung.

### EP‑API Web‑API (HTTP)
- FEAT‑API‑001 – start_http_api – 29.05.2026 → 04.06.2026 – App‑Factory/Uvicorn.
- FEAT‑API‑002 – api_get_status – 29.05.2026 → 04.06.2026 – Statusaggregation.
- FEAT‑API‑003 – api_get_metrics – 05.06.2026 → 11.06.2026 – SPL/Leq/Bänder (Basis zunächst SPL/Leq).
- FEAT‑API‑004 – api_start/stop_measurement – 05.06.2026 → 11.06.2026 – Idempotente Übergänge.
- FEAT‑API‑005 – api_set_config – 05.06.2026 → 11.06.2026 – Bewertung/Timeweighting/Kal‑Faktor.
- FEAT‑API‑006 – api_export_session – 19.06.2026 → 25.06.2026 – Export/Checksumme triggern.
- FEAT‑API‑007 – api_detect_cal_1khz – 12.06.2026 → 18.06.2026 – Binding zu CAL‑006.
- FEAT‑API‑008 – api_calibrate_auto – 19.06.2026 → 25.06.2026 – Binding zu CAL‑007.

### EP‑UI Web‑GUI
- FEAT‑UI‑001 – ui_dashboard_page – 05.06.2026 → 11.06.2026 – Live‑SPL/Leq; Start mit Minimalumfang.
- FEAT‑UI‑002 – ui_controls_page – 12.06.2026 → 18.06.2026 – Start/Stop/Weighting/Kal‑Trigger.
- FEAT‑UI‑003 – ui_config_page – 19.06.2026 → 25.06.2026 – Export/Storage‑Status.

### EP‑EXP Export & Datenintegrität
- FEAT‑EXP‑001 – export_session_json – 19.06.2026 → 25.06.2026 – JSON Schema/Session.
- FEAT‑EXP‑002 – write_sha256 – 19.06.2026 → 25.06.2026 – Prüfsumme.
- FEAT‑EXP‑003 – prune_old_exports – 26.06.2026 → 02.07.2026 – Aufräumstrategie.

### EP‑REC Audioaufzeichnung (optional)
- FEAT‑REC‑001 – start_recording_wav – 26.06.2026 → 02.07.2026 – Optional, wenn Puffer.
- FEAT‑REC‑002 – recording_consumer – 26.06.2026 → 02.07.2026 – Optional.
- FEAT‑REC‑003 – stop_recording – 26.06.2026 → 02.07.2026 – Optional.
- FEAT‑REC‑004 – API Recording Steuerung – 26.06.2026 → 02.07.2026 – Optional.

### EP‑CLI CLI (optional)
- FEAT‑CLI‑001 – cli_main – 26.06.2026 → 02.07.2026 – Optional.

### Zusatzaufgaben – Dokumentation
- Anforderungen pflegen – 15.05.2026 → 01.06.2026 – Traceability REQ→Feature bis Review #2.
- API‑Dokumentation – 12.06.2026 → 25.06.2026 – OpenAPI/Beispiele vor Sprint 7 fertig.
- JSON‑Schema – 19.06.2026 → 25.06.2026 – Struktur/Beispiele, Export ready.
- Signalverarbeitung (Formeln/Annahmen) – 12.06.2026 → 18.06.2026 – Nach Umsetzung SIG.
- Kalibrier‑Prozedur – 19.06.2026 → 25.06.2026 – Nach CAL/Endpoints.
- Testplan – 22.05.2026 → 11.06.2026 – Laufend pflegen; Basis ab Sprint 2 vorhanden.
- Betrieb/Setup‑Guide – 29.05.2026 → 04.06.2026 – Nach Audio‑Grundfunktion.
- Lizenz/Hinweise – 26.06.2026 → 02.07.2026 – Vor Release abschließen.

### Zusatzaufgaben – Präsentationen & Termine
- Zwischenbericht #1 (18.05.) – 15.05.2026 → 18.05.2026 – 7–8 Slides, 10 min + Q&A.
- Review #2 (01.06.) – 29.05.2026 → 01.06.2026 – SPL/GUI/API Kurzdemo.
- Review #3 (15.06.) – 12.06.2026 → 15.06.2026 – F/S, A/Z, Stabilität.
- Review #4 (29.06.) – 26.06.2026 → 29.06.2026 – Spektren, Kalibrierung, Export.
- Abschluss/Abgabe (04.07., 00:01) – 03.07.2026 → 04.07.2026 – Funktionsdemo, Doku final.
- Präsentationsvorbereitung – 26.06.2026 → 03.07.2026 – Folien/Demos, Proben.

### Zusatzaufgaben – Hardware/3D‑Druck/Zusammenbau
- I2S‑Verdrahtung INMP441 – 15.05.2026 → 21.05.2026 – Ermöglicht echten Audioeingang.
- Systemkonfiguration (I2S/ALSA) – 15.05.2026 → 21.05.2026 – /boot/config.txt, asound.
- Gehäuse‑Design – 12.06.2026 → 18.06.2026 – Einfaches Schutzgehäuse.
- 3D‑Druck – 19.06.2026 → 25.06.2026 – Teile drucken, Passprobe.
- Zusammenbau – 26.06.2026 → 02.07.2026 – Finaler Aufbau.
- Stromversorgung (Akkutest optional) – 19.06.2026 → 25.06.2026 – Lasttest.
- Inbetriebnahme‑Check – 29.05.2026 → 04.06.2026 – Datenfluss, SD‑Schreibtest, WLAN/SSH.

### Zusatzaufgaben – Tests & Validierung
- Unit‑Tests – 22.05.2026 → 11.06.2026 – SIG/AUD Kerntests (laufend ausbauen).
- Integrationstests – 05.06.2026 → 25.06.2026 – API/Pipeline/Export E2E.
- Systemtests (Pi) – 19.06.2026 → 25.06.2026 – Stabilität 48 kHz/24 bit.
- Validierung vs. NTi XL2 – 26.06.2026 → 02.07.2026 – Abweichungen dokumentieren.

---

## Meilensteine je Sprint (Zielbilder)

- Sprint 1: Audio‑Pfad roh lauffähig (I2S/USB, Callback, Ringpuffer), Kurz‑Demo für 18.05.; Anforderungen‑Doku v1.
- Sprint 2: Pipeline start/stop stabil; RMS/SPL korrekt; erster Testplan; erste Unittests grün.
- Sprint 3: A‑Filter entworfen/integriert; HTTP‑API steht (Status); Inbetriebnahme‑Check; kurze Demo am 01.06.
- Sprint 4: Zeitgewichtungen/Leq; API: Metrics/Start‑Stop/Config; UI Dashboard v1.
- Sprint 5: Kalibrier‑Kette funktionsfähig; UI Controls; SPC‑Entwurf begonnen; Review am 15.06.
- Sprint 6: Spektren + Export + SHA256; API‑Export; UI Config; Systemtests; JSON‑Schema/Doku.
- Sprint 7: Aufräumen, Prune, optionale Recording/CLI; Validierung; Releasevorbereitung; Review am 29.06.
- Puffer: Finalisierung, Doku, Präsentation, Tag v1.0, Abgabe.

## Risiken/Reserven

- Falls I2S‑Hardware hakt: kurzfristig auf USB‑Audio ausweichen (SPL‑Funktion bleibt möglich).
- SPC (Oktav/Terz) und Recording sind nachrangig; bei Zeitdruck kürzen oder in Minimalumfang ausliefern.
- Engpässe bei Kalibrierung: manuelle Kal‑Faktoren erlauben, Auto‑Kalibrierung notfalls in Sprint 7 verschieben.

