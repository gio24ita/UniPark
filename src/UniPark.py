# Modulo UniPark: Gestione logica del sistema di parcheggio.
# Questo file contiene solo il Modello e il Controller, senza interfaccia grafica.

import random
from threading import Lock

# ==================== MODELLO DATI (MODEL) ====================

class ParkingZone:
    """Classe che modella lo stato di un singolo parcheggio fisico.
    Utilizza un oggetto Lock() per prevenire la 'race condition': evita che 
    due thread (quello della simulazione e quello utente) modifichino 
    i posti disponibili nello stesso millisecondo causando errori.
    """

    def __init__(self, name, capacity, free_slots):
        self.name = name
        self.capacity = capacity
        # Garantiamo che i posti liberi non siano mai negativi o superiori alla capienza totale
        self.free_slots = max(0, min(free_slots, capacity))
        self.waiting = 0
        self.lock = Lock()

    @property 
    def occupied_slots(self):
        """Calculo dinamico dei posti occupati deducendoli da quelli liberi."""
        return self.capacity - self.free_slots

    @property 
    def occupancy_rate(self):
        """Restituisce la percentuale di riempimento attuale."""
        return (self.occupied_slots / self.capacity) * 100

    def park(self):
        """Logica di ingresso: sottrae uno slot se libero, altrimenti mette in coda."""
        with self.lock:
            if self.free_slots > 0:
                self.free_slots -= 1
                return True
            self.waiting += 1
            return False

    def unpark(self):
        """Logica di uscita: se c'è coda entra il primo in attesa, altrimenti libera un posto."""
        with self.lock:
            if self.waiting > 0:
                self.waiting -= 1
                return True
            if self.free_slots < self.capacity:
                self.free_slots += 1
                return True
            return False

    def get_status_dict(self):
        """Espone lo stato della zona in un formato dizionario per facilitare i test automatici."""
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
    """Orchestratore principale che gestisce l'insieme dei parcheggi dell'Università."""

    def __init__(self):
        # Inizializziamo le tre zone previste dal progetto
        self.zones = [
            ParkingZone("Zona A (Viale A. Doria)", 60, random.randint(20, 60)),
            ParkingZone("Zona B (DMI)", 45, random.randint(15, 45)),
            ParkingZone("Zona C (Via S. Sofia)", 80, random.randint(30, 80)),
        ]

        # Creiamo una mappa rapida (ID -> Oggetto) per accesso veloce
        self.zone_map = {"a": self.zones[0], "b": self.zones[1], "c": self.zones[2]}
        self.running = True

    def get_total_capacity(self):
        """Calcola la capienza totale di tutte le zone sommate."""
        return sum(z.capacity for z in self.zones)

    def get_zone_by_name(self, name):
        """Cerca una zona specifica scorrendo la lista."""
        for zone in self.zones:
            if zone.name == name:
                return zone
        return None