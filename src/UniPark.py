# Modulo UniPark: Gestione logica del sistema di parcheggio.
# Questo file contiene solo il Modello e il Controller, senza interfaccia grafica.

import random
from threading import Lock

# ==================== MODELLO DATI (MODEL) ====================


class ParkingZone:
    # Modello che gestisce i dati del singolo parcheggio in modo Thread-Safe

    # Rappresenta una zona di parcheggio
    # Implementa un meccanismo di locking per garantire l'accesso thread-safe agli attributi condivisi (free_slots, waiting)
    def __init__(self, name, capacity, free_slots):
        self.name = name
        self.capacity = capacity
        self.free_slots = max(0, min(free_slots, capacity))
        self.waiting = 0
        self.lock = Lock()

    @property  # Calcolo dinamico per garantire la coerenza dei dati senza ridondanza di stato
    def occupied_slots(self):
        # Calcola i posti occupati
        return self.capacity - self.free_slots

    @property
    def occupancy_rate(self):
        # Calcola la percentuale di occupazione
        return (self.occupied_slots / self.capacity) * 100

    def park(self):
        # Tenta di parcheggiare un'auto
        with self.lock:
            if self.free_slots > 0:
                self.free_slots -= 1
                return True
            self.waiting += 1
            return False

    def unpark(self):
        # Tenta di far uscire un'auto
        with self.lock:
            if self.waiting > 0:
                self.waiting -= 1
                return True
            if self.free_slots < self.capacity:
                self.free_slots += 1
                return True
            return False

    def get_status_dict(self):
        # Restituisce un dizionario con lo stato attuale
        # Necessario per i test unitari

        with self.lock:
            return {
                "name": self.name,
                "capacity": self.capacity,
                "free_slots": self.free_slots,
                "occupied": self.occupied_slots,
                "waiting": self.waiting,
                "rate": self.occupancy_rate,
            }


# ==================== SISTEMA CENTRALE (CONTROLLER) ====================


class UniParkSystem:
    # Controller del sistema e gestisce l'inizializzazione delle zone
    # Questa classe è fondamentale per i test e per inizializzare la GUI

    def __init__(self):
        self.zones = [
            ParkingZone("Zona A (Viale A. Doria)", 60, random.randint(20, 60)),
            ParkingZone("Zona B (DMI)", 45, random.randint(15, 45)),
            ParkingZone("Zona C (Via S. Sofia)", 80, random.randint(30, 80)),
        ]

        self.zone_map = {"a": self.zones[0], "b": self.zones[1], "c": self.zones[2]}

        self.running = True

    def get_total_capacity(self):
        # Restituisce la capacità totale di tutto il sistema
        return sum(z.capacity for z in self.zones)

    def get_zone_by_name(self, name):
        # Recupera una zona specifica tramite il suo nome identificativo
        for zone in self.zones:
            if zone.name == name:
                return zone
        return None
