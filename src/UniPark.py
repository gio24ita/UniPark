import random      # Importa il modulo per generare numeri casuali
import time        # Importa il modulo per gestire il tempo (pause, sleep)
import threading   # Importa il modulo per gestire l'esecuzione parallela (multithreading)
import os          # Importa il modulo per interagire con il sistema operativo (es. pulire schermo)
import sys         # Importa il modulo per parametri e funzioni di sistema

### SPIEGAZIONE BLOCCO: CONFIGURAZIONE ANSI ###
# Windows, nelle versioni più vecchie o nel CMD standard, non abilita di default
# i codici speciali (ANSI escape codes) che servono per i colori e per muovere il cursore.
# Questo comando forza l'abilitazione di questa funzionalità.
# ---------------------------------------------------------------------------
if os.name == "nt":      # Se il sistema operativo è Windows ("nt")
    os.system("")        # Esegue un comando vuoto che, come effetto collaterale, abilita i colori ANSI nel terminale

### SPIEGAZIONE BLOCCO: CLASSE PARKINGZONE ###
# Questa classe definisce l'oggetto "Zona di Parcheggio".
# Ogni zona ha un nome, una capacità massima e un numero di posti liberi attuali.
# I metodi park() e unpark() modificano il numero di posti liberi controllando
# di non andare sotto zero o sopra la capacità massima.
# ---------------------------------------------------------------------------
class ParkingZone:
    def __init__(self, name, capacity, free_slots):
        self.name = name              # Assegna il nome alla zona (es. "Zona A")
        self.capacity = capacity      # Assegna la capacità massima (es. 60)
        self.free_slots = free_slots  # Assegna i posti liberi iniziali

    def park(self):
        # Metodo per parcheggiare un'auto
        if self.free_slots > 0:       # Se c'è almeno un posto libero
            self.free_slots -= 1      # Diminuisce di 1 il conteggio dei posti liberi
        
            
    def unpark(self):
        # Metodo per far uscire un'auto
        if self.free_slots < self.capacity: # Se i posti liberi sono meno della capacità (quindi c'è almeno un'auto dentro)
            self.free_slots += 1            # Aumenta di 1 il conteggio dei posti liberi
        
            
### SPIEGAZIONE BLOCCO: ISTANZE GLOBALI ###
# Qui creiamo le tre zone "reali" che useremo nel programma.
# Vengono inizializzate con posti liberi casuali per dare varietà all'avvio.
# Essendo dichiarate qui fuori, sono variabili "globali" accessibili sia dal thread
# automatico che dal ciclo principale dell'utente.
# ---------------------------------------------------------------------------
a = ParkingZone("Zona A", 60, random.randint(1, 60))  # Crea Zona A con posti liberi random tra 1 e 60
b = ParkingZone("Zona B", 45, random.randint(1, 45))  # Crea Zona B con posti liberi random tra 1 e 45
c = ParkingZone("Zona C", 80, random.randint(1, 80))  # Crea Zona C con posti liberi random tra 1 e 80

### SPIEGAZIONE BLOCCO: AGGIORNAMENTO GRAFICO (ANSI) ###
# Questa è la funzione più complessa visivamente. Invece di ristampare tutto lo schermo,
# usa codici di escape per:
# 1. Salvare dove si trova il cursore dell'utente (in basso, dove sta scrivendo).
# 2. Saltare alla prima riga in alto.
# 3. Sovrascrivere la riga con i nuovi dati aggiornati.
# 4. Tornare esattamente dove era l'utente, permettendogli di continuare a scrivere senza interruzioni.
# ---------------------------------------------------------------------------
def update_header_only():
    """Aggiorna solo la riga in alto."""
    # Crea la stringa formattata con i dati attuali (02d significa "almeno 2 cifre", es. 05)
    status_text = f"--- STATO LIVE: A:{a.free_slots:02d} | B:{b.free_slots:02d} | C:{c.free_slots:02d} ---"

    print(
        f"\033[s"       # ANSI: Salva la posizione attuale del cursore
        f"\033[1;1H"    # ANSI: Sposta il cursore alla Riga 1, Colonna 1 (in alto a sinistra)
        f"\033[2K"      # ANSI: Cancella tutto il contenuto della riga corrente (per pulizia)
        f"\033[1;36m"   # ANSI: Imposta il colore del testo a Ciano brillante
        f"{status_text}"# Inserisce il testo dello stato preparato prima
        f"\033[0m"      # ANSI: Resetta il colore al default (bianco/grigio)
        f"\033[u",      # ANSI: Ripristina il cursore alla posizione salvata all'inizio (unsave)
        end="",         # Non andare a capo alla fine della print
        flush=True,     # Forza la scrittura immediata sul terminale (senza aspettare il buffer)
    )

def clear_screen():
    # Funzione cross-platform per pulire tutto lo schermo
    if os.name == "nt":     # Se siamo su Windows
        os.system("cls")    # Esegui comando 'cls'
    else:                   # Se siamo su Linux/Mac
        os.system("clear")  # Esegui comando 'clear'

