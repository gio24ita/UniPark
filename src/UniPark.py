import os
import random
import shutil
import sys
import threading
import time
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

            self.waiting += 1
            return False

    def unpark(self):
        with self.lock:
            # Logica FIFO per la coda
            if self.waiting > 0:
                self.waiting -= 1
                return True  # Un'auto esce, una dalla coda entra subito

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
                "rate": self.occupancy_rate,
            }


# ==================== SISTEMA UNIPARK (CONTROLLER & VIEW) ====================


class UniParkSystem:
    def __init__(self):
        # Inizializzazione Zone (Semplificata per evitare troppi attributi)
        # R0902: Too many instance attributes (Fixed by using list directly)
        self.zones = [
            ParkingZone("Viale A. Doria", 60, random.randint(20, 60)),
            ParkingZone("DMI", 45, random.randint(15, 45)),
            ParkingZone("Via S. Sofia", 80, random.randint(30, 80)),
        ]

        self.zone_map = {"a": self.zones[0], "b": self.zones[1], "c": self.zones[2]}

        self.running = True

        # Lock globale per la scrittura a schermo
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
                return f"{clean_text}\033[K"  # \033[K pulisce il resto della riga

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
                total_capacity += status["capacity"]
                total_free += status["free_slots"]
                total_waiting += status["waiting"]

                # Barra grafica
                bar_max_len = max(5, col_width - 18)
                bar_len = min(10, bar_max_len)
                filled = int((status["occupied"] / status["capacity"]) * bar_len)
                # C0104: Disallowed name "bar" -> Renamed to progress_bar
                progress_bar = "█" * filled + "░" * (bar_len - filled)

                if status["rate"] > 95:
                    state_emoji = "🔴 PIENO"
                elif status["rate"] > 70:
                    state_emoji = "🟠 AFFOLLATO"
                else:
                    state_emoji = "🟢 LIBERO"

                # Costruzione blocco testo zona
                line1 = f"📍 {status['name']}"
                line2 = f"   {state_emoji}"
                line3 = f"   [{progress_bar}] {int(status['rate'])}%"
                line4 = f"   Lib: {status['free_slots']}/{status['capacity']}"
                line5 = f"   Coda: {status['waiting']}"

                columns_data.append(
                    [
                        line1.ljust(col_width - 1),
                        line2.ljust(col_width - 1),
                        line3.ljust(col_width),
                        line4.ljust(col_width),
                        line5.ljust(col_width),
                    ]
                )

            lines.append(make_line(""))

            # Unione colonne
            for row_tuple in zip(*columns_data):
                row_str = " | ".join(row_tuple)
                lines.append(make_line(row_str))

            # Footer
            lines.append(make_line("-" * dash_width))
            text_footer = (
                f"📊 TOTALE: {total_free}/{total_capacity} liberi | "
                f"{total_waiting} in coda"
            )
            lines.append(make_line(text_footer))
            lines.append(make_line("=" * dash_width))

            # --- STAMPA ANSI MAGICA ---
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
        Questa funzione gira in un thread separato PER OGNI ZONA.
        """
        while self.running:
            # 1. Simulazione temporale non deterministica
            attesa = random.uniform(2.0, 5.0)
            time.sleep(attesa)

            if not self.running:
                break

            evento = random.randint(0, 100)

            # W0612: Unused variable 'changed' removed
            if evento < 40:
                zone.park()
            elif 40 <= evento < 80:
                zone.unpark()

            self.print_live_dashboard()

    # ------------------ SEZIONE INPUT & CONTROLLO ------------------

    def handle_user_command(self, command: str):
        parts = command.strip().lower().split()
        if not parts:
            return

        action = parts[0]
        if action == "exit":
            self.running = False
            return

        if action in ["park", "unpark"]:
            if len(parts) < 2 or parts[1] not in self.zone_map:
                self.show_feedback(f"⚠️  Usa: {action} [a|b|c]")
                return

            zone = self.zone_map[parts[1]]

            if action == "park":
                success = zone.park()
                msg = (
                    f"✅ MANUAL PARK: {zone.name}"
                    if success
                    else f"⏳ PARK: {zone.name} PIENA → Coda"
                )
            else:
                success = zone.unpark()
                msg = (
                    f"👋 MANUAL UNPARK: {zone.name}"
                    if success
                    else f"⚠️  UNPARK: {zone.name} vuota"
                )

            self.show_feedback(msg)
            self.print_live_dashboard()
        else:
            self.show_feedback(f"⚠️  Comando sconosciuto: {action}")

    def reset_prompt(self):
        sys.stdout.write(f"\033[{self.PROMPT_LINE};1H> \033[K")
        sys.stdout.flush()

    def _read_char_windows(self):
        # C0415, E0401: Suppress import errors for non-Windows platforms
        import msvcrt  # pylint: disable=import-outside-toplevel,import-error

        char = msvcrt.getch()
        if char == b"\r":
            return "\n"
        if char == b"\x08":
            return "\b"
        return char.decode("utf-8", errors="ignore")

    def start(self):
        """Entry point dell'applicazione"""
        self.clear_screen()

        # Riserva spazio vuoto iniziale per l'interfaccia
        for _ in range(self.PROMPT_LINE + 2):
            print()

        self.print_live_dashboard()

        # --- AVVIO MULTI-THREADING ---
        threads = []
        for zone in self.zones:
            t = threading.Thread(target=self._zone_worker, args=(zone,))
            t.daemon = True
            t.start()
            threads.append(t)

        self.reset_prompt()

        # --- LOOP DI INPUT PRINCIPALE ---
        # Leggiamo i caratteri uno alla volta e proteggiamo ogni stampa
        # con un Mutex (Lock) per evitare sovrapposizioni grafiche.

        while self.running:
            try:
                # Posizionamento cursore protetto
                # Impediamo che un thread sposti il cursore mentre noi ci posizioniamo.
                with self.system_lock:
                    sys.stdout.write(f"\033[{self.PROMPT_LINE};3H")
                    sys.stdout.flush()

                cmd = ""

                # Loop di lettura carattere per carattere
                while True:
                    char = (
                        sys.stdin.read(1)
                        if os.name != "nt"
                        else self._read_char_windows()
                    )

                    if char in ("\n", "\r"):  # Tasto Invio
                        break

                    if char in ("\x7f", "\b"):  # Gestione Backspace manuale
                        if cmd:
                            cmd = cmd[:-1]

                            with self.system_lock:
                                sys.stdout.write("\b \b")
                                sys.stdout.flush()
                    else:
                        cmd += char

                        # Senza questo lock, il carattere potrebbe apparire in mezzo alla dashboard
                        # se un aggiornamento avviene in questo esatto millisecondo.
                        with self.system_lock:
                            sys.stdout.write(char)
                            sys.stdout.flush()

                # 2. Pulizia "Ghost Text"
                # Usiamo \033[2K (Clear Line) invece di \033[K.
                # Questo risolve il bug dove il vecchio comando rimaneva visibile parzialmente.
                with self.system_lock:
                    sys.stdout.write(f"\033[{self.PROMPT_LINE};1H\033[2K")
                    # Vai alla riga SUCCESSIVA e cancella tutto (rimuove il "park a" lasciato sotto)
                    sys.stdout.write(f"\033[{self.PROMPT_LINE + 1};1H\033[2K")
                    sys.stdout.flush()

                # Esecuzione comando
                if cmd.strip():
                    self.handle_user_command(cmd.strip())

                self.reset_prompt()

            except KeyboardInterrupt:
                self.running = False
                break
            except Exception:  # pylint: disable=broad-exception-caught
                # Gestione robusta errori per non crashare l'intera simulazione
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
