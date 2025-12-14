import os
import random
import threading
import time

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
        with self.lock:
            return f"{self.free_slots}/{self.capacity} ({self.waiting})"


# --- ISTANZE GLOBALI ---
a = ParkingZone("Zona A", 60, random.randint(1, 60))
b = ParkingZone("Zona B", 45, random.randint(1, 45))
c = ParkingZone("Zona C", 80, random.randint(1, 80))


# --- GESTIONE GRAFICA CORRETTA ---
def update_header_only():
    """Aggiorna solo la riga in alto."""
    # Nota: spezziamo la riga lunga per Pylint
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
        for single_zone in zone:
            evento = random.randint(0, 100)
            if evento < 40:
                single_zone.park()  # Arrivo: tenta park o coda
            elif 40 <= evento < 60:
                single_zone.unpark()  # Partenza: libera se possibile e gestisce coda

        update_header_only()


# --- AVVIO PROGRAMMA ---
clear_screen()
print("\n")  # Spazio per header
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
        print(
            "\r⚠️  Formato errato! Usa: 'azione zona' (es. park a)", end="", flush=True
        )
        time.sleep(0.5)
        print("\r\033[K", end="", flush=True)
        continue

    azione, nome_zona = parti[0], parti[1]

    if nome_zona in mappa_zone:
        zona = mappa_zone[nome_zona]

        if azione == "park":
            esito = zona.park()
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

            time.sleep(0.5)
            print("\r\033[K", end="", flush=True)

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

        update_header_only()

    else:
        print(f"\r❌ Zona '{nome_zona}' inesistente!", end="", flush=True)
        time.sleep(0.5)
        print("\r\033[K", end="", flush=True)
