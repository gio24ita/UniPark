import random
import time
import threading  # <--- IMPORTA QUESTO
import os
from threading import Lock

# --- TUE CLASSI ---
class ParkingZone:
    def __init__(self, name, capacity, free_slots):
        self.name = name
        self.capacity = capacity
        self.free_slots = free_slots

    def park(self):
        if self.free_slots == 0:
            print(f"\n[AUTO] No free slots on {self.name}")
        else:
            self.free_slots -= 1
            # print ridotto per non sporcare troppo la console
            # print(f"[AUTO] Parked on {self.name}")

    def unpark(self):
        if self.free_slots == self.capacity:
            pass  # Non stampiamo nulla se è vuoto per pulizia
        else:
            self.free_slots += 1
            # print(f"[AUTO] Unparked on {self.name}")


class ZonaA(ParkingZone): pass


class ZonaB(ParkingZone): pass


class ZonaC(ParkingZone): pass

# --- ISTANZE GLOBALI (CONDIVISE) ---
a = ZonaA("Zona A", 60, random.randint(1,60))
b = ZonaB("Zona B", 45, random.randint(1,45))
c = ZonaC("Zona C", 80, random.randint(1,80))
#d = ZonaD("Zona D", 10, random.randint(1,10))

# --- LOCK PER SINCRONIZZAZIONE TRA THREAD ---
zone_lock = Lock()


def print_status():
    with zone_lock:
        print(f"\n--- STATO LIVE: A:{a.free_slots} | B:{b.free_slots} | C:{c.free_slots} ---")

def clear_screen():
    # Controlla se il sistema è Windows ('nt') o Unix/Linux/Mac
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

# --- 1. FUNZIONE PER IL FLUSSO AUTOMATICO (BACKGROUND) ---
def flusso_automatico():
    """Simulazione realistica con eventi indipendenti e tempi variabili"""

    #zone = [a, b, c, d]
    zone = [a, b, c]

    while True:
        # 1. Attesa variabile
        attesa = random.uniform(2.0, 6.0)
        time.sleep(attesa)

        # 2. LOGICA: Le auto si muovono
        with zone_lock:
            for zona in zone:
                evento = random.randint(0, 100)
                if evento < 40:
                    zona.park()
                elif 40 <= evento < 60:
                    zona.unpark()
                else:
                    pass

        # 3. PULIZIA E AGGIORNAMENTO (MIGLIORATE)
        clear_screen()
        print_status()

        # IMPORTANTE: Ristampiamo questo avviso perché clear_screen()
        # cancella la richiesta di input dell'utente.
        print("\n[Simulazione attiva] Inserisci comando (es. 'park a') e premi Invio: ", end="", flush=True)



# --- 2. CONFIGURAZIONE DEL THREAD ---
# Creiamo il thread che eseguirà la funzione 'flusso_automatico'
simulazione_thread = threading.Thread(target=flusso_automatico)



# 'daemon=True' significa che se chiudi il programma principale,
# anche questo thread muore automaticamente.
simulazione_thread.daemon = True

# Avviamo il thread
simulazione_thread.start()

# --- 3. CODICE PRINCIPALE (INTERAZIONE UTENTE) ---
# Da qui in poi, il codice viene eseguito IN PARALLELO al while di sopra

print("Simulazione avviata in background! Tu puoi digitare comandi.")
print("Comandi disponibili: 'park |NOME ZONA|', 'unpark |NOME ZONA|', 'exit'...")

# --- 1. CREA UNA MAPPA (DIZIONARIO) ---
# Questo serve al computer per capire che se scrivo "a", intendo l'oggetto 'a'
mappa_zone = {
    "a": a,
    "b": b,
    "c": c,
}

while True:
    # Esempio input utente: "park a" o "unpark b"
    comando_input = input("Inserisci comando (es. 'park a'): ").strip().lower()

    if comando_input == "exit":
        print("Chiusura simulazione...")
        break

    # --- 2. DIVIDI LA FRASE IN PAROLE ---
    try:
        # split() trasforma "park a" in ['park', 'a']
        parti = comando_input.split()

        # Se l'utente ha scritto meno di 2 parole (es. solo "park"), saltiamo il giro
        if len(parti) != 2:
            print("⚠️ Formato errato. Usa: azione zona (es. 'park a')")
            continue

        azione = parti[0]  # es. "park"
        nome_zona = parti[1]  # es. "a"

        # --- 3. VERIFICA SE LA ZONA ESISTE ---
        if nome_zona in mappa_zone:
            zona_selezionata = mappa_zone[nome_zona]  # Prende l'oggetto reale (a, b, c o d)

            # --- 4. ESEGUE L'AZIONE ---
            if azione == "park":
                print(f"--> Utente sta parcheggiando in {nome_zona.upper()}...")
                zona_selezionata.park()  # Chiama il metodo sull'oggetto giusto

                # Pulisci e aggiorna
                clear_screen()
                print_status()

            elif azione == "unpark":
                print(f"--> Utente sta uscendo da {nome_zona.upper()}...")
                zona_selezionata.unpark()

                # Pulisci e aggiorna #DA MIGLIORARE (PROVATELO E GUARDATE COME SI COMPORTA)
                clear_screen()
                print_status()

            else:
                print("⚠️ Azione non riconosciuta. Usa 'park' o 'unpark'.")

        else:
            print(f"⚠️ Zona '{nome_zona}' non trovata. Zone valide: a, b, c.")

    except Exception as e:
        print(f"Errore: {e}")