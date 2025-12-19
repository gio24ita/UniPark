import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk

# IMPORTIAMO LA CLASSE CORRETTA DAL FILE CORRETTO
from UniparkGUI import UniParkApp

@pytest.fixture
def mock_app():
    """Crea la GUI 'finta' per i test."""
    # Blocchiamo tutte le chiamate grafiche
    with patch('tkinter.Tk'), \
         patch('tkinter.Label'), \
         patch('tkinter.Button'), \
         patch('tkinter.Frame'), \
         patch('tkinter.LabelFrame'), \
         patch('tkinter.ttk.Progressbar'), \
         patch('tkinter.scrolledtext.ScrolledText'):
        
        # Blocco l'importazione del sistema reale e ne metto uno finto
        with patch('UniparkGUI.UniParkSystem') as MockSystemClass:
            
            # Configuro il sistema finto
            mock_system = MockSystemClass.return_value
            
            # Configuro una zona finta
            mock_zone = MagicMock()
            mock_zone.name = "TestZone"
            mock_zone.capacity = 100
            mock_zone.occupied_slots = 50
            mock_zone.waiting = 0
            mock_zone.occupancy_rate = 50.0
            mock_zone.free_slots = 50
            # Importante: il codice usa 'with zone.lock:', MagicMock lo gestisce da solo
            
            mock_system.zones = [mock_zone]
            
            # Avvio l'app
            app = UniParkApp()
            app.running = False # Fermo il loop infinito
            
            return app, mock_zone

def test_gui_initialization(mock_app):
    app, _ = mock_app
    # Verifica che l'app sia stata creata
    assert app is not None
    # Verifica che il widget per la zona di test sia stato creato
    assert "TestZone" in app.zone_widgets

def test_gui_manual_park(mock_app):
    app, mock_zone = mock_app
    
    # Simulo successo
    mock_zone.park.return_value = True
    app.manual_action(mock_zone, "park")
    mock_zone.park.assert_called()

def test_gui_manual_unpark(mock_app):
    app, mock_zone = mock_app
    
    # Simulo successo
    mock_zone.unpark.return_value = True
    app.manual_action(mock_zone, "unpark")
    mock_zone.unpark.assert_called()

def test_gui_update_widgets(mock_app):
    app, mock_zone = mock_app
    
    # Cambio i valori della zona finta
    mock_zone.occupied_slots = 80
    mock_zone.capacity = 100
    mock_zone.occupancy_rate = 80.0
    mock_zone.free_slots = 20
    
    # Chiamo l'aggiornamento grafico manuale
    app.update_widgets_once()
    
    # Verifico (indirettamente) che non ci siano errori
    w = app.zone_widgets["TestZone"]
    # Se il codice è arrivato qui senza errori, i widget sono stati aggiornati
    assert w is not None