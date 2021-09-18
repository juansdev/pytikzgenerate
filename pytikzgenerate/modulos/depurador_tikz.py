import re, json
from typing import List, Union, Dict
from copy import deepcopy
# Librerias propias
from modulos.submodulos.base_pytikz import BasePytikz
from modulos.logging import GenerarDiagnostico
from modulos.submodulos.depurador_tikz.tratamiento_parametros import TratamientoParametros
from modulos.submodulos.validadores import Validadores

class DepuradorTikz(BasePytikz):
    """Realiza la depuracion del codigo TikZ, verifica si el codigo TikZ es compatible con un codigo PyTikZ."""

    def __init__(self, codigo_tikz_ordenado: List[List[Union[list, str]]]):
        self.codigo_tikz_ordenado = codigo_tikz_ordenado
        # Aqui se guardaran todos los comandos validos de Tikz.
        self.comandos_tikz_validados = []
        # Cantidad de lineas de codigo...
        self.linea_de_codigo = 1
        # Mensajes de error de codigo
        self.mensajes_de_error = []
        # Aqui se guardan los comandos creados por el usuario...
        self.comandos_de_usuario = {}
        # Aqui se guardan los comandos a animar por el usuario...
        self.comandos_a_animar = {}
        # Tool utilizado por las funciones agregar_comando y cuando se invoca ese comando creado por el usuario...
        self.tratamiento_parametros = TratamientoParametros()
        # Instanciar la clase de Validadores
        self.validadores = Validadores()

    def depurar_codigo(self) -> Union[List[list], Dict[str, list]]:
        r"""Depura el codigo, solo hasta una indentacion de nivel 2 (8 espacios), siguiendo las siguientes validaciones:

        1. Nombres de los comandos, verifica si el nombre del comando es compatible con PyTikZ.
        - Si es correcto se almacena en la variable "self.comando_tikz".

        2. Parametros de los comandos, verifica si las llaves bien sea "[]" o "{}", estan escritos correctamente, asi como sus valores, ordenandome los parametros en un Array como el siguiente: [["estilo"],{"estilo":"valor"}]. Donde los valores iran en un Array o en el Dict, si el parametro se trata de un valor de "llave:valor" (Dict) o solo de "valor" (Array).
            EJ: [[red, dotted],{line width= "3pt"}]
        - Si es correcto se almacena en la variable "self.parametros_comando".

        3. Posiciones de los comandos, verifica si las llaves "()", estan escritos correctamente, asi como sus valores ordenados dentro de ella, se almacenan en un Array como el siguiente: [(X1,Y1),(X2,Y2)]
        - Si es correcto se almacena en la variable "self.posiciones".

        4. La figura/s de un comando, verifica si el nombre de la figura es compatible con PyTikZ.
        - Si es correcto se almacena en la variable "self.figuras"

        5. La funcion de una figura, se trata de los parametros de una figura (No confundir con parametros de un comando), se guardan de la siguiente manera: [[],{}].
            EJ: [[],{"start angle":"0", "end angle":"45","radius":"1"}]
        - Si es correcto se almacena en la variable "self.funcion_de_figura".

        6. Con los comandos personalizados \newcommand, se realizan dos cosas:
        - Se almacena en la variable "self.comandos_de_usuario", los comandos personalizados con sus respectivos comandos anidados.
        - Cuando un comando es invocado, se valida la metrica y el tipo de dato de los parametros de dicho comando.
        - Si es valido el comando invocado, se recupera de la variable "self.comandos_de_usuario y se pasan los comandos a la funcion "__validador_codigo", para realizar las validaciones anteriormente mencionada.

        7. Los comandos que invocan un comando creado por el comando \newcommand, o al invocar \foreach, los comandos anidados pasan a ser retornados validandosen como comandos de dibujos.

        8. Los comandos \tikzset, \definecolor, \animarPytikz y \guardarPytikz se realizan dos cosas:
        - Se validan los parametros, si estan correctamente escrito, si lo esta se almacena en la variable "self.funcion_de_comando".
        - Estos comandos pasan a ser retornados validandosen como otros comandos.

        Retorna:
        1. Si no se cumple alguna validacion, me retorna un Dict, de la siguiente manera: {"error":["mensajes_de_error"]}
        2. Si se cumplen todas las validaciones, me retorna una List, que tendra List correspondiente cada uno a un comando, donde sera guardado con el siguiente orden:
        - Caso comandos de dibujo: [self.comando_tikz,self.parametros_comando,self.posiciones,self.figuras,self.funcion_de_figura]
        - Otros comandos: [self.comando_tikz, self.funcion_de_comando, self.parametros_comando]
        """
        for codigo in self.codigo_tikz_ordenado:
            if(len(self.mensajes_de_error) > 0):
                error = {"error": self.mensajes_de_error}
                return error
                
            self.__limpiar_variables()

            # Si no hay codigo anidado... Nivel 0
            if(not isinstance(codigo, list)):
                self.__validador_codigo(codigo)
            # Si hay codigo anidado... Nivel 0 -> Nivel 1
            elif(isinstance(codigo, list)):
                codigo_anidado = codigo
                for codigo in codigo_anidado:
                    # Si hay codigo anidado... Nivel 1 -> Nivel 2
                    if(isinstance(codigo, list)):
                        codigo_anidado = codigo
                        for codigo in codigo_anidado:
                            self.__anidar(codigo, True)
                            self.__limpiar_variables()
                     # Si no hay codigo anidado... Nivel 1
                    else:
                        self.__anidar(codigo)
                    self.__limpiar_variables()
                # CASO 1 "newcommand":Guardar los comandos creados por el usuario y luego borrar la linea de comando que lo creo en la variable...
                if self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][0] == "newcommand":
                    self.__agregar_comando(self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][1])
                    self.comandos_tikz_validados.pop()
            self.linea_de_codigo += 1
        if(len(self.mensajes_de_error) > 0 or not len(self.comandos_tikz_validados)):
            if(not len(self.comandos_tikz_validados)):
                self.mensajes_de_error.append(
                    "No has invocado ningun comando, este error suele suceder cuando no hay una correcta identacion o has escrito un comando personalizado pero no lo has invocado.")
            error = {"error": self.mensajes_de_error}
            return error
        return self.comandos_tikz_validados

    def __limpiar_variables(self)->None:
        """Limpiar las propiedades a sus valores originales, estas propiedades son las que se retornaran en la funcion "depurar_codigo" dentro de un Array."""
        self.comando_tikz = ""
        self.funcion_de_comando = [[], {}]
        self.parametros_comando = [[], {}]
        self.posiciones = []
        self.figuras = []
        self.funcion_de_figura = [[], {}]

    def __validador_codigo(self, codigo:str, contenido_comando: bool = False) -> Union[
        # Solo si contenido_comando es True
        list,
        # Si contenido_comando es False
        None
        ]:
        r"""Se realiza las siguientes validaciones en el codigo:
        1. Valida si el nombre del comando es compatible con los comandos PyTikZ.
        2. Valida si los parametros estan correctamente escritos.
        3. Valida si las posiciones estan correctamente escritas.
        4. Valida si las figuras son compatibles con las figuras PyTiKZ.

        Parametros:
        1. codigo(str), es una linea de codigo TikZ.
        2. contenido_comando(bool), si es False, se agrega una lista ordenada con los elementos del comando, al "self.comandos_tikz_validados". Si es True, se retorna la lista ordenada con los elementos del comando.

        Retorna, solo en el caso de que "contenido_comando" sea True.:
        1. Una lista con los siguientes elementos dependiendo del comando a ejecutar en cuestion:
        - Caso comandos de dibujo: [self.comando_tikz,self.parametros_comando,self.posiciones,self.figuras,self.funcion_de_figura]
        - Otros comandos: [self.comando_tikz, self.funcion_de_comando, self.parametros_comando]
        """

        # COMANDOS PARA DIBUJAR

        if(re.search(r"^ *\\draw[ \[]", codigo) or
            re.search(r"^ *\\filldraw[ \[]", codigo) or
            re.search(r"^ *\\fill[ \[]", codigo) or
            re.search(r"^ *\\shade[ \[]", codigo)):

            if(re.search(r"^ *\\draw[ \[]", codigo)):
                self.comando_tikz = "draw"
            elif(re.search(r"^ *\\filldraw[ \[]", codigo)):
                self.comando_tikz = "filldraw"
            elif(re.search(r"^ *\\fill[ \[]", codigo)):
                self.comando_tikz = "fill"
            else:
                self.comando_tikz = "shade"

            self.figuras = self.__validar_figuras(codigo)
            self.__validador_parametros_comando(codigo)
            self.__validador_posiciones(codigo)

            if not contenido_comando:
                self.comandos_tikz_validados.append(
                    [self.comando_tikz, self.parametros_comando, self.posiciones, self.figuras, self.funcion_de_figura])
            else:
                return [self.comando_tikz, self.parametros_comando, self.posiciones, self.figuras, self.funcion_de_figura]

        # OTROS COMANDOS

        elif(re.search(r"^ *\\tikzset", codigo) or
              re.search(r"^ *\\definecolor", codigo) or
              re.search(r"^ *\\newcommand", codigo) or
              re.search(r"^ *\\animarPytikz", codigo) or
              re.search(r"^ *\\guardarPytikz", codigo) or
              re.search(r"^ *\\foreach", codigo)):

            # DEFINIR VARIABLES PERSONALIZADAS

            if(re.search(r"^ *\\tikzset", codigo)):
                self.comando_tikz = "tikzset"
            elif(re.search(r"^ *\\definecolor", codigo)):
                self.comando_tikz = "definecolor"

            # DEFINIR COMANDOS PERSONALIZADOS - CONTENIDO ANIDADO

            elif(re.search(r"^ *\\newcommand", codigo)):
                self.comando_tikz = "newcommand"

            # ANIMAR INSTRUCCIONES DE DIBUJO - CONTENIDO ANIDADO

            elif(re.search(r"^ *\\animarPytikz", codigo)):
                self.comando_tikz = "animarPytikz"
            elif(re.search(r"^ *\\guardarPytikz", codigo)):
                self.comando_tikz = "guardarPytikz"

            # COMANDO DE BUCLE - CONTENIDO ANIDADO

            elif(re.search(r"^ *\\foreach", codigo)):
                self.comando_tikz = "foreach"

            self.__validador_parametros_comando(codigo)

            if not contenido_comando:
                self.comandos_tikz_validados.append(
                    [self.comando_tikz, self.funcion_de_comando, self.parametros_comando])
            else:
                return [self.comando_tikz, self.funcion_de_comando, self.parametros_comando]

        # SI ES UN COMANDO CREADO POR EL USUARIO O UN COMANDO QUE NO SE CONOCE
        else:
            # Si se trata de un comando creado por el usuario...
            comando_usuario_valido = False
            for comando in list(self.comandos_de_usuario.keys()):
                nombre_comando = comando.replace("\\", "")
                if(re.search(r"^ *\\"+nombre_comando, codigo)):
                    self.comando_tikz = comando
                    self.__validador_parametros_comando(codigo)
                    comando_usuario_valido = True
            # Si no se conoce...
            if not comando_usuario_valido:
                nombre_comando_desconocido = ",".join(
                    re.findall(r"^ *\\.*", codigo))
                self.mensajes_de_error.append("Error en la linea "+str(self.linea_de_codigo) + ": El comando '" +
                                              nombre_comando_desconocido+"' no esta registrado en el sistema o no existe.")

    def __validar_figuras(self, codigo:str)->Union[List[str],str]:
        """Verifica si la figura TikZ es compatible con PyTikZ. Si se trata de una figura con parametros, se agregan los parametros a "self.funcion_de_figura".
        
        Retorna: 
        1. Si la figura es valida, se retorna el Array con las figuras (List[str)).
        2. Si no es valida, se retorna un ""."""
        figuras=[]
        #SOLO UNA FIGURA
        if(re.search("[\) ]rectangle[\( ]",codigo)):
            figuras_regex=re.compile("[\) ]rectangle[\( ]")
            for figura in figuras_regex.finditer(codigo):
                figuras.append(figura.group().replace(")", "").replace("(", "").strip())
                break
        if(re.search("[\) ]circle[\( ]",codigo)):
            figuras_regex=re.compile("[\) ]circle[\( ]")
            for figura in figuras_regex.finditer(codigo):
                figuras.append(figura.group().replace(")", "").replace("(", "").strip())
                break
        if(re.search("[\) ]--[\( ]",codigo)):
            figuras_regex=re.compile("[\) ]--[\( ]")
            for figura in figuras_regex.finditer(codigo):
                figuras.append(figura.group().replace(")", "").replace("(", "").strip())
                break
        if(re.search("[\) ]grid[\( ]",codigo)):
            figuras_regex=re.compile("[\) ]grid[\( ]")
            for figura in figuras_regex.finditer(codigo):
                figuras.append(figura.group().replace(")", "").replace("(", "").strip())
                break
        #MAS DE UNA FIGURA
        if(re.search("[\) ]arc[\( ]",codigo)):
            figuras_regex=re.compile("[\) ]arc[\( ]")
            for figura in figuras_regex.finditer(codigo):
                figuras.append(figura.group().replace(")", "").replace("(", "").strip())
        if(re.search("[\. ]controls[\( ]",codigo)):
            figuras_regex=re.compile("[\. ]controls[\( ]")
            for figura in figuras_regex.finditer(codigo):
                figuras.append(figura.group().replace(".", "").replace("(", "").strip())
        if(re.search("arc\[.*\]",codigo)):
            #Arreglar
            parametros = codigo[slice(codigo.find("arc["), len(codigo))]
            parametros = parametros[slice(parametros.find("[")+1, parametros.find("]"))].split(",")
            for parametro in parametros:
                if(parametro.find("=") != -1):
                    clave_parametro=parametro[slice(0, parametro.find("="))]
                    valor_parametro=parametro[slice(parametro.find("=")+1, len(parametro))]
                    self.funcion_de_figura[1][clave_parametro]=valor_parametro
                else:
                    self.funcion_de_figura[0].append(parametro)
            figuras.append("arc")
        return figuras if len(figuras) > 0 else ""

    def __validador_parametros_comando(self, codigo: str)->None:
        """Valida los parametros del comando, en el caso de que sea valido, se hace lo siguiente, dependiendo del comando en cuestion:
        
        1. Comandos de dibujos:
        - Agrega los parametros del comando al Array "self.parametros_comando".
        2. Otros comandos:
        - Agrega los parametros del comando al Array "self.funcion_de_comando"."""
        #Esto lo hago asi ya que los comandos personalizados a invocar, se guardan asi "\lineaHorizontal", por conveniencia.
        nombre_comando = self.comando_tikz.replace("\\", "")
        # Tiene parametros por Array []
        if(re.search(r"^ *\\"+nombre_comando+"\[.*\]",codigo)):
            self.__parametros_array(codigo)
        # Es un comando Foreach y tiene parametro por Array y por Objeto (Sin clave:valor)
        elif(re.search(r"^ *\\foreach [\\\w]+ \[?.*?\]?in {", codigo)):
            self.__parametros_array(codigo)
        # Tiene parametros con clave:valor o sin clave:valor
        # EJ: 
        # - \newcommand{\lineaVertical}
        # - \tikzset{estilo_sin_parametros global/.style = {draw=red}}
        # - \tikzset{estilo_con_parametros global/.style n args = {3}{line width=#3, fill = #2, #1}, estilo global/.default = {cyan}{red}{50pt}}
        elif(re.search(r"^ *\\"+nombre_comando+"{.*}", codigo)):
            # Cantidad de objetos...
            indice_de_objeto = [i for i, letra in enumerate(codigo,0) if letra == "}"]
            #Caso 1. \newcommand{\oabajocentro}
            if len(indice_de_objeto) == 1:
                parametro = codigo[slice(codigo.find("{")+1, codigo.find("}"))]
                if self.comando_tikz == "newcommand":
                    if(parametro.find("\\") != -1):
                        #\lineaVertical
                        self.funcion_de_comando[1]["comando"] = parametro
                        #Tiene parametros: \newcommand{\oabajocentro}[1][1]{
                        if(re.search(r"}\[.*\]",codigo)):
                            self.__parametros_array(codigo)
                    else:
                        self.mensajes_de_error.append("Error en la linea "+str(self.linea_de_codigo) + ": El nombre del comando que deseas crear, debe de comenzar con \\.")
                # else:
                #     self.funcion_de_comando[0] = parametro
            #Caso \tikzset{estilo_sin_parametros global/.style = {draw=red}}
            elif len(indice_de_objeto) == 2:
                parametros = codigo[slice(codigo.find("{"), indice_de_objeto[1]+1)]
                #parametros = {estilo_sin_parametros global/.style = {draw=red}}
                parametros = "{"+'"'+parametros[parametros.find("{")+1:parametros.find("=")]+'":"'+parametros[parametros.find("=")+1:len(parametros)-1]+'"'+"}"
                #parametros = {"estilo_sin_parametros global/.style" : "{draw=red}"}
                diccionario_objeto = {}
                try:
                    diccionario_objeto = json.loads(parametros)
                except:
                    self.mensajes_de_error.append("Error en la linea "+str(self.linea_de_codigo)+": Las propiedades de los estilos de la variable local, no estan definidos correctamente.")
                if diccionario_objeto:
                    key_diccionario_objeto = list(diccionario_objeto.keys())[0]
                    valor_diccionario_objeto = diccionario_objeto[key_diccionario_objeto]
                    valor_diccionario_objeto = valor_diccionario_objeto[slice(valor_diccionario_objeto.find("{")+1, valor_diccionario_objeto.find("}"))].split(",")
                    objeto_valor = [[], {}]
                    for parametros in valor_diccionario_objeto:
                        if(parametros.find("=") != -1):
                            valor_clave_parametro = parametros[slice(0, parametros.find("="))]
                            valor_valor_parametro = parametros[slice(parametros.find("=")+1, len(parametros))]
                            objeto_valor[1][valor_clave_parametro] = valor_valor_parametro
                        else:
                            objeto_valor[0].append(parametros)
                    # [[],{estilo global/.style: [["dashed"],{line width:1.25pt,draw:cyan!75!gray}]}]
                    self.funcion_de_comando[1][key_diccionario_objeto] = objeto_valor
            #Caso 1. \tikzset{estilo_con_parametros global/.style n args = {3}{line width=#3, fill = #2, #1}, estilo global/.default = {cyan}{red}{50pt}}
            #Caso 2. \definecolor{ColorA}{RGB}{255,0,0}
            else:
                parametros = codigo[slice(codigo.find("{"), indice_de_objeto[0]+1)]+"}"
                index_declaracion_valor = [i for i, letra in enumerate(parametros) if letra == "="]
                if not len(index_declaracion_valor):
                    self.__parametros_objeto(codigo)
                else:
                    objeto_valor_parametros = [i for i, letra in enumerate(parametros) if letra == "{"]
                    objeto_valor_general = [i for i, letra in enumerate(codigo) if letra == "{"]
                    #parametros = {estilo_con_parametros global/.style n args = {3}{line width=#3, fill = #2, #1}, estilo global/.default = {cyan}{red}{50pt}}
                    parametros = "{"+'"'+parametros[parametros.find("{")+1:parametros.find("=")]+'":{"'+parametros[objeto_valor_parametros[1]+1:parametros.find("}")]+'":"'+codigo[objeto_valor_general[2]:len(codigo)-1]+'"}}'
                    #parametros = {"estilo_con_parametros global/.style n args" : { "3" : "{line width=#3, fill = #2, #1}, estilo global/.default = {cyan}{red}{50pt}"}}
                    diccionario_objeto = {}
                    try:
                        diccionario_objeto = json.loads(parametros)
                    except:
                        self.mensajes_de_error.append("Error en la linea "+str(self.linea_de_codigo)+": Las propiedades de los estilos de la variable local, no estan definidos correctamente.")
                    if diccionario_objeto:
                        # key_diccionario_objeto_padre = "estilo global/.style n args"
                        key_diccionario_objeto_padre = list(diccionario_objeto.keys())[0]
                        # valor_diccionario_objeto = { "3" : "{line width=#3, fill = #2, #1}, estilo global/.default = {cyan}{red}{50pt}" }
                        valor_diccionario_objeto = diccionario_objeto[key_diccionario_objeto_padre]
                        # key_diccionario_objeto = "3"
                        key_diccionario_objeto = list(valor_diccionario_objeto.keys())[0]
                        # valor_diccionario_objeto = "{line width=#3, fill = #2, #1}, estilo global/.default = {cyan}{red}{50pt}"
                        valor_diccionario_objeto = valor_diccionario_objeto[str(key_diccionario_objeto)]
                        # valor_diccionario_objeto = ["{line width=#3", "fill = #2", "#1}", "estilo global/.default = {cyan}{red}{50pt}"]
                        valor_diccionario_objeto = valor_diccionario_objeto.split(",")
                        valor_diccionario_objeto_limpio = []
                        for valor in valor_diccionario_objeto:
                            if re.search(r"[{}]",valor):
                                if re.search(r"{.*}",valor):
                                    valor = valor.replace("{","").replace("=",",").replace("}",",")
                                    parametros = [valor.strip() for valor in valor.split(",") if valor]
                                    #['estilo global/.default ', ' cyan', 'red', '50pt']
                                    nombre_estilo = parametros[0]
                                    estilos = "["+",".join(parametros[1::])+"]"
                                    #'estilo global/.default =[cyan,red,50pt]'
                                    valor_diccionario_objeto_limpio.append(nombre_estilo+"="+estilos)
                                else:
                                    valor_diccionario_objeto_limpio.append(valor.replace("{","").replace("}","").strip())
                            else:
                                valor_diccionario_objeto_limpio.append(valor.strip())
                        objeto_valor = [[[], {}], [[], {}]]
                        #valor_diccionario_limpio = ['line width=#3', 'fill = #2', '#1', 'estilo global/.default=[cyan,red,50pt]']
                        for indice,parametro in enumerate(valor_diccionario_objeto_limpio,0):

                            if(re.search("=",parametro)):
                                valor_clave_parametro = parametro[slice(0, parametro.find("="))]
                                valor_valor_parametro = parametro[slice(parametro.find("=")+1, len(parametro))]

                            if indice != len(valor_diccionario_objeto_limpio)-1:
                                if(re.search("=",parametro)):
                                    objeto_valor[0][1][valor_clave_parametro] = valor_valor_parametro
                                else:
                                    objeto_valor[0][0].append(parametro)
                            else:
                                if(re.search("=",parametro)):
                                    objeto_valor[1][1][valor_clave_parametro] = valor_valor_parametro
                                else:
                                    objeto_valor[1][0].append(parametro)
                                    
                        self.funcion_de_comando[1][key_diccionario_objeto_padre.strip()] = {key_diccionario_objeto: objeto_valor}
        
        # ¿Se trata de un comando creado que esta invocando el usuario sin parametro alguno?, o de algun comando que no requiera parametros como animarPytikz o guardarPytikz...
        elif(self.comando_tikz in list(self.comandos_de_usuario.keys())):
            # Extraer y validar los parametros a definir comparando con los parametros definidos por el usuario...
            cantidad_de_parametros = self.__extraer_validar_parametros_a_definir()[0]
            if not cantidad_de_parametros:
                comandos = []
                for comando_establecido in self.comandos_de_usuario[self.comando_tikz]:
                    comandos.append(comando_establecido)
                self.funcion_de_comando[1]["ejecutar"] = comandos
                if self.comando_tikz == "animarPytikz":
                    self.comando_tikz = "animarPytikz"
                else:
                    self.comando_tikz = "guardarPytikz"
                self.comandos_tikz_validados.append([self.comando_tikz, self.funcion_de_comando, self.parametros_comando])
            else:
                self.mensajes_de_error.append("Error en la linea "+str(self.linea_de_codigo)+": Debes de definir la cantidad de parametros de "+str(cantidad_de_parametros)+" en el comando que invocaste.")

    def __parametros_objeto(self, codigo:str)->None:
        r"""1. Se recorren los objetos {} de un comando, extrayendo la llave en una variable y los valores en una Array. Este procedimiento varia segun el comando.
        1.1. En el caso del comando \definecolor, se realiza lo siguientE:
        1.1.1. Extraer nombre del color
        1.1.2. Extraer el tipo del color
        1.1.3. Extraer el codigo del color y convertirlo en un Array
        1.1.4. Guardar lo extraido en "self.funcion_de_comando"
        1.2. En el caso de de los comandos creados por el usuario, se realiza lo siguiente:
        1.2.1. Extraer los valores establecidos en matrices.
        1.2.2. Extraer los valores establecidos en objetos.
        1.2.3. Extraer y validar los parametros a definir, cuya validacion se realiza al compararlos con los parametros definidos por el usuario.
        1.2.4. La cantidad de parametros del comando \newcommand, debe de coincidir con la cantidad de parametros del comando invocado.
        - \newcommand{\lineaHorizontal}[3] -> Corresponde a una cantidad_de_parametros de "3"
        - \lineaHorizontal[100pt]{110pt}{black} -> Corresponde a una cantidad de valores_a_establecer de "3"
        1.2.5. Reemplazamos los valores del comando invocado, con los comandos anidados del \newcommand en cuestion, como la siguiente manera:
        - comandos_sin_establecer: {'\\lineaHorizontal': [['draw', [[], {'fill': '#3'}], [['100pt', '#1'], ['110pt', '#2']], ['rectangle'], [[], {}]]]}
        - comandos_establecidos: {'\\lineaHorizontal': [['draw', [[], {'fill': 'black'}], [['100pt', '110pt'], ['110pt', '100pt']], ['rectangle'], [[], {}]]]}
        1.2.6. Luego se agrega el valor de la llave con el nombre del comando, en la variable "self.comandos_tikz_validados".
        """
        # Cantidad de objetos...
        indice_de_objeto = [i for i, letra in enumerate(codigo,0) if letra == "}"]

        if len(indice_de_objeto):
            primer_objeto=codigo[slice(codigo.find("{"), indice_de_objeto[0]+1)]+"}"
        else:
            primer_objeto=""
        
        if self.comando_tikz == "definecolor":
            nombre_color=primer_objeto.replace("{", "").replace("}", "").strip()
            tipo_color=codigo[slice(indice_de_objeto[0]+1, indice_de_objeto[1]+1)].replace("{", "").replace("}", "").strip()
            codigo_color=codigo[slice(indice_de_objeto[1]+1, indice_de_objeto[2]+1)].replace("{", "").replace("}", "").strip().split(",")
            objeto_valor=[[], {tipo_color: codigo_color}]
            self.funcion_de_comando[1][nombre_color]=objeto_valor
        elif self.comando_tikz in list(self.comandos_de_usuario.keys()):
            valores_a_establecer=[]
            parametro = self.parametros_comando[0][0]
            valores_a_establecer.append(parametro)
            self.parametros_comando=[[], {}]
            if primer_objeto:
                primer_objeto=primer_objeto.replace("{", "").replace("}", "")
                valores_a_establecer.append(primer_objeto)
                for i in range(0,len(indice_de_objeto)-1):
                    valor=codigo[slice(indice_de_objeto[i]+1, indice_de_objeto[i+1]+1)].replace("{", "").replace("}", "")
                    valores_a_establecer.append(valor)

            cantidad_de_parametros,parametros_sin_establecer=self.__extraer_validar_parametros_a_definir()
            
            if cantidad_de_parametros == len(valores_a_establecer):
               
                #Lo extraido, se cataloga. Los valores que corresponde a un estilo, se guardan en "valores_estilos" y los que son posiciones en "valores_posiciones".
                valores_estilos=[]
                valores_posicion=[]
                for valor in valores_a_establecer:
                    valor_resultante=self.validadores.validar_metrica(valor, no_error=True)
                    if not valor_resultante:
                        valores_estilos.append(valor)
                    else:
                        valores_posicion.append(valor)
                comandos_sin_establecer=deepcopy(self.comandos_de_usuario)
                # parametros_sin_establecer=> [[["#1","#2"],["#1","#2"]],[["#1","#2"],["#1","#2"]]]
                for count_exterior,parametro in enumerate(parametros_sin_establecer,0):
                    # parametro=> [["#2"],["#2"]]
                    for indice_parametros,conjunto_parametro in enumerate(parametro,0):
                        # conjunto_parametro=>["#2"]
                        # ¿Tiene uno (0) o mas de un parametro en los mismos comandos de estilo o de posicion?
                        cant_param=len(set(conjunto_parametro))-1
                        if cant_param >= 0:
                            count_interior=0
                            # conjunto_parametro=>["#1","#2"]
                            for parametro in list(set(conjunto_parametro)):
                                if count_exterior == 0:  # Si son parametros a establecer en estilos...
                                    # Cantidad de parametros a definir...
                                    count_interior_max=len(valores_estilos)-1
                                    # for e,_ in enumerate(comandos_sin_establecer[comando]):
                                    # {'top color': '#1!30!white', 'bottom color': '#1!70!black', ' line width ': ' 1pt', 'rounded corners': '2ex', 'yshift': '-0.3cm', 'xshift': '0.2cm'}
                                    comandos_sin_establecer_object=comandos_sin_establecer[self.comando_tikz][indice_parametros][1][1]
                                    for k in comandos_sin_establecer_object:
                                        comandos_sin_establecer[self.comando_tikz][indice_parametros][1][1][k]=comandos_sin_establecer_object[k].replace(
                                            parametro, valores_estilos[count_interior])
                                    if count_interior_max > count_interior:
                                        count_interior += 1
                                    else:
                                        count_interior=0
                                elif count_exterior == 1:  # Si son parametros a establecer en posiciones...
                                    # Cantidad de parametros a definir...
                                    count_interior_max=len(valores_posicion)-1
                                    # [['#1', '100pt'], ['10pt', '10pt']]
                                    comandos_sin_establecer_arr=comandos_sin_establecer[self.comando_tikz][indice_parametros][2]
                                    for e in range(len(comandos_sin_establecer_arr)):
                                        arr_actualizado=[
                                            comando for comando in comandos_sin_establecer_arr[e]]
                                        get_indexs_a_actualizar=lambda x, xs: [
                                            i for (y, i) in zip(xs, range(len(xs))) if x == y]
                                        indexs_a_actualizar=get_indexs_a_actualizar(
                                            parametro, arr_actualizado)
                                        if len(indexs_a_actualizar):
                                            for index in indexs_a_actualizar:
                                                arr_actualizado[index]=arr_actualizado[index].replace(
                                                    parametro, valores_posicion[count_interior])
                                                comandos_sin_establecer[self.comando_tikz][indice_parametros][2][e]=list(
                                                    arr_actualizado)
                                    if count_interior_max > count_interior:
                                        count_interior += 1
                                    else:
                                        count_interior=0
                        indice_parametros += 1
                    count_exterior += 1

                comandos_establecidos = comandos_sin_establecer
                # Si hay mas de 2 comandos de dibujado invocados...
                if len(self.comandos_tikz_validados)-1 >= 0:
                    # Si se desea añadir los comandos invocados al "ejecutar" del comando "animarPytikz" o "guardarPytikz", se añadira con todo y nombre del nomando personalizado...
                    if self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][0] == "animarPytikz" or self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][0] == "guardarPytikz":
                        comandos={self.comando_tikz: comandos_establecidos[self.comando_tikz]}
                        if not "ejecutar" in self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][1][1]:
                            self.funcion_de_comando[1]["ejecutar"]=[comandos]
                            # REEMPLAZAR VALORES VACIÓS DEL COMANDO ANIMARPYTIKZ
                            self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][1]=self.funcion_de_comando
                        else:
                            # AÑADIR MÁS VALORES ANIDADOS DEL COMANDO ANIMARPYTIKZ
                            self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][1][1]["ejecutar"].append(comandos)
                    # Si no entonces solo añadir...
                    else:
                        for comando_establecido in comandos_establecidos[self.comando_tikz]:
                            self.comandos_tikz_validados.append(comando_establecido)
                # Si no los hay...
                else:
                    for comando_establecido in comandos_establecidos[self.comando_tikz]:
                        self.comandos_tikz_validados.append(comando_establecido)
            else:
                self.mensajes_de_error.append("Error en la linea "+str(self.linea_de_codigo)+": La cantidad de valores a colocar "+str(len(valores_a_establecer))+" es diferente a la cantidad de parametros del comando lo cual son "+str(cantidad_de_parametros))

    def __parametros_array(self, codigo:str)->None:
        r"""1. Recorre los parametros anidados en un [] de un comando. Se ordena y se agrega a la variable "self.parametros_comando".
        2. En el caso del comando \foreach, se hacen dos cosas mas:
        - Extraer las variables del comando, ejemplo si hay dos variables asi "\r" "\i", se extraen y se almacenan en una variable asi ["r","i"], y se guardan en la variable "self.parametros_comando".
        - Extraer los "each" del comando, ejemplo si hay "\foreach \r in {3/A,2/B,1/C}", se extraen y se almacenan en una variable asi ["3/A","2/B","1/C"], y se guardan en la variable "self.parametros_comando".

        Los comandos que tienen este tipo de parametro son:
        - \newcommand{\ocentro}[1][1]{ NOTA: Solo se toma en cuenta el primer Array.
        - \foreach \p\r [count=\i] in {1/1} {
        - \comando_de_dibujo[estilo_con_parametros global={red}{blue}{1.5pt}];
        - \comando_personalizado[300pt]{310pt}{black}"""
        if self.comando_tikz == "foreach":
            #Extraer variables
            variables=[]
            for var in codigo.split("\\"):
                if var and not re.search("foreach",var):
                    if re.search(" ",var):
                        var=var[0:re.search(" ", var).start()]
                    variables.append(var.strip())
            self.parametros_comando[1]["variables"]=variables
            #Extraer "each"
            patron_inicio_objeto=r"^ *\\foreach.*\[?.*\]? in {"
            patron_final_objeto=r"}"
            if(re.search(patron_inicio_objeto, codigo) and re.search(patron_final_objeto, codigo)):
                parametros_objeto=codigo[
                    re.search(patron_inicio_objeto, codigo).end():
                    re.search(patron_final_objeto, codigo).start()
                ].split(",")
                self.parametros_comando[0].append(parametros_objeto)
            #Extraer valores del Array
            patron_inicio_array=r"^ *\\foreach.*\["
            patron_final_array=r"\]"
            if(re.search(patron_inicio_array, codigo) and re.search(patron_final_array, codigo)):
                parametros=codigo[
                    re.search(patron_inicio_array, codigo).end():
                    re.search(patron_final_array, codigo).end()-1
                ].replace("\\","").split(",")
            else:
                parametros=""
        else:
            parametros=codigo[slice(codigo.find("[")+1, codigo.find("]"))].split(",")
        
        for parametro in parametros:
            # Caso 1. [estilo_con_parametros global={red}{blue}{1.5pt}]
            # Caso 2. ['count=i']
            if(re.search("=",parametro)):
                clave_parametro=parametro[slice(0, parametro.find("="))]
                valor_parametro=parametro[slice(parametro.find("=")+1, len(parametro))]
                self.parametros_comando[1][clave_parametro]=valor_parametro
            else:
                # Caso 2. \newcommand{\ocentro}[1][1]
                if self.comando_tikz == "newcommand":
                    self.funcion_de_comando[0].append(parametro)
                # Caso 3. \lineaVertical[300pt]{310pt}{black}
                else:
                    # En el caso de que se cree despues de [] unos objetos asi: []{}
                    self.parametros_comando[0].append(parametro)
                    self.__parametros_objeto(codigo)

    def __extraer_validar_parametros_a_definir(self)->List[any]:
        r"""Se extrae los parametros a definir desde la variable "self.comandos_de_usuario" del valor de la llave de "self.comando_tikz". Y se guarda la cantidad de parametros asi como un Array de los parametros con el identificador (#), de los comandos anidados de un \newcommand.
        
        Retorna:
        - List[cantidad_de_parametros(int), parametros_sin_establecer(List)]"""
        # Extraer los parametros a definir...
        # [0] => Parametros de estilos, [1] => Parametros de posiciones...
        parametros_sin_establecer=[[], []]

        for i in range(len(self.comandos_de_usuario[self.comando_tikz])):
            estilos_parametrizados=self.comandos_de_usuario[self.comando_tikz][i][1][1]
            estilos_sin_definir=self.tratamiento_parametros.extraerParametrosSinDefinir(estilos_parametrizados=estilos_parametrizados, comando_invocado=True)

            posiciones_parametrizados=self.comandos_de_usuario[self.comando_tikz][i][2]
            posiciones_sin_definir=self.tratamiento_parametros.extraerParametrosSinDefinir(posiciones_parametrizados, comando_invocado=True)

            if len(estilos_sin_definir):
                parametros_sin_establecer[0].append(estilos_sin_definir)
            if len(posiciones_parametrizados):
                parametros_sin_establecer[1].append(posiciones_sin_definir)

        # Validar si la cantidad de parametros corresponde a la cantidad de valores a establecer..
        len_param=[]
        num_superior=0
        for i, arr in enumerate(parametros_sin_establecer):
            cantidad_de_parametros=[]  # [[#1],[#1,#2]]
            for parametro in arr:  # [#1,#1]
                cantidad_de_parametros.append(list(set(parametro)))
            for parametro in cantidad_de_parametros:
                for param in parametro:  # ["#1,#2"]
                    param=int(param.replace("#", ""))
                    len_param.append(param)
                len_param=list(set(len_param))
                if num_superior < len(len_param):
                    num_superior=len(len_param)
        cantidad_de_parametros = num_superior
        return[cantidad_de_parametros,parametros_sin_establecer]

    def __validador_posiciones(self, codigo:str)->None:
        r"""1. Se extrae los valores de la tupla () del codigo, para luego validar si son valores correctos, dependiendo del tipo de valor, entre los valores estan:
        - Angulo inicial (int), Angulo final (int), Radio (str).
        - Posicion X (str) y Posicion Y (str)
        - Radio (str)
        1.1. Tambien se valida si existe "cycle" en el codigo.
        2. Si se pasa todas las validaciones, los valores se agregan a la variable "self.posiciones", en el caso de la validacion del "cycle;", se agrega es la palabra "cycle". """
        if re.search(r"[\(\)]",codigo):
            codigo_copia=codigo
            # Primero se saca el contenido de los ()
            while True:
                if re.search(r"\((.+?)\)",codigo_copia):
                    posicion_normal=codigo_copia[slice(codigo_copia.find("(")+1, codigo_copia.find(")"))].split(",")
                    posicion_por_angulo=codigo_copia[slice(codigo_copia.find("(")+1, codigo_copia.find(")"))].split(":")
                elif re.search(r"[\(\)]",codigo_copia):
                    self.mensajes_de_error.append("Error en la linea "+str(self.linea_de_codigo)+": Se esperaba ()")
                    posicion_normal=[]
                    posicion_por_angulo=[]
                else:
                    posicion_normal=[]
                    posicion_por_angulo=[]
                # arc (0:30:3mm) -> Parametros donde (Angulo inicial, Angulo final, radio)
                if(len(posicion_por_angulo) == 3):
                    posicion_valido=True
                    # Se verifica si los valores de los () sean validos
                    for indice,posicion in enumerate(posicion_por_angulo,0):
                        # ["",""]
                        if not posicion:
                            self.mensajes_de_error.append("Error en la linea "+str(self.linea_de_codigo)+": Debe de haber 3 coordenadas, el valor Angulo Inicial, Angulo Final y el Radio")
                            posicion_valido=False
                            break
                        # [1.1,2.2]
                        else:
                            if indice < 2:
                                try:
                                    float(posicion)
                                except:
                                    self.mensajes_de_error.append("Error en la linea "+str(self.linea_de_codigo)+": El valor debe de ser de tipo FLOAT o INTEGER")
                                    posicion_valido=False
                                    break
                    if posicion_valido:
                        self.posiciones.append(list(map(str, posicion_por_angulo)))
                        # Elimino el parametro ya validado del codigo.
                        codigo_copia=codigo_copia[slice(codigo_copia.find(")")+1, len(codigo_copia))]
                    else:
                        self.posiciones=[]
                        break
                # Solo hay 2 posiciones X y Y.
                elif(len(posicion_normal) == 2):
                    posicion_valido=True
                    # Se verifica si los valores de los () sean validos
                    for posicion in posicion_normal:
                        # ["",""]
                        if not posicion:
                            self.mensajes_de_error.append("Error en la linea "+str(self.linea_de_codigo)+": Debe de haber 2 coordenadas, el Valor X y el Valor Y")
                            posicion_valido=False
                            break
                    if posicion_valido:
                        self.posiciones.append(list(map(str, posicion_normal)))
                        # Elimino el parametro ya validado del codigo.
                        codigo_copia=codigo_copia[slice(codigo_copia.find(")")+1, len(codigo_copia))]
                    else:
                        self.posiciones=[]
                        break
                # Solo hay 1 parametro...
                # \Circle
                elif(len(posicion_normal) == 1 and "circle" in self.figuras):
                    self.posiciones.append(posicion_normal[0])  # "0.8cm"
                    # Elimino el parametro ya validado del codigo.
                    codigo_copia=codigo_copia[slice(codigo_copia.find(")")+1, len(codigo_copia))]
                else:
                    for posicion in posicion_normal:
                        # Si hay mas o menos de 2 posiciones...
                        if(posicion != ""):
                            self.mensajes_de_error.append("Error en la linea "+str(
                                self.linea_de_codigo)+": Se esperaban 2 coordenadas con un valor valido.")
                            break
                        else:
                            self.mensajes_de_error.append("Error en la linea "+str(
                                self.linea_de_codigo)+": El valor de la coordenada debe de ser de tipo FLOAT o INTEGER")
                            break
                    break
        if re.search(r"cycle;",codigo) and len(self.posiciones) > 0:
            # Este Cycle solo debe de existir al final...
            self.posiciones.append("cycle")

    def __agregar_comando(self, funcion_de_comando:Dict[str,Dict[str,Union[str,list]]])->None:
        r"""1. Se valida si la cantidad_de_parametros coincide con la cantidad de parametros_sin_definir.
        2. Si todo es valido, se agrega todos los comandos creados por el usuario en la variable "self.comandos_de_usuario".
        Con el objetivo de que en la verificación de comandos, se pueda validar si el comando invocado fue creado por el usuario, y poder así continuar con las demás validaciones, siguiendo el procedimiento como cualquier otro comando."""
        cantidad_de_parametros=funcion_de_comando[0][0]
        nombre_funcion=funcion_de_comando[1]["comando"]
        funcion_ejecutable=funcion_de_comando[1]["ejecutar"]
        # Validar si se cumple con la cantidad de parametros en Funcion Ejecutable, establecida...
        for i in range(len(funcion_ejecutable)):
            estilos_parametrizados=funcion_ejecutable[i][1][1]
            estilos_sin_definir=self.tratamiento_parametros.extraerParametrosSinDefinir(
                estilos_parametrizados=estilos_parametrizados)

            posiciones_parametrizados=funcion_ejecutable[i][2]
            posiciones_sin_definir=self.tratamiento_parametros.extraerParametrosSinDefinir(
                posiciones_parametrizados)

            if len(estilos_sin_definir) and len(posiciones_sin_definir):
                parametros_sin_definir=estilos_sin_definir+posiciones_sin_definir
            elif len(estilos_sin_definir):
                parametros_sin_definir=estilos_sin_definir
            elif len(posiciones_sin_definir):
                parametros_sin_definir=posiciones_sin_definir
            else:
                parametros_sin_definir=[]
            result_validacion_secuencia=self.tratamiento_parametros.validarSecuenciaNumerica(
                cantidad_de_parametros, parametros_sin_definir)
            if type(result_validacion_secuencia) is dict:
                self.mensajes_de_error.append(
                    "Error en la linea "+str(self.linea_de_codigo)+": "+result_validacion_secuencia["error"])
                break
        if not len(self.mensajes_de_error):
            # Si todas las validaciones son correctas...
            self.comandos_de_usuario[nombre_funcion]=funcion_ejecutable

    def __anidar(self, codigo:str, anidado_nivel_2:bool=False)->None:
        r"""
        1. Si en la variable "self.comandos_tikz_validados", el ultimo comando se trata de un comando de anidacion (\newcommand, \foreach, etc), se validan los comandos anidados usando la funcion "self.__validador_codigo", y se almacena lo retornado en la variable "codigo".
        1.1. En el caso de que el comando de anidacion ya tenga almacenado sus comandos anidados en forma de codigo en la variable "self.comandos_tikz_validados", entonces se recupera y se guarda en la variable "array_codigo", para luego al recorrer las identanciones de la variable "codigo", el valor de la variable "array_codigo", se va actualizando con el nuevo "codigo".
        1.2. En el caso de que no tenga todavia ningun codigo de sus comandos anidados, se almacena el contenido de la variable "codigo" en el comando anidado, en la variable "self.comandos_tikz_validados".
        
        2. En el caso de que no se trate de un comando de anidacion, entonces la variable "codigo", es utilizado en la funcion "self.__validador_codigo".
        """
        # Leer comandos que se almacenaran en esta clase...
        comando_anidador=self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][0]
        # Si se trata de un comando que esta dentro de un comando anidador... [foreach, newcommand, animarPytikz, guardarPytikz]
        if comando_anidador in self.COMANDOS_ANIDADORES:
            codigo=self.__validador_codigo(codigo, True)
            if "ejecutar" in list(self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][1][1].keys()):
                array_codigo=self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][1][1]["ejecutar"]
                if codigo:
                    # Si hay código anidado en el código anterior, deberá de ser añadido dentro de ese array de código.
                    if anidado_nivel_2:
                        codigo_anidado=self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][1][1]["ejecutar"]
                        ultimo_comando_sub_anidado=codigo_anidado[len(codigo_anidado)-1][0]
                        if ultimo_comando_sub_anidado == "foreach":
                            if("ejecutar" in array_codigo[len(array_codigo)-1][1][1].keys()):
                                array_codigo[len(array_codigo)-1][1][1]["ejecutar"].append(codigo)
                            else:
                                array_codigo[len(array_codigo)-1][1][1]["ejecutar"]=[codigo]
                        else:
                            array_codigo[len(array_codigo)-1][1].append(codigo)
                    # Caso contrario, se añadira como una línea de código más
                    else:
                        array_codigo.append(codigo)
                self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][1][1]["ejecutar"]=array_codigo
            else:
                self.comandos_tikz_validados[len(self.comandos_tikz_validados)-1][1][1]["ejecutar"]=[codigo]
        # Si se trata de comandos que no tienen comandos anidadores, y son comandos preexistentes o personalizados que estan siendo invocados..
        else:
            self.__validador_codigo(codigo)