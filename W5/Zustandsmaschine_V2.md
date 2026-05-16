# Zustandsmaschine SPL-Meter (Raspberry Pi Zero 2 W)

Dokument-ID: W5-ZUST-16052026

Bezieht sich auf: SPL_Meter_Class_Diagram_Prototype.pdf

Zweck: Robuste, testbare Steuerlogik für Audioein-/ausgabe, DSP und Bedienung (UI/CLI) mit definierten Fehlerpfaden und Wiederanlauf.

## Namenskonvention

- Events/Trigger der Zustandsmaschine werden in snake_case notiert, z. B. start_measure, stop_measure, start_record.
- Methoden aus dem Klassendiagramm werden mit Klassennamen und Methodennamen notiert, z. B. AudioProcessor.startMeasurement().
- Guards werden in eckigen Klammern angegeben, z. B. [input_ready && calibration_valid].

## Zustände

**Boot** (Systeminitialisierung)

Zweck:
- Initialisierung des SPL-Meter-Systems nach Programmstart.

Entry:
- Konfiguration laden (Default-Konfiguration verwenden, falls keine vorhanden ist).
- Logging initialisieren.
- UI/CLI initialisieren.
- AudioDeviceManager.getDevices() ausführen.
- Geeignetes Audioeingabegerät prüfen.
- Gespeicherten Kalibrierfaktor laden.
- Speicherstatus prüfen.

Do:
- Initialisierungsergebnisse bewerten.
- Systemflags wie config_valid, input_ready, calibration_available, calibration_valid und storage_ok setzen.

Exit:
- Systemstatus an Idle oder Fehler übergeben.
- Startstatus protokollieren.

Transitions:
- Boot → Idle bei erfolgreicher Initialisierung (init_ok)
- Boot → Fehler bei kritischem Initialisierungsfehler (init_fail)


**Idle** (sicherer Wartezustand)

Zweck:
- Betriebsbereiter Wartezustand des SPL-Meters nach erfolgreicher Initialisierung.

Entry:
- Sicherstellen, dass kein Mess-, Kalibrier- oder Diagnosestream aktiv ist.
- Systemstatus in UI/CLI anzeigen.
- Benutzeraktionen freigeben.
- Ggf. Hinweis anzeigen: „Kalibrierung empfohlen“ oder „Messbereit“.

Do:
- UI/CLI-Eingaben entgegennehmen, z. B. Konfigurationsänderungen, Kalibrierstart oder Messstart.
- Aktuellen Systemstatus anzeigen.
- Verfügbare Aktionen abhängig von Statusflags aktivieren/deaktivieren.
- Warnhinweise für unkalibrierte oder nicht valide Messstarts anzeigen.

Exit:
- Auslösendes Benutzerkommando validieren und protokollieren.
- Zielzustand protokollieren.
- Sicherstellen, dass der Zielzustand exklusive Ressourcen wie Audio-Stream oder Puffer übernehmen darf.

Transitions:
- Idle → Kalibrieren bei start_calibration [input_ready].
- Idle → Messbereit bei calibration_valid_detected [input_ready && calibration_valid].
- Idle → Messen.Live bei start_measure_uncalibrated [input_ready && allow_uncalibrated].
- Idle → Diagnose bei start_diag [config_valid].
- Idle → Fehler bei error.


**Kalibrieren** (94 dB / 1 kHz Referenzabgleich)

Zweck:
- Ermittlung und Speicherung des Kalibrierfaktors anhand eines bekannten Referenzsignals von 94 dB SPL bei 1 kHz.

Entry:
- Kalibriermodus starten.
- Benutzerhinweis anzeigen: Kalibrator aufsetzen und starten.
- Audio-Stream exklusiv öffnen, damit das Referenzsignal ohne parallele Mess- oder Diagnosezugriffe erfasst werden kann.
- Kalibrierpuffer initialisieren, um Audiodaten der Kalibrierung isoliert von vorherigen Messdaten auszuwerten.
- AudioProcessor.startCalibration() aufrufen.

Do:
- Kalibriersignal erfassen.
- Signalstabilität prüfen, z. B. Pegelverlauf, Clipping und SNR.
- Pegel des Referenzsignals berechnen.
- Kalibrierfaktor bestimmen.
- Plausibilität des Kalibrierfaktors prüfen, z. B. Pegelverlauf, Clipping, SNR und dominanter Frequenzanteil bei 1 kHz.

Exit:
- Audio-Stream schließen.
- Kalibrierfaktor nur bei erfolgreicher Kalibrierung speichern, inklusive Metadaten wie Zeitstempel und Audioeingabegerät.
- Kalibrierstatus aktualisieren.
- Ergebnis in UI/CLI anzeigen und loggen.

Transitions:
- Kalibrieren → Messbereit bei calib_done [calibration_valid].
- Kalibrieren → Idle bei calib_abort.
- Kalibrieren → Idle bei calib_failed.
- Kalibrieren → Fehler bei error.


**Messbereit** (gültig kalibriert)

