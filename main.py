import tkinter as tk
from gui import AplicacionBiblioteca

if __name__ == "__main__":
    root = tk.Tk()
    # Arrancamos la clase que controla toda la interfaz
    app = AplicacionBiblioteca(root)
    # Iniciamos el bucle de eventos para mantener la ventana abierta
    root.mainloop()