 # Anforderungen SPL-Meter (Raspberry Pi Zero W)

 Dokument-ID: W3-ANF-20260428

 Quellen:
 - Meeting: W3/Meeting_20260428.txt (28.04.2026)
 - Stil/Leitlinien: W3/anforderungen_simon.txt
 - Formatvorlage: W3/Anforderungen.pdf (Stand nicht einsehbar; Format wird bei Bedarf nachgezogen)

 Geltungsbereich:
 - Entwicklung eines schallpegelmessenden Systems (SPL-Meter) auf Basis Raspberry Pi Zero W mit Python.

 Normative/Referenzdokumente:
 - IEC 61672-2 (Zeitgewichtungen und Prüfverfahren), IEC 61672-1 (Begriffe/Leistungsanforderungen) sofern anwendbar.

 ## ID-Schema und Schreibweise
 - ID: `REQ-<KATEGORIE>-<laufende Nr.>` (z. B. `REQ-FUNC-001`).
 - Priorität: MUSS/KANN.
 - Anforderungen sind unteilbar, aktiv formuliert und testbar (Akzeptanzkriterium).
 - Hierarchie: Grobe Anforderungen können über Unterpunkte verfeinert werden (z. B. 001.a, 001.b).

 ## Annahmen und Randbedingungen
 - Ein einzelnes Mikrofon wird verwendet (keine Richtcharakteristikkompensation).
 - Web-GUI soll leichtgewichtig sein (Streamlit präferiert).
 - Kein dediziertes Display am Gerät.

 ---

 ## Funktionale Anforderungen

 - ID: REQ-FUNC-001
   Titel: Digitaler Audioeingang (USB oder I2S)
   Priorität: MUSS
   Beschreibung: Das System verarbeitet in Echtzeit ein digitales Audiosignal eines angeschlossenen Mikrofons über USB (UAC) oder I2S.
   Akzeptanzkriterium/Test: Bei 48 kHz/24 bit kontinuierliche Rahmenverarbeitung ohne Buffer-Underruns über ≥5 Minuten; Quelle/Interface wird erkannt und ausgewählt.
   Quelle: Meeting Zeilen 7–9

 - ID: REQ-FUNC-002
   Titel: Echtzeit-SPL-Berechnung
   Priorität: MUSS
   Beschreibung: Das System berechnet kontinuierlich SPL-Kennwerte aus dem Audiostream in quasi-Echtzeit.
   Akzeptanzkriterium/Test: Sichtbar flüssige Aktualisierung in der GUI; Log zeigt keine Verarbeitungsüberläufe bei 48 kHz/24 bit über ≥5 Minuten.
   Quelle: Meeting Zeilen 8

 - ID: REQ-FUNC-003
   Titel: Zeitbewertungen (F, S) und Leq
   Priorität: MUSS
   Beschreibung: Das System stellt Zeitgewichtungen „Fast (F)“ und „Slow (S)“ sowie die energieäquivalente Größe Leq bereit gemäß IEC 61672.
   Akzeptanzkriterium/Test: Verifikation der Zeitkonstanten über Testsignale gemäß IEC 61672-2; Leq über definierte Testdauer korrekt.
   Quelle: Meeting Zeilen 9, 21–26

 - ID: REQ-FUNC-004
   Titel: Frequenzbewertungen A und Z
   Priorität: MUSS
   Beschreibung: Das System wendet A- und Z-Bewertung auf den Messkanal an.
   Akzeptanzkriterium/Test: Frequenzgangprüfung mit Sinus-Sweeps; Toleranzen gemäß IEC 61672-1/-2 eingehalten.
   Quelle: Meeting Zeilen 10, 25

 - ID: REQ-FUNC-005
   Titel: Oktav- und Terzbandanalyse
   Priorität: MUSS
   Beschreibung: Das System berechnet bandbegrenzte Pegel in Oktav- und Terzbändern (logarithmische Aufteilung).
   Akzeptanzkriterium/Test: Prüfspektren in Referenzbändern liefern korrekte Bandpegel innerhalb definierter Toleranzen.
   Quelle: Meeting Zeilen 11, 33–35

 - ID: REQ-FUNC-006
   Titel: Webbasierte GUI
   Priorität: MUSS
   Beschreibung: Eine leichtgewichtige, webbasierte GUI stellt Live-Werte, Start/Stop, Konfiguration und Export bereit (Streamlit präferiert).
   Akzeptanzkriterium/Test: Zugriff über Browser im gleichen Netzwerk; GUI-Start < 10 s; Funktionen bedienbar.
   Quelle: Meeting Zeilen 12, 39–41, 77–79

 - ID: REQ-FUNC-007
   Titel: JSON-Ausgabeformat
   Priorität: MUSS
   Beschreibung: Mess- und Metadaten können als JSON exportiert werden.
   Akzeptanzkriterium/Test: Export erzeugt valide JSON-Datei mit Zeitstempeln, Konfiguration und Messwerten; Schema dokumentiert.
   Quelle: Meeting Zeilen 77–79

 - ID: REQ-FUNC-008
   Titel: Kalibrierfunktion 94 dB @ 1 kHz
   Priorität: MUSS
   Beschreibung: Das System erlaubt die Kalibration mit 94 dB bei 1 kHz und speichert den Kalibrierfaktor gerätebezogen.
   Akzeptanzkriterium/Test: Nach Kalibrierung weichen Messwerte bei 94 dB/1 kHz ≤ ±0,5 dB vom Referenzgerät ab.
   Quelle: Meeting Zeilen 64–67, 14–16

 - ID: REQ-FUNC-009
   Titel: CLI/TUI-Steuerung
   Priorität: KANN
   Beschreibung: Das System bietet zusätzlich eine Befehlszeilen- oder Textoberfläche lokal (USB/seriell) und/oder remote (SSH).
   Akzeptanzkriterium/Test: Start/Stop/Konfiguration per CLI möglich; Hilfetext vorhanden; Verbindung über USB/seriell und SSH getestet.
   Quelle: Meeting Zeilen 17, 43–44

 - ID: REQ-FUNC-010
   Titel: Audioaufzeichnung der Messung
   Priorität: KANN
   Beschreibung: Optionales Mitschneiden des Audiostroms parallel zur Pegelberechnung.
   Akzeptanzkriterium/Test: Aktivierte Aufzeichnung erzeugt Audiodatei ohne Dropouts; Dateigröße entspricht Dauer und Format.
   Quelle: Meeting Zeilen 14

 - ID: REQ-FUNC-011
   Titel: Integration in „tapy“ (TUB Sensorlibrary)
   Priorität: KANN
   Beschreibung: Das System stellt eine CLI/API bereit, die eine Einbindung in „tapy“ ermöglicht.
   Akzeptanzkriterium/Test: Beispielintegration demonstriert Befehle für Start/Stop/Abfrage; Dokumentation vorhanden.
   Quelle: Meeting Zeilen 74–76

 ---

 ## Qualitäts-, Leistungs- und Schnittstellenanforderungen

 - ID: REQ-PERF-001
   Titel: Unterstützte Abtastraten
   Priorität: MUSS
   Beschreibung: Das System unterstützt Abtastraten bis einschließlich 48 kHz.
   Akzeptanzkriterium/Test: Verifikation mit 48 kHz Eingangsquelle; stabile Verarbeitung ohne Underruns.
   Quelle: Meeting Zeilen 45–47

 - ID: REQ-PERF-002
   Titel: Wortbreite/Datenpfad
   Priorität: MUSS
   Beschreibung: Externe Wortbreite 24 bit; interne 32-bit-Verarbeitung ist zulässig/unterstützt.
   Akzeptanzkriterium/Test: Signalpfadprüfung zeigt 24-bit Eingabe; interne Berechnung in 32-bit möglich.
   Quelle: Meeting Zeilen 51–53

 - ID: REQ-QUAL-001
   Titel: Keine automatische Pegelregelung
   Priorität: MUSS
   Beschreibung: Es wird keine automatische Verstärkungsregelung (AGC) eingesetzt; Gain ist fest/definiert.
   Akzeptanzkriterium/Test: Pegeländerungen im Eingang führen proportionalen Änderungen ohne AGC-Artefakte.
   Quelle: Meeting Zeilen 69–70

 - ID: REQ-INTF-001
   Titel: Kommunikationsschnittstellen
   Priorität: MUSS
   Beschreibung: Steuerung/Datenausgabe wahlweise über Netzwerk (WiFi/SSH) und/oder USB (seriell/CDC) möglich.
   Akzeptanzkriterium/Test: Verbindungen aufgebaut; Kommandos erfolgreich; Datenübertragung verifiziert.
   Quelle: Meeting Zeilen 43–44, 71–73

 - ID: REQ-NET-001
   Titel: Nutzung des WiFi-Chips
   Priorität: MUSS
   Beschreibung: Der integrierte WiFi-Chip des Pi Zero W wird für GUI/Remote-Zugriff genutzt.
   Akzeptanzkriterium/Test: GUI-Zugriff über WLAN; CLI-Zugriff via SSH.
   Quelle: Meeting Zeilen 71–73

 - ID: REQ-DATA-001
   Titel: Checksummen für Datenintegrität
   Priorität: MUSS
   Beschreibung: Exportierte Dateien enthalten eine Checksumme zur Integritätsprüfung.
   Akzeptanzkriterium/Test: Prüfsumme erkennt gezielte Bitfehler; Verifikationsskript vorhanden.
   Quelle: Meeting Zeilen 80–82

 - ID: REQ-DATA-002
   Titel: Speicherbedarf und -strategie
   Priorität: KANN
   Beschreibung: Mindestens 500 MB freier Speicher werden unterstützt; differenzbasierte Speicherung (Delta-Encoding) optional.
   Akzeptanzkriterium/Test: 12 h Messdaten (ohne Audio) speicherbar; Delta-Strategie reduziert Dateigröße messbar.
   Quelle: Meeting Zeilen 21–23, 66–67, 60–62

 - ID: REQ-PWR-001
   Titel: Energieversorgung
   Priorität: MUSS/KANN
   Beschreibung: USB-Betrieb MUSS unterstützt werden; Akkubetrieb für ≥12 h ist KANN.
   Akzeptanzkriterium/Test: Betrieb über USB stabil; mit geeignetem Akku Laufzeitnachweis ≥12 h.
   Quelle: Meeting Zeilen 57–63

 - ID: REQ-MECH-001
   Titel: Gehäuse
   Priorität: KANN
   Beschreibung: Ein einfaches Schutzgehäuse für Elektronik und Mikrofonanschluss wird bereitgestellt.
   Akzeptanzkriterium/Test: Gehäuse schützt vor Berührung/Transport; Anschlüsse zugänglich.
   Quelle: Meeting Zeilen 54–56

 - ID: REQ-UI-001
   Titel: Kein lokales Display
   Priorität: MUSS
   Beschreibung: Am Gerät ist kein dediziertes Anzeige-Display vorgesehen; GUI ausschließlich webbasiert.
   Akzeptanzkriterium/Test: System startet ohne Display; GUI bedienbar.
   Quelle: Meeting Zeilen 37–38

 - ID: REQ-MIC-001
   Titel: Mikrofon und Richtcharakteristik
   Priorität: MUSS
   Beschreibung: System ist für ein einzelnes Mikrofon ohne Richtcharakteristikkompensation ausgelegt.
   Akzeptanzkriterium/Test: Messkette mit Single-Channel validiert; keine Richtungsfilter aktiv.
   Quelle: Meeting Zeilen 27–31, 48–50

 - ID: REQ-STD-001
   Titel: Zeitgewichtungen gemäß IEC 61672-2
   Priorität: MUSS
   Beschreibung: Implementierte Zeitgewichtungen entsprechen IEC 61672-2.
   Akzeptanzkriterium/Test: Standardkonforme Prüfungen bestanden (Protokoll).
   Quelle: Meeting Zeilen 25–26

 - ID: REQ-LIC-001
   Titel: Lizenzmodell
   Priorität: MUSS/KANN
   Beschreibung: Open-Source-Lizenz bevorzugt (z. B. GPLv3), finale Lizenz wird festgelegt.
   Akzeptanzkriterium/Test: Lizenzdateien im Repo vorhanden; rechtliche Prüfung erfolgt.
   Quelle: Meeting Zeilen 83–85

 - ID: REQ-VAL-001
   Titel: Vergleich gegen Referenzmessgerät
   Priorität: MUSS
   Beschreibung: Validierung der Messergebnisse durch Vergleich mit NTi Audio XL2 innerhalb definierter Toleranzen.
   Akzeptanzkriterium/Test: Abweichung bei Referenztests ≤ ±1 dB (Band-/Bewertungsabhängig zu präzisieren).
   Quelle: Meeting Zeilen 86–90

 ---

 ## Zustandsmaschine, Diagnose und Fehlerhandling

 - ID: REQ-ARCH-001
   Titel: Zustandsmaschine
   Priorität: MUSS
   Beschreibung: Das System implementiert klar definierte Zustände: Boot → Idle → Messen → (optional) Aufzeichnen → Kalibrieren → Diagnose → Fehler; Zustandsübergänge sind definiert und wiederanlaufrobust.
   Akzeptanzkriterium/Test: UML- oder Zustandsdiagramm vorhanden; Neustart in jedem Zustand möglich ohne Datenverlust/Korruption.
   Quelle: anforderungen_simon.txt Zeilen 16–19, 21–23

 - ID: REQ-DIAG-001
   Titel: Diagnosejobs pro Substate
   Priorität: MUSS
   Beschreibung: Für wesentliche Substates existieren Diagnosefunktionen (z. B. Audiopfadtest, Latenztest, Speichertest).
   Akzeptanzkriterium/Test: Diagnoseaufrufe liefern PASS/FAIL mit Log; Fehlerursachen werden ausgewiesen.
   Quelle: anforderungen_simon.txt Zeilen 20–23

 - ID: REQ-ERR-001
   Titel: Fehlerbehandlung
   Priorität: MUSS
   Beschreibung: Fehler (z. B. fehlendes Mikrofon, Übersteuerung, Buffer-Underruns) werden erkannt, geloggt und führen zu definiertem Degradations- oder Recovery-Verhalten.
   Akzeptanzkriterium/Test: Injektion definierter Fehler erzeugt erwartete Reaktionen und Logs; System bleibt bedienbar oder wechselt in Fehlerzustand.
   Quelle: anforderungen_simon.txt Zeilen 21–23

 ---

 ## Projekt- und Prozessrahmen (informativ)

 - ID: REQ-PROC-001
   Titel: Lieferzyklen
   Priorität: KANN
   Beschreibung: Entwicklung in zweiwöchigen Iterationen mit sichtbaren Zwischenständen.
   Akzeptanzkriterium/Test: Review-Meetings alle zwei Wochen; funktionsfähige Inkremente.
   Quelle: Meeting Zeilen 86–88

 ---

 ## Offene Punkte/Klärungen
 - „SSI oder USB als Commandline Schnittstelle“: Ist „SSH“ oder serielle Schnittstelle gemeint? (Präzisierung nötig)
 - Ziel-Toleranzen für IEC-Konformität (Band-/Bewertungsabhängig) festlegen.
 - „24 bit / Datenrate 32 möglich“: Exakte Vorgaben für interne Wortbreite/Speicherformat präzisieren.
 - Speicherziel „500 MB“: Mindestkapazität Geräteseite oder Projektannahme?
 - Gehäuseanforderungen (IP-Schutz, Befestigung, Abmessungen) spezifizieren.
 - Lizenzfestlegung finalisieren (GPLv3 oder Alternative).

 ---

 Ende des Dokuments.
