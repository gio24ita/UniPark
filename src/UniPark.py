import os
import random
import threading
import time

### 1. CONFIGURAZIONE DEL SISTEMA ###
# Questo blocco serve a garantire che i colori e i movimenti del cursore
# funzionino anche su Windows. Windows (specialmente cmd.exe vecchi)
# non supporta nativamente i codici ANSI senza questa "spinta".
if os.name == "nt":
    os.system("")  # Esegue un comando vuoto che abilita la modalità VT100 su Windows


### 2. CLASSE PARKING ZONE (Il "modello" dei dati) ###
# Questa classe rappresenta una singola zona di parcheggio.
# Contiene la logica per gestire i posti e, soprattutto, la sicurezza (Lock)
# per evitare che il computer e l'utente modifichino i dati nello stesso istante.
class ParkingZone:
    def __init__(self, name, capacity, free_slots):
        self.name = name
        self.capacity = capacity

        # Controllo dati: evitiamo di avere più posti liberi della capienza massima
        if free_slots > capacity:
            self.free_slots = capacity
        elif free_slots < 0:
            self.free_slots = 0
        else:
            self.free_slots = free_slots


        self.waiting = 0  # Contatore per la lunghezza della coda d'attesa
        self.lock = threading.Lock()

    def park(self):
        """Tenta di parcheggiare: se posto libero, parcheggia; altrimenti, aggiunge alla coda."""
        with self.lock:
            if self.free_slots > 0:
                self.free_slots -= 1
                return True  # Parcheggiato con successo
            else:
                self.waiting += 1
                return False  # Aggiunto alla coda

    def unpark(self):
        """Libera un posto: se possibile, libera e poi parcheggia il primo in coda se presente."""
        with self.lock:
            if self.free_slots < self.capacity:
                self.free_slots += 1
                # Controlla se c'è qualcuno in coda
                if self.waiting > 0:
                    self.waiting -= 1
                    self.free_slots -= 1  # Parcheggia il primo in coda
                return True
            return False

    def get_status(self):
        """Restituisce lo stato attuale: posti liberi/capacità (in coda)."""

        # IL LOCK (LUCCHETTO):
        # È fondamentale nel multithreading. Immaginalo come la chiave del bagno.
        # Solo chi ha la chiave (thread automatico o utente) può entrare,
        # modificare i posti e poi uscire restituendo la chiave.
        self.lock = threading.Lock()

    def park(self):
        # 'with self.lock' acquisisce la chiave. Se è occupata, aspetta qui in fila.
        with self.lock:
            if self.free_slots > 0:
                self.free_slots -= 1
                return True  # Parcheggio riuscito

            return False  # Parcheggio pieno

    def unpark(self):
        with self.lock:  # Anche qui serve la chiave per evitare conflitti
            if self.free_slots < self.capacity:
                self.free_slots += 1
                return True  # Uscita riuscita

            return False  # Il parcheggio era già vuoto

    def get_status(self):
        # Anche solo per leggere il numero serve il lock, per evitare di leggere
        # un numero mentre sta venendo modificato (es. lettura "sporca").

        with self.lock:
            return f"{self.free_slots}/{self.capacity} ({self.waiting})"


### 3. CREAZIONE DELLE ZONE (Oggetti Globali) ###
# Creiamo le tre zone che useremo nel programma.
# Usiamo numeri casuali (random) per non partire sempre con gli stessi valori.
a = ParkingZone("Zona A", 60, random.randint(1, 60))
b = ParkingZone("Zona B", 45, random.randint(1, 45))
c = ParkingZone("Zona C", 80, random.randint(1, 80))


