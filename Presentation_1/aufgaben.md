# Aufgabenliste – SPL‑Meter (Raspberry Pi Zero 2 W)

Hinweis: Die Features aus `Presentation_1/features.md` sind hier als Aufgaben übernommen und nach Epics gruppiert. Ergänzt um Doku-, Präsentations- sowie Hardware-/3D‑Druck-/Aufbau‑Aufgaben. Quellen: `W3/Anforderungen.md`, `W4/Vorschläge_anforderungen.ipynb`, `W5/termine_und_daten.md`.

## EP-AUD Audioeingang & Buffer

- **[FEAT-AUD-001]** `init_audio_stream(samplerate, blocksize, dtype, device)` – I2S/USB Eingang initialisieren (48 kHz/24 bit), Low‑Latency setzen.
  - Erwartet: Auswahl/Erkennung des ALSA‑Geräts (I2S/USB), Parametrisierung von `samplerate`, `blocksize`, `dtype`; Fehlerbehandlung bei nicht verfügbarem Gerät.
  - Schritte: Geräteauflistung und Auto‑Select implementieren; Konfiguration testen (48 kHz/24‑bit); Minimal‑Start/Stop‑Skript.
  - Akzeptanz: Stream öffnet und läuft stabil ≥5 min ohne Underruns (48 kHz/24 bit). Fehlermeldung bei fehlendem Gerät. Logeintrag beim Start/Stop.
  - Zeitaufwand: 4 h

- **[FEAT-AUD-002]** `audio_callback(in_data, frames, time, status)` – Callback: 24→32‑bit float, Ringpuffer schreiben, Underruns zählen.
  - Erwartet: Konvertierung in float32 ohne Clipping, non‑blocking Push in Ringpuffer, Zähler/Flag für `input_underflow`/`overflow`.
  - Schritte: Callback implementieren; Statusbehandlung; Mikro‑Benchmark (Durchsatz/Blockzeit) dokumentieren.
  - Akzeptanz: Keine Blockierung im Callback; Underrun‑Zähler erhöht sich nur bei forcierten Szenarien; Profiling zeigt Verarbeitung < 10% der Blockzeit.
  - Zeitaufwand: 4 h

- **[FEAT-AUD-003]** `ring_push(block) / ring_pop()` – Ringpuffer Producer/Consumer implementieren.
  - Erwartet: Thread‑sichere, lock‑arme Struktur; Kapazitätsgrenze; Strategie bei Volllauf (älteste/neuste verwerfen) konfigurierbar.
  - Schritte: Implementierung und Unit‑Tests (Füllen/Leeren, Race‑Szenarien); Messung der Latenz.
  - Akzeptanz: 0 Datenkorruption unter Parallelität; definierte Strategie bei Volllauf; Durchsatz ≥ Echtzeitanforderung.
  - Zeitaufwand: 3 h

- **[FEAT-AUD-004]** `start_audio_pipeline()` / `stop_audio_pipeline()` – Stream Lebenszyklus starten/stoppen.
  - Erwartet: Idempotente Start/Stop‑Routinen, Ressourcen sauber freigeben, erneuter Start ohne Neustart möglich.
  - Schritte: Lifecycle‑Wrapper; Exception‑Handling; Tests Start→Stop→Start.
  - Akzeptanz: Wiederholtes Start/Stop ohne Leak/Crash; Logs vorhanden.
  - Zeitaufwand: 2 h

- **[FEAT-AUD-005]** `convert_int24_to_float32(buffer)` – Korrekte Normierung 24‑bit‑in‑32‑bit zu float32.
  - Erwartet: Nutzung des vollen 24‑bit‑Dynamikbereichs (Division mit 2^31), korrektes Handling des Vorzeichens.
  - Schritte: Implementierung; Unit‑Tests mit Grenzwerten (0x7FFFFF, 0x800000, 0).
  - Akzeptanz: Tests bestehen; numerische Abweichung < 1e‑7.
  - Zeitaufwand: 2 h

## EP-SIG Signalverarbeitung (SPL/Weightings/Leq)

