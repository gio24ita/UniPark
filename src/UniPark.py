import os
import random
import threading
import time

# ==============================================================================
# CONFIGURAZIONE SISTEMA & GESTIONE CONCORRENZA
# ==============================================================================

# Abilitazione codici ANSI per terminali Windows legacy.
# Necessario per visualizzare colori e muovere il cursore correttamente.
if os.name == "nt":
    os.system("")

# --- SCREEN MUTEX (MUTUAL EXCLUSION) ---
# Questo Lock agisce come un "semaforo" per l'accesso alla console (stdout).
# PROBLEMA: Se due thread provano a stampare contemporaneamente, il testo si mescola
# creando artefatti visivi.
# SOLUZIONE: Chi vuole scrivere deve acquisire questo lock.
screen_lock = threading.Lock()


# ==============================================================================
# MODELLO DATI: CLASSE PARKING ZONE
# ==============================================================================


class ParkingZone:
    """
    Rappresenta un'area di parcheggio gestita in modo thread-safe.
    Incapsula lo stato (posti liberi, code) e la logica di accesso.
    """

    def __init__(self, name, capacity, free_slots):
        self.name = name
        self.capacity = capacity

        # Validazione dati (Clamping): Assicura che i posti iniziali siano
        # logici (tra 0 e la capacità massima), prevenendo stati inconsistenti.
        self.free_slots = max(0, min(free_slots, capacity))
        self.waiting = 0

        # --- DATA MUTEX ---
        # Ogni zona ha il proprio lock privato. Questo garantisce l'atomicità
        # delle operazioni su QUESTA specifica zona, senza bloccare le altre.
        self.data_lock = threading.Lock()

    def park(self):
        """
        Tenta di parcheggiare un veicolo.
        Thread-safe: Gestisce automaticamente la concorrenza.
        Returns: True se parcheggiato, False se aggiunto in coda.
        """
        # CRITICAL SECTION: Nessun altro thread può modificare questa zona ora.
        with self.data_lock:
            if self.free_slots > 0:
                self.free_slots -= 1
                return True
            self.waiting += 1
            return False

    def unpark(self):
        """
        Rimuove un veicolo dal parcheggio.
        Gestisce la priorità della coda FIFO (First-In-First-Out).
        Returns: True se l'operazione ha avuto effetto, False se vuoto.
        """
        with self.data_lock:
            # Priorità alla coda: se esce un'auto, entra subito chi aspetta.
            if self.waiting > 0:
                self.waiting -= 1
                return True  # Posto liberato e rioccupato istantaneamente

            # Se non c'è coda, si libera effettivamente un posto.
            if self.free_slots < self.capacity:
                self.free_slots += 1
                return True

            return False


# ==============================================================================
# ISTANZE GLOBALI
# ==============================================================================

# Inizializzazione delle risorse condivise con stato iniziale casuale
a = ParkingZone("Zona A", 60, random.randint(1, 60))
b = ParkingZone("Zona B", 45, random.randint(1, 45))
c = ParkingZone("Zona C", 80, random.randint(1, 80))

# Lookup table per mappare l'input stringa dell'utente all'oggetto reale
mappa_zone = {"a": a, "b": b, "c": c}


# ==============================================================================
# GESTIONE INTERFACCIA UTENTE (UI)
# ==============================================================================


def update_header():
    """
    Rendering della Dashboard in tempo reale.
    Utilizza sequenze di escape ANSI per aggiornare solo la riga superiore
    senza causare flickering (sfarfallio) o cancellare l'input utente.

    WARNING: Questa funzione NON acquisisce il lock da sola.
    Il chiamante DEVE possedere 'screen_lock' prima di invocarla.
    """
    status = (
        f"--- STATO LIVE: A:{a.free_slots:02d}/{a.capacity} (Q:{a.waiting}) | "
        f"B:{b.free_slots:02d}/{b.capacity} (Q:{b.waiting}) | "
        f"C:{c.free_slots:02d}/{c.capacity} (Q:{c.waiting}) ---"
    )

    # ANSI MAGIC:
    # \033[s    -> Salva la posizione attuale del cursore (dove l'utente scrive)
    # \033[1;1H -> Sposta il cursore forzatamente alla riga 1, colonna 1
    # \033[2K   -> Pulisce interamente la riga corrente (la riga 1)
    # \033[1;36m-> Imposta il colore del testo a Ciano Brillante
    # {status}  -> Stampa il testo
    # \033[0m   -> Resetta il colore al default
    # \033[u    -> Ripristina il cursore alla posizione salvata (dove l'utente scrive)
    print(f"\033[s\033[1;1H\033[2K\033[1;36m{status}\033[0m\033[u", end="", flush=True)


