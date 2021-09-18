import re
from typing import List, Union

#Librerias propias
from modulos.logging import GenerarDiagnostico

class IndentadorTikz():
    """Realiza la validacion de indentacion del codigo TikZ, si el codigo esta bien indentado siguiendo la regla de indentacion de un multiplo de 4 de espacios. Se guaradara en un Array de indentacion, donde tendra anidaciones de Array dependiendo si el comando esta anidado dentro de otro comando o no, se conservan los espacios.
    
    Un ejemplo de un Array de indentacion seria:
    
    - Si se ejecuta siguiente comando: \shade (10pt,220pt) rectangle (60pt, 270pt);
    - El Array de indentacion seria: ['\\shade (10pt,220pt) rectangle (60pt, 270pt);']
    
    Un ejemplo de un Array de indentacion anidado seria:
    
    - Si se ejecuta siguiente comando:
    \foreach \r in {3,2,1} {
        %0 Grados
        \draw[draw=black, line width=3pt] (10.12,7.45) arc (0:360:\r);
    };
    - El Array de indentacion seria:
    ['\\foreach \\r in {3,2,1} {', ['    \\draw[draw=black, line width=3pt] (10.12,7.45) arc (0:360:\\r);']]
    
    Metodo:
    - indentar, retorna un Array de indentacion.
    """

    def __init__(self,codigo_tikz:str):
        """Al recibir el codigo_tikz(str), se realizan los siguientes pasos:
        1. Se eliminan los siguientes comandos y sus anidados del codigo_tikz:
        - %% (Comentarios)
        - foreach
        - newcommand
        
        2. Todos los comandos anidados (foreach y newcommand), pasan de ser de tipo "str" a tipo "array", con el separador del "\n".
        
        3. El resto de comandos, pasan de ser de tipo "str" a tipo "array, con el separador del "\".

        4. Todos los comandos se almacenaran en el atritubo de nombre "codigo_tikz_ordenado" (No se almacena codigo vacio), donde no tendra una anidacion de Arrays (El array solo contara con valores "str").
        4.1. Antes de ser almacenados, se verificara si el codigo es un "\t", si lo es no se añadira, pero el codigo siguiente tendra el espacio correspondiente al "\t". Cada "\t" corresponde a 4 espacios.
        """

        #Variables necesarios para realizar la indentacion
        self.codigo_tikz_ordenado = []
        self.codigo_tikz_indentado = []
        self.indentaciones = []

        #Todos los comentarios, borrar comentarios del codigo TikZ para que no sea procesado.
        regex_comentario = re.findall(
            re.compile(r" *%.*%*"),
            codigo_tikz
        )
        conjunto_de_comentarios = []
        for comentario in regex_comentario:
            conjunto_de_comentarios.append(comentario.split("\n"))
            for comando_comentario in conjunto_de_comentarios:
                for codigo in comando_comentario:
                    codigo_tikz = codigo_tikz.replace(codigo,"")

        #Todos los Foreach
        regex_foreach = re.findall(
            re.compile(r" *\\foreach+ [\\\w]+ \[?.*?\]?in {.+?} *{\n.*?\n*};",re.DOTALL),
            codigo_tikz
        )
        conjunto_de_foreach = []
        for foreach in regex_foreach:
            conjunto_de_foreach.append(foreach.split("\n"))
            for comando_foreach in conjunto_de_foreach:
                for codigo in comando_foreach:
                    codigo_tikz = codigo_tikz.replace(codigo,"")
        
        #Todos los Newcommand
        regex_newcommand = re.findall(
            re.compile(r" *\\newcommand+\{[\\\w]+\}\[\d+\]\[\d\] *{\n.*?\n*};",re.DOTALL),
            codigo_tikz
        )
        conjunto_de_newcommand = []
        for newcommand in regex_newcommand:
            conjunto_de_newcommand.append(newcommand.split("\n"))
            for comando_newcommand in conjunto_de_newcommand:
                for codigo in comando_newcommand:
                    codigo_tikz = codigo_tikz.replace(codigo,"")

        #Antes de añadir, reemplazar tabuladores por "", y por cada tabulador añadir 4 de espacios al codigo siguiente.
        #Generar un Array por comando separandolos por "\"
        codigo_tikz = self.__agregar_espacios_de_tabulador(codigo_tikz.split("\\"))
        
        #Añadir código Newcommand al listado de codigos.
        for comando_newcommand in conjunto_de_newcommand:
            comando_newcommand = self.__agregar_espacios_de_tabulador(comando_newcommand)
            for codigo in comando_newcommand:
                if codigo:#No se admite codigo vacio
                    self.codigo_tikz_ordenado.append(codigo)

        #El resto del código...
        for codigo in codigo_tikz:
            if codigo:#No se admite codigo vacio
                self.codigo_tikz_ordenado.append(codigo)

        #Añadir código Foreach al listado de codigos PD: Se añade despues, ya que puede ir anidado dentro de un AnimarPytikz.
        for comando_foreach in conjunto_de_foreach:
            comando_foreach = self.__agregar_espacios_de_tabulador(comando_foreach)
            for codigo in comando_foreach:
                if codigo:#No se admite codigo vacio
                    self.codigo_tikz_ordenado.append(codigo)

        #Convierte si empieza con "\n" o "\};" a "".
        for indice_codigo,codigo in enumerate(self.codigo_tikz_ordenado,0):
            indices_saltos_de_linea = [(m.start(0),m.end(0)) for m in re.finditer(r" *\\+\n", codigo)]
            codigo_arr = list(codigo)
            indice_final_anterior = 0
            for indice_salto_de_linea in indices_saltos_de_linea:
                indice_inicial, indice_final = indice_salto_de_linea
                es_una_secuencia = True if indice_final_anterior+1 == indice_inicial else False
                if indice_inicial == 0 or es_una_secuencia:
                    for indice_codigo_arr,_ in enumerate(codigo_arr[indice_inicial::],indice_inicial):
                        codigo_arr[indice_codigo_arr] = ""
                        if indice_codigo_arr == indice_final:
                            break
                    indice_final_anterior = indice_final
                else:
                    break
            #No deberia de estar vacio...
            validacion_codigo = "".join(codigo_arr).replace("\\};","").strip()
            if not validacion_codigo:
                self.codigo_tikz_ordenado[indice_codigo] = validacion_codigo
            else:
                self.codigo_tikz_ordenado[indice_codigo] = codigo.replace("\n","")

        #Todo codigo vacio es eliminado.
        self.codigo_tikz_ordenado = [codigo for codigo in self.codigo_tikz_ordenado if codigo]
        GenerarDiagnostico(self.__class__.__name__,"Codigo TikZ ordenado","debug")
        GenerarDiagnostico(self.__class__.__name__,self.codigo_tikz_ordenado,"debug")

    def indentar(self)->List[List[Union[list,str]]]:
        """Para realizar la indentacion, se hacen los siguientes pasos:
        
        1. Se recorre el atributo "codigo_tikz_sin_ordenar", con un proposito, agregar la cantidad de indentaciones(int) por cada linea de codigo en el atributo "indentaciones".
        
        2. Se recorre el atributo "indentaciones", con un proposito, la de agregar los elementos del atributo "codigo_tikz_ordenado" en el array "codigo_tikz_indentado" pero ya ordenado por una Jerarquia de Arrays, cuya anidacion dependera de la anidacion del codigo en cuestion segun indentacion de espacios con multiplo de 4.
        
        Retorna:
        - Una lista con el codigo correctamente anidado dependiendo de la indentacion de esta."""
        
        #FASE 1
        indice = 0
        
        for codigo in self.codigo_tikz_ordenado:
            #Sacar longitud de la indentacion
            if(re.search(r"^ ",codigo) and re.search(r"\b\S",codigo)):
                self.indentaciones.append(len(codigo[
                        re.search(r"^ ",codigo).start():#Desde el primer espacio
                        re.search(r"\b\S",codigo).start()-1]#Hasta el primer caracter
                    ))
            else: self.indentaciones.append(0)
            indice += 1
        
        #FASE 2: Se ordena el Codigo TikZ en una Matriz segun Jerarquia dada por la Indentacion del Codigo.
        indice = 0
        indice_anidado = 0
        indentado_anterior = None

        for indentado in self.indentaciones:
            #Si el siguiente comando pertecene al mismo nivel del anterior comando o es el primer comando...
            if indentado == indentado_anterior or indentado_anterior == None:
                #Nivel 0
                if indentado == 0 or indentado_anterior == None:
                    if len(self.codigo_tikz_ordenado) > indice:
                        self.codigo_tikz_indentado.append(self.codigo_tikz_ordenado[indice])
                #Nivel 1
                elif indentado == 4:
                    self.codigo_tikz_indentado[indice_anidado].append(self.codigo_tikz_ordenado[indice])
                #Nivel 2
                elif indentado == 8:
                    self.codigo_tikz_indentado[indice_anidado_anterior][indice_anidado_posterior].append(self.codigo_tikz_ordenado[indice])
                indentado_anterior = indentado
                
            #Si el siguiente comando pertecene a un nivel diferente del anterior comando...
            elif indentado != indentado_anterior:
                if len(self.codigo_tikz_ordenado) > indice:
                    #NIVEL 1 -> NIVEL 2
                    if indentado_anterior == 4 and indentado == 8:
                        #Actualizar matriz de codigo tikz ordenado
                        indice_anidado_anterior = indice_anidado#Estara anidado en el ultimo elemento de la anidacion PADRE.
                        self.codigo_tikz_indentado[indice_anidado_anterior].append([self.codigo_tikz_ordenado[indice]])
                        indice_anidado_posterior = len(self.codigo_tikz_indentado[indice_anidado_anterior])-1#Estara anidado en el ultimo elemento de la anidacion PADRE que es una Anidacion (Matriz).
                        #Ya ubicado la matriz dentro de su anidacion correspondiente, no se volvera a ejecutar este codigo hasta que se cambie la anidacion...
                        indentado_anterior = indentado
                    
                    #NIVEL 0 -> NIVEL 1
                    elif indentado_anterior == 0 and indentado == 4:
                        #Actualizar matriz de codigo tikz ordenado
                        self.codigo_tikz_indentado.append([self.codigo_tikz_ordenado[indice]])
                        indice_anidado = len(self.codigo_tikz_indentado)-1#Esta anidado en el ultimo elemento de la matriz...
                        #Ya ubicado la matriz dentro de su anidacion correspondiente, no se volvera a ejecutar este codigo hasta que se cambie la anidacion...
                        indentado_anterior = indentado

                    #NIVEL 1 -> NIVEL 0
                    elif indentado_anterior == 4 and indentado == 0:
                        #Actualizar matriz de codigo tikz ordenado
                        self.codigo_tikz_indentado.append(self.codigo_tikz_ordenado[indice])
                        indice_anidado = 0#No esta anidado...
                        #Ya ubicado la matriz dentro de su anidacion correspondiente, no se volvera a ejecutar este codigo hasta que se cambie la anidacion...
                        indentado_anterior = indentado
                    
                    #NIVEL 2 -> NIVEL 1
                    elif indentado_anterior == 8 and indentado == 4:
                        #Actualizar matriz de codigo tikz ordenado
                        self.codigo_tikz_indentado[indice_anidado_anterior].append([self.codigo_tikz_ordenado[indice]])
                        indice_anidado = len(self.codigo_tikz_indentado)-1#Esta anidado en el ultimo elemento de la matriz...
                        #Ya ubicado la matriz dentro de su anidacion correspondiente, no se volvera a ejecutar este codigo hasta que se cambie la anidacion...
                        indentado_anterior = indentado
            indice+=1

        GenerarDiagnostico(self.__class__.__name__,"Indentaciones detectadas por lineas","debug")
        GenerarDiagnostico(self.__class__.__name__,self.indentaciones,"debug")
        return self.codigo_tikz_indentado

    def __agregar_espacios_de_tabulador(self,array:List[str])->List[str]:
        """1. Recorre el array, verificando si se comienza un elemento con el "\t", si es asi entonces se le reemplaza por 4 espacios.
        2. Al finalizar el primer recorrido, se vuelve a recorrer el mismo array pero esta vez con el objetivo, de agregar los espacios anteriores (Tabuladores) al comando, es decir se haria lo siguinte:
        - Array entrante: ["\t","\t","\draw"]
        - Array de salida:["","",'    '+'    '+\draw]
        2.1. Los tabuladores pasan de ser de 4 espacios, a ser un String vacio.
        2.2. Si los comandos no empiezan con un "\", se agregan.
        
        Parametro:
        - arary(List[str])

        Retorna:
        - array(List[str])
        """
        for indice_codigo,codigo in enumerate(array,0):
            indices_tabuladores = [(m.start(0),m.end(0)) for m in re.finditer(r" *\t+", codigo)]
            codigo_arr = list(codigo)
            indice_final_anterior = 0
            for indice_tabulador in indices_tabuladores:
                indice_inicial, indice_final = indice_tabulador
                es_una_secuencia = True if indice_final_anterior+1 == indice_inicial else False
                if indice_inicial == 0 or es_una_secuencia:
                    for indice_codigo_arr,_ in enumerate(codigo_arr[indice_inicial::],indice_inicial):
                        codigo_arr[indice_codigo_arr] = "    "
                        if indice_codigo_arr == indice_final:
                            break
                    indice_final_anterior = indice_final
                else:
                    break
            if len(indices_tabuladores):
                array[indice_codigo] = "".join(codigo_arr)
        agregar_espacios = ""
        for indice_codigo,codigo in enumerate(array,0):
            if codigo and not codigo.isspace():
                codigo = array[indice_codigo]
                if codigo.find("\\") == -1:#Si el comando no tiene el "\draw", entonces añadirlo...
                    array[indice_codigo] = agregar_espacios+"\\"+array[indice_codigo]
                else:#Si el comando lo tiene, solo añadir los espacios
                    array[indice_codigo] = agregar_espacios+array[indice_codigo]
                agregar_espacios = ""
            else:
                agregar_espacios+=codigo
        return array