- **[FEAT-SIG-001]** `compute_rms(block)` – Block‑RMS vektorisiert.
  - Erwartet: Numerisch stabile RMS‑Berechnung (float32/64) ohne Python‑Loops.
  - Schritte: NumPy‑Implementierung; Unit‑Tests (Konstant‑, Sinus‑, Nullsignal).
  - Akzeptanz: Abweichung zum Referenzwert < 1e‑6; Laufzeit << Blockzeit.
  - Zeitaufwand: 1 h

- **[FEAT-SIG-002]** `compute_spl_db(block, cal_factor, ref_pa)` – RMS → dB SPL inkl. Kalibrierung.
  - Erwartet: Umrechnung gemäß 20·log10(x/ref); Anwendung Kalibrierfaktor (Pa ↔ dB SPL).
  - Schritte: Implementierung; Tests mit synthetischen Pegeln und bekannten Offsets.
  - Akzeptanz: 94 dB Referenz wird nach Kalibrierung ±0,5 dB getroffen.
  - Zeitaufwand: 3 h

- **[FEAT-SIG-003]** `design_a_weighting(fs)` – A‑Bewertungs‑Filter (IEC‑konform) entwerfen.
  - Erwartet: Stabiler IIR (biquad‑Kette) mit dokumentierten Koeffizienten für fs=48 kHz.
  - Schritte: Filterentwurf/Validierung (Frequenzgang); Speicherung der Koeffizienten.
  - Akzeptanz: Frequenzgang im Toleranzband der IEC 61672‑1/‑2 (Stützfrequenzen).
  - Zeitaufwand: 4 h

- **[FEAT-SIG-004]** `apply_weighting(block, coeffs)` – A/Z‑Bewertung anwenden.
  - Erwartet: Vektorisierte Filterung blockweise; zustandsbehaftet über Blöcke.
  - Schritte: Implementierung mit `scipy.signal.lfilter` o. ä.; Pufferung der Zustände.
  - Akzeptanz: Keine Instabilität; Durchsatz in Echtzeit.
  - Zeitaufwand: 1 h

- **[FEAT-SIG-005]** `time_weighted_spl_update(state, inst_spl_db, mode)` – Zeitgewichtungen F/S.
  - Erwartet: Exponentialfilter mit korrekten Zeitkonstanten (Fast/Slow).
  - Schritte: Implementierung; Sprungantworttest; Vergleich gegen Referenzkurve.
  - Akzeptanz: 63%‑Wert bei τ innerhalb ±1% Toleranz.
  - Zeitaufwand: 4 h

- **[FEAT-SIG-006]** `leq_accumulate(state, inst_spl_db, dt)` – Leq‑Integration.
  - Erwartet: Energieäquivalente Mittelung über ein Fenster; numerisch stabil.
  - Schritte: Implementierung; Test mit konstantem Signal über 60 s.
  - Akzeptanz: Leq ≈ Eingangspegel (±0,2 dB) bei konstantem Ton.
  - Zeitaufwand: 3 h

- **[FEAT-SIG-007]** `select_weighting(mode)` – Auswahl A/Z‑Koeffizienten.
  - Erwartet: Sichere Umschaltung; Validierung der aktiven Koeffizienten.
  - Schritte: Mapping implementieren; Negativtests (ungültiger Modus).
  - Akzeptanz: Korrekte Anwendung im Datenpfad; Fehler bei ungültigem Modus.
  - Zeitaufwand: 1 h

## EP-SPC Spektralanalyse (Oktav/Terz)

- **[FEAT-SPC-001]** `design_octave_filterbank(fs, bands)` – IIR‑Filterbank für Oktav/Terz.
  - Erwartet: Koeffizienten je Band (Mittenfrequenzen normgerecht), stabil und dokumentiert.
  - Schritte: Entwurf/Validierung; Auswahl Bandset (z. B. 1/3‑Oktav 100 Hz–10 kHz).
  - Akzeptanz: Test‑Sweep ergibt korrekte Bandverläufe innerhalb Toleranzen.
  - Zeitaufwand: 8 h

- **[FEAT-SPC-002]** `compute_band_levels(block, filters)` – Bandpegel (RMS→dB) je Band.
  - Erwartet: Parallele Filterung/Leistungsberechnung; effiziente Umsetzung.
  - Schritte: Implementieren; Performance‑Test (ms/Block); Vergleich mit Referenzdaten.
  - Akzeptanz: Echtzeitfähig bei Ziel‑Blockgröße; Abweichung < ±1 dB.
  - Zeitaufwand: 6 h

