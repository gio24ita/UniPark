import random
import time
import threading
import os

# --- CONFIGURAZIONE ANSI PER WINDOWS ---
if os.name == "nt":
    os.system("")

# --- CLASSE PARCHEGGIO ---
class ParkingZone:
    def __init__(self, name, capacity, free_slots):
        self.name = name
        self.capacity = capacity

        if free_slots > capacity:
            self.free_slots = capacity
        elif free_slots < 0:
            self.free_slots = 0
        else:
            self.free_slots = free_slots

        self.lock = threading.Lock()

    def park(self):
        with self.lock:
            if self.free_slots > 0:
                self.free_slots -= 1
                return True

            # Pylint fix: rimosso else inutile
            return False

    def unpark(self):
        with self.lock:
            if self.free_slots < self.capacity:
                self.free_slots += 1
                return True

            # Pylint fix: rimosso else inutile
            return False

    def get_status(self):
        with self.lock:
            return f"{self.free_slots}/{self.capacity}"

# --- ISTANZE GLOBALI ---
a = ParkingZone("Zona A", 60, random.randint(1, 60))
b = ParkingZone("Zona B", 45, random.randint(1, 45))
c = ParkingZone("Zona C", 80, random.randint(1, 80))

# --- GESTIONE GRAFICA CORRETTA ---
def update_header_only():
    """Aggiorna solo la riga in alto."""
    # 1. Calcoliamo la stringa
    # Nota: spezziamo la riga lunga per Pylint
    status_text = (
        f"--- STATO LIVE: A:{a.free_slots:02d} | "
        f"B:{b.free_slots:02d} | C:{c.free_slots:02d} ---"
    )

    # 2. Stampiamo la stringa usando i codici ANSI
    print(
        f"\033[s"       # ANSI: Salva la posizione attuale del cursore
        f"\033[1;1H"    # ANSI: Sposta il cursore alla Riga 1, Colonna 1
        f"\033[2K"      # ANSI: Cancella la riga corrente
        f"\033[1;36m"   # ANSI: Colore Ciano
        f"{status_text}"# Testo
        f"\033[0m"      # ANSI: Reset colore
        f"\033[u",      # ANSI: Ripristina il cursore dov'era
        end="",
        flush=True,
    )

def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


# --- THREAD AUTOMATICO ---
def flusso_automatico():
    zone = [a, b, c]
    while True:
        time.sleep(random.uniform(0.5, 2.0))
        # Fix W0621: Cambiato nome variabile da 'zona' a 'single_zone'
        # per non confonderla con quella globale
        for single_zone in zone:
            evento = random.randint(0, 100)
            if evento < 40:
                single_zone.park()
            elif 40 <= evento < 60:
                single_zone.unpark()

        update_header_only()

# --- AVVIO PROGRAMMA ---
clear_screen()
print("\n") # Spazio per header
print("Simulazione avviata. Scrivi i comandi sotto (es. 'park a').\n")

simulazione_thread = threading.Thread(target=flusso_automatico)
simulazione_thread.daemon = True
simulazione_thread.start()

# --- LOOP UTENTE ---
mappa_zone = {"a": a, "b": b, "c": c}

while True:
    try:
        comando_input = input("Inserisci comando: ").strip().lower()
    except EOFError:
        break

    if not comando_input:
        continue

    # Pulisci la riga dell'input utente
    print("\033[A\033[K", end="", flush=True)

    if comando_input == "exit":
        break

    parti = comando_input.split()

    if len(parti) != 2:
        print("\r⚠️  Formato errato! Usa: 'azione zona' (es. park a)", end="", flush=True)
        time.sleep(0.5)
        print("\r\033[K", end="", flush=True)
        continue

    azione, nome_zona = parti[0], parti[1]

    if nome_zona in mappa_zone:
        zona = mappa_zone[nome_zona]

        if azione == "park":
            esito = zona.park() # Ora catturiamo il True/False che ritorna la tua classe
            if esito:
                print(f"\r✅ Comando: PARK su {zona.name}", end="", flush=True)
            else:
                print(f"\r❌ Parcheggio PIENO su {zona.name}!", end="", flush=True)

            time.sleep(0.5)
            print("\r\033[K", end="", flush=True)

        elif azione == "unpark":
            esito = zona.unpark()
            if esito:
                print(f"\r✅ Comando: UNPARK su {zona.name}", end="", flush=True)
            else:
                print(f"\r❌ Parcheggio già VUOTO su {zona.name}!", end="", flush=True)

            time.sleep(0.5)
            print("\r\033[K", end="", flush=True)

        else:
            print(f"\r❌ Azione '{azione}' non valida!", end="", flush=True)
            time.sleep(0.5)
            print("\r\033[K", end="", flush=True)

        update_header_only()

    else:
        print(f"\r❌ Zona '{nome_zona}' inesistente!", end="", flush=True)
        time.sleep(0.5)
        print("\r\033[K", end="", flush=True)