Zweck:
- Bereitstellung eines gültig kalibrierten Zustands vor Start einer regulären Messung.

Entry:
- Gültigen Kalibrierstatus inklusive Metadaten anzeigen.
- Messfunktionen in UI/CLI freigeben.
- Aktuelle Messkonfiguration prüfen und anzeigen.
- Systemstatus auf „messbereit“ setzen.

Do:
- Auf Benutzeraktionen warten.
- Kalibrierstatus und Audioeingang überwachen.
- Konfigurationsänderungen entgegennehmen.
- Bei messkettenrelevanten Änderungen calibration_invalidated auslösen.
- Erneute Kalibrierung ermöglichen.

Exit:
- Auslösendes Benutzerkommando protokollieren.
- Aktuelle Messkonfiguration für Zielzustand übernehmen.
- Ressourcenanforderung für Zielzustand vorbereiten.

Transitions:
- Messbereit → Messen.Live bei start_measure [input_ready && calibration_valid].
- Messbereit → Kalibrieren bei recalibrate [input_ready].
- Messbereit → Diagnose bei start_diag [config_valid].
- Messbereit → Idle bei calibration_invalidated.
- Messbereit → Fehler bei error.


**Messen** (laufende Messsession)

Zweck:
- Durchführung einer laufenden SPL-Messung.
- Oberzustand für Live-Messung und Messung mit zusätzlicher Audioaufzeichnung.

Entry:
- Messkonfiguration für die Messsession einfrieren.
- measurement_quality anhand des Kalibrierstatus setzen: valid / uncalibrated / calibration_expired.
- Bei nicht gültiger Kalibrierung Warnhinweis in UI/CLI anzeigen und Messdaten entsprechend markieren.
- AudioProcessor.startMeasurement(sampleRate) aufrufen.
  Diese Funktion initiiert bzw. umfasst:
  - Audio-Stream exklusiv öffnen.
  - Messpuffer initialisieren.
  - DSP-Pipeline starten.
- UI/CLI auf Messbetrieb umstellen.

Do:
- Audioblöcke kontinuierlich erfassen.
- AudioProcessor.processBlock(block) ausführen.
- SPL-Kennwerte berechnen bzw. aktualisieren, z. B. RMS, Fast, Slow, Leq, A/Z sowie Oktav-/Terzbandpegel.
- UI/CLI live aktualisieren.
- Messdaten und Metadaten puffern/loggen.
- Clipping, Buffer-Probleme und Device-Loss überwachen.

Exit:
- AudioProcessor.stopMeasurement() aufrufen.
- DSP-Pipeline stoppen.
- Audio-Stream schließen.
- Messpuffer finalisieren.
- Messdaten für optionalen JSON-Export vorbereiten.
- Messstatus protokollieren.
- UI/CLI aus Messbetrieb zurücksetzen.

Transitions:
- Messen → Idle bei stop_measure.
- Messen → Fehler bei error.


**Messen.Live** (Messung ohne Recording)

Zweck:
- Laufende SPL-Messung ohne zusätzliche Audioaufzeichnung.

Entry:
- Recording-Status auf „inaktiv“ setzen.
- UI/CLI so setzen, dass „Aufzeichnung starten“ verfügbar ist.

Do:
- Live-Messwerte anzeigen und aktualisieren.
- Keine zusätzliche Audiodatei schreiben.

Exit:
- Keine Messressourcen schließen, da der Oberzustand Messen weiter aktiv sein kann.

Transitions:
- Messen.Live → Messen.Aufzeichnung bei start_record [storage_ok].


**Messen.Aufzeichnung** (Messung mit Recording)

Zweck:
- Laufende SPL-Messung mit zusätzlicher Audioaufzeichnung.

Entry:
- Aufzeichnungsdatei öffnen.
- Aufzeichnungsmetadaten schreiben, z. B.:
  - Startzeit.
  - Messkonfiguration.
  - Kalibrierstatus.
  - measurement_quality.
  - Audioeingabegerät.
- Checksumme/Integritätsprüfung vorbereiten.
- Recording-Status in UI/CLI setzen.
- AudioProcessor.startRecording() aufrufen.

Do:
- SPL-Messung aus dem Oberzustand Messen fortführen.
- Audiostream zusätzlich in Datei schreiben.
- Dateigröße und Speicherstatus überwachen.
- Checksumme fortlaufend aktualisieren.
- UI/CLI mit Recording-Status aktualisieren.

Exit:
- Aufzeichnung stoppen.
- Datei sauber schließen.
- Checksumme finalisieren.
- Aufzeichnungsmetadaten speichern.
- Ergebnis loggen und in UI/CLI anzeigen.

Transitions:
- Messen.Aufzeichnung → Messen.Live bei stop_record.


**Diagnose** (Systemtests)

Zweck:
- Durchführung definierter Systemtests ohne reguläre Messung.

Entry:
- Diagnosemodus starten.
- Reguläre Messung/Aufzeichnung blockieren.
- Auszuwählende Diagnosejobs vorbereiten.
- UI/CLI auf Diagnosemodus umstellen.

