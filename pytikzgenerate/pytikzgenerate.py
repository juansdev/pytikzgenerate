#Otros
import pathlib, os
#Kivy
from kivy.utils import platform
#Globales
import globales
#Librerias propias
from modulos import IndentadorTikz
from modulos import DepuradorTikz
from modulos import Transpilador
from modulos import ValidadorPytikz
from modulos.kivy.otros_widgets.aviso_informativo import AvisoInformativo
from modulos.logging import GenerarDiagnostico

class PytikzGenerate():
    """Clase PytikzGenerate, genera graficos a partir del codigo TikZ utilizando el motor grafico de Kivy, y lo dibuja en un Widget de Kivy, antes de graficar se realizan las siguientes validaciones:
    
    1. Verifica la indentacion del codigo TikZ, debe de contar con minimo 0 espacios de indentacion hasta un maximo de 8 espacios de indentacion, la indentacion debe de realizarse con un multiplo de 4 de espacios.
    
    2. El codigo correctamente indentado, pasara a la Depuracion, donde se valida si el codigo esta bien escrito, siguiendo las validaciones y la compatiblilidad a un codigo PyTikZ. (Despues de la depuracion, el codigo se tratara como un codigo PyTikZ, por conveniencia).
    
    Nota: Con codigo PyTikZ nos referimos a lo que el sistema reconoce de un codigo TikZ, esto debido a que no todas las funcionalidades del codigo TikZ estan actualmente implementado en la aplicacion. (Ver el manual de PyTikZ para mas detalles).

    3. La depuracion sera valida o no, dependiendo si el sistema reconoce todo o no de un codigo TikZ. 
    
    3.1. En el caso de que la depuracion sea valida, se procedera a Validar la metrica y el tipo de dato del codigo PyTikZ, }
    si esta todo correcto, se ejecutara el codigo, esto va desde dibujarse en pantalla o simplemente guardara el dibujo en un formato de imagen, esto dependiendo del codigo a ejecutar en cuestion.
    
    3.2. En el caso de que la depuracion no sea valida, se lanzara un aviso informativo de error."""

    __version__ = "0.2.0"

    def __init__(self,codigo_tikz:str,area_de_dibujar:object,user_data_dir=None):
        """Se recibe 2 parametros, y 1 parametro opcional:
        codigo_tikz(str): Es el codigo tikz en cadena de texto.
        area_de_dibujar(object): Es el Widget en donde se desea dibujar el codigo tikz escrito, se recomienda un Widget de tipo RelativeLayout.
        user_data_dir=None(object): Las rutas que utilizamos para guardar los archivos en un entorno Android, es apartir de la ruta raiz "user_data_dir" de la clase MDApp (Si se utiliza el Framework de Kivy el KivyMD) o App (Si utiliza puramente Kivy).
        
        Los valores validos para el parametro user_data_dir, son: 
        - MDApp().user_data_dir
        - App().user_data_dir"""
        #Configuracion - Globales
        globales.ruta_raiz = os.path.dirname(os.path.abspath(__file__))
        if(platform == "android"):
            globales.ruta_imagen = os.path.join(os.path.dirname(user_data_dir), 'DCIM')
        else:
            ruta_usuario = str(pathlib.Path.home())#'C:\\Users\\juanf'
            globales.ruta_imagen = os.path.join(ruta_usuario, 'Pictures')
        for ubicacion,carpetas_necesarias in globales.carpetas_necesarias.items():
            for carpeta_necesaria in carpetas_necesarias:
                if(ubicacion == "imagen"):
                    ruta_ubicacion = pathlib.Path(os.path.join(globales.ruta_imagen,carpeta_necesaria))
                ruta_ubicacion.mkdir(parents=True, exist_ok=True)
        #Mostrar rutas globales
        GenerarDiagnostico(self.__class__.__name__,"Ruta raiz del directorio: "+globales.ruta_raiz,"info")
        GenerarDiagnostico(self.__class__.__name__,"Ruta de la carpeta imagen: "+globales.ruta_imagen,"info")
        #Ordenar codigo de forma Jerarjica por Anidado.
        self.codigo_tikz_indentado = IndentadorTikz(codigo_tikz).indentar()
        GenerarDiagnostico(self.__class__.__name__,"Codigo TikZ indentado","info")
        GenerarDiagnostico(self.__class__.__name__,self.codigo_tikz_indentado,"info")
        
        #Se analiza cada codigo si esta escrito correctamente segun la documentacion TikZ
        depuracion_validado = DepuradorTikz(self.codigo_tikz_indentado).depurar_codigo()
        GenerarDiagnostico(self.__class__.__name__,"Codigo TikZ depurado","info")
        GenerarDiagnostico(self.__class__.__name__,depuracion_validado,"info")

        #Si es valido...
        if(isinstance(depuracion_validado,list)):
            #Aqui se guardaran todos los comandos validos de Tikz.
            comandos_tikz_depurado = depuracion_validado
            #Instanciar ValidadorPytikZ
            validador_pytikz = ValidadorPytikz(area_de_dibujar)
            #Transpilacion de TikZ a codigo PyTiZ
            transpilador = Transpilador()
            comandos_pytikz_depurado = transpilador.tikz_a_pytikz(comandos_tikz_depurado)
            GenerarDiagnostico(self.__class__.__name__,"Codigo PyTikZ transpilado","info")
            GenerarDiagnostico(self.__class__.__name__,comandos_pytikz_depurado,"info")
            #Guardar valor en la propiedad comandos_pytikz_depurado de la clase ValidadorPytikZ
            validador_pytikz.comandos_pytikz_depurado = comandos_pytikz_depurado
            #Si el codigo PyTikZ es valido, se procede a dibujar...
            error_validacion = validador_pytikz.validar_pytikz()
            if(error_validacion):
                self.__lanzar_error(error_validacion["error"])

        #Si lo no lo es...
        elif(isinstance(depuracion_validado,dict)):
            self.__lanzar_error(depuracion_validado["error"])

    def __lanzar_error(self,error_arr):
        """Lanza un aviso mostrando todos los errores ocurridos durante la ejecucion del codigo."""
        #Si devuelve un error juntar los mensajes en un String
        mensaje_de_error = ""
        cantidad_error = 1
        for error in error_arr:
            mensaje_de_error+="#"+str(cantidad_error)+" "+error+"\n"
            cantidad_error+=1
        #Lanzar dialog de error
        AvisoInformativo(titulo="Error al ejecutar el codigo TikZ",mensaje=mensaje_de_error)