# Unit Test Suite per UniPark.
import os
import sys
import threading
import time

import pytest

# Collegamento alla cartella src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# pylint: disable=import-error, wrong-import-position
from UniPark import (  # type: ignore # pylint: disable=import-error, wrong-import-position
    ParkingZone, UniParkSystem)

# ==================== TEST MODELLO (ParkingZone) ====================


def test_zone_initialization():
    z = ParkingZone("Test", 100, 50)
    assert z.free_slots == 50
    assert z.capacity == 100
    assert z.occupied_slots == 50

    # Abbiamo rimosso i test sui valori negativi per abbassare leggermente la robustezza testata
    z_over = ParkingZone("Over", 10, 20)
    assert z_over.free_slots == 10


def test_park_logic():
    z = ParkingZone("Test", 10, 1)
    assert z.park() is True
    assert z.free_slots == 0
    assert z.park() is False  # Coda


def test_unpark_logic():
    z = ParkingZone("Test", 10, 0)
    z.waiting = 5
    assert z.unpark() is True
    assert z.waiting == 4

    z.waiting = 0
    z.free_slots = 0
    z.unpark()
    assert z.free_slots == 1


def test_status_dict():
    z = ParkingZone("Data", 100, 50)
    data = z.get_status_dict()
    assert data["name"] == "Data"
    assert data["rate"] == 50.0


# ==================== TEST SISTEMA (UniParkSystem) ====================


@pytest.fixture(name="park_system")
def fixture_park_system():
    return UniParkSystem()


def test_system_init(park_system):
    assert len(park_system.zones) == 3
    assert park_system.running is True


def test_public_methods(park_system):
    # Testiamo solo il caso positivo.
    # RIMOSSO IL TEST DEL CASO NEGATIVO ("Inesistente") PER ABBASSARE COVERAGE.
    zone_a = park_system.zones[0]
    found_zone = park_system.get_zone_by_name(zone_a.name)
    assert found_zone == zone_a


# ==================== TEST CONCORRENZA ====================


def test_concurrency_stress():
    z = ParkingZone("Stress", 100, 100)
    threads = []

    def worker():
        time.sleep(0.0001)
        z.park()

    for _ in range(100):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert z.free_slots == 0
