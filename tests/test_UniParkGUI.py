# pylint: disable=redefined-outer-name
from unittest.mock import MagicMock, patch
import pytest

# Importiamo la classe GUI
from UniparkGUI import UniParkApp


@pytest.fixture
def mock_app():
    """
    Creates a 'fake' GUI for testing.
    Compatible with GitHub Actions (Headless) and resolves RecursionError.
    """

    # 1. TOTAL BLOCK OF TKINTER (HEADLESS MODE)
    # The lambda prevents Python from looking for a monitor
    with patch("tkinter.Tk.__init__", lambda self, *args, **kwargs: None):

        # 2. MOCK GRAPHICAL WIDGETS AND MODULES
        # Qui abbiamo aggiunto maxsize, minsize, Canvas e PhotoImage!
        with patch("tkinter.Tk.geometry"), patch("tkinter.Tk.title"), patch(
            "tkinter.Tk.configure"
        ), patch("tkinter.Tk.resizable"), patch(
            "tkinter.Tk.maxsize"          
        ), patch(
            "tkinter.Tk.minsize"          
        ), patch("tkinter.Tk.protocol"), patch(
            "tkinter.Tk.destroy"
        ), patch(
            "tkinter.Tk.mainloop"
        ), patch(
            "tkinter.ttk.Style"
        ), patch(
            "tkinter.Label"
        ), patch(
            "tkinter.Button"
        ), patch(
            "tkinter.Frame"
        ), patch(
            "tkinter.LabelFrame"
        ), patch(
            "tkinter.ttk.Progressbar"
        ), patch(
            "tkinter.scrolledtext.ScrolledText"
        ), patch(
            "tkinter.Canvas"
        ), patch(
            "tkinter.PhotoImage"
        ), patch(
            "UniparkGUI.UniParkApp.after"
        ) as mock_after:

            # 3. MOCK BACKEND SYSTEM
            # NOTA: Ora questo è indentato correttamente a destra!
            with patch("UniparkGUI.UniParkSystem") as MockSystemClass:

                # Configure Backend
                mock_system = MockSystemClass.return_value

                mock_zone = MagicMock()
                mock_zone.name = "TestZone"
                mock_zone.capacity = 100
                mock_zone.occupied_slots = 50
                mock_zone.waiting = 0
                mock_zone.occupancy_rate = 50.0
                mock_zone.free_slots = 50

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

                # --- START APP ---
                app = UniParkApp()

                # Manually restore the mocked 'after' to the instance
                app.after = mock_after

                # Set vital variables
                app.running = False
                app.system = mock_system
                app.zones = mock_system.zones
                app.canvas = MagicMock() # Mock the canvas to avoid draw errors

                # Manually populate fake widgets
                app.zone_widgets = {
                    "TestZone": {
                        "progress": MagicMock(),
                        "lbl_status": MagicMock(),
                        "lbl_details": MagicMock(),
                        "lbl_queue": MagicMock(),
                        "btn_park": MagicMock(),
                        "btn_unpark": MagicMock()
                    }
                }

                app.root = app

                return app, mock_zone


def test_gui_initialization(mock_app):
    """Test that the app starts."""
    app, _ = mock_app
    assert app is not None
    assert "TestZone" in app.zone_widgets


def test_gui_user_park(mock_app):
    """Test clicking the PARK button."""
    app, mock_zone = mock_app
    
    # NOTA: Ora si chiama user_action (non più manual_action)
    app.user_action(mock_zone, "park")

    # Checks
    mock_zone.park.assert_called()
    app.after.assert_called()


def test_gui_user_unpark(mock_app):
    """Test clicking the UNPARK button."""
    app, mock_zone = mock_app
    
    # NOTA: Ora si chiama user_action
    app.user_action(mock_zone, "unpark")

    mock_zone.unpark.assert_called()
    app.after.assert_called()


def test_gui_update_widgets(mock_app):
    """Test graphical update."""
    app, mock_zone = mock_app

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

    app.update_widgets_once()

    # Verifica che la UI sia stata chiamata per aggiornarsi
    app.zone_widgets["TestZone"]["progress"].config.assert_called()