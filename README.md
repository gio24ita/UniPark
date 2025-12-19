# UniPark: Simulazione e Gestione Parcheggi Universitari

## Introduzione
**UniPark** è un software dimostrativo (Demo) sviluppato per simulare la gestione in tempo reale dei parcheggi della Cittadella Universitaria (Zone: Viale A. Doria, DMI, Via S. Sofia).

Il progetto ha un focus didattico e algoritmico: dimostra la gestione delle risorse (posti auto) e delle code d'attesa in un ambiente simulato, utilizzando esclusivamente strutture dati in memoria di Python.

## Scopo e Funzionalità

| Categoria | Descrizione |
| :--- | :--- |
| **Obiettivo Funzionale** | Simulare la gestione in tempo reale dei posti auto disponibili e delle code d'attesa (FIFO) nelle principali zone della Cittadella Universitaria. |
| **Natura del Progetto** | È una demo software didattica, **non collegata a sensori reali**, mirata a illustrare algoritmi e strutture dati in Python. |
| **Meccanismo Core** | La simulazione si basa sulla **generazione autonoma del flusso di auto** (*Auto-Flow Generation*) per testare la logica interna dinamicamente. |
| **Interazione** | L'utente può interagire manualmente (occupando/liberando posti) per dimostrazione e debug. |
| **Tecnologia Dati** | Utilizza esclusivamente strutture dati **in memoria (Dizionari, Liste, Code)** di Python, evitando l'overhead di un database SQL. |

## Lato Tecnico e Requisiti

| Componente | Specifiche |
| :--- | :--- |
| **Linguaggio** | Il codice verrà scritto interamente in **Python**. |
| **Interfaccia Grafica** | Per l'implementazione del Front-End (sezione opzionale del progetto) verrà utilizzato **Tkinter**. |
| **Quality Assurance** | Verranno effettuati **Unit-Tests** per validare la correttezza algoritmica. |
| **Code Style** | Verrà utilizzato l'auto-formatter **Black** (fortemente raccomandato) per mantenere l'uniformità del codice. |
| **Standard Commit** | Verranno utilizzati i **Conventional Commits** per una cronologia Git chiara. |
| **Pipeline CI** | Verrà creata una pipeline (GitHub Actions) per eseguire controlli automatici (*linting* e *style checks*) su ogni Pull Request. |
| **Sincronizzazione** | Tutto il codice verrà scritto mantenendo a mente i principi di Clean Code e la manutenzione. |
