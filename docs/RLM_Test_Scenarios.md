# RLM Test Scenarios

**Zweck:** Demonstrieren der Vorteile von RLM gegenüber RAG, Volltextsuche und einfachen LLM-Abfragen.

---

## Testdokumente

| Dokument | Größe | Sprache | Typ |
|----------|-------|---------|-----|
| UStR 2000 | 2.2M Zeichen | Deutsch | Steuerrichtlinie |
| Beliebiger Vertrag | 50-200 Seiten | Deutsch/Englisch | Legal |
| Technische Spec | 100+ Seiten | Englisch | Dokumentation |

---

## Test 1: Vollständige Listen extrahieren

**Schwäche von RAG:** Chunking schneidet Listen ab → nur 3-5 von 8 Items
**Schwäche von LLM:** Halluziniert fehlende Items oder fasst zusammen

### Testfrage (UStR)
```
Welche Voraussetzungen müssen erfüllt werden beim EUSt-Abzug
bei kostenpflichtigen Reparaturen in fremdem Auftrag?
```

### Erwartete Antwort
- Quelle: **Rz 1859a** (Abschnitt 12.1.3.4.3)
- Genau **8 Voraussetzungen** verbatim
- Keine Paraphrasierung

### Bewertungskriterien
| Methode | Erwartetes Ergebnis |
|---------|---------------------|
| Volltextsuche | Findet Stelle, aber keine Strukturierung |
| RAG | 4-6 Items, keine Rz-Referenz |
| Einfaches LLM | Halluziniert/synthetisiert 5-6 generische Items |
| **RLM** | Alle 8 Items verbatim + Rz 1859a Zitat |

---

## Test 2: Präzise Quellenangabe

**Schwäche von RAG:** Verliert Metadaten (Rz-Nummer, Seitenzahl)
**Schwäche von LLM:** Erfindet plausible aber falsche Referenzen

### Testfrage
```
In welcher Randziffer wird der EUSt-Abzug bei Reparaturen
in fremdem Auftrag geregelt?
```

### Erwartete Antwort
- **Rz 1859a**
- Abschnitt 12.1.3.4.3
- Seitenzahl (falls im Dokument)

### Bewertungskriterien
| Methode | Erwartetes Ergebnis |
|---------|---------------------|
| Volltextsuche | Kann Rz finden, aber ohne Kontext |
| RAG | Oft falsche oder keine Rz-Nummer |
| Einfaches LLM | Erfindet plausible Rz (z.B. "Rz 1234") |
| **RLM** | Korrekte Rz 1859a mit Verifikation |

---

## Test 3: Negativ-Test (Information nicht vorhanden)

**Schwäche von RAG:** Findet ähnliche aber falsche Passagen
**Schwäche von LLM:** Halluziniert eine plausible Antwort

### Testfrage
```
Was sind die Voraussetzungen für den Vorsteuerabzug
bei Kryptowährungstransaktionen?
```

### Erwartete Antwort
- "Keine spezifische Regelung im Dokument gefunden"
- Oder: Verweis auf allgemeine Vorsteuerabzugsregeln (falls vorhanden)
- **Keine Erfindung** von Krypto-spezifischen Regeln

### Bewertungskriterien
| Methode | Erwartetes Ergebnis |
|---------|---------------------|
| Volltextsuche | Keine Treffer (korrekt) |
| RAG | Findet irrelevante "ähnliche" Passagen |
| Einfaches LLM | Erfindet plausible Krypto-Steuerregeln |
| **RLM** | Ehrlich: "Nicht gefunden" oder allg. Regeln |

---

## Test 4: Spracherhaltung

**Schwäche von LLM:** Übersetzt automatisch ins Englische

### Testfrage (auf Deutsch, deutsches Dokument)
```
Was besagt § 12 UStG bezüglich ermäßigter Steuersätze?
```

### Erwartete Antwort
- Antwort **auf Deutsch**
- Originaltext verbatim (nicht übersetzt)
- Korrekte Paragraphenreferenz