- **[FEAT-SPC-003]** `downsample_for_bands(block, target_fs)` – Optionales Downsampling zur Entlastung.
  - Erwartet: Anti‑Aliasing‑Filter + Decimation; Qualitätserhalt für Zielbänder.
  - Schritte: FIR/IIR‑Anti‑Aliasing wählen; Tests auf Spektralverfälschung.
  - Akzeptanz: Keine relevanten Artefakte in Zielbändern; CPU‑Last sinkt messbar.
  - Zeitaufwand: 3 h

## EP-CAL Kalibrierung 94 dB @ 1 kHz

- **[FEAT-CAL-001]** `detect_cal_tone_1khz(blocks, fs)` – Kalibratorton detektieren/validieren.
  - Erwartet: Fensterung + FFT/Goertzel; Ausgabe Pegel/Güte (SNR/THD optional).
  - Schritte: Implementierung; Schwellen/Validierung definieren; Tests mit 1 kHz‑Sinus.
  - Akzeptanz: Rauscherkennung robust; Fehlalarme < 1% bei realem Rauschen.
  - Zeitaufwand: 4 h

- **[FEAT-CAL-002]** `compute_cal_factor(measured_db, reference_db)` – Kalibrierfaktor berechnen.
  - Erwartet: Offset/Skalierung konsistent; Rundung/Präzision dokumentiert.
  - Schritte: Implementierung; Tests mit synthetischen Offsets.
  - Akzeptanz: Nach Anwendung trifft Referenzpegel ±0,5 dB.
  - Zeitaufwand: 1 h

- **[FEAT-CAL-003]** `save_calibration(device_id, factor)` – Kalibrierung speichern.
  - Erwartet: Gerätespezifische Persistenz (Datei/JSON) inkl. Zeitstempel/Checksumme optional.
  - Schritte: Pfadschema; Schreib/Lesetests; Fehlerfälle (kein Speicher) behandeln.
  - Akzeptanz: Persistenz robust; Wiederanlauf lädt korrekten Faktor.
  - Zeitaufwand: 1 h

- **[FEAT-CAL-004]** `load_calibration(device_id)` – Kalibrierung laden.
  - Erwartet: Sicheres Laden mit Default‑Fallback; Validierung Wertebereich.
  - Schritte: Implementierung; Unit‑Tests (korrupt/fehlend).
  - Akzeptanz: Korrektes Fallback + Logwarnung; gültiger Faktor im Betrieb.
  - Zeitaufwand: 1 h

- **[FEAT-CAL-005]** `apply_calibration(value_pa, factor)` – Kalibrierung anwenden.
  - Erwartet: Anwendung im SPL‑Pfad ohne erneutes Runden/Clipping.
  - Schritte: Einbindung in `compute_spl_db`; Tests.
  - Akzeptanz: Korrekte Verschiebung ohne Artefakte.
  - Zeitaufwand: 1 h

- **[FEAT-CAL-006]** `detect_cal_tone_1khz(window_s)` – API‑gestützte Detektion (GET `/detect_cal_1khz`).
  - Erwartet: Nutzung eines aktuellen Fensterpuffers; Rückgabe Pegel/Güte.
  - Schritte: Fenstermanagement; API‑Binding; einfache Ratenbegrenzung.
  - Akzeptanz: Endpoint liefert Werte < 300 ms; sinnvolle Ergebnisse bei anliegendem Ton.
  - Zeitaufwand: 2 h

- **[FEAT-CAL-007]** `calibrate_auto(reference_db, window_s, threshold)` – Auto‑Kalibrierung (POST `/calibrate_auto`).
  - Erwartet: End‑to‑End Kalibrier‑Offset setzen/speichern nach erfolgreicher Detektion.
  - Schritte: Payload validieren; Faktor berechnen; persistieren; Erfolg/Fehler codes.
  - Akzeptanz: Nach Aufruf sind SPL‑Werte um Referenz ±0,5 dB korrigiert.
  - Zeitaufwand: 2 h

## EP-API Web‑API (HTTP)

