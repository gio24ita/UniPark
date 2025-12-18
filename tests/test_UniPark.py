# Unit Test Suite per UniPark.
# Testa il Modello (Logic) e il Controller in isolamento.

import threading
import time

import pytest

from UniPark import ParkingZone, UniParkSystem

# ==================== TEST MODELLO (ParkingZone) ====================


def test_zone_initialization():
    """Verifica che la zona si inizializzi correttamente e corregga valori strani."""
    # Test valori normali
    z = ParkingZone("Test", 100, 50)
    assert z.free_slots == 50
    assert z.capacity == 100
    assert z.occupied_slots == 50

    # Test valori sballati (Clamping)
    z_over = ParkingZone("Over", 10, 20)  # 20 liberi su 10 posti?
    assert z_over.free_slots == 10  # Deve diventare 10

    z_under = ParkingZone("Under", 10, -5)  # -5 liberi?
    assert z_under.free_slots == 0  # Deve diventare 0


def test_park_logic():
    """Testa entrata auto e gestione code."""
    z = ParkingZone("Test", 10, 1)  # 1 posto libero

    # Primo parcheggio: successo
    assert z.park() is True
    assert z.free_slots == 0
    assert z.waiting == 0

    # Secondo parcheggio: pieno -> coda
    assert z.park() is False
    assert z.free_slots == 0
    assert z.waiting == 1


def test_unpark_logic():
    """Testa uscita auto e scorrimento coda."""
    z = ParkingZone("Test", 10, 0)
    z.waiting = 5  # 5 in coda

    # Esce uno -> entra quello dalla coda
    assert z.unpark() is True
    assert z.free_slots == 0  # Rimane 0 perché è entrato quello in attesa
    assert z.waiting == 4

    # Svuotiamo la coda per liberare un posto reale
    z.waiting = 0
    z.free_slots = 0
    z.unpark()
    assert z.free_slots == 1


def test_status_dict():
    """Verifica che i dati per la UI siano completi."""
    z = ParkingZone("Data", 100, 50)
    data = z.get_status_dict()
    assert "rate" in data
    assert data["rate"] == 50.0
    assert data["name"] == "Data"


# ==================== TEST SISTEMA (UniParkSystem) ====================


@pytest.fixture
def park_system():
    """Fixture che crea un'istanza pulita del sistema."""
    return UniParkSystem()


def test_system_init(park_system):
    """Verifica inizializzazione del controller."""
    assert len(park_system.zones) == 3
    assert "a" in park_system.zone_map
    assert park_system.running is True


def test_concurrency_stress():
    """
    Test di stress multithread per verificare il Lock.
    100 thread provano a parcheggiare contemporaneamente su 100 posti.
    """
    z = ParkingZone("Stress", 100, 100)  # 100 posti liberi
    threads = []

    def worker():
        time.sleep(0.0001)  # Micro-sleep per favorire race conditions
        z.park()

    for _ in range(100):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Alla fine, i posti liberi devono essere ESATTAMENTE 0
    # Senza Lock, questo test fallirebbe spesso.
    assert z.free_slots == 0
    assert z.occupied_slots == 100
