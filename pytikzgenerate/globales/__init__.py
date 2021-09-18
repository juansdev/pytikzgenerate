"""Variables globales de la clase PyTikZ"""
def init():
    global ruta_raiz
    global ruta_imagen
    global carpetas_necesarias
    ruta_raiz = ""
    ruta_imagen = ""
    #"imagen" -> Todas las carpetas en "imagen", son las que se encuentra en "C:\Users\juanf\Pictures" (Window) o "sdcard/dcim" (Android).
    carpetas_necesarias = {
        "imagen":["Pytikz"]
    }