- **[FEAT-API-001]** `start_http_api(host, port)` – FastAPI/Server starten, Audio‑Pipeline einbinden.
  - Erwartet: Start via Uvicorn, CORS/Timeouts sinnvoll; Health‑Endpoint; Logging.
  - Schritte: App‑Factory; Server‑Startskript; Netzwerk‑Test im WLAN.
  - Akzeptanz: Start < 10 s; Aufruf im LAN erreichbar; Health liefert 200.
  - Zeitaufwand: 4 h

- **[FEAT-API-002]** `api_get_status()` – Status/Fehler/Konfiguration liefern.
  - Erwartet: JSON inkl. Stream‑Status, Underruns, aktiver Bewertung, Blocksize.
  - Schritte: Statusaggregation; Pydantic‑Schema; Fehlerpfade testen.
  - Akzeptanz: Schema stabil; Antwort < 100 ms lokal.
  - Zeitaufwand: 1 h

- **[FEAT-API-003]** `api_get_metrics()` – SPL/Leq/Bänder als JSON liefern.
  - Erwartet: 10 Hz Aktualisierung; optionale Felder (Bänder) konfigurierbar.
  - Schritte: Snapshot aus Signalpfad; Pydantic‑Modelle; Beispielantworten.
  - Akzeptanz: Valides JSON; Latenz < 150 ms; keine Blockierung der Pipeline.
  - Zeitaufwand: 2 h

- **[FEAT-API-004]** `api_start_measurement()` / `api_stop_measurement()` – Messung starten/stoppen.
  - Erwartet: Idempotente Übergänge; Fehlercodes bei ungültigem Zustand.
  - Schritte: Bindings zu Start/Stop; Tests (doppelt Start/Stop).
  - Akzeptanz: 200/204 bei Erfolg; sinnvolle Fehlermeldungen.
  - Zeitaufwand: 2 h

- **[FEAT-API-005]** `api_set_config(payload)` – Bewertung/Timeweighting/Kal‑Faktor setzen.
  - Erwartet: Validierte Eingaben; persistente Anwendung während Laufzeit.
  - Schritte: Pydantic‑Schemas; Anwendung im Signalpfad; Tests.
  - Akzeptanz: Änderungen greifen innerhalb eines Blocks; 4xx bei invaliden Werten.
  - Zeitaufwand: 3 h

- **[FEAT-API-006]** `api_export_session()` – Export/Checksumme anstoßen.
  - Erwartet: Trigger des Exports; Pfad/Dateiname mit Zeitstempel; Rückgabe Download‑Info.
  - Schritte: Export anstoßen; Prüfsumme schreiben; Fehlerfälle behandeln (Speicher voll).
  - Akzeptanz: Datei vorhanden + .sha256; Größen/Schema korrekt.
  - Zeitaufwand: 3 h

- **[FEAT-API-007]** `api_detect_cal_1khz(window_s)` – Ergebnis der Kalibrator‑Detektion liefern.
  - Erwartet: Rückgabe Pegel+Güte; Parameter `window_s` validiert.
  - Schritte: Binding zu FEAT‑CAL‑006; Response‑Schema; Grenzfälle testen.
  - Akzeptanz: Sinnvolle Werte bei vorhandenem 1 kHz‑Ton; 4xx bei ungültigen Parametern.
  - Zeitaufwand: 1 h

- **[FEAT-API-008]** `api_calibrate_auto(payload)` – Auto‑Kalibrierung über API ausführen.
  - Erwartet: ReferenzdB, Fenster, Schwellwert; setzt Faktor persistent.
  - Schritte: Binding zu FEAT‑CAL‑007; Erfolg/Fehlercodes; Audit‑Log.
  - Akzeptanz: Faktor gesetzt und gespeichert; anschließende Messwerte korrigiert.
  - Zeitaufwand: 1 h

## EP-UI Web‑GUI

- **[FEAT-UI-001]** `ui_dashboard_page()` – Live‑Werte SPL F/S/Leq, Indikatoren/Warnungen.
  - Erwartet: 10 Hz Refresh; Anzeige Underruns/Clipping; responsives Layout.
  - Schritte: Streamlit‑Layout; Polling gegen API; Fehlerindikatoren.
  - Akzeptanz: Flüssige Anzeige; klare Warnmeldungen; keine Blockierung der API.
  - Zeitaufwand: 6 h

