# Datový Vektorizátor – ETL Pipeline pro AI Chatbot

Tato složka obsahuje nezávislou komponentu pro **ETL (Extract, Transform, Load)** proces. Slouží k automatizovanému zpracování textového obsahu, jeho vyčištění, segmentaci na logické bloky (**chunky**) a následné vektorizaci (**embeddings**) pomocí lokálního AI modelu. Výsledek se ukládá do lokální vektorové databáze **ChromaDB**.

Podporované zdroje dat – lze kombinovat libovolně:

| Zdroj | Kdy se aktivuje |
|---|---|
| **MySQL databáze** (CMS) | `DB_NAME` je vyplněno v `.env` |
| **PDF soubory** | `FILES_DIR` ukazuje na složku s `.pdf` soubory |
| **HTML soubory** | `FILES_DIR` ukazuje na složku s `.html` / `.htm` soubory |

Tato data jsou připravena pro integraci s `chat-api`, kde chatbot bude moci v databázi **sémanticky vyhledávat** – tzn. najít obsah podle *smyslu* dotazu, nikoli jen klíčových slov.

---

## Jak ETL pipeline funguje

```
  MySQL (CMS)        PDF / HTML soubory
      │                      │
      ▼                      ▼
  extract_data()      extract_files()       ← extract.py
      │                      │
      └──────────┬───────────┘
                 │  all_data (spojená data z obou zdrojů)
                 ▼
          [transform.py]  ← 1. Odstranění HTML tagů (BeautifulSoup)
                 │          2. Rozdělení textu na chunky (LangChain RecursiveCharacterTextSplitter)
                 │          Výstup: [{'id': '...', 'text': '...čistý text...', 'metadata': {...}}]
                 ▼
            [load.py]     ← Vektorizace textu (HuggingFace model multilingual-e5-small)
                 │          Uložení vektorů + textu + metadata do ChromaDB
                 ▼
           chroma_db/     ← Lokální souborová vektorová databáze (připravena pro chatbota)
```

---

## Struktura složky

```
data-vectorizer/
├── main.py           ← Spouštěč: volá extract → transform → load v pořadí
├── extract.py        ← Extrakce dat z MySQL (extract_data) a souborů (extract_files)
├── transform.py      ← Čištění HTML + chunking textu
├── load.py           ← Vektorizace + upsert do ChromaDB
├── test_query.py     ← Interaktivní REPL pro testování sémantického vyhledávání
├── requirements.txt  ← Seznam Python závislostí s fixovanými verzemi
├── .env.example      ← Šablona konfiguračního souboru (zkopírujte na .env)
├── .env              ← Přístupové údaje a konfigurace (NENÍ v Gitu!)
├── db-structure.md   ← Schéma MySQL tabulek, ze kterých se čerpají data
├── files/            ← (volitelné) Sem vložte PDF / HTML soubory ke vektorizaci
└── chroma_db/        ← Složka s lokální ChromaDB (generovaná, NENÍ v Gitu)
```

---

## Instalace a spuštění

### Předpoklady – Python na Windows

> [!WARNING]
> **Varování k verzi Pythonu:** Vyhněte se Pythonu 3.13. Starší závislosti (zejména `numpy` přes LangChain) mají problémy s kompilací kvůli změnám C-API. Používejte **Python 3.11 nebo 3.12**.

**Máte dvě možnosti:**

#### Možnost A: Python 3.12 + C++ Build Tools *(doporučeno)*

Moderní Python + nástroje pro kompilaci balíčků ze zdrojových kódů.

1. Ujistěte se, že máte nainstalovaný **Python 3.12**
2. Stáhněte a nainstalujte **[Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)**
3. V instalátoru zaškrtněte **„Desktop development with C++"**
4. Ponechte výchozí volitelné komponenty (MSVC, Windows SDK) a nainstalujte

#### Možnost B: Python 3.11 *(nejjednodušší)*

Pro Python 3.11 existují předkompilované binární balíčky (wheels) – žádná kompilace není potřeba.

---

### Krok 1 – Vytvoření a aktivace virtuálního prostředí

```powershell
# Windows (PowerShell) – z kořene repozitáře
cd data-vectorizer

# Vytvoření prostředí (pro vynucení verze: py -3.11 -m venv venv)
python -m venv venv

# Aktivace prostředí
.\venv\Scripts\activate
```

```bash
# Linux / macOS
cd data-vectorizer
python3 -m venv venv
source venv/bin/activate
```

> Po aktivaci se v terminálu vlevo zobrazí `(venv)`.

---

### Krok 2 – Instalace závislostí

```bash
pip install -r requirements.txt
```