### Bewertungskriterien
| Methode | Erwartetes Ergebnis |
|---------|---------------------|
| RAG | Oft gemischte Sprache |
| Einfaches LLM | Antwortet auf Englisch |
| **RLM** | Deutsch, verbatim aus Dokument |

---

## Test 5: Tiefe Dokumentstruktur

**Schwäche von RAG:** Chunking zerstört hierarchische Struktur
**Schwäche von Volltextsuche:** Kein Verständnis für Kontext

### Testfrage
```
Welche Unterabschnitte enthält Abschnitt 12.1.3
und was regeln sie jeweils?
```

### Erwartete Antwort
- Liste aller Unterabschnitte (12.1.3.1, 12.1.3.2, etc.)
- Kurzbeschreibung jedes Abschnitts
- Hierarchische Struktur erkennbar

### Bewertungskriterien
| Methode | Erwartetes Ergebnis |
|---------|---------------------|
| Volltextsuche | Findet nur einzelne Treffer |
| RAG | Vermischt verschiedene Abschnitte |
| Einfaches LLM | Kann Struktur nicht erfassen |
| **RLM** | Iterative Navigation durch Struktur |

---

## Test 6: Cross-Reference innerhalb Dokument

**Schwäche von RAG:** Chunks sind isoliert, keine Querverweise

### Testfrage
```
Rz 1859a verweist auf welche anderen Randziffern?
Was steht in diesen?
```

### Erwartete Antwort
- Liste der referenzierten Rz-Nummern
- Inhalt dieser Referenzen
- Zusammenhang erklärt

### Bewertungskriterien
| Methode | Erwartetes Ergebnis |
|---------|---------------------|
| Volltextsuche | Findet nur die Zahlen |
| RAG | Kann Querverweise nicht auflösen |
| **RLM** | Iterativ: erst Rz finden, dann Referenzen folgen |

---

## Test 7: Große Zahlen / Beträge extrahieren

**Schwäche von LLM:** Zahlen werden oft falsch wiedergegeben

### Testfrage
```
Welche Betragsgrenze gilt für die Kleinunternehmerregelung
nach § 6 Abs. 1 Z 27 UStG?
```

### Erwartete Antwort
- Exakter Betrag aus dem Dokument
- Keine gerundete oder erfundene Zahl

### Bewertungskriterien
| Methode | Erwartetes Ergebnis |
|---------|---------------------|
| Einfaches LLM | Oft falsche/veraltete Beträge |
| **RLM** | Verbatim aus aktuellem Dokument |

---

## Test 8: Zeitliche Gültigkeit

**Schwäche von LLM:** Training-Cutoff, veraltete Informationen

### Testfrage
```
Welche Änderungen wurden mit der letzten Novelle
(GZ 2025-0.986.432) eingeführt?
```

### Erwartete Antwort
- Spezifische Änderungen aus dem Dokument
- Datum der Novelle
- Betroffene Paragraphen

### Bewertungskriterien
| Methode | Erwartetes Ergebnis |
|---------|---------------------|
| Einfaches LLM | Weiß nichts über 2025-Novelle |
| RAG | Kann Änderungen nicht isolieren |
| **RLM** | Sucht gezielt nach GZ-Nummer, extrahiert Neuerungen |

---

---

## Test 9: Synonyme / Semantische Suche

**Stärke von RAG:** Embeddings finden semantisch ähnliche Begriffe
**Lösung bei RLM:** Claude generiert Synonyme vor der Suche

### Testfrage
```
What are the conditions for input tax credit on imported goods?
```

### Dokument enthält
- "Vorsteuerabzug" (nicht "input tax credit")
- "EUSt" (nicht "imported goods VAT")
- "Voraussetzungen" (nicht "conditions")

### Erwartete RLM-Vorgehensweise
1. Claude denkt: "input tax credit" = "Vorsteuerabzug", "EUSt"
2. Claude sucht: `search.py doc.txt "Vorsteuer" "EUSt" "Einfuhr" "Voraussetzung"`
3. Findet relevante Stelle trotz anderer Terminologie

