import sys
from unittest.mock import MagicMock, patch

import pytest

# Importiamo la classe corretta
from UniparkGUI import UniParkApp


@pytest.fixture
def mock_app():
    """Crea la GUI 'finta' per i test, compatibile con GitHub Actions (No Display)."""

    # MOCK MASSIVO: Sostituiamo interamente i moduli tkinter
    # Invece di patchare pezzo per pezzo, patchiamo l'intero namespace grafico
    with patch("UniparkGUI.tk") as mock_tk, patch("UniparkGUI.ttk") as mock_ttk, patch(
        "UniparkGUI.scrolledtext"
    ) as mock_st:

        # Configuriamo il Mock di Tk (la finestra principale)
        mock_root = mock_tk.Tk.return_value

        # MOCK DEL SISTEMA BACKEND
        with patch("UniparkGUI.UniParkSystem") as MockSystemClass:

            # Configurazione Backend Finto
            mock_system = MockSystemClass.return_value

            mock_zone = MagicMock()
            mock_zone.name = "TestZone"
            mock_zone.capacity = 100
            mock_zone.occupied_slots = 50
            mock_zone.waiting = 0
            mock_zone.occupancy_rate = 50.0
            mock_zone.free_slots = 50

            # Setup dei valori di ritorno
            mock_zone.get_status_dict.return_value = {
                "name": "TestZone",
                "capacity": 100,
                "occupied": 50,
                "waiting": 0,
                "rate": 50.0,
                "free_slots": 50,
            }
            mock_zone.park.return_value = True
            mock_zone.unpark.return_value = True

            mock_system.zones = [mock_zone]

            # --- AVVIO DELL'APP ---
            # Poiché abbiamo mockato 'UniparkGUI.tk', quando l'app chiama tk.Tk(),
            # riceve il nostro mock_root e NON cerca di aprire finestre reali.
            app = UniParkApp()

            # Impostiamo manualmente le variabili vitali
            app.running = False

            # Riempire manualmente i widget perché i mock non creano vera logica UI
            app.zone_widgets = {
                "TestZone": {
                    "progress": MagicMock(),
                    "lbl_status": MagicMock(),
                    "lbl_details": MagicMock(),
                    "lbl_queue": MagicMock(),
                }
            }

            return app, mock_zone


def test_gui_initialization(mock_app):
    """Testa che l'app si avvii senza errori."""
    app, _ = mock_app
    assert app is not None
    assert "TestZone" in app.zone_widgets


def test_gui_manual_park(mock_app):
    """Testa il click sul bottone PARK."""
    app, mock_zone = mock_app
    app.manual_action(mock_zone, "park")
    mock_zone.park.assert_called()


def test_gui_manual_unpark(mock_app):
    """Testa il click sul bottone UNPARK."""
    app, mock_zone = mock_app
    app.manual_action(mock_zone, "unpark")
    mock_zone.unpark.assert_called()


def test_gui_update_widgets(mock_app):
    """Testa l'aggiornamento grafico."""
    app, mock_zone = mock_app

    # Cambiamo i dati simulati
    new_stats = {
        "name": "TestZone",
        "capacity": 100,
        "occupied": 90,
        "waiting": 5,
        "rate": 90.0,
        "free_slots": 10,
    }
    mock_zone.get_status_dict.return_value = new_stats
    mock_zone.occupied_slots = 90
    mock_zone.occupancy_rate = 90.0

    # Eseguiamo l'aggiornamento
    app.update_widgets_once()

    # Verifichiamo che abbia provato ad aggiornare la progress bar
    app.zone_widgets["TestZone"]["progress"].__setitem__.assert_any_call("value", 90.0)
