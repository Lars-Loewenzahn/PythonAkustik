 # Zustandsmaschine SPL‑Meter (Raspberry Pi Zero W)

 Dokument-ID: W3-ZUST-20260430

 Bezieht sich auf: REQ-ARCH-001, REQ-DIAG-001, REQ-ERR-001 in `W3/Anforderungen.md`

 Zweck: Robuste, testbare Steuerlogik für Audioein-/ausgabe, DSP und Bedienung (GUI/CLI) mit definierten Fehlerpfaden und Wiederanlauf.

 ## Statechart (Mermaid)

 ```mermaid
 stateDiagram-v2
   [*] --> Boot
   Boot --> Idle: init_ok
   Boot --> Fehler: init_fail

   Idle --> Messen: start_measure [input_ready && (calibrated || allow_uncalibrated)]
   Messen --> Idle: stop_measure
   Messen --> Kalibrieren: start_calibration
   Kalibrieren --> Idle: calib_done
   Kalibrieren --> Fehler: calib_abort

   Idle --> Diagnose: start_diag
   Diagnose --> Idle: diag_done

   state Messen {
     [*] --> Aktiv
     Aktiv --> Aufzeichnen: start_record
     Aufzeichnen --> Aktiv: stop_record
     Aktiv --> Fehler: error
     Aufzeichnen --> Fehler: error
   }

   Fehler --> Idle: recover
   note right of Fehler: Streams schließen, sicherer Zustand, Backoff-Retry
 ```

 ## Zustände (Verantwortung, Entry/Exit)

 - **Boot**
   - Entry: Konfiguration laden; Audio-Backends (USB/I2S) scannen; Filterkoeffizienten (A/Z, Oktav/Terz) vorberechnen; Logging initialisieren.
   - Exit: Systemkontext vollständig befüllt (input_ok, config_ok).

 - **Idle**
   - Do: GUI/CLI bedienen; geringer Ressourcenverbrauch; Statusanzeigen.
   - Exit: Übergang eröffnet exklusive Ressourcen (Audio-Stream, Puffer).

 - **Messen.Aktiv**
   - Entry: Audio-Stream öffnen; DSP-Pipeline starten (Zeit-/Frequenzbewertungen, Leq, Bänder); periodische JSON-Updates.
   - Do: Fensterweise Verarbeitung; Clipping-/Underrun-Detektion; GUI aktualisieren.
   - Exit: DSP anhalten; Puffer spülen.

 - **Messen.Aufzeichnen**
   - Entry: Audiodatei/Container öffnen; Metadaten/Checksum initialisieren.
   - Exit: Datei atomar schließen; Checksumme schreiben; Statistik protokollieren.

 - **Kalibrieren**
   - Entry: 94 dB @ 1 kHz Ablauf starten; Signal erfassen; Kalibrierfaktor berechnen/speichern (gerätebezogen).
   - Exit: Vorzustand wiederherstellen (Streams/DSP), Status protokollieren.

 - **Diagnose**
   - Do: Audiopfadtest, Latenz-/Puffer-Test, Speichertest; Ergebnisse mit PASS/FAIL und Ursachen loggen.

 - **Fehler**
   - Entry: Streams schließen; sichere Defaults; Benutzerhinweis; Telemetrie.
   - Do: Recovery mit exponentiellem Backoff; beschränkte Re-Init-Versuche.
   - Exit: Erfolgreiche Wiederherstellung führt zu `Idle`.

 ## Ereignisse (Trigger)

 - **init_ok / init_fail**: Ergebnis der Systeminitialisierung (Boot).
 - **start_measure / stop_measure**: Start/Stop Messbetrieb aus GUI/CLI/API.
 - **start_calibration / calib_done / calib_abort**: Kalibrierzyklus.
 - **start_record / stop_record**: Mitschnitt toggeln (nur im Messbetrieb).
 - **start_diag / diag_done**: Diagnoseroutinen ausführen/abschließen.
 - **error / recover**: Fehler erkannt / erfolgreiche Wiederherstellung.

 ## Guards (Bedingungen)

 - **input_ready**: Eingabegerät vorhanden und geöffnet (USB UAC oder I2S), stabile Pufferung.
 - **calibrated**: Kalibrierfaktor vorhanden und gültig (z. B. jüngstes Datum, Konsistenzprüfung).
 - **allow_uncalibrated**: Konfigurierbare Ausnahme für Vorabtests ohne Kalibrierung.

 ## Fehlerklassen und Reaktionen (REQ-ERR-001)

 - **device_lost** (Mikrofon getrennt): Wechsel nach `Fehler`, Streams schließen, Auto-Reconnect; bei Erfolg `recover` → `Idle`.
 - **buffer_underrun/overflow**: Loggen, Versuch Puffergrößen anzupassen; bei Persistenz → `Fehler`.
 - **clip_detected**: Benutzerhinweis; kein Zustandswechsel, aber Messwert-Flag.
 - **storage_full/checksum_fail**: Aufzeichnung stoppen; Integrität melden; ggf. `Fehler`.

 ## Testbarkeit (Akzeptanzbeispiele)

 - **Boot→Idle**: Mit angeschlossenem USB-Mikrofon; `init_ok` ausgelöst; GUI zeigt „bereit“ in < 10 s.
 - **Idle→Messen**: 48 kHz/24 bit ohne Underruns ≥ 5 min; Leq/FS/AZ plausibel.
 - **Messen:Aufzeichnen**: Datei ohne Dropouts; Checksumme verifiziert.
 - **Kalibrieren**: 94 dB @ 1 kHz → Abweichung ≤ ±0,5 dB zum Referenzgerät.
 - **Fehlerpfad**: Device unplug → `Fehler` → Replug → `recover` → `Idle`.

 ## Implementierungshinweis (informativ)

 - **Event-Engine**: Python `asyncio` als Dispatcher.
 - **State-Framework**: `transitions` (pytransitions) für Zustände/Guards/Actions.
 - **Audio/DSP**: Callback-Thread (PortAudio/ALSA) → threadsicher in Async-Queue; DSP mit `numpy/scipy.signal` (SOS, A/Z, Bänder).

 Ende des Dokuments.
