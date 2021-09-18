import re
# Librerias propias
from .base_pytikz import BasePytikz
from .validadores import Validadores

class Evaluar(BasePytikz):
    
    def __init__(self):
        self.mensajes_de_error = []

    def resivar_metricas(self,string_numeros,string_tipo_ecuacion=False):
        """Resiva si un string tiene numeros con unidades metricas iguales, un string puede ser una ecuacion como "5pt+5pt" o "5pt,3pt", lo importante es que cada numero con unidad metrica se encuentren separados con una "," (Si es el caso que no sean ecuaciones, si son ecuaciones pueden ser separados mediante el signo de operacion).
        
        En el caso que el String sea una operacion, se debe habilitar el argumento string_tipo_ecuacion.
        
        La funcion retornara un array llamado "numeros_ordenados", que tendra en su interior arrays de cada tipo de unidad metrica es decir. Si escribes un String como "5pt+5pt", obtendras un array de esta forma [["5pt","5pt"]], pero si escribes un String como "5pt+5cm", obtendras un array de esta forma [["5pt"],["5cm"]].
        
        En el caso de que el argumento "string_tipo_ecuacion", este activo. Se retornara ademas del array, el "string_numeros" ya actualizado con las unidades metricas, en los numeros que carecian de uno, con la unidad metrica por defecto "cm". Se retornara un array de esta manera: [string_numeros,numeros_ordenados]. En el caso de que la ecuacion no sea valida, retornara un diccionario, con la key "error" donde se tendra el mensaje del error."""
        numeros_ordenados = []
        numeros_con_metrica = []
        numeros_sin_metrica = re.findall(r" *[0-9.]+[A-z]*",string_numeros)
        #Verificar los numeros que constan de unidad metrica.
        for metrica in self.METRICA_VALIDOS:
            if re.search(metrica,string_numeros):
                numeros = re.findall(r" *[0-9.]+"+metrica,string_numeros)
                for numero_con_metrica in numeros:
                    numeros_con_metrica.append(numero_con_metrica)
        #Verificar los numeros que no constan de unidad metrica.
        for numero_con_metrica in numeros_con_metrica:
            if(numero_con_metrica in numeros_sin_metrica):
                indice_eliminar = numeros_sin_metrica.index(numero_con_metrica)
                del numeros_sin_metrica[indice_eliminar]
        #Se reemplaza los valores sin metrica, con su metrica por defecto que es "cm", en la string_numeros.
        #Sin repetir valores...
        numeros_sin_metrica = list(dict.fromkeys(numeros_sin_metrica))
        #Se separa el string_numeros en un array, donde solo estan los numeros con su unidad metrica.
        numeros_de_string_numeros = re.findall(r" *[0-9.]+[A-z]*",string_numeros)

        for numero_de_string_numeros in numeros_de_string_numeros:
            try:
                index_coincidir_sin_metrica = numeros_sin_metrica.index(numero_de_string_numeros)
            except:
                index_coincidir_sin_metrica = -1
            if index_coincidir_sin_metrica != -1:
                numero_sin_metrica = numeros_sin_metrica[index_coincidir_sin_metrica]
                index_numero_de_string_numeros_sin_metrica = numeros_de_string_numeros.index(numero_sin_metrica)
                numeros_de_string_numeros[index_numero_de_string_numeros_sin_metrica] = numeros_de_string_numeros[index_numero_de_string_numeros_sin_metrica] + "cm"

        if(string_tipo_ecuacion):
            #En el caso de las ecuaciones, se reune los operadores en un array, para luego ser juntada con los numeros, para formar un unico string de ecucacion actualizado.
            operadores_de_string_numeros = re.findall(r" *[\+\-\/\*]",string_numeros)
            #Actualizamos la string_numeros...
            string_numeros = ""
            #Caso de ser: +100pt+0-50-10+20cm
            indice = 0
            if(len(operadores_de_string_numeros) == len(numeros_de_string_numeros)):
                for operador_de_string_numeros in operadores_de_string_numeros:
                    string_numeros+=operador_de_string_numeros+numeros_de_string_numeros[indice]
                    indice+=1
            #Caso de ser: 100pt+0-50-10+20cm	
            elif(len(numeros_de_string_numeros) - 1 == len(operadores_de_string_numeros)):
                for numero_de_string_numeros in numeros_de_string_numeros:
                    if indice == len(operadores_de_string_numeros):
                        string_numeros+=numero_de_string_numeros
                    else:
                        string_numeros+=numero_de_string_numeros+operadores_de_string_numeros[indice]
                    indice+=1
            #Error, la operacion no es valida.
            else:
                return {"error":"Error al evaluar '"+string_numeros+"', no es una operacion valida"}
            # print("string_numeros actualizado")
            # print(string_numeros)
        
        if(string_tipo_ecuacion):
            #Ordenar en un array la string_numeros, todos los numeros tendran una metrica...
            for metrica in self.METRICA_VALIDOS:
                if re.search(metrica,string_numeros):
                    numeros = re.findall(r" *[0-9.]+"+metrica,string_numeros)
                    numeros_ordenados.append(numeros)
            return [string_numeros,numeros_ordenados]
        else:
            string_numeros = ",".join(numeros_de_string_numeros)
            #Ordenar en un array la string_numeros, todos los numeros tendran una metrica...
            for metrica in self.METRICA_VALIDOS:
                if re.search(metrica,string_numeros):
                    numeros = re.findall(r" *[0-9.]+"+metrica,string_numeros)
                    numeros_ordenados.append(numeros)
            return numeros_ordenados
       
    def evaluar_metrica(self,ecuacion,modo_float=False):
        """Evalua un valor tipo String como el siguiente "2cm+2cm". 
        Retorna un String si la operacion es valida con el resultado siguiendo el EJ anterior seria "4cm"
        Si esta activado el "modo_float", retornara un Float con el resultado de la operacion en lugar de un String.
        Retorna un None si no es valido, y la propiedad 'mensajes_de_error' contendra los errores en cuestion.
        """
        ecuacion_validado = self.resivar_metricas(ecuacion,True)
        if isinstance(ecuacion_validado,dict):
            self.mensajes_de_error.append(ecuacion_validado["error"])
            return None
        else:
            ecuacion_validado,numeros_ordenados = ecuacion_validado
        #Las unidades metricas deben de ser del mismo tipo, o en su defecto si no se tiene un tipo evaluar...
        if(len(numeros_ordenados)<=1):
            #Si consta de unidad metrica del mismo tipo, se transformaran a un valor float segun unidad metrica...
            validadores = Validadores()
            for tipo_de_metrica in numeros_ordenados:
                for variable_con_metrica in tipo_de_metrica:
                    numero = validadores.validar_metrica(variable_con_metrica)
                    if(isinstance(numero,float)):
                        ecuacion = ecuacion.replace(variable_con_metrica,str(numero))
                    else:
                        indice = 0
                        for mensaje_de_error_generado in validadores.mensajes_de_error:
                            validadores.mensajes_de_error[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                            indice +=1
                        self.mensajes_de_error.extend(self.validadores.mensajes_de_error)
                        return None
            valor_final = str(eval(ecuacion))
            if not modo_float:
                unidad_metrica_utilizado = list(filter(None,re.findall(r"[A-z]*",numeros_ordenados[0][0])))[0]
                return valor_final+unidad_metrica_utilizado
            else:
                return float(valor_final)
        else:
            self.mensajes_de_error.append("Error al evaluar '"+ecuacion+"', deben de ser del mismo tipo de unidad metrica")
            return None