import random
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

# IMPORTIAMO LA LOGICA DAL MODELLO
from UniPark import UniParkSystem


class UniParkApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- Configurazione Finestra ---
        self.title("UniPark Dashboard - Control Center")
        self.geometry("950x700")
        self.configure(bg="#f0f2f5")  # Sfondo (Light Grey)
        self.resizable(True, True)

        # Gestione chiusura
        self.running = True
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # --- Setup Stili ---
        self.setup_styles()

        # --- Costruzione Layout ---
        self.create_header()
        self.create_dashboard_area()
        self.create_log_area()

        # --- Avvio Thread ---
        self.start_background_workers()

        # --- Avvio Loop UI ---
        self.update_ui_loop()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Colori
        self.colors = {
            "primary": "#2c3e50",  # Blu scuro
            "success": "#27ae60",  # Verde
            "warning": "#f39c12",  # Arancione
            "danger": "#c0392b",  # Rosso
            "bg": "#f0f2f5",  # Grigio sfondo
            "card": "#ffffff",  # Bianco schede
        }

        # Stile Card
        style.configure(
            "Card.TFrame",
            background=self.colors["card"],
            relief="raised",
            borderwidth=1,
        )

        # Stile Progress Bars colorate
        style.configure(
            "Green.Horizontal.TProgressbar",
            background=self.colors["success"],
            troughcolor="#ecf0f1",
        )
        style.configure(
            "Orange.Horizontal.TProgressbar",
            background=self.colors["warning"],
            troughcolor="#ecf0f1",
        )
        style.configure(
            "Red.Horizontal.TProgressbar",
            background=self.colors["danger"],
            troughcolor="#ecf0f1",
        )

    def create_header(self):
        # Header superiore
        header_frame = tk.Frame(self, bg=self.colors["primary"], height=70)
        header_frame.pack(fill="x", side="top")

        title = tk.Label(
            header_frame,
            text="🅿️ UNIPARK CONTROL CENTER",
            font=("Segoe UI", 20, "bold"),
            bg=self.colors["primary"],
            fg="white",
        )
        title.pack(pady=15)

    def create_dashboard_area(self):
        # Crea le schede per ogni zona
        container = tk.Frame(self, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        self.zone_widgets = {}

        for i, zone in enumerate(self.zones):
            # Card Frame
            card = tk.LabelFrame(
                container,
                text=f" {zone.name} ",
                font=("Arial", 12, "bold"),
                bg="white",
                fg="#34495e",
                bd=1,
                relief="solid",
                padx=15,
                pady=15,
            )
            card.pack(side=tk.LEFT, fill="both", expand=True, padx=10)

            # Info Stato
            lbl_status = tk.Label(
                card,
                text="Inizializzazione...",
                font=("Arial", 11, "bold"),
                bg="white",
                anchor="w",
            )
            lbl_status.pack(fill="x", pady=(5, 5))

            # Progress Bar
            progress = ttk.Progressbar(
                card, orient="horizontal", length=100, mode="determinate"
            )
            progress.pack(fill="x", pady=10)

            # Dettagli numerici
            lbl_details = tk.Label(
                card, text="--/--", font=("Consolas", 10), bg="white", fg="#7f8c8d"
            )
            lbl_details.pack(anchor="e")

            # Coda (Evidenziata)
            lbl_queue = tk.Label(
                card,
                text="Coda: 0",
                font=("Arial", 11, "bold"),
                bg="white",
                fg="#e67e22",
            )
            lbl_queue.pack(anchor="e", pady=5)

            # Pulsanti di Azione
            btn_frame = tk.Frame(card, bg="white")
            btn_frame.pack(side="bottom", fill="x", pady=10)

            btn_park = tk.Button(
                btn_frame,
                text="PARK (+1)",
                bg=self.colors["success"],
                fg="white",
                font=("Arial", 9, "bold"),
                relief="flat",
                cursor="hand2",
                command=lambda z=zone: self.manual_action(z, "park"),
            )
            btn_park.pack(side=tk.LEFT, fill="x", expand=True, padx=2)

            btn_unpark = tk.Button(
                btn_frame,
                text="UNPARK (-1)",
                bg=self.colors["danger"],
                fg="white",
                font=("Arial", 9, "bold"),
                relief="flat",
                cursor="hand2",
                command=lambda z=zone: self.manual_action(z, "unpark"),
            )
            btn_unpark.pack(side=tk.LEFT, fill="x", expand=True, padx=2)

            # Salvataggio riferimenti
            self.zone_widgets[zone.name] = {
                "progress": progress,
                "lbl_status": lbl_status,
                "lbl_details": lbl_details,
                "lbl_queue": lbl_queue,
            }

    def create_log_area(self):
        # Area di log scorrevole
        log_frame = tk.LabelFrame(
            self,
            text="System Logs",
            bg=self.colors["bg"],
            font=("Segoe UI", 10, "bold"),
        )
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.log_area = scrolledtext.ScrolledText(
            log_frame, height=8, state="disabled", font=("Consolas", 9)
        )
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)

        # Tag colori
        self.log_area.tag_config("INFO", foreground="black")
        self.log_area.tag_config("SUCCESS", foreground=self.colors["success"])
        self.log_area.tag_config("WARNING", foreground=self.colors["warning"])
        self.log_area.tag_config("ERROR", foreground=self.colors["danger"])

    def log_msg(self, msg, level="INFO"):
        # Scrive nel log in modo thread-safe
        def _write():
            self.log_area.config(state="normal")
            timestamp = time.strftime("%H:%M:%S")
            self.log_area.insert(tk.END, f"[{timestamp}] {msg}\n", level)
            self.log_area.see(tk.END)
            self.log_area.config(state="disabled")

        self.after(0, _write)

    # ==================== LOGICA & WORKERS ====================

    def _zone_worker(self, zone):
        # Simulazione traffico in background
        while self.running:
            time.sleep(random.uniform(2.0, 5.0))
            if not self.running:
                break

            # Genera eventi casuali (park/unpark)
            evento = random.randint(0, 100)
            if evento < 40:
                if zone.park():
                    self.log_msg(f"AUTO-PARK: Auto entrata in {zone.name}", "INFO")
                else:
                    self.log_msg(f"AUTO-PARK: {zone.name} PIENA -> Coda", "WARNING")
            elif 40 <= evento < 80:
                if zone.unpark():
                    self.log_msg(f"AUTO-UNPARK: Auto uscita da {zone.name}", "INFO")

    def manual_action(self, zone, action):
        # Gestione pulsanti manuali
        if action == "park":
            if zone.park():
                self.log_msg(f"MANUALE: Park in {zone.name}", "SUCCESS")
            else:
                self.log_msg(f"MANUALE: Coda in {zone.name}", "WARNING")
        elif action == "unpark":
            if zone.unpark():
                self.log_msg(f"MANUALE: Unpark da {zone.name}", "SUCCESS")
            else:
                self.log_msg(f"MANUALE: Errore {zone.name} vuota", "ERROR")

        # Aggiornamento immediato (senza aspettare il loop)
        self.update_widgets_once()

    def start_background_workers(self):
        for zone in self.zones:
            t = threading.Thread(target=self._zone_worker, args=(zone,), daemon=True)
            t.start()

    def update_ui_loop(self):
        # Polling loop per aggiornare la grafica
        if self.running:
            self.update_widgets_once()
            self.after(200, self.update_ui_loop)

    def update_widgets_once(self):
        # Logica di aggiornamento singolo widget
        for zone in self.zones:
            widgets = self.zone_widgets[zone.name]

            with zone.lock:
                occ = zone.occupied_slots
                cap = zone.capacity
                wait = zone.waiting
                rate = zone.occupancy_rate
                free = zone.free_slots

            # Progress Bar
            widgets["progress"]["value"] = rate
            widgets["progress"]["maximum"] = 100

            if rate > 90:
                widgets["progress"].configure(style="Red.Horizontal.TProgressbar")
                status_txt = "● PIENO"  # Pallino rosso simulato
                fg_col = self.colors["danger"]
            elif rate > 70:
                widgets["progress"].configure(style="Orange.Horizontal.TProgressbar")
                status_txt = "● AFFOLLATO"  # Pallino arancione simulato
                fg_col = "#e67e22"
            else:
                widgets["progress"].configure(style="Green.Horizontal.TProgressbar")
                status_txt = "● DISPONIBILE"  # Pallino verde simulato
                fg_col = self.colors["success"]

            # Label
            widgets["lbl_status"].config(text=status_txt, fg=fg_col)
            widgets["lbl_details"].config(text=f"{occ}/{cap} Occ. | {free} Lib.")

            if wait > 0:
                widgets["lbl_queue"].config(
                    text=f"⚠ Coda: {wait}", fg=self.colors["danger"]
                )
            else:
                widgets["lbl_queue"].config(text="Nessuna Coda", fg="#bdc3c7")

    def on_close(self):
        if messagebox.askokcancel("Esci", "Vuoi davvero chiudere UniPark?"):
            self.running = False
            self.destroy()


if __name__ == "__main__":
    app = UniParkApp()
    app.mainloop()
