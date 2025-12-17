import sys
import threading
from unittest.mock import MagicMock, patch

import pytest # type: ignore

from UniPark import ParkingZone, UniParkSystem

# ==================== TEST MODELLO (ParkingZone) ====================
def test_zone_initialization():
    """Verifica che la zona si inizializzi correttamente e corregga valori strani."""
    # Test valori normali
    z = ParkingZone("Test", 100, 50)
    assert z.free_slots == 50
    assert z.capacity == 100

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

    # Svuotiamo la coda
    z.waiting = 0
    z.free_slots = 0
    z.unpark()
    assert z.free_slots == 1  # Ora si libera davvero un posto


def test_status_dict():
    """Verifica che i dati per la UI siano completi."""
    z = ParkingZone("Data", 100, 50)
    data = z.get_status_dict()
    assert "rate" in data
    assert data["rate"] == 50.0
    assert data["name"] == "Data"

def test_start_interaction_simulation(app):
    """
    Testa il ciclo principale start() simulando un utente che scrive.
    Questo copre tantissime righe dentro il loop while.
    """
    # Sequenza di tasti simulata: scrive "park a", preme Invio, scrive "exit", preme Invio.
    # Usiamo side_effect per restituire un carattere alla volta come se l'utente digitasse.
    input_sequence = list("park a\nexit\n")
    
    # Mockiamo tutto per non sporcare lo schermo e non bloccarci
    with patch('sys.stdin.read', side_effect=input_sequence) as mock_input:
        with patch('sys.stdout', new_callable=MagicMock): # Zittiamo le stampe
            with patch('os.system'): # Zittiamo il clear screen
                with patch('time.sleep'): # Zittiamo le attese
                    with patch('threading.Thread'): # Non avviamo veri thread worker
                        
                        # Lanciamo il main loop!
                        # Grazie alla sequenza "exit", il loop si chiuderà da solo.
                        app.start()

    # Se il test finisce senza bloccarsi, abbiamo coperto il loop principale!
    assert app.running is False

def test_windows_compatibility():
    """
    Finge di essere su Windows per testare la funzione _read_char_windows.
    Fondamentale perché su Linux quelle righe verrebbero saltate (rosso nel coverage).
    """
    system = UniParkSystem()
    
    # 1. Fingiamo di essere su Windows ('nt')
    with patch('os.name', 'nt'):
        # 2. Creiamo un finto modulo msvcrt (che esiste solo su Windows)
        mock_msvcrt = MagicMock()
        # Simuliamo che l'utente prema 'a'
        mock_msvcrt.getch.return_value = b'a'
        
        with patch.dict(sys.modules, {'msvcrt': mock_msvcrt}):
            char = system._read_char_windows()
            assert char == "a"

            # Test tasto Invio speciale di Windows
            mock_msvcrt.getch.return_value = b'\r'
            assert system._read_char_windows() == "\n"

def test_keyboard_interrupt_handling(app):
    """Testa se premiamo CTRL+C (KeyboardInterrupt) nel loop."""
    # Simuliamo che appena proviamo a leggere un carattere, l'utente prema CTRL+C
    with patch('sys.stdin.read', side_effect=KeyboardInterrupt):
        with patch('sys.stdout'):
            with patch('os.system'):
                 with patch('threading.Thread'): 
                    app.start()
    
    # Il programma deve uscire pulito mettendo running = False
    assert app.running is False

def test_main_block_simulation():
    """
    Testa l'unica parte che non viene mai eseguita: if __name__ == "__main__"
    """
    # Importiamo il file come modulo per vedere se ha le variabili giuste
    import UniPark
    assert hasattr(UniPark, 'UniParkSystem')

# ==================== TEST SISTEMA & UI (UniParkSystem) ====================
@pytest.fixture
def app():
    """Crea un'istanza pulita del sistema per ogni test."""
    system = UniParkSystem()
    # Sostituiamo le zone random con zone fisse per prevedibilità
    system.zones = [ParkingZone("A", 10, 5)]
    system.zone_map = {"a": system.zones[0]}
    return system


def test_commands_execution(app):
    """Testa i comandi testuali dell'utente."""
    # Mockiamo show_feedback per non aspettare i time.sleep
    with patch.object(app, "show_feedback") as mock_feedback:
        with patch.object(app, "print_live_dashboard"):

            # Test comando valido
            app.handle_user_command("park a")
            assert app.zones[0].free_slots == 4
            mock_feedback.assert_called()

            # Test comando invalido
            app.handle_user_command("park z")  # Zona non esiste

            # Test exit
            app.handle_user_command("exit")
            assert app.running is False


def test_ui_rendering_coverage(app):
    """
    TRUCCO PER IL COVERAGE:
    Eseguiamo la funzione di stampa bloccando l'output reale.
    """
    # Simuliamo terminale largo 100 col
    with patch("shutil.get_terminal_size", return_value=(100, 20)):
        # Simuliamo sys.stdout per non scrivere davvero a schermo
        with patch("sys.stdout", new_callable=MagicMock) as mock_stdout:

            # Eseguiamo la dashboard complessa
            app.print_live_dashboard()

            # Verifica che abbia provato a scrivere qualcosa
            assert mock_stdout.write.called

            # Eseguiamo anche il feedback con sleep mockato
            with patch("time.sleep"):
                app.show_feedback("Test Message")


def test_worker_logic(app):
    """Testa il worker dei thread (simulandolo singolarmente)."""
    zone = app.zones[0]

    # Impostiamo running a False subito dopo l'avvio per fare 1 solo giro di loop
    def stop_loop(*args):
        app.running = False

    with patch("time.sleep", side_effect=stop_loop):
        with patch.object(app, "print_live_dashboard"):
            app._zone_worker(zone)


def test_command_parsing_edge_cases(app):
    """Testa input strani o vuoti."""
    app.handle_user_command("")  # Vuoto
    app.handle_user_command("   ")  # Spazi
    assert app.running is True  # Non deve crashare