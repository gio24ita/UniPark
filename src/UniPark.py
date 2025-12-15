"""
UniPark - Versione HYBRID MULTI-THREAD
Struttura: UI Avanzata (Codice 2) + Logica Multi-Thread Indipendente (Codice 1)
Descrizione: Ogni zona parcheggio ha il suo thread dedicato che opera a velocità variabile.
"""

import os
import random
import threading
import time
import sys
import shutil
from threading import Lock

# --- CONFIGURAZIONE ANSI PER WINDOWS ---
if os.name == "nt":
    os.system("")

# ==================== LOGICA DATI (MODEL) ====================

class ParkingZone:
    """Modello che gestisce i dati del singolo parcheggio in modo Thread-Safe."""
    def __init__(self, name, capacity, free_slots):
        self.name = name
        self.capacity = capacity
        # Clamping dei valori iniziali
        self.free_slots = max(0, min(free_slots, capacity))
        self.waiting = 0
        # Lock specifico per i dati di questa zona
        self.lock = Lock()

    @property
    def occupied_slots(self):
        return self.capacity - self.free_slots

    @property
    def occupancy_rate(self):
        return (self.occupied_slots / self.capacity) * 100

    def park(self):
        with self.lock:
            if self.free_slots > 0:
                self.free_slots -= 1
                return True
            else:
                self.waiting += 1
                return False

    def unpark(self):
        with self.lock:
            # Logica FIFO per la coda
            if self.waiting > 0:
                self.waiting -= 1
                return True  # Un'auto esce, una dalla coda entra subito (saldo 0 sui posti)
            
            if self.free_slots < self.capacity:
                self.free_slots += 1
                return True
            return False

    def get_status_dict(self):
        """Restituisce una fotografia dello stato attuale per la UI."""
        with self.lock:
            return {
                "name": self.name,
                "capacity": self.capacity,
                "free_slots": self.free_slots,
                "occupied": self.occupied_slots,
                "waiting": self.waiting,
                "rate": self.occupancy_rate
            }

# ==================== SISTEMA UNIPARK (CONTROLLER & VIEW) ====================

