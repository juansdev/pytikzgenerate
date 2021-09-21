from bisect import bisect, insort
from typing import Tuple, List, Dict, Union
# Librerias propias
from ..base_pytikz import BasePytikz

class TratamientoParametros(BasePytikz):
    """Clase que trata directamente con los parametros/posiciones de los comandos personalizados, asi como los comandos anidados, y con el comando de invocacion.
    
    Metodos:
    - extraerParametrosSinDefinir
    - validarSecuenciaNumerica"""

    def __extraer_valores(self,valor:str,comando_invocado:bool)->Union[str,int,None]:
        """Recibe los valores de los parametros/posiciones, con el tipo "str" y devuelve solo los valores que tengan identificador (#), si el parametro "comando_invocado" es False lo devuelve junto a su identificador (#) con el tipo "str", caso contrario, lo devuelve sin su identificador con el tipo "int".
        
        Parametros:
        - valor(str), el valor de los parametros/posiciones de un comando.
        - comando_invocado(bool), es True/False dependiendo si el comando se trata de llamar a un comando personalizado o no.
        
        Retorna:
        - El valor con su identificador (#) con el tipo "str", o el valor sin su identificador (#) con el tipo "int". Y si no hay valor con identificador, devuelve un None."""
        if valor.find("#")!=-1:
            for delimitador in self.DELIMITADORES_PARAMETROS_COMANDO_PERSONALIZADO:
                array_valor = valor.split(delimitador)
                if len(array_valor):
                    for valor in array_valor:
                        if valor.find("#")!=-1:
                            if not comando_invocado:
                                valor = valor.replace("#","")
                                if valor.isdigit():
                                    return int(valor)
                            else:
                                return valor
        return None

    def extraerParametrosSinDefinir(self,posiciones_parametrizados:List[List[str]]=[],estilos_parametrizados:Dict[str,str]=[],comando_invocado:bool=False)->List[Union[str,int]]:
        """Recibe los parametros y posiciones de los comandos anidados en un comando personalizado. El tipo de parametro a recibir, depende si se trata de valores sin llaves (List) o con llave:valor (Dict). Y devuelve unicamente los parametros sin definir sin su identificador (#), en el caso de que "comando_invocado" es False, caso contrario, los devuelve con su identificador.
        
        Parametros:
        - posiciones_parametrizados(List(List[str)), corresponde a las posiciones del comando anidado.
        - estilos_parametrizados(Dict(str:str)), corresponde al diccionario de parametros de estilo.
        - comando_invocado(bool), en el caso de que el comando aun no fuese invocado, el valor a volver serian de tipo List[str], caso contrario seria de tipo List[int] (Ver la funcion __extraer_valores, donde este parametro es relevante).
        
        Retorna:
        - parametros_sin_definir(List(str||int)), retorna una lista con los parametros sin definir con su identificador (#) con el tipo de dato "str". EJ: ['#1', '#2'].
        Como tambien puede retornar una lista sin su identificador (#), con el tipo de dato "int". EJ: [1,2]."""
        parametros_sin_definir = []
        if len(posiciones_parametrizados):
            for valor_arr in posiciones_parametrizados:
                for valor in valor_arr:
                    parametro_sin_definir = self.__extraer_valores(valor,comando_invocado)
                    if parametro_sin_definir:
                        parametros_sin_definir.append(parametro_sin_definir)
        elif len(list(estilos_parametrizados.values())):
            for valor in list(estilos_parametrizados.values()):
                parametro_sin_definir = self.__extraer_valores(valor,comando_invocado)
                if parametro_sin_definir:
                    parametros_sin_definir.append(parametro_sin_definir)
        return parametros_sin_definir
        
    def validarSecuenciaNumerica(self,cantidad_parametros:str,secuencia_numerica:List[int])->Union[bool,Dict[str,str]]:
        """Se valida si los valores del Array de la "secuencia_numerica" tengan una secuencia numerica es decir [1,2,3]. Para validar esto se hace lo siguiente:
        1. Se valida si la "secuencia_numerica" tenga una longitud mayor a 0.
        2. Se ordena los valores del array "secuencia_numerica", de menor a mayor.
        3. Se recorren los valores, y se valida si los valores estan en secuencia.
        3.1. Se compara el valor anterior, validando si es un valor diferente y si es un valor que al sumarse a uno, coincida con el valor actual, entonces se trata de valores secuenciales. 
        - Validacion 1. EJ: [1,2] -> Son valores diferentes. True.
        - Validacion 2. EJ: [1,2] -> Se suma el valor anterior "1", en 1. -> [2,2] -> El valor anterior es igual al valor actual. True.
        4. Se valida si "cantidad_parametros" es de tipo "int" (Se convierte "str" a "int").
        5. Se compara la longitud de "secuencia_numerica" con la "cantidad_parametros", si coinciden, devuelve un True.

        Parametros:
        - cantidad_parametros(str), es la cantidad de parametros que tiene un comando personalizado.
        - secuencia_numerica(List(int)), es la secuencia de los parametros sin definir con identificador (#) de un comando personalizado, solo que se guardan sin su identificador (#) y es de tipo "int".

        Retorna:
        - Si "secuencia_numerica" tiene una longitud de 0 devuelve True.
        - Si se cumplen todas las condiciones se devuelve True.
        - Si no se cumple alguna validacion, se retorna un diccionario de error, de la siguiente manera: {"error":"mensaje_de_error"} 
        """
        if not len(secuencia_numerica): return True
        #Los parametros deben ser secuenciales [1,2,3]. ETC
        parametros_sin_definir_ordenado = []
        for e in secuencia_numerica:
            bisect(parametros_sin_definir_ordenado, e)
            insort(parametros_sin_definir_ordenado, e)
        for indice,_ in enumerate(parametros_sin_definir_ordenado,0):
            if indice>0:
                #1,2 -> El numero anterior es diferente al "2". True. (Es secuencial)
                son_numeros_diferentes = parametros_sin_definir_ordenado[indice-1] != parametros_sin_definir_ordenado[indice]
                #2,2 -> El numero anterior al sumarse 1, es igual al "2". False. (Es secuencial)
                no_son_numeros_iguales = parametros_sin_definir_ordenado[indice-1]+1 != parametros_sin_definir_ordenado[indice]
                if not son_numeros_diferentes and no_son_numeros_iguales:
                    parametros_sin_definir_ordenado = []
                    break
        if not len(parametros_sin_definir_ordenado):
            return {"error":"Error cerca de '#' se esperaba una secuencia numerica de parametros, ej: #1,#2,#3"}
        else:
            try:
                int(cantidad_parametros)
            except:
                return {"error":"Error cerca de la cantidad de parametros '#' se esperaba un numero INTEGER."}
            cantidad_parametros = int(cantidad_parametros)
            if len(secuencia_numerica) != cantidad_parametros:
                return {"error":str(cantidad_parametros)+" es diferente a la cantidad de parametros definidos (#) "+str(len(secuencia_numerica))}
            else:
                return True