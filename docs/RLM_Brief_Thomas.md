# RLM: Die Lösung für das RAG-Problem

**Servus Thomas!**

Hier ein kurzer Überblick über das RLM-Projekt, das ich für unsere Steuerberatung adaptiert habe. Ich weiß, Du hast wenig Zeit – daher nur das Wesentliche.

---

## Das Problem: RAG funktioniert nicht für Rechtsdokumente

Du kennst das Problem mit klassischem RAG:

| RAG-Problem | Auswirkung bei uns |
|-------------|-------------------|
| **Chunking zerstört Kontext** | Rz 1859a wird mitten im Satz abgeschnitten |
| **Embedding-Suche ist ungenau** | "EUSt-Abzug" findet nicht "Einfuhrumsatzsteuer" |
| **Synthese statt Zitat** | LLM erfindet Voraussetzungen statt zu zitieren |
| **Keine Quellenangabe** | Unbrauchbar für Gutachten |

**Unser Ziel:** Exakte Zitate mit Rz-Nummern aus 2M+ Zeichen Dokumenten.

---

## Die Lösung: RLM (MIT CSAIL, Januar 2025)

**Kernidee:** Das LLM schreibt Python-Code, um das Dokument selbst zu durchsuchen.

```
┌─────────────────────────────────────┐
│         Benutzer-Anfrage            │
│  "EUSt-Abzug Voraussetzungen?"      │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         RLM Orchestrator            │
│  • Sendet Prompt an LLM             │
│  • Extrahiert Python-Code           │
│  • Führt Code in Sandbox aus        │
│  • Loop bis FINAL() aufgerufen      │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         Python REPL Sandbox         │
│                                     │
│  CONTEXT = "2.2M Zeichen UStR..."   │
│                                     │
│  # LLM schreibt diesen Code:        │
│  matches = re.findall(              │
│    r'Rz\s*1859.*?EUSt', CONTEXT)    │
│                                     │
│  llm_query("Extrahiere verbatim...") │
│                                     │
│  FINAL("Laut Rz 1859a: ...")        │
└─────────────────────────────────────┘
```

**Das LLM lernt automatisch:**
- **Peeking:** Dokument-Struktur verstehen
- **Grepping:** Regex-Suche nach Schlüsselwörtern
- **Rekursion:** Sub-LLM für Chunk-Analyse
- **Verifikation:** Zitat gegen Quelle prüfen

---

## Unser Test: UStR 2000 (2.2 Mio. Zeichen)

**Frage:** *"Welche Voraussetzungen müssen erfüllt werden beim EUSt-Abzug bei kostenpflichtigen Reparaturen in fremdem Auftrag?"*

### Vorher (Standard RAG / GPT-4)
```
❌ 6 generische Voraussetzungen
❌ Keine Rz-Nummer
❌ Antwort auf Englisch
❌ "Document did not contain specific information" (falsch!)
```

### Nachher (RLM)
```
✅ "Laut Rz 1859a (Abschnitt 12.1.3.4.3.):"
✅ Alle 8 Voraussetzungen VERBATIM
✅ Antwort auf Deutsch
✅ Gegen Quelle verifiziert
✅ Kosten: $0.12 pro Anfrage
```

---

## Benchmark-Ergebnisse (MIT)

| Benchmark | Standard LLM | RLM | Verbesserung |
|-----------|-------------|-----|--------------|
| OOLONG (132k tokens) | ~30 Punkte | ~64 Punkte | **+114%** |
| OOLONG (263k tokens) | ~31 Punkte | ~46 Punkte | **+49%** |
| BrowseComp (1000 docs) | versagt | **perfekt** | ∞ |

---

## Der große Gedanke: Portable Agentic Skill

**Vision:** RLM als `.skill`-Datei verpacken, kompatibel mit:

| Platform | Status | Integration |
|----------|--------|-------------|
| **Claude Code** | ✅ Fertig | `/rlm` Skill + Subagent |
| **ChatGPT** | 🔜 Möglich | Custom GPT + Actions |
| **MS Copilot** | 🔜 Möglich | Copilot Studio Plugin |
| **OpenWebUI** | 🔜 Möglich | Python Function Tool |

**Das würde bedeuten:**
- Jeder Berater könnte UStR/EStR/BAO durchsuchen
- Automatische Rz-Zitierung in Gutachten
- Prüfbare Quellenangaben (Compliance!)
- Keine Halluzinationen mehr bei Rechtsfragen

---

## Technische Details (für Dich)

```python
from rlm import RLM
from rlm.backends import AnthropicBackend

rlm = RLM(
    backend=AnthropicBackend(),
    model="claude-sonnet-4",           # Root: $3/MTok
    recursive_model="claude-haiku-3",  # Sub-LLM: $0.25/MTok
    max_iterations=10,
    verbose=True,
)

result = rlm.completion(
    context=open("UStR_2000.txt").read(),  # 2.2M chars
    query="EUSt-Abzug Voraussetzungen?"
)

print(result.answer)  # Laut Rz 1859a: ...
print(result.stats.total_cost)  # $0.12
```

**Key Insight:** Die Prompt-Änderung von "synthesize" → "extract verbatim" war der entscheidende Fix.

---

## Nächste Schritte

1. **Kurzfristig:**
   - Skill-File-Format definieren
   - Deutsche Prompts optimieren

2. **Mittelfristig:**
   - OpenWebUI Integration testen
   - Copilot Studio Plugin bauen

3. **Langfristig:**
   - AI Champions RLM-Schulung
   - Integration in Gutachten-Workflow

---

## Links & Ressourcen

- **MIT Paper:** [arXiv:2512.24601](https://arxiv.org/abs/2512.24601)
- **MIT Blog:** [alexzhang13.github.io/blog/2025/rlm](https://alexzhang13.github.io/blog/2025/rlm/)
- **Unser Code:** `/home/jerry/projects/rlm/`
- **Claude Skill:** `/rlm` (global verfügbar)

---

**Fragen? Lass uns bei einem Kaffee darüber reden!**

*Jerry*

---
*Erstellt: 21. Januar 2026*