class UniParkSystem:
    def __init__(self):
        # Inizializzazione Zone
        self.zona_a = ParkingZone("Viale A. Doria", 60, random.randint(20, 60))
        self.zona_b = ParkingZone("DMI", 45, random.randint(15, 45))
        self.zona_c = ParkingZone("Via S. Sofia", 80, random.randint(30, 80))

        self.zones = [self.zona_a, self.zona_b, self.zona_c]
        self.zone_map = {"a": self.zona_a, "b": self.zona_b, "c": self.zona_c}
        
        self.running = True
        
        # Lock globale per la scrittura a schermo (evita che i thread scrivano uno sopra l'altro)
        self.system_lock = Lock()
        
        # Layout UI
        self.DASHBOARD_HEIGHT = 12
        self.PROMPT_LINE = self.DASHBOARD_HEIGHT + 2

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    # ------------------ SEZIONE RENDERING (UI) ------------------

    def print_live_dashboard(self):
        """
        Ridisegna SOLO la dashboard in alto, preservando cursore e input utente.
        Thread-Safe grazie a self.system_lock.
        """
        with self.system_lock:
            cols, _ = shutil.get_terminal_size((80, 20))
            dash_width = max(cols - 2, 40)
            
            lines = []
            
            def make_line(text):
                clean_text = text[:dash_width]
                return f"{clean_text}\033[K" # \033[K pulisce il resto della riga

            # Header
            lines.append(make_line("=" * dash_width))
            lines.append(make_line("🅿️  UNIPARK LIVE - DASHBOARD REAL-TIME"))
            lines.append(make_line("=" * dash_width))

            total_capacity = 0
            total_free = 0
            total_waiting = 0
            
            columns_data = []
            col_width = (dash_width // 3) - 3

            # Calcolo dati per ogni zona
            for zone in self.zones:
                status = zone.get_status_dict()
                total_capacity += status['capacity']
                total_free += status['free_slots']
                total_waiting += status['waiting']

                # Barra grafica
                bar_max_len = max(5, col_width - 18)
                bar_len = min(10, bar_max_len)
                filled = int((status['occupied'] / status['capacity']) * bar_len)
                bar = "█" * filled + "░" * (bar_len - filled)

                if status['rate'] > 95: state_emoji = "🔴 PIENO"
                elif status['rate'] > 70: state_emoji = "🟠 AFFOLLATO"
                else: state_emoji = "🟢 LIBERO"

                # Costruzione blocco testo zona
                line1 = f"📍 {status['name']}"
                line2 = f"   {state_emoji}"
                line3 = f"   [{bar}] {int(status['rate'])}%"
                line4 = f"   Lib: {status['free_slots']}/{status['capacity']}"
                line5 = f"   Coda: {status['waiting']}"

                columns_data.append([
                    line1.ljust(col_width - 1),
                    line2.ljust(col_width - 1),
                    line3.ljust(col_width),
                    line4.ljust(col_width),
                    line5.ljust(col_width)
                ])

            lines.append(make_line(""))
            
            # Unione colonne
            for row_tuple in zip(*columns_data):
                row_str = " | ".join(row_tuple)
                lines.append(make_line(row_str))

            # Footer
            lines.append(make_line("-" * dash_width))
            lines.append(make_line(f"📊 TOTALE: {total_free}/{total_capacity} liberi | {total_waiting} in coda"))
            lines.append(make_line("=" * dash_width))

            # --- STAMPA ANSI MAGICA ---
            # 1. Nascondi cursore (?25l)
            # 2. Salva posizione (s)
            # 3. Scrivi righe in alto
            # 4. Ripristina posizione (u)
            # 5. Mostra cursore (?25h)
            
            sys.stdout.write("\033[?25l") 
            sys.stdout.write("\033[s")    
            
            for i, line in enumerate(lines, start=1):
                sys.stdout.write(f"\033[{i};1H{line}")
            
            sys.stdout.write("\033[u")    
            sys.stdout.write("\033[?25h") 
            sys.stdout.flush()

    def show_feedback(self, msg):
        """Mostra messaggi temporanei sotto la dashboard."""
        feedback_line = self.DASHBOARD_HEIGHT + 1
        sys.stdout.write(f"\033[?25l\033[{feedback_line};1H{msg}\033[K\033[?25h")
        sys.stdout.flush()
        time.sleep(1.2)
        sys.stdout.write(f"\033[?25l\033[{feedback_line};1H\033[K\033[?25h")
        sys.stdout.flush()

    # ------------------ SEZIONE MULTI-THREAD (WORKERS) ------------------

    def _zone_worker(self, zone):
        """
        WORKER INDIPENDENTE (Logica presa dal Primo Codice).
        Questa funzione gira in un thread separato PER OGNI ZONA.
        """
        while self.running:
            # 1. Simulazione temporale non deterministica (ogni zona ha i suoi tempi)
            attesa = random.uniform(2.0, 5.0)
            time.sleep(attesa)

            # 2. Generazione evento casuale
            if not self.running: break # Controllo sicurezza uscita
            
            evento = random.randint(0, 100)
            
            # Logica probabilistica (40% park, 40% unpark, 20% idle)
            changed = False
            if evento < 40:
                zone.park()
                changed = True
            elif 40 <= evento < 80:
                zone.unpark()
                changed = True
            
            # 3. Aggiorna la dashboard solo se qualcosa è cambiato (o per refresh)
            # Nota: Essendo multi-thread, più zone potrebbero chiedere l'update contemporaneamente.
            # Il lock dentro print_live_dashboard gestirà la coda.
            self.print_live_dashboard()

    # ------------------ SEZIONE INPUT & CONTROLLO ------------------

    def handle_user_command(self, command: str):
        parts = command.strip().lower().split()
        if not parts: return

        action = parts[0]
        if action == "exit":
            self.running = False
            return

        if action in ["park", "unpark"]:
            if len(parts) < 2 or parts[1] not in self.zone_map:
                self.show_feedback(f"⚠️  Usa: {action} [a|b|c]")
                return

            zone = self.zone_map[parts[1]]
            
            # Esecuzione immediata comando manuale
            if action == "park":
                success = zone.park()
                msg = f"✅ MANUAL PARK: {zone.name}" if success else f"⏳ PARK: {zone.name} PIENA → Coda"
            else:
                success = zone.unpark()
                msg = f"👋 MANUAL UNPARK: {zone.name}" if success else f"⚠️  UNPARK: {zone.name} vuota"
            
            # Aggiornamento immediato visivo
            self.show_feedback(msg)
            self.print_live_dashboard()
        else:
            self.show_feedback(f"⚠️  Comando sconosciuto: {action}")

    def reset_prompt(self):
        sys.stdout.write(f"\033[{self.PROMPT_LINE};1H> \033[K")
        sys.stdout.flush()

    def _read_char_windows(self):
        import msvcrt
        char = msvcrt.getch()
        if char == b'\r': return '\n'
        elif char == b'\x08': return '\b'
        return char.decode('utf-8', errors='ignore')

    def start(self):
        self.clear_screen()
        
        # Riserva spazio verticale
        for i in range(self.PROMPT_LINE + 2):
            print()
        
        self.print_live_dashboard()
        
        # --- AVVIO MULTI-THREADING ---
        # Invece di un thread unico, ne avviamo 3 separati (uno per zona)
        threads = []
        for zone in self.zones:
            t = threading.Thread(target=self._zone_worker, args=(zone,))
            t.daemon = True # Si chiudono se si chiude il main
            t.start()
            threads.append(t)

        self.reset_prompt()

        # --- LOOP DI INPUT PRINCIPALE ---
        while self.running:
            try:
                # Ripristina cursore input
                sys.stdout.write(f"\033[{self.PROMPT_LINE};3H")
                sys.stdout.flush()
                
                # Lettura carattere per carattere (Non-blocking per la UI)
                cmd = ""
                while True:
                    char = sys.stdin.read(1) if os.name != "nt" else self._read_char_windows()
                    
                    if char == '\n' or char == '\r':
                        break
                    elif char == '\x7f' or char == '\b': # Backspace
                        if cmd:
                            cmd = cmd[:-1]
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                    else:
                        cmd += char
                        sys.stdout.write(char)
                        sys.stdout.flush()
                
                # Pulisci riga input
                sys.stdout.write(f"\033[{self.PROMPT_LINE};1H\033[K")
                sys.stdout.flush()
                
                if cmd.strip():
                    self.handle_user_command(cmd.strip())
                
                self.reset_prompt()
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception:
                self.reset_prompt()
        
        # Uscita pulita
        sys.stdout.write(f"\033[{self.PROMPT_LINE + 2};1H")
        print("\n✅ Sistema UniPark terminato.")

# ==================== MAIN ====================

if __name__ == "__main__":
    app = UniParkSystem()

    os.system("cls" if os.name == "nt" else "clear")
    print("\n" + "=" * 60)
    print("🎓 UNIPARK - Sistema Gestione Parcheggi")
    print("=" * 60)
    print("\n📋 Zone disponibili:")
    print("   A - Viale A. Doria (60)")
    print("   B - DMI (45)")
    print("   C - Via S. Sofia (80)")
    print("\n🎮 Comandi:")
    print("   park   [a|b|c] - Parcheggia")
    print("   unpark [a|b|c] - Esci")
    print("   exit           - Chiudi")
    print("\n" + "=" * 60 + "\n")
    input("Premi INVIO per avviare la simulazione... ")

    app.start()