- **[FEAT-UI-002]** `ui_controls_page()` – Start/Stop, Bewertung/Timeweighting, Kalibrier‑Trigger.
  - Erwartet: Buttons/Toggles; valide Requests; Nutzerfeedback.
  - Schritte: Formular/Controls; API‑Calls; Erfolg/Fehlermeldungen.
  - Akzeptanz: Funktionen steuern zuverlässig; UI bleibt responsiv.
  - Zeitaufwand: 4 h

- **[FEAT-UI-003]** `ui_config_page()` – Einstellungen, Export/Download, Storage‑Status.
  - Erwartet: Konfig‑Formulare; Export auslösen + Downloadlink; Speicherverbrauch anzeigen.
  - Schritte: UI‑Elemente; API‑Integration; Download‑Handling.
  - Akzeptanz: Export durchführbar; Statusdaten korrekt; Eingaben validiert.
  - Zeitaufwand: 4 h

## EP-EXP Export & Datenintegrität

- **[FEAT-EXP-001]** `export_session_json(session, path)` – Mess‑/Metadaten als JSON exportieren.
  - Erwartet: Vollständiges JSON (Werte, Zeitstempel, Konfig, Geräteinfo).
  - Schritte: Serialisierung; Pfadmanagement; Beispiel‑Exports.
  - Akzeptanz: JSON validiert; Schema stabil; Dateigröße plausibel.
  - Zeitaufwand: 4 h

- **[FEAT-EXP-002]** `write_sha256(file_path)` – .sha256‑Datei erzeugen.
  - Erwartet: SHA256 für Exportdatei; separate .sha256‑Datei.
  - Schritte: Hash‑Berechnung; Schreibtest; Verifikationsskript.
  - Akzeptanz: Prüfsumme erkennt Bitfehler; Skript PASS/FAIL.
  - Zeitaufwand: 1 h

- **[FEAT-EXP-003]** `prune_old_exports(max_bytes)` – Speicherstrategie/Aufräumen.
  - Erwartet: Schwellwert‑basiertes Löschen älterer Exporte; Logeinträge.
  - Schritte: Größenberechnung; Sortierung; Löschroutine; Dry‑Run.
  - Akzeptanz: Freier Speicher wird Zielwert erreicht; keine aktiven Dateien gelöscht.
  - Zeitaufwand: 3 h

## EP-REC Audioaufzeichnung (optional)

- **[FEAT-REC-001]** `start_recording_wav(path)` – WAV‑Header/Start.
  - Erwartet: Streaming‑fähiges Schreiben; Dateiname mit Zeitstempel; Header vorbereiten.
  - Schritte: Datei öffnen; Header schreiben; Pfad prüfen.
  - Akzeptanz: Datei beginnt sofort zu wachsen; keine Blockierung der Pipeline.
  - Zeitaufwand: 4 h

- **[FEAT-REC-002]** `recording_consumer()` – Consumer‑Thread schreibt streamend.
  - Erwartet: Entkoppelt per Ringpuffer; effizientes Flushen; Fehlerhandling (Speicher voll).
  - Schritte: Thread implementieren; Stresstest (simulierte langsame SD‑Karte).
  - Akzeptanz: Keine Dropouts im Echtzeit‑Pfad; definierte Strategie bei Volllauf.
  - Zeitaufwand: 6 h

- **[FEAT-REC-003]** `stop_recording()` – WAV finalisieren/schließen.
  - Erwartet: Header finalisieren (Länge), Datei robust schließen.
  - Schritte: Abschlussroutine; Prüfen Dateigröße; Integritätstest.
  - Akzeptanz: Datei von Playern lesbar; Größe = Dauer × Bitrate.
  - Zeitaufwand: 2 h

- **[FEAT-REC-004]** API Recording Steuerung (POST `/record/start`, `/record/stop`).
  - Erwartet: Start/Stop‑Endpunkte; Status/Fehlercodes.
  - Schritte: API‑Binding; Tests; UI‑Integration vorbereitet.
  - Akzeptanz: Start/Stop remote steuerbar; Datei wie erwartet erstellt.
  - Zeitaufwand: 1 h

## EP-CLI CLI (optional)