> [!TIP]
> Pokud instalace vyprší chybou `TimeoutError: The read operation timed out` (u velkých balíčků jako `torch`), použijte prodloužený timeout:
> ```bash
> pip install --default-timeout=200 -r requirements.txt
> ```

**Závislosti projektu:**

| Balíček | Verze | Účel |
|---|---|---|
| `langchain` | 0.3.7 | Orchestrace AI procesů |
| `langchain-community` | 0.3.5 | Komunitní integrace (text splittery) |
| `langchain-huggingface` | 0.1.2 | Integrace HuggingFace modelů |
| `langchain-chroma` | 0.1.4 | LangChain wrapper pro ChromaDB |
| `chromadb` | 0.5.15 | Lokální vektorová databáze |
| `sentence-transformers` | 3.3.1 | Inference AI embedding modelu |
| `beautifulsoup4` | 4.12.3 | Parsování a čištění HTML |
| `mysql-connector-python` | 9.1.0 | Připojení k MySQL databázi (volitelné) |
| `python-dotenv` | 1.0.1 | Načítání proměnných ze souboru `.env` |
| `pypdf` | 5.1.0 | Extrakce textu z PDF souborů (volitelné) |

---

### Krok 3 – Konfigurace

```bash
# Zkopírujte šablonu
cp .env.example .env
```

Poté otevřete `.env` a nakonfigurujte **alespoň jeden zdroj dat**:

```ini
# ── ZDROJ 1: MySQL databáze (volitelné) ─────────────────────────────────────
# Ponechte DB_NAME prázdné, pokud MySQL nepoužíváte.
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=vase_heslo
DB_NAME=jmeno_vasi_databaze

# ── ZDROJ 2: PDF / HTML soubory (volitelné) ──────────────────────────────────
# Nastavte cestu ke složce se soubory. Ponechte prázdné, pokud soubory nepoužíváte.
# Příklad pro lokální vývoj: FILES_DIR=./files
FILES_DIR=

# ── ChromaDB ─────────────────────────────────────────────────────────────────
# Lokální vývoj (bez Dockeru): ../chat-api/chroma_db
# Docker Compose: ./chroma_db
CHROMA_DB_DIR=../chat-api/chroma_db
CHROMA_COLLECTION=chatbot_data
EMBEDDING_MODEL=intfloat/multilingual-e5-small
```

> [!IMPORTANT]
> Musí být nastaven **alespoň jeden** ze zdrojů (`DB_NAME` nebo `FILES_DIR`). Pokud jsou nastaveny oba, data se sloučí a vektorizují dohromady.

> [!CAUTION]
> Soubor `.env` obsahuje hesla a nesmí být nikdy commitován do Gitu. Je správně přidán do `.gitignore`.

---

### Krok 4 – Příprava souborů (pouze pro zdroj PDF/HTML)

Vložte PDF nebo HTML soubory do složky definované v `FILES_DIR` (např. `./files`). Soubory mohou být uspořádány do podsložek – skript je projde rekurzivně.

```
data-vectorizer/
└── files/
    ├── dokumenty/
    │   ├── prijimacirizeni.pdf
    │   └── skolni-rad.pdf
    └── stranky/
        └── o-skole.html
```

> [!TIP]
> ID každého souboru je odvozeno z jeho relativní cesty. Přejmenování nebo přesunutí souboru = nový záznam v databázi.

---

### Krok 5 – Spuštění ETL procesu (vektorizace)

```bash
python main.py
```

Při prvním spuštění proběhne stahování AI modelu `multilingual-e5-small` ze serverů HuggingFace (**~100–300 MB**). Při dalších spuštěních se model načte z lokální cache.

**Příklad výstupu při použití obou zdrojů:**
```
==================================================
Spouštím vektorizaci pro AI Chatbota
==================================================
Připojování k databázi...
Stahuji hlavní obsah článků...
...
Úspěšně extrahováno celkem 87 záznamů.
[files] Načteno: dokumenty/prijimacirizeni.pdf (pdf)
[files] Načteno: dokumenty/skolni-rad.pdf (pdf)
[files] Načteno: stranky/o-skole.html (html_file)
[files] Celkem načteno 3 souborů.
Celkem zdrojů ke zpracování: 90 (DB: 87, soubory: 3)
Čištění textu a chunking (rozdělování na bloky)...
Transformace dokončena. Z původních 90 záznamů vzniklo 231 chunků.
Připravuji uložení 231 záznamů do vektorové databáze...
  Přidávám 231 nových záznamů...
Uložení dokončeno!
==================================================
Vektorizace úspěšně dokončena za 52.41 sekund!
==================================================
```

---

## Testování vektorové databáze