def clear_screen():
    """Pulisce il terminale in modo cross-platform (Windows/Unix)."""
    os.system("cls" if os.name == "nt" else "clear")


# ==============================================================================
# LOGICA DI SIMULAZIONE (BACKGROUND WORKERS)
# ==============================================================================


def thread_zona_individuale(zona):
    """
    Funzione Worker eseguita da ogni Thread indipendente.
    Simula il comportamento autonomo di una singola zona di parcheggio.
    """
    while True:
        # 1. Simulazione temporale non deterministica
        # Ogni zona "vive" con i propri ritmi, indipendentemente dalle altre.
        attesa = random.uniform(2.0, 5.0)
        time.sleep(attesa)

        # 2. Generazione evento casuale (Business Logic simulata)
        evento = random.randint(0, 100)

        # Logica probabilistica:
        # 0-39%  -> Arrivo auto (Park)
        # 40-79% -> Partenza auto (Unpark)
        # 80-100%-> Nessun evento (Idle)
        if evento < 40:
            zona.park()
        elif 40 <= evento < 80:
            zona.unpark()

        # 3. Aggiornamento UI Thread-Safe
        # Acquisiamo il lock globale dello schermo per aggiornare la dashboard.
        # Se l'utente sta scrivendo o un altro thread sta aggiornando, aspettiamo qui.
        with screen_lock:
            update_header()


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # Setup iniziale dell'ambiente grafico
    clear_screen()
    print(
        "\n\nSimulazione Multi-Thread UniPark avviata.\nOgni zona è gestita da un processo indipendente.\n"
    )

    # Primo rendering statico della dashboard
    with screen_lock:
        update_header()

    # --- AVVIO CONCORRENZA ---
    # Istanziamo un Thread separato per ogni zona.
    # daemon=True: Questi thread sono "servitori". Se il programma principale
    # (Main Thread) termina, questi thread vengono uccisi immediatamente dal SO.
    t_a = threading.Thread(target=thread_zona_individuale, args=(a,), daemon=True)
    t_b = threading.Thread(target=thread_zona_individuale, args=(b,), daemon=True)
    t_c = threading.Thread(target=thread_zona_individuale, args=(c,), daemon=True)

    t_a.start()
    t_b.start()
    t_c.start()

    # --- EVENT LOOP PRINCIPALE (Input Utente) ---
    while True:
        try:
            # Input bloccante: il programma aspetta qui l'utente.
            # I thread in background continuano a girare mentre siamo fermi qui.
            cmd = input("Comando (es. 'park a') > ").strip().lower()

            # Appena ricevuto l'input, puliamo la riga per mantenere la UI pulita.
            with screen_lock:
                # \033[A (Cursore su di 1) + \033[2K (Cancella riga)
                print("\033[A\033[2K", end="", flush=True)

            # Gestione uscita graceful
            if cmd == "exit":
                break

            # Gestione input vuoto (utente preme solo Invio)
            if not cmd:
                continue

            # Parsing del comando
            parts = cmd.split()
            if len(parts) != 2:
                # Feedback errore temporaneo
                with screen_lock:
                    print(f"\r❌ Formato errato!", end="", flush=True)
                    time.sleep(1)
                    print(f"\r\033[2K", end="", flush=True)  # Cancella msg errore
                continue

            azione, zona_key = parts[0], parts[1]

            # Validazione zona
            if zona_key not in mappa_zone:
                with screen_lock:
                    print(f"\r❌ Zona inesistente", end="", flush=True)
                    time.sleep(1)
                    print(f"\r\033[2K", end="", flush=True)
                continue

            target_zone = mappa_zone[zona_key]

            # Esecuzione logica comando manuale
            msg = ""
            if azione == "park":
                ok = target_zone.park()
                msg = (
                    f"✅ Manuale: Park in {target_zone.name}"
                    if ok
                    else f"⚠️ {target_zone.name} PIENO!"
                )
            elif azione == "unpark":
                ok = target_zone.unpark()
                msg = (
                    f"✅ Manuale: Unpark da {target_zone.name}"
                    if ok
                    else f"❌ {target_zone.name} vuoto!"
                )
            else:
                msg = "❌ Azione ignota"

            # Rendering Feedback Utente + Aggiornamento Immediato Dashboard
            with screen_lock:
                print(f"\r{msg}", end="", flush=True)
                update_header()

            # Mantieni il feedback visibile per 0.5 secondi
            time.sleep(0.5)

            # Cleanup finale della riga di feedback
            with screen_lock:
                print(f"\r\033[2K", end="", flush=True)

        except KeyboardInterrupt:
            # Gestione Ctrl+C per uscita pulita
            break