- **[FEAT-CLI-001]** `cli_main()` – Dünner CLI‑Client gegen HTTP‑API (Start/Stop/Status/Export).
  - Erwartet: Befehle `status`, `start`, `stop`, `export`, `config`; Hilfe/Usage‑Text.
  - Schritte: Typer/Click‑Skeleton; Request‑Wrapper; Fehlerhandling.
  - Akzeptanz: Alle Befehle liefern erwartete Antworten/Exit‑Codes; Doku vorhanden.
  - Zeitaufwand: 6 h

---

## Zusatzaufgaben – Dokumentation

- **Anforderungen pflegen** – `W3/Anforderungen.md` aktualisieren (Traceability: REQ→Feature, Akzeptanzkriterien).
  - Erwartet: Vollständige Zuordnung REQ→Feature; offene Punkte gepflegt.
  - Akzeptanz: Reviewfähig (Dozent); Änderungsverlauf dokumentiert.
  - Zeitaufwand: 4 h

- **API‑Dokumentation** – OpenAPI/Schema aus FastAPI prüfen/ergänzen; Endpunkte, Payloads, Beispiele.
  - Erwartet: Sauberes OpenAPI; Beispiel‑Requests/Responses.
  - Akzeptanz: Swagger UI vollständig; CI‑Lint (optional) grün.
  - Zeitaufwand: 3 h

- **JSON‑Schema** – Struktur/Beispieldateien dokumentieren (inkl. Prüfsummenprozess).
  - Erwartet: Schema/Beispiele + Prüfsummen‑Workflow.
  - Akzeptanz: Beispiel validiert; Prüfsumme verifiziert.
  - Zeitaufwand: 2 h

- **Signalverarbeitung** – Mathematische Herleitung (SPL, A/Z, F/S, Leq) kurz dokumentieren.
  - Erwartet: Formeln, Annahmen, Toleranzen; Verweis auf IEC.
  - Akzeptanz: Konsistenz mit Implementierung/Tests.
  - Zeitaufwand: 4 h

- **Kalibrier‑Prozedur** – Schrittfolge, Referenz (94 dB/1 kHz), Toleranzen, Speicherung.
  - Erwartet: Schritt‑für‑Schritt‑Guide; Screenshots/API‑Beispiele.
  - Akzeptanz: Nachvollziehbar; ±0,5 dB Ziel erreicht.
  - Zeitaufwand: 2 h

- **Testplan** – Test‑Pyramide (Unit/Integration/System), IEC‑Prüfungen, Stabilität 48 kHz/24 bit.
  - Erwartet: Testfälle/Kriterien; Automatisierungsgrad; Priorisierung.
  - Akzeptanz: Abdeckung dokumentiert; kritische Pfade adressiert.
  - Zeitaufwand: 3 h

- **Betrieb/Setup‑Guide** – Installation, Startskripte, Dienste, Troubleshooting (AGC aus, Audio‑Devices).
  - Erwartet: Setup‑Schritte; häufige Fehler/Behebung.
  - Akzeptanz: Neuer Pi in < 1 h betriebsbereit.
  - Zeitaufwand: 3 h

- **Lizenz/Hinweise** – Lizenzdatei und Third‑Party‑Hinweise pflegen.
  - Erwartet: Lizenztext; Third‑Party Lizenzen; Copyright.
  - Akzeptanz: Repo compliant.
  - Zeitaufwand: 1 h

## Zusatzaufgaben – Präsentationen & Termine

- **Zwischenbericht #1 (18.05.)** – 7–8 Slides, 10 min + Q&A. Inhalte laut `W5/termine_und_daten.md`.
  - Erwartet: Einführung, Vorgehen, Anforderungsstand, Probleme, nächstes Vorgehen; Demo (Video/GIF/Live).
  - Zeitaufwand: 6 h (Erstellung 4 h, Probe 2 h)

- **Review #2 (01.06.)** – Fortschritt SPL/GUI/API, kurze Demo.
  - Erwartet: Live‑Pegel, Start/Stop, JSON‑Schema; Lessons Learned.
  - Zeitaufwand: 4 h

