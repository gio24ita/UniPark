# Modulo UniParkGUI: Interfaccia di controllo e monitoraggio in tempo reale.
# Questo file gestisce la Dashboard grafica (Tkinter), la visualizzazione HUD
# dei parcheggi e la simulazione dei flussi di traffico tramite multithreading.

import os
import random
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext, ttk

# ==================== INTERFACCIA GRAFICA (UI) ====================

# Importiamo il core logico. Se UniPark.py non esiste, l'app si chiude con un errore.
try:
    from UniPark import UniParkSystem
except ImportError:
    messagebox.showerror(
        "Errore",
        "File UniPark.py non trovato. Assicurati che sia nella stessa cartella.",
    )
    sys.exit(1)


class UniParkApp(tk.Tk):
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        super().__init__()

        # --- Configurazione Finestra (PANNELLO FISSO BLINDATO) ---
        # Impostiamo una dimensione fissa (1280x800) per garantire che i badge
        # sulla mappa siano sempre perfettamente allineati all'immagine satellitare.
        self.title("UniPark - Intelligent Parking Management")
        self.geometry("1280x800")
        self.resizable(False, False)

        # Blocchiamo fisicamente i limiti della finestra per evitare lo Snap Assist di Windows
        self.maxsize(1280, 800)
        self.minsize(1280, 800)

        # Inizializziamo colori e configurazione base
        self.set_theme_colors()
        self.configure(bg=self.colors["bg_app"])
        self.running = True
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Inizializziamo il sistema logico (il Model/Controller)
        self.system = UniParkSystem()
        self.zones = self.system.zones

        # Questa variabile tiene traccia della zona occupata manualmente dall'utente
        self.user_parked_zone = None

        # Coordinate in pixel calibrate sull'immagine 1280x800
        self.map_coords = {
            "Zona A (Viale A. Doria)": (700, 100),
            "Zona B (DMI)": (620, 430),
            "Zona C (Via S. Sofia)": (160, 520),
        }

        # --- SINCRONIZZAZIONE ORARIO INIZIALE ---
        # All'avvio leggiamo l'ora reale e popoliamo i parcheggi di conseguenza
        _, prob_park = self.get_time_phase()
        for zone in self.zones:
            target_occ = (prob_park / 100.0) + random.uniform(-0.05, 0.05)
            target_occ = max(0.02, min(0.98, target_occ))
            with zone.lock:
                zone.free_slots = int(zone.capacity * (1.0 - target_occ))
                zone.waiting = 0

        # Creiamo lo scheletro dell'interfaccia
        self.setup_styles()
        self.create_header()
        self.setup_main_layout()

        # Avviamo i thread per il traffico simulato e il loop di aggiornamento UI
        self.start_background_workers()
        self.update_ui_loop()

    def get_time_phase(self):
        """Calcola la fase attuale basata sull'orologio di sistema e imposta la probabilità di sosta."""
        hour = datetime.now().hour
        if 8 <= hour < 14:
            return "PICCO MATTUTINO", 85  # Molte auto in entrata
        elif 14 <= hour < 16:
            return "TRAFFICO POMERIDIANO", 55  # Situazione stabile
        elif 16 <= hour < 19:
            return "DEFLUSSO POMERIDIANO", 25  # Le auto iniziano a uscire
        elif 19 <= hour < 22:
            return "SVUOTAMENTO SERALE", 10  # Parcheggi quasi deserti
            return "FASCIA NOTTURNA", 2  # Nessuna attività

    def set_theme_colors(self):
        """Palette colori centrale dell'applicazione per facilitare future modifiche al tema."""
        self.colors = {
            "bg_app": "#0A0A0E",
            "bg_panel": "#141419",
            "bg_header": "#0F0F14",
            "border_color": "#2A2A35",
            "text_primary": "#FFFFFF",
            "text_secondary": "#A0A0B5",
            "accent_green": "#00E676",
            "accent_orange": "#FF9100",
            "accent_red": "#FF1744",
            "accent_cyan": "#00E5FF",
            "log_bg": "#050508",
            "btn_disabled": "#22222A",
            "log_in": "#4ADE80",
            "log_out": "#94A3B8",
        }

    def setup_styles(self):
        """Configura l'aspetto visivo dei widget moderni (ttk)."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Card.TLabelframe",
            background=self.colors["bg_panel"],
            bordercolor=self.colors["border_color"],
            relief="solid",
            borderwidth=1,
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=self.colors["bg_panel"],
            foreground=self.colors["accent_cyan"],
            font=("Segoe UI", 12, "bold"),
        )

        style.configure(
            "TProgressbar", thickness=6, troughcolor="#22222A", borderwidth=0
        )
        style.configure(
            "Green.Horizontal.TProgressbar", background=self.colors["accent_green"]
        )
        style.configure(
            "Orange.Horizontal.TProgressbar", background=self.colors["accent_orange"]
        )
        style.configure(
            "Red.Horizontal.TProgressbar", background=self.colors["accent_red"]
        )

    def create_header(self):
        """Costruisce la barra superiore con titolo, orologio e fase traffico."""
        header_frame = tk.Frame(
            self,
            bg=self.colors["bg_header"],
            height=90,
            bd=1,
            relief="solid",
            highlightbackground=self.colors["border_color"],
            highlightthickness=1,
        )
        header_frame.pack(fill="x", side="top")

        # TITOLO (FONT 28) E SOTTOTITOLO
        title_container = tk.Frame(header_frame, bg=self.colors["bg_header"])
        title_container.pack(side=tk.LEFT, padx=25, pady=10)

        tk.Label(
            title_container,
            text="UNIPARK CONTROL CENTER",
            font=("Segoe UI", 28, "bold"),
            bg=self.colors["bg_header"],
            fg=self.colors["text_primary"],
        ).pack(anchor="w")
        tk.Label(
            title_container,
            text="Sistema di Gestione Flussi e Parcheggi Intelligente",
            font=("Segoe UI", 11),
            bg=self.colors["bg_header"],
            fg=self.colors["text_secondary"],
        ).pack(anchor="w")

        # OROLOGIO E FASE
        time_container = tk.Frame(header_frame, bg=self.colors["bg_header"])
        time_container.pack(side=tk.RIGHT, padx=25, pady=10)

        self.clock_label = tk.Label(
            time_container,
            text="00:00:00",
            font=("Consolas", 24, "bold"),
            bg=self.colors["bg_header"],
            fg=self.colors["text_primary"],
        )
        self.clock_label.pack(anchor="e")

        self.phase_label = tk.Label(
            time_container,
            text="[ FASE TRAFFICO ]",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["bg_header"],
            fg=self.colors["accent_cyan"],
        )
        self.phase_label.pack(anchor="e")

    def setup_main_layout(self):
        """Organizza lo spazio principale in Mappa (Sinistra) e Dashboard (Destra)."""
        main_container = tk.Frame(self, bg=self.colors["bg_app"])
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # --- PANNELLO MAPPA (Sinistra) ---
        map_panel = tk.Frame(
            main_container,
            bg=self.colors["bg_panel"],
            bd=1,
            relief="solid",
            highlightbackground=self.colors["border_color"],
            highlightthickness=1,
        )
        map_panel.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 10))

        self.canvas = tk.Canvas(map_panel, bg="#121212", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        try:
            # Caricamento immagine satellitare. Deve trovarsi nella stessa cartella dello script.
            cartella_corrente = os.path.dirname(os.path.abspath(__file__))
            percorso_immagine = os.path.join(cartella_corrente, "mappa.png")
            self.bg_img = tk.PhotoImage(file=percorso_immagine)
            self.canvas.create_image(
                0, 0, anchor="nw", image=self.bg_img, tags="static_map"
            )
        except Exception as e:
            # pylint: disable=broad-exception-caught
            self.canvas.create_text(
                400,
                300,
                text="Mappa non trovata ('mappa.png')",
                font=("Consolas", 14, "bold"),
                fill=self.colors["accent_red"],
                tags="static_map",
            )

        # --- PANNELLO DASHBOARD (Destra) ---
        dashboard_panel = tk.Frame(main_container, bg=self.colors["bg_app"], width=460)
        dashboard_panel.pack(side=tk.RIGHT, fill="y")
        dashboard_panel.pack_propagate(False)

        tk.Label(
            dashboard_panel,
            text="MONITORAGGIO ZONE IN TEMPO REALE",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg_app"],
            fg=self.colors["text_secondary"],
        ).pack(pady=(0, 10), anchor="w")

        self.zone_widgets = {}

        # Generazione automatica dei pannelli laterali basata sulla lista zone del Model
        for zone in self.zones:
            card = ttk.LabelFrame(
                dashboard_panel,
                text=f" {zone.name.upper()} ",
                style="Card.TLabelframe",
                padding=12,
            )
            card.pack(fill="x", pady=5)

            info_frame = tk.Frame(card, bg=self.colors["bg_panel"])
            info_frame.pack(fill="x", pady=(0, 5))

            lbl_status = tk.Label(
                info_frame,
                text="Scansione...",
                font=("Segoe UI", 11, "bold"),
                bg=self.colors["bg_panel"],
                fg=self.colors["text_primary"],
                anchor="w",
            )
            lbl_status.pack(fill="x")

            progress = ttk.Progressbar(
                info_frame,
                orient="horizontal",
                length=100,
                mode="determinate",
                style="Green.Horizontal.TProgressbar",
            )
            progress.pack(fill="x", pady=6)

            lbl_details = tk.Label(
                info_frame,
                text="--/--",
                font=("Consolas", 11),
                bg=self.colors["bg_panel"],
                fg=self.colors["text_primary"],
                anchor="e",
            )
            lbl_details.pack(fill="x")

            action_frame = tk.Frame(card, bg=self.colors["bg_panel"])
            action_frame.pack(fill="x", pady=(4, 0))

            lbl_queue = tk.Label(
                action_frame,
                text="Coda: 0",
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["bg_panel"],
                fg=self.colors["accent_orange"],
                anchor="w",
            )
            lbl_queue.pack(side=tk.LEFT)

            btn_park = tk.Button(
                action_frame,
                text="PARCHEGGIA",
                bg=self.colors["accent_green"],
                fg="#121212",
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                bd=0,
                padx=12,
                pady=5,
                cursor="hand2",
                activebackground="#00C853",
                command=lambda z=zone: self.user_action(z, "park"),
            )
            btn_park.pack(side=tk.RIGHT, padx=5)

            btn_unpark = tk.Button(
                action_frame,
                text="ESCI",
                bg=self.colors["accent_red"],
                fg="white",
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                bd=0,
                padx=12,
                pady=5,
                cursor="hand2",
                activebackground="#DC2626",
                state=tk.DISABLED,
                command=lambda z=zone: self.user_action(z, "unpark"),
            )
            btn_unpark.pack(side=tk.RIGHT)

            # Conserviamo i riferimenti ai widget per poterli aggiornare dinamicamente nel loop
            self.zone_widgets[zone.name] = {
                "lbl_status": lbl_status,
                "progress": progress,
                "lbl_details": lbl_details,
                "lbl_queue": lbl_queue,
                "btn_park": btn_park,
                "btn_unpark": btn_unpark,
            }

        # Terminale di Log in basso a destra
        tk.Label(
            dashboard_panel,
            text="REGISTRO EVENTI DI SISTEMA",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["bg_app"],
            fg=self.colors["text_secondary"],
        ).pack(pady=(15, 5), anchor="w")

        log_container = tk.Frame(
            dashboard_panel, bd=1, bg=self.colors["border_color"], relief="solid"
        )
        log_container.pack(fill="both", expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_container,
            bg=self.colors["log_bg"],
            fg=self.colors["text_secondary"],
            font=("Consolas", 10),
            bd=0,
            padx=10,
            pady=10,
        )
        self.log_area.pack(fill="both", expand=True)

        # Mappatura dei colori per i tag nel log
        self.log_area.tag_config("log_in", foreground=self.colors["log_in"])
        self.log_area.tag_config("log_out", foreground=self.colors["log_out"])
        self.log_area.tag_config(
            "user", foreground=self.colors["accent_cyan"], font=("Consolas", 10, "bold")
        )
        self.log_area.tag_config(
            "alert",
            foreground=self.colors["accent_orange"],
            font=("Consolas", 10, "bold"),
        )

    def log_msg(self, type_tag, zone_name, action_desc, color_tag):
        """Scrive un messaggio formattato nel terminale HUD dell'interfaccia."""

        def _write():
            self.log_area.config(state="normal")
            timestamp = datetime.now().strftime("%H:%M:%S")
            # ljust assicura l'allineamento perfetto delle colonne nel log
            formatted_msg = f"[{timestamp}] [{type_tag.ljust(8)}] {zone_name.ljust(7)} | {action_desc}\n"
            self.log_area.insert(tk.END, formatted_msg, color_tag)
            self.log_area.see(tk.END)
            self.log_area.config(state="disabled")

        self.after(0, _write)

    def user_action(self, zone, action):
        """Gestisce il click dei bottoni da parte dell'utente reale."""
        nome_breve = zone.name.split("(")[0].strip().upper()
        if action == "park":
            if zone.park():
                self.user_parked_zone = zone.name
                self.log_msg(
                    "UTENTE", nome_breve, "Parcheggio assegnato con successo", "user"
                )
            else:
                self.log_msg(
                    "ALLERTA", nome_breve, "Accesso negato, capacità massima", "alert"
                )

        elif action == "unpark":
            if zone.unpark():
                self.user_parked_zone = None
                self.log_msg(
                    "UTENTE", nome_breve, "Veicolo rimosso dal sistema", "user"
                )
            else:
                self.log_msg("ERRORE", nome_breve, "Anomalia durante l'uscita", "alert")

        self.update_widgets_once()

    def _zone_worker(self, zone):
        """Thread worker autonomo: simula ingressi e uscite automatiche di veicoli."""
        nome_breve = zone.name.split("(")[0].strip().upper()
        while self.running:
            time.sleep(random.uniform(3.5, 8.0))
            if not self.running:
                break

            _, prob_park = self.get_time_phase()
            evento = random.randint(0, 100)

            if evento < prob_park:
                if zone.park():
                    self.log_msg(
                        "INGRESSO", nome_breve, "Rilevato ingresso veicolo", "log_in"
                    )
            else:
                with zone.lock:
                    # Garantiamo che non svuoti il posto occupato dall'utente
                    occupied_by_others = zone.occupied_slots - (
                        1 if self.user_parked_zone == zone.name else 0
                    )

                if occupied_by_others > 0:
                    if zone.unpark():
                        self.log_msg(
                            "USCITA", nome_breve, "Rilevata uscita veicolo", "log_out"
                        )

    def start_background_workers(self):
        """Avvia un thread parallelo per ogni zona di parcheggio caricata."""
        for zone in self.zones:
            threading.Thread(
                target=self._zone_worker, args=(zone,), daemon=True
            ).start()

    def update_ui_loop(self):
        """Ciclo di refresh dell'interfaccia grafica gestito da Tkinter."""
        if self.running:
            self.update_widgets_once()

            ora_attuale = datetime.now().strftime("%H:%M:%S")
            self.clock_label.config(text=ora_attuale)

            fase_attuale, _ = self.get_time_phase()
            self.phase_label.config(text=f"[ {fase_attuale.upper()} ]")

            # Richiamiamo questa funzione ogni 500ms
            self.after(500, self.update_ui_loop)

    def update_widgets_once(self):
        """Ridisegna gli indicatori HUD sulla mappa e aggiorna i dati numerici nella Sidebar."""
        # Pulisce tutti gli elementi mobili vecchi per evitare sovrapposizioni
        self.canvas.delete("dynamic")

        for zone in self.zones:
            widgets = self.zone_widgets[zone.name]
            # Estraiamo i dati atomici con il lock per coerenza multithreading
            with zone.lock:
                occ, cap, wait, free, rate = (
                    zone.occupied_slots,
                    zone.capacity,
                    zone.waiting,
                    zone.free_slots,
                    zone.occupancy_rate,
                )

            # Calcolo colori dinamici basati sulla percentuale di riempimento
            if rate >= 100:
                status_txt, status_col, prog_style = (
                    "STATO: PIENO",
                    self.colors["accent_red"],
                    "Red.Horizontal.TProgressbar",
                )
            elif rate >= 60:
                status_txt, status_col, prog_style = (
                    "STATO: AFFOLLATO",
                    self.colors["accent_orange"],
                    "Orange.Horizontal.TProgressbar",
                )
            else:
                status_txt, status_col, prog_style = (
                    "STATO: DISPONIBILE",
                    self.colors["accent_green"],
                    "Green.Horizontal.TProgressbar",
                )

            widgets["lbl_status"].config(text=status_txt, fg=status_col)
            widgets["progress"].config(value=rate, style=prog_style)
            widgets["lbl_details"].config(
                text=f"Occupati: {occ}/{cap}  |  Liberi: {free}"
            )

            widgets["lbl_queue"].config(
                text=f"In Coda: {wait}" if wait > 0 else "Nessuna coda",
                fg=(
                    self.colors["accent_orange"]
                    if wait > 0
                    else self.colors["text_secondary"]
                ),
            )

            # Logica dei bottoni: se parcheggiato in una zona, blocca gli altri bottoni park
            is_user_here = self.user_parked_zone == zone.name
            if self.user_parked_zone is None:
                widgets["btn_park"].config(
                    state=tk.NORMAL, bg=self.colors["accent_green"], fg="#121212"
                )
                widgets["btn_unpark"].config(
                    state=tk.DISABLED, bg=self.colors["btn_disabled"]
                )
            else:
                widgets["btn_park"].config(
                    state=tk.DISABLED, bg=self.colors["btn_disabled"]
                )
                widgets["btn_unpark"].config(
                    state=tk.NORMAL if is_user_here else tk.DISABLED,
                    bg=(
                        self.colors["accent_red"]
                        if is_user_here
                        else self.colors["btn_disabled"]
                    ),
                )

            # --- DISEGNO BADGE HUD SULLA MAPPA ---
            x, y = self.map_coords.get(zone.name, (0, 0))
            nome_breve = zone.name.split("(")[0].strip().upper()

            # Se l'utente è parcheggiato qui, il badge diventa Ciano
            pin_color = self.colors["accent_cyan"] if is_user_here else status_col

            # Rettangolo principale con numero posti liberi
            self.canvas.create_rectangle(
                x - 35,
                y - 25,
                x + 35,
                y + 25,
                fill=self.colors["bg_app"],
                outline=pin_color,
                width=2,
                tags="dynamic",
            )
            self.canvas.create_text(
                x,
                y,
                text=f"{free}",
                font=("Consolas", 20, "bold"),
                fill=pin_color,
                tags="dynamic",
            )

            # Etichetta con nome della zona sotto il badge
            self.canvas.create_rectangle(
                x - 35,
                y + 25,
                x + 35,
                y + 45,
                fill=pin_color,
                outline=pin_color,
                tags="dynamic",
            )
            self.canvas.create_text(
                x,
                y + 35,
                text=nome_breve,
                font=("Segoe UI", 8, "bold"),
                fill=self.colors["bg_app"],
                tags="dynamic",
            )

            # Etichetta extra per evidenziare la posizione dell'utente
            if is_user_here:
                self.canvas.create_rectangle(
                    x - 45,
                    y - 50,
                    x + 45,
                    y - 30,
                    fill=self.colors["bg_app"],
                    outline=pin_color,
                    width=1,
                    tags="dynamic",
                )
                self.canvas.create_text(
                    x,
                    y - 40,
                    text="LA TUA AUTO",
                    font=("Segoe UI", 8, "bold"),
                    fill=pin_color,
                    tags="dynamic",
                )

    def on_close(self):
        """Gestisce lo spegnimento sicuro dei thread prima di chiudere la finestra."""
        if messagebox.askokcancel("Esci", "Vuoi chiudere UniPark Control Center?"):
            self.running = False
            self.destroy()
            # os._exit(0) uccide immediatamente tutti i thread orfani in background
            os._exit(0)  # pylint: disable=protected-access


if __name__ == "__main__":
    app = UniParkApp()
    app.mainloop()
