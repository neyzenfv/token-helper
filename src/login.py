import threading
from tkinter import messagebox
import time

def start_web_login(token: str, app, target_btn=None):
    if not target_btn:
        target_btn = getattr(app, 'login_btn', None)
    threading.Thread(target=_run, args=(token, app, target_btn), daemon=True).start()

def _run(token: str, app, btn):
    driver = None
    try:
        from selenium import webdriver

        options = webdriver.ChromeOptions()
        options.add_argument('--log-level=3')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=options)

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": f'window.localStorage.setItem("token", "\\"{token}\\"")'
        })

        driver.get("https://discord.com/app")

        while True:
            try:
                _ = driver.window_handles
                time.sleep(1)
            except Exception:
                break

    except Exception as e:
        msg = str(e)
        if msg and "target window already closed" not in msg.lower():
            app.after(0, lambda m=msg: messagebox.showerror("Erreur", f"Erreur Chrome :\n{m}"))
    finally:
        if btn:
            orig = btn.cget("text")
            final = "🚀  Connect" if ("Connect" in orig or "Ouverture" in orig) else "Se connecter"
            app.after(0, lambda: btn.configure(state="normal", text=final))