- **Review #3 (15.06.)** – Zeit/Frequenzbewertungen, Stabilitätstests.
  - Erwartet: F/S, A/Z, erste Stabilität bei 48 kHz/24 bit.
  - Zeitaufwand: 4 h

- **Review #4 (29.06.)** – Spektren, Kalibrierung, Export, optional Recording.
  - Erwartet: Oktav/Terz Ergebnisse, Auto‑Kalibrierung, Export mit SHA256.
  - Zeitaufwand: 4 h

- **Abschluss/Abgabe (04.07., 00:01)** – Funktionsdemo, Doku final.
  - Erwartet: Finaler Stand; Repository aufgeräumt; Release v1.0.
  - Zeitaufwand: 4 h

- **Präsentationsvorbereitung** – Folien/Demos, Sprecher, Proben.
  - Zeitaufwand: 3 h

## Zusatzaufgaben – Hardware/3D‑Druck/Zusammenbau

- **I2S‑Verdrahtung INMP441** – gemäß `W4/Vorschläge_anforderungen.ipynb` (Pins 1/6/12/35/38; L/R → GND).
  - Erwartet: Saubere Verdrahtung; Sichtprüfung; Durchgangstest.
  - Zeitaufwand: 2 h

- **Systemkonfiguration** – `/boot/config.txt` (dtparam=i2s=on, dtoverlay=i2s-mmap), `/etc/asound.conf` (pcm.i2smic, default).
  - Erwartet: Reboot; Device sichtbar (`arecord -l`); Testaufnahme.
  - Zeitaufwand: 1 h

- **Gehäuse‑Design** – Einfaches Schutzgehäuse (REQ‑MECH‑001), Halterung für Mikrofon/Anschlüsse.
  - Erwartet: CAD‑Modell; STL exportiert; Kabelwege/Belüftung bedacht.
  - Zeitaufwand: 6 h

- **3D‑Druck** – Teile drucken, Nachbearbeitung, Passprobe.
  - Erwartet: Druckprofile; Stützstrukturen; Finish; Montageprobe.
  - Zeitaufwand: 4 h

- **Zusammenbau** – Pi, Mikro, ggf. Button/LED, Kabel, Befestigungsmaterial.
  - Erwartet: Mechanischer Aufbau; Kabelmanagement; Fotos/Protokoll.
  - Zeitaufwand: 2 h

- **Stromversorgung** – USB‑Betrieb, optional Akku‑Test (≥12 h als KANN, REQ‑PWR‑001).
  - Erwartet: Lasttest; Laufzeitmessung (bei Akku); Stabilität ok.
  - Zeitaufwand: 1 h

- **Inbetriebnahme‑Check** – Datenflussprüfung (Kurzer Test‑Read), SD‑Schreibtest, WLAN/SSH.
  - Erwartet: Checkliste abgearbeitet; Logs dokumentiert.
  - Zeitaufwand: 2 h

## Zusatzaufgaben – Tests & Validierung

- **Unit‑Tests** – SPL‑Berechnung, A‑Filter, Zeitgewichtungen, Leq.
  - Erwartet: Tests für Mathe/Filter/Zeitgewichtungen (70% Anteil der Pyramide).
  - Zeitaufwand: 6 h

- **Integrationstests** – Audio‑Pipeline Blockfluss, JSON‑Export, API‑Endpunkte.
  - Erwartet: End‑to‑End Flows; API‑Tests mit Test‑Client.
  - Zeitaufwand: 6 h

- **Systemtests (Pi)** – 5‑Min‑Stabilität 48 kHz/24 bit, Buffer‑Underruns unter Last.
  - Erwartet: Stabilität belegt; Underrun‑Zähler bleibt 0 im Normalbetrieb.
  - Zeitaufwand: 3 h

- **Validierung** – Vergleich gegen NTi XL2 (REQ‑VAL‑001), Dokumentation der Abweichungen.
  - Erwartet: Messreihe; Protokoll; Abweichungen ≤ ±1 dB (abhängig von Band/Bewertung).
  - Zeitaufwand: 4 h

---

## Hinweise zur Bearbeitung

- Priorisierung gemäß Phasen in `features.md` (Fundament → Schnittstellen → Erweiterungen → Optionales).
- Aufgaben aus optionalen Epics (REC/CLI) nur einplanen, wenn Zeitpuffer besteht.