Po úspěšné vektorizaci si můžete otestovat, jak dobře databáze odpovídá na dotazy v češtině:

```bash
python test_query.py
```

Spustí se interaktivní REPL, kde zadáte dotaz a skript vrátí nejrelevantnější chunky z databáze včetně skóre vzdálenosti:

```
Vítejte v testovacím vyhledávání! (Pro ukončení napište 'q')

Zadejte svůj dotaz: Jaká je otevírací doba?

[AI] Hledám v databázi nejrelevantnější obsah pro: 'Jaká je otevírací doba?'

Nalezeno 3 výsledků:

==================================================
Výsledek 1 | Skóre vzdálenosti: 0.2341
Typ obsahu: article
Zdrojová URL: /o-nas/otviraci-doba
ID modulu: article_42
--------------------------------------------------
Škola je otevřena od pondělí do pátku 7:00–17:00...
```

> **Skóre vzdálenosti:** Nižší číslo = vyšší podobnost. Hodnoty pod 0.5 jsou zpravidla velmi relevantní.

---

## Popis jednotlivých souborů

### `extract.py` – Extrakce dat

Obsahuje dvě nezávislé funkce:

#### `extract_data()` — MySQL zdroj
Načítá obsah z databáze přes tři SQL dotazy:

1. **Hlavní obsah článků** (`cms_article`) – perex + obsah publikovaných článků
2. **WYSIWYG moduly článků** (`cms_article_module`, `cms_article_module_data`) – rozšířený obsah z modulů
3. **WYSIWYG moduly stránek** (`cms_page`, `cms_box`, `cms_box_data`) – obsah stránek

Schéma databázových tabulek je zdokumentováno v [`db-structure.md`](./db-structure.md).

#### `extract_files()` — PDF / HTML zdroj
Rekurzivně prochází složku `FILES_DIR` a extrahuje text z:
- **`.pdf`** – pomocí `pypdf`, stránka po stránce
- **`.html` / `.htm`** – surové HTML předané do `transform.py`, kde ho `BeautifulSoup` vyčistí

ID každého souboru je stabilní MD5 hash relativní cesty → bezpečný upsert (opakované spuštění nepřidává duplikáty).

---

### `transform.py` – Čištění a chunking

**1. Čištění HTML:**
```python
soup = BeautifulSoup(raw_html, "html.parser")
text = soup.get_text(separator=" ", strip=True)
# "<p>Ahoj <b>světe</b>!</p>" → "Ahoj světe !"
```

**2. Chunking (rozdělení na bloky):**
```python
RecursiveCharacterTextSplitter(
    chunk_size=800,    # Max. 800 znaků v jednom bloku
    chunk_overlap=100, # 100 znaků překryvu pro zachování kontextu
    separators=["\n\n", "\n", ".", " ", ""]  # Preferuje přirozené konce vět
)
```

Překryv (`chunk_overlap`) zajišťuje, že pokud je odpověď na dotaz na rozhraní dvou bloků, bude nalezena v obou a chatbot ji nezamešká.

---

### `load.py` – Vektorizace a uložení do ChromaDB

**AI model:** `intfloat/multilingual-e5-small`
- Open-source model optimalizovaný pro vícejazyčné texty včetně češtiny
- Běží lokálně na CPU (GPU volitelné přes `model_kwargs={'device': 'cuda'}`)
- Vytváří **384-dimenzionální vektory** reprezentující sémantický smysl textu

**Upsert logika:**
- Při každém spuštění skript zkontroluje, která ID v databázi již existují
- **Nové záznamy** jsou přidány, **existující** jsou aktualizovány
- Bezpečné opakované spuštění bez `DuplicateIDError`

---

### `main.py` – Orchestrátor ETL

Skript automaticky detekuje, které zdroje jsou nakonfigurovány, a spustí jen ty aktivní:

```python
db_enabled    = bool(os.getenv("DB_NAME"))    # MySQL → extract_data()
files_enabled = bool(os.getenv("FILES_DIR"))  # Soubory → extract_files()
```

Pokud není nastaven ani jeden zdroj, skript srozumitelně upozorní a skončí.

---

## Opakované spuštění a re-index

Skript lze spustit opakovaně:
- **Nové záznamy** z libovolného zdroje jsou automaticky přidány
- **Změněný obsah** (stejné ID) je aktualizován
- **Přejmenované nebo přesunuté soubory** dostanou nové ID → vzniknou jako nové záznamy (staré zůstanou v DB)

Pokud potřebujete **úplný reset** (smazání a nové naplnění celé databáze):

```bash
# Smažte složku s databází
rm -rf chroma_db/

# Spusťte vektorizaci znovu (vše bude přidáno jako nové)
python main.py
```