Do:
- Audiopfadtest ausführen.
- Latenz-/Puffer-Test ausführen.
- Speichertest ausführen.
- Optional Performance-/CPU-Test ausführen.
- Ergebnisse als PASS/FAIL bewerten und Ursachen erfassen.
- Einzelne Diagnosejobs prüfen zusätzliche Voraussetzungen, z. B. input_ready für Audiopfadtests.

Exit:
- Diagnoseergebnisse speichern/loggen.
- UI/CLI mit Ergebnis aktualisieren.
- Genutzte Ressourcen freigeben.
- Statusflags ggf. aktualisieren.

Transitions:
- Diagnose → Idle bei diag_done.
- Diagnose → Fehler bei error.


**Fehler** (sicherer Fehlerzustand)

Zweck:
- Sicherer Zustand bei kritischen technischen Fehlern mit definierter Fehlerbehandlung und Wiederanlaufstrategie.

Entry:
- Kritischen Fehler erfassen und klassifizieren.
- Audio-Stream und andere exklusive Ressourcen schließen.
- Laufende Aufzeichnung sicher beenden und ggf. als unvollständig markieren.
- Fehler in UI/CLI anzeigen.
- Fehler mit Zeitpunkt, vorherigem Zustand und Fehlerklasse protokollieren.
- Recovery-Strategie vorbereiten.

Do:
- System in sicherem Zustand halten.
- Benutzeraktionen wie recover, retry oder shutdown entgegennehmen.
- Je nach Fehlerklasse Wiederherstellungsversuche durchführen.
- Recovery-Status in UI/CLI aktualisieren.

Exit:
- Recovery-Ergebnis protokollieren.
- Fehlerstatus zurücksetzen, falls behoben.
- Statusflags wie input_ready, storage_ok und calibration_valid aktualisieren.
- System in Idle übergeben.

Transitions:
- Fehler → Idle bei recover.
- Fehler → Fehler bei retry_failed.
- Fehler → [*] bei shutdown.

## Ereignisse / Trigger

- **init_ok / init_fail**: Ergebnis der Systeminitialisierung im Zustand Boot.
- **start_calibration**: Benutzer startet eine Kalibrierung über UI/CLI.
- **recalibrate**: Benutzer startet aus dem messbereiten Zustand eine erneute Kalibrierung.
- **calib_done**: Kalibrierung wurde erfolgreich abgeschlossen.
- **calib_abort**: Kalibrierung wurde durch den Benutzer abgebrochen.
- **calib_failed**: Kalibrierung wurde durchgeführt, aber das Signal oder der Kalibrierfaktor war nicht plausibel.
- **calibration_valid_detected**: Eine gültige gespeicherte Kalibrierung wurde erkannt.
- **calibration_invalidated**: Die bisher gültige Kalibrierung wurde ungültig, z. B. durch Änderung der Messkette.
- **start_measure**: Benutzer startet eine reguläre Messung.
- **start_measure_uncalibrated**: Benutzer startet eine erlaubte Testmessung ohne gültige Kalibrierung.
- **stop_measure**: Benutzer beendet die laufende Messung.
- **start_record / stop_record**: Benutzer startet bzw. beendet die zusätzliche Audioaufzeichnung während der Messung.
- **start_diag / diag_done**: Benutzer startet eine Diagnose bzw. Diagnose wurde abgeschlossen.
- **error**: Kritischer technischer Fehler wurde erkannt.
- **recover**: Fehler wurde behoben bzw. Wiederherstellung war erfolgreich.
- **retry_failed**: Wiederherstellungsversuch ist fehlgeschlagen.
- **shutdown**: System bzw. Anwendung wird beendet.

## Guards / Statusflags (Bedingungen)

- **config_valid**: Die Systemkonfiguration wurde geladen und ist plausibel. Sie enthält gültige Parameter wie Abtastrate, Wortbreite, Audioquelle, Bewertungsarten und Exportoptionen.

- **input_ready**: Ein geeignetes Audioeingabegerät ist vorhanden und für den Betrieb verwendbar.

- **calibration_available**: Ein gespeicherter Kalibrierfaktor ist vorhanden.

- **calibration_valid**: Ein Kalibrierfaktor ist vorhanden und für die aktuelle Messkette gültig. Dabei ggf. Zeitstempel, Audioeingabegerät, Konfiguration und Plausibilität des Faktors berücksichtigen.

- **storage_ok**: Der Speicher ist verfügbar und beschreibbar.

- **allow_uncalibrated**: Eine unkalibrierte Testmessung ist konfigurationsseitig erlaubt. In diesem Fall darf eine Messung auch ohne gültige Kalibrierung gestartet werden, muss aber entsprechend markiert werden.

- **measurement_quality**: Kennzeichnung der Messvalidität einer laufenden Messung. Mögliche Werte sind `valid`, `uncalibrated` und `calibration_expired`. Dieser Wert wird in UI, Logging und Export übernommen.