### 4. FUNZIONE GRAFICA (La "Magia" ANSI) ###
# Questa funzione è responsabile dell'aggiornamento della barra in alto.
# Usa codici di escape complessi per saltare in alto, scrivere e tornare in basso
# senza disturbare quello che l'utente sta scrivendo.
def update_header_only():
    """Aggiorna solo la riga in alto."""

    # Nota: spezziamo la riga lunga per Pylint


    # Prepariamo il testo. :02d significa "formatta il numero con almeno 2 cifre" (es. 05)

    status_text = (
        f"--- STATO LIVE: A:{a.free_slots:02d}/{a.capacity} Q:{a.waiting:02d} | "
        f"B:{b.free_slots:02d}/{b.capacity} Q:{b.waiting:02d} | "
        f"C:{c.free_slots:02d}/{c.capacity} Q:{c.waiting:02d} ---"
    )


    # Stampiamo la stringa usando i codici ANSI
    print(
        f"\033[s"  # Salva posizione cursore
        f"\033[1;1H"  # Sposta a riga 1, colonna 1
        f"\033[2K"  # Cancella riga
        f"\033[1;36m"  # Colore ciano
        f"{status_text}"  # Testo
        f"\033[0m"  # Reset colore
        f"\033[u",  # Ripristina cursore
        end="",
        flush=True,

    # SPIEGAZIONE CODICI ANSI:
    # \033[s    -> SALVA la posizione del cursore (dove stai scrivendo ora)
    # \033[1;1H -> VAI alla riga 1, colonna 1 (angolo in alto a sinistra)
    # \033[2K   -> CANCELLA tutta la riga (per pulire vecchie scritte)
    # \033[1;36m -> COLORE Ciano brillante
    # \033[0m   -> RESET colore (torna bianco)
    # \033[u    -> RIPRISTINA il cursore dove l'avevamo salvato
    print(
        f"\033[s\033[1;1H\033[2K\033[1;36m{status_text}\033[0m\033[u",
        end="",  # end="" evita di andare a capo automaticamente
        flush=True,  # flush=True forza la stampa immediata (essenziale con sleep)

    )


### 5. UTILITY PER PULIRE LO SCHERMO ###
# Una semplice funzione che capisce se sei su Windows o Linux/Mac
# e lancia il comando giusto per pulire tutto il terminale all'inizio.
def clear_screen():
    if os.name == "nt":
        os.system("cls")  # Windows
    else:
        os.system("clear")  # Linux


### 6. IL THREAD AUTOMATICO (Il "Motore" nascosto) ###
# Questa funzione girerà in parallelo al programma principale.
# Simula la vita reale: auto che arrivano e partono da sole.
def flusso_automatico():  # DA RIVEDERE
    zone = [a, b, c]
    while True:
        # Aspetta un tempo casuale tra 0.5 e 2 secondi
        time.sleep(random.uniform(0.5, 2.0))




        for single_zone in zone:
            # Tira una moneta (o quasi): genera un numero da 0 a 100
            evento = random.randint(0, 100)

            if evento < 40:
                single_zone.park()  # Arrivo: tenta park o coda
            elif 40 <= evento < 60:
                single_zone.unpark()  # Partenza: libera se possibile e gestisce coda


            if evento < 40:  # 40% di probabilità di parcheggiare
                single_zone.park()
            elif 40 <= evento < 60:  # 20% di probabilità di uscire
                single_zone.unpark()


        # Importante: dopo che il computer ha mosso le auto, aggiorna la grafica
        update_header_only()


### 7. AVVIO DEL PROGRAMMA ###
# Qui prepariamo il terreno prima di entrare nel ciclo infinito.
clear_screen()
print("\n")  # Lasciamo una riga vuota in alto per l'header
print("Simulazione avviata. Scrivi i comandi sotto (es. 'park a').\n")

# Configuriamo il thread
simulazione_thread = threading.Thread(target=flusso_automatico)
# daemon = True significa: "Se l'utente chiude il programma principale,
# tu (thread) devi morire subito, non restare attivo in background".
simulazione_thread.daemon = True
simulazione_thread.start()  # Via!


### 8. LOOP PRINCIPALE (Interazione Utente) ###
# Questa parte gestisce l'input della tastiera.
# Deve essere robusta contro errori di digitazione.
mappa_zone = {"a": a, "b": b, "c": c}  # Collega la lettera "a" all'oggetto a

while True:
    try:
        # Chiediamo l'input. .strip() toglie spazi vuoti, .lower() rende tutto minuscolo
        comando_input = input("Inserisci comando: ").strip().lower()
    except EOFError:
        break  # Se premo Ctrl+D esce

    if not comando_input:
        continue  # Se premo invio a vuoto, ricomincia

    # PULIZIA VISIVA INPUT:
    # Appena premi invio, questa riga cancella quello che hai scritto
    # per tenere il terminale pulito e mostrare solo il risultato.
    # \033[A (Cursore su di 1 riga) + \033[K (Cancella riga)
    print("\033[A\033[K", end="", flush=True)

    if comando_input == "exit":
        break

    parti = comando_input.split()  # Divide la frase in parole

    # Controllo se ho scritto due parole (es. "park" e "a")
    if len(parti) != 2:
        # \r riporta il cursore a inizio riga per sovrascrivere
        print(
            "\r⚠️  Formato errato! Usa: 'azione zona' (es. park a)", end="", flush=True
        )
        time.sleep(0.5)
        print("\r\033[K", end="", flush=True)  # Cancella l'errore dopo 0.5s
        continue

    azione, nome_zona = parti[0], parti[1]

    # Logica di controllo comandi
    if nome_zona in mappa_zone:
        zona = mappa_zone[nome_zona]

        if azione == "park":

            esito = zona.park()

            esito = zona.park()  # Proviamo a parcheggiare

            if esito:
                print(
                    f"\r✅ Comando: PARK su {zona.name} (parcheggiato)",
                    end="",
                    flush=True,
                )
            else:
                print(
                    f"\r⚠️  Parcheggio PIENO su {zona.name}, aggiunto in coda!",
                    end="",
                    flush=True,
                )

            time.sleep(0.5)  # Lascia leggere il messaggio
            print("\r\033[K", end="", flush=True)  # Pulisce la riga

        elif azione == "unpark":
            esito = zona.unpark()
            if esito:
                print(
                    f"\r✅ Comando: UNPARK su {zona.name} (liberato)",
                    end="",
                    flush=True,
                )
            else:
                print(f"\r❌ Parcheggio già VUOTO su {zona.name}!", end="", flush=True)

            time.sleep(0.5)
            print("\r\033[K", end="", flush=True)

        else:
            print(f"\r❌ Azione '{azione}' non valida!", end="", flush=True)
            time.sleep(0.5)
            print("\r\033[K", end="", flush=True)

        # Aggiorniamo subito l'header per dare un feedback immediato all'utente
        update_header_only()

    else:
        print(f"\r❌ Zona '{nome_zona}' inesistente!", end="", flush=True)
        time.sleep(0.5)
        print("\r\033[K", end="", flush=True)
