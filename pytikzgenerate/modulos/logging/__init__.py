"""Modulo encargado de generar informacion de diagnostico en consola.

Clase:
- GenerarDiagnosito"""

#Otras librerias
import logging, os
class GenerarDiagnostico(object):
    """Genera informacion de diagnostico para ser mostrado en la consola. Se almacenara el diagnostico en el archivo app.log, en la ruta raiz del proyecto."""
    logging.basicConfig(
        filename=os.path.join("./","app.log"),
        encoding='utf-8',
        level='DEBUG'
    )

    __instance = None

    def __new__(cls, *args):
        """Utilizamos el patron de diseño Singleton, almacena la primera instanciazacion en la propiedad "__instance".

        Parametro:
        - cls (object), clase a instanciar.
        - args (List[any]), argumentos de la clase.
        
        Retorna:
        - La clase instanciada (object).
        """
        if GenerarDiagnostico.__instance is None:
            GenerarDiagnostico.__instance = object.__new__(cls)
        return GenerarDiagnostico.__instance
    
    def __init__(self,nombre_clase:str,mensaje:str,tipo_de_diagnostico:str):
        """Registra un mensaje de diagnostico.
        
        Parametros:
        - mensaje (str), mensaje del diagnostico.
        - tipo_de_diagnostico (str), el valor debe de ser entre ['info','debug','warning','error','critical']. """
        tipos_de_diagnosticos = ['info','debug','warning','error','critical']
        if tipo_de_diagnostico in tipos_de_diagnosticos:
            while(len(nombre_clase)<12):
                nombre_clase+=" "
            mensaje = "[%s] %s"%(nombre_clase,mensaje)
            if tipo_de_diagnostico == "info":
                self.info(mensaje)
            elif tipo_de_diagnostico == "debug":
                self.debug(mensaje)
            elif tipo_de_diagnostico == "warning":
                self.warning(mensaje)
            elif tipo_de_diagnostico == "error":
                self.error(mensaje)
            else:
                self.critical(mensaje)
        else:
            self.warning("El tipo de diagnostico no es el correcto.")

    def critical(self, mensaje:str)->None:
        """Registra un mensaje de diagnostico de tipo "critical".
        
        Parametro:
        - mensaje (str), mensaje del diagnostico."""
        logging.critical(mensaje)
    
    def error(self, mensaje:str) -> None:
        """Registra un mensaje de diagnostico de tipo "error".
        
        Parametro:
        - mensaje (str), mensaje del diagnostico."""
        logging.error(mensaje)
    
    def warning(self, mensaje:str) -> None:
        """Registra un mensaje de diagnostico de tipo "warning".
        
        Parametro:
        - mensaje (str), mensaje del diagnostico."""
        logging.warning(mensaje)
    
    def info(self, mensaje:str) -> None:
        """Registra un mensaje de diagnostico de tipo "info".
        
        Parametro:
        - mensaje (str), mensaje del diagnostico."""
        logging.info(mensaje)
    
    def debug(self, mensaje:str) -> None:
        """Registra un mensaje de diagnostico de tipo "debug".
        
        Parametro:
        - mensaje (str), mensaje del diagnostico."""
        logging.debug(mensaje)