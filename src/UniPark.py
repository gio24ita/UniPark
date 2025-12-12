import random
import time
import threading
import os


# Classe Parcheggio
class ParkingZone:
    def __init__(self, name, capacity, free_slots):
        self.name = name
        self.capacity = capacity

        # se per errore arrivano dati strani (es. più auto che posti), li correggiamo subito
        if free_slots > capacity:
            self.free_slots = capacity
        elif free_slots < 0:
            self.free_slots = 0
        else:
            self.free_slots = free_slots

        # IL LOCK (LA CHIAVE DI SICUREZZA), Creiamo un lucchetto specifico per QUESTA zona.
        # Così ogni zona avrà la sua key
        self.lock = threading.Lock()
        """
        serve a evitare il Race Condition
        immaginalo come un semaforo rosso/verde
        serve a evitare che tu e il simulatore/altro utente parcheggiate allo stesos momento
        e nello stesso parcheggio con 1 solo posto libero
        va a finire che parcheggimao con il contatore a -1
        """

    def park(self):
        """
        funzione per il parcheggio dell'auto
        usiamo il lock per evitare conflitti tra utente e computer.
        ritorniamo True se parcheggiamo, False se è pieno.
        """
        with self.lock:  # aspetta che la chiave si libera, poi entra e chiudi la chiave
            if self.free_slots > 0:
                self.free_slots -= 1
                return True
            else:
                return False
        # appena esci dal "with", la chiave è free

    def unpark(self):
        """
        funzione per l'uscita dal parcheggio
        ritorniamo True se usciamo, False se era già vuoto.
        """
        with self.lock:  # <-- impostiamo il solito lock
            if self.free_slots < self.capacity:
                self.free_slots += 1
                return True
            else:
                return False

    def get_status(self):
        """funzione che restituisce una stringa con lo stato attuale (utile per i print)"""
        with self.lock:
            return f"{self.free_slots}/{self.capacity}"

    def __str__(self):
        """funzione che permette di fare print(zona) e vedere un testo clean"""
        return f"[{self.name}] Posti liberi: {self.get_status()}"


# FINE CLASSE PARCHEGGIO


# Creazione aree parcheggio
a = ParkingZone("Zona A", 60, random.randint(1, 60))
b = ParkingZone("Zona B", 45, random.randint(1, 45))
c = ParkingZone("Zona C", 80, random.randint(1, 80))


def print_status():
    #    print(f"\n--- STATO LIVE: A:{a.free_slots} | B:{b.free_slots} | C:{c.free_slots} |  D:{d.free_slots} ---")
    print(
        f"\n--- STATO LIVE: A:{a.free_slots} | B:{b.free_slots} | C:{c.free_slots} ---"
    )


def clear_screen():
    # Controlla se il sistema è Windows ('nt') o Unix/Linux/Mac
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


# --- 1. FUNZIONE PER IL FLUSSO AUTOMATICO (BACKGROUND) ---
def flusso_automatico():
    """Simulazione realistica con eventi indipendenti e tempi variabili"""

    # zone = [a, b, c, d]
    zone = [a, b, c]

    while True:
        # 1. Attesa variabile
        attesa = random.uniform(2.0, 6.0)
        time.sleep(attesa)

        # 2. LOGICA: Le auto si muovono
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
        print(
            "\n[Simulazione attiva] Inserisci comando (es. 'park a') e premi Invio: ",
            end="",
            flush=True,
        )


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
            zona_selezionata = mappa_zone[
                nome_zona
            ]  # Prende l'oggetto reale (a, b, c o d)

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
            print(f"⚠️ Zona '{nome_zona}' non trovata. Zone valide: a, b, c, d.")

    except Exception as e:
        print(f"Errore: {e}")
