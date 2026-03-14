import sys
import os
import threading
import customtkinter as ctk

sys.path.insert(0, os.path.dirname(__file__))

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

def main():
    from ui.loading import LoadingScreen
    from ui.main_window import MainWindow
    from scanner import scan_all

    app = MainWindow()
    app.withdraw()

    scan_results = []

    def on_progress(text, pct):
        try:
            loader.update_progress(text, pct)
        except Exception:
            pass

    def do_scan():
        results = scan_all(progress_callback=on_progress)
        scan_results.extend(results)
        try:
            loader.finish_scan()
        except Exception:
            pass

    def on_loading_done():
        app.load_tokens(scan_results)
        app.deiconify()
        app.start_fade_in()

    loader = LoadingScreen(on_done_callback=on_loading_done)

    t = threading.Thread(target=do_scan, daemon=True)
    t.start()

    app.mainloop()

if __name__ == "__main__":
    main()