### Bewertungskriterien
| Methode | Erwartetes Ergebnis |
|---------|---------------------|
| Volltextsuche | ❌ Findet nichts (falsche Sprache) |
| RAG | ✅ Embeddings finden semantische Ähnlichkeit |
| Einfaches LLM | ⚠️ Könnte halluzinieren |
| **RLM** | ✅ Claude expandiert Synonyme vor Suche |

### Fazit
RAG hat hier einen natürlichen Vorteil. RLM kompensiert durch Claude's Sprachverständnis für Synonym-Expansion.

---

## Zusammenfassung: Wann schlägt RLM andere Methoden?

| Szenario | Volltextsuche | RAG | Einfaches LLM | RLM |
|----------|---------------|-----|---------------|-----|
| Vollständige Listen | ❌ | ⚠️ | ❌ | ✅ |
| Präzise Quellenangabe | ⚠️ | ❌ | ❌ | ✅ |
| Negativ-Test (nicht vorhanden) | ✅ | ❌ | ❌ | ✅ |
| Spracherhaltung | ✅ | ⚠️ | ❌ | ✅ |
| Dokumentstruktur | ❌ | ❌ | ❌ | ✅ |
| Cross-References | ❌ | ❌ | ❌ | ✅ |
| Exakte Zahlen/Beträge | ✅ | ⚠️ | ❌ | ✅ |
| Aktualität (neueste Änderungen) | ✅ | ⚠️ | ❌ | ✅ |
| **Synonyme/Semantik** | ❌ | **✅** | ⚠️ | ⚠️* |

**Legende:** ✅ = gut, ⚠️ = teilweise, ❌ = schlecht

\* RLM kompensiert durch LLM-basierte Synonym-Expansion, aber RAG hat hier natürlichen Vorteil.

---

## Hybrid-Ansatz: Das Beste aus beiden Welten

Für optimale Ergebnisse könnte man kombinieren:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  RAG Retrieval  │ ──► │  RLM Extraction │ ──► │ Verified Answer │
│  (find chunks)  │     │  (exact quotes) │     │  (with citation)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

1. **RAG** findet relevante Chunks via Embeddings (semantisch)
2. **RLM** extrahiert verbatim aus diesen Chunks (präzise)
3. **Ergebnis:** Semantische Suche + exakte Zitate

---

## Schnell-Demo (2 Minuten)

Für eine kurze Demo vor Stakeholdern:

1. **Zeige das Problem:** Stelle die EUSt-Frage an ChatGPT/Copilot
   - Ergebnis: Generische Antwort, falsche Anzahl, keine Quelle

2. **Zeige RLM:** Gleiche Frage mit RLM Skill
   - Ergebnis: Rz 1859a, alle 8 Voraussetzungen, verbatim

3. **Highlight:**
   - "Das LLM hat nicht halluziniert - es hat den Text gefunden"
   - "Jeder Berater kann das für Gutachten verwenden"
   - "Compliance: Nachvollziehbare Quellenangaben"

---

## Testprotokoll-Vorlage

```markdown
## Test: [Name]
**Datum:**
**Tester:**
**Dokument:**

### Frage
[Exakte Testfrage]

### Ergebnis: Einfaches LLM (ChatGPT/Copilot)
- Antwort:
- Quellenangabe: Ja/Nein
- Korrekt: Ja/Nein/Teilweise
- Anmerkungen:

### Ergebnis: RAG (falls verfügbar)
- Antwort:
- Quellenangabe: Ja/Nein
- Korrekt: Ja/Nein/Teilweise
- Anmerkungen:

### Ergebnis: RLM
- Antwort:
- Quellenangabe: Ja/Nein
- Korrekt: Ja/Nein/Teilweise
- Iterationen:
- Kosten: $
- Anmerkungen:

### Fazit
[Welche Methode war am besten und warum]
```