### SPIEGAZIONE BLOCCO: THREAD AUTOMATICO ###
# Questa funzione gira in parallelo al programma principale ("in background").
# Simula il passaggio del tempo e l'arrivo/partenza casuale di auto.
# Dopo ogni modifica ai dati, chiama update_header_only() per aggiornare la grafica in alto.
# ---------------------------------------------------------------------------
def flusso_automatico():
    zone = [a, b, c]   # Lista locale delle zone per poterci iterare sopra
    while True:        # Ciclo infinito
        # Aspetta un tempo casuale tra 0.5 e 2.0 secondi
        time.sleep(random.uniform(0.5, 2.0))
        
        for zona in zone:                 # Per ogni zona nella lista
            evento = random.randint(0, 100) # Genera un numero casuale da 0 a 100 (probabilità)
            if evento < 40:               # 40% di probabilità che arrivi un'auto
                zona.park()               # Chiama il metodo park
            elif 40 <= evento < 60:       # 20% di probabilità (tra 40 e 60) che un'auto esca
                zona.unpark()             # Chiama il metodo unpark
        
        # Dopo aver modificato i dati delle zone, aggiorna la riga in alto
        update_header_only()

### SPIEGAZIONE BLOCCO: AVVIO E SETUP ###
# Qui prepariamo il terminale e avviamo il thread secondario.
# È importante impostare il thread come "daemon", così quando l'utente chiude
# il programma principale, anche il thread muore automaticamente senza bloccare il processo.
# ---------------------------------------------------------------------------
clear_screen()  # Pulisce lo schermo per partire da una situazione pulita
print("\n")     # Stampa una riga vuota iniziale (sarà quella occupata dall'header)
print("Simulazione avviata. Scrivi i comandi sotto (es. 'park a').\n") # Istruzioni per l'utente

# Crea l'oggetto Thread, dicendogli di eseguire la funzione 'flusso_automatico'
simulazione_thread = threading.Thread(target=flusso_automatico)
simulazione_thread.daemon = True  # Imposta il thread come Demone (si chiude se si chiude il main)
simulazione_thread.start()        # Avvia effettivamente l'esecuzione del thread

### SPIEGAZIONE BLOCCO: LOOP PRINCIPALE (UTENTE) ###
# Questo è il cuore dell'interazione utente. Gira all'infinito aspettando input.
# Gestisce l'input, controlla errori di formato, verifica se le zone esistono
# e fornisce feedback visivi temporanei sulla stessa riga dell'input usando \r (carriage return).
# ---------------------------------------------------------------------------
mappa_zone = {"a": a, "b": b, "c": c} # Dizionario per collegare stringhe ("a") agli oggetti reali (a)

while True: # Ciclo infinito principale
    try:
        # Chiede l'input all'utente. .strip() toglie spazi, .lower() rende tutto minuscolo
        comando_input = input("Inserisci comando: ").strip().lower()
    except EOFError: # Gestisce l'errore se l'utente preme Ctrl+D (fine input)
        break        # Esce dal ciclo

    if not comando_input: # Se l'utente ha premuto Invio senza scrivere nulla
        continue          # Salta al prossimo giro del ciclo

    # Sequenza per cancellare la riga appena scritta dall'utente:
    # \033[A = Sposta il cursore in alto di una riga
    # \033[K = Cancella la riga dal cursore alla fine
    print("\033[A\033[K", end="", flush=True)

    if comando_input == "exit": # Se il comando è "exit"
        break                   # Esce dal ciclo while e termina il programma

    parti = comando_input.split() # Divide la frase in parole (es. "park a" -> ["park", "a"])

    # --- CONTROLLO 1: Formato del comando ---
    if len(parti) != 2: # Se non ci sono esattamente 2 parole
        # \r riporta a inizio riga. Stampa errore. flush=True forza la stampa.
        print("\r⚠️  Formato errato! Usa: 'azione zona' (es. park a)", end="", flush=True)
        time.sleep(1.5)             # Aspetta 1.5 secondi per far leggere il messaggio
        print("\r\033[K", end="", flush=True) # Cancella il messaggio di errore
        continue                    # Ricomincia il ciclo while dall'inizio

    azione, nome_zona = parti[0], parti[1] # Assegna la prima parola ad 'azione' e la seconda a 'nome_zona'

    # --- CONTROLLO 2: La zona esiste? ---
    if nome_zona in mappa_zone:     # Controlla se la stringa 'nome_zona' è una chiave nel dizionario
        zona = mappa_zone[nome_zona] # Recupera l'oggetto zona corrispondente
        
        # --- CONTROLLO 3: L'azione è valida? ---
        if azione == "park":          # Se l'azione è "park"
            zona.park()               # Esegue il metodo park sull'oggetto
            # Stampa feedback di successo (sovrascrivendo la riga con \r)
            print(f"\r✅ Comando: PARK su {zona.name}", end="", flush=True)
            time.sleep(1)             # Mostra il messaggio per 1 secondo
            print("\r\033[K", end="", flush=True) # Cancella il messaggio
            
        elif azione == "unpark":      # Se l'azione è "unpark"
            zona.unpark()             # Esegue il metodo unpark sull'oggetto
            print(f"\r✅ Comando: UNPARK su {zona.name}", end="", flush=True)
            time.sleep(1)
            print("\r\033[K", end="", flush=True)
            
        else:
            # Caso Else: L'azione non è né park né unpark
            print(f"\r❌ Azione '{azione}' non valida!", end="", flush=True)
            time.sleep(1.5)
            print("\r\033[K", end="", flush=True)

        # Importante: Dopo un comando manuale, forziamo l'aggiornamento dell'header
        # per vedere subito il numero cambiare, senza aspettare il thread automatico.
        update_header_only()

    else:
        # Caso Else del controllo zona: La zona digitata non è nel dizionario
        print(f"\r❌ Zona '{nome_zona}' inesistente!", end="", flush=True)
        time.sleep(1.5)
        print("\r\033[K", end="", flush=True)