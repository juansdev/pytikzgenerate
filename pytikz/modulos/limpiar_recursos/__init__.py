"""Modulo encargado de realizar la limpieza de los recursos temporales del aplicativo.

Funcion: 
- limpiar_recursos"""

import os
#Librerias propias
import globales

#Limpiar contenido de la carpeta source
def limpiar_recursos()->None:
    """Limpia los recursos de la carpeta y subcarpetas ubicadas en la ruta "modulos/pytikz/recursos/"."""
    carpeta_padre = os.path.join(globales.ruta_raiz,"modulos/pytikz/recursos/")
    carpetas_a_eliminar = ["crear_imagen/grafica_original","relleno","relleno_lineas_libre","crear_imagen/grafica_recortada"]
    rutas_de_carpeta = []
    for carpeta in carpetas_a_eliminar:
        rutas_de_carpeta.append(carpeta_padre+carpeta)
    for ruta_de_carpeta in rutas_de_carpeta:
        for archivo in os.listdir(ruta_de_carpeta):
            os.remove(os.path.join(ruta_de_carpeta, archivo))