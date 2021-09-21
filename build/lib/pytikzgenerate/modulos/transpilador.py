import re
from copy import deepcopy
# Librerias propias
from pytikzgenerate.modulos.submodulos.base_pytikz import BasePytikz

class Transpilador(BasePytikz):
    """
    La clase Transpilador se encarga de transpilar codigo TikZ a codigo PyTikZ.
    """
    def tikz_a_pytikz(self,comandos_tikz_depurado):
        """Funcion que retorna codigo depurado del "PyTikZ" en base a codigo depurado del "TikZ" como Array de entrada"""
        comandos_pytikz_depurado = []
        indice = 0
        for comando_tikz in comandos_tikz_depurado:
            nombre_comando = comando_tikz[0]
            if nombre_comando in self.COMANDOS_DIBUJAR_PYTIKZ:
                parametros_comando = comando_tikz[1]
                draw_posicion = comando_tikz[2]
                figuras = comando_tikz[3]
                funcion_de_figura = comando_tikz[4]
                if(len(figuras)):
                    if(figuras[0]=="arc"):
                        comandos_pytikz_depurado.append(self.arco(comando_tikz,draw_posicion,funcion_de_figura))
                    elif(figuras[0] == "rectangle"):
                        comandos_pytikz_depurado.append(self.rectangulo(comando_tikz,draw_posicion))
                    elif(figuras[0] =="circle"):
                        comandos_pytikz_depurado.append(self.circulo(comando_tikz,draw_posicion))
                    elif(figuras[0] =="controls"):
                        comandos_pytikz_depurado.append(self.bezier(comando_tikz))
                    elif(figuras[0] =="--"):
                        comandos_pytikz_depurado.append(self.linea(comando_tikz))
                    elif(figuras[0] == "grid"):
                        comandos_pytikz_depurado.append(comando_tikz)
            elif nombre_comando in self.COMANDOS_VARIABLES_PYTIKZ:
                comandos_pytikz_depurado.append(comando_tikz)
            indice+=1
        return comandos_pytikz_depurado
        
    #Funciones de __tikz_a_pytikz
    def rectangulo(self,comando_tikz,draw_posicion):
        return comando_tikz

    def arco(self,comando_tikz,draw_posicion,funcion_de_figura):
        #Valores TikZ
        x_string,y_string = draw_posicion[0]
        if(len(draw_posicion) > 1):
            angulo_inicial_string,angulo_final_string,radio_string = draw_posicion[1]
        else:
            angulo_inicial_string,angulo_final_string,radio_string = list(funcion_de_figura[1].values())
        #Extraer  valores de x y y, separados de la metrica
        x,x_metrica = self.__extraer_valor_metrica(x_string)
        y,y_metrica = self.__extraer_valor_metrica(y_string)
        angulo_inicial,angulo_inicial_metrica = self.__extraer_valor_metrica(angulo_inicial_string)
        radio,radio_metrica = self.__extraer_valor_metrica(radio_string)
        #Valores PyTikZ
        #1. Modificar el valor de la posicion
        #Los valores indicados en el diccionario "desde_hasta_cm", es lo que se debe de restarle a las posiciones en (X,Y), respectivamente. El valor a restarle depende directamente del angulo inicial.
        desde_hasta_cm = {
            0:[2,1],
            45:[1.7,1.7],
            90:[1,2],
            135:[.3,1.7],
            180:[0,1],
            225:[.3,.3],
            270:[1,0],
            315:[1.7,.3],
            360:[2,1]
        }
        #1.2. Ya teniendo unos rangos lo cual estan indicados en el diccionario "desde_hasta_cm", debemos de sacar los valores a restar que hay entre esos angulos, es decir los valores a restar entre los angulos 0-45, ¿Que valor a restar correpondria al valor 1?, mediante unas operaciones, se saca ese valor teniendo en base los valores ya sabidos del diccionario "desde_hasta_cm".
        #Todos los valores desde el angulo 0 hasta el angulo 360, se guarda en "restar_cm".
        #Se guarda, como llave el numero del angulo y como valor un array de los valores (X,Y) a restar. EJ: Angulo 1 -> {1,[1.993333, 1.015556]}.
        restar_cm = {}
        #Los arrays de "restar_x" y "restar_y" son necesarios para sacar los valores. Debido a que se guardan los valores a restar en "x" o "y" respectivamente en sus arrays, valores que son necesarios utilizar, en especial el ultimo guardado tras cada iteracion para realizar la operacion.
        restar_x = []
        restar_y = []
        for angulo_hasta, restar_x_y in desde_hasta_cm.items():
            if angulo_hasta == 0:
                restar_cm[angulo_hasta] = restar_x_y
                desde_x,desde_y = restar_x_y
                restar_x.append(desde_x)
                restar_y.append(desde_y)
            else:
                index_angulo_desde = list(desde_hasta_cm.keys()).index(angulo_hasta)-1
                angulo_desde = list(desde_hasta_cm.keys())[index_angulo_desde]
                desde_x,desde_y = desde_hasta_cm[angulo_desde]
                hasta_x,hasta_y = desde_hasta_cm[angulo_hasta]
                #Esta operacion, es necesaria realizarla para obtener la cantidad que se debe de restar al valor_a_restar X anterior o valor_a_restar Y anterior. Mirar el Excel, para ver a mas profundidad esta operacion.
                operacion_x,operacion_y = [(desde_x-hasta_x)/45,(desde_y-hasta_y)/45]
                rango_inicial = int(angulo_desde)+1
                rango_final = int(angulo_hasta)+1
                for angulo_entre in range(rango_inicial,rango_final):
                    desde_x = restar_x[len(restar_x)-1]
                    desde_y = restar_y[len(restar_y)-1]
                    restar_x.append(desde_x-operacion_x)
                    restar_y.append(desde_y-operacion_y)
                    restar_cm[angulo_entre] = [restar_x[len(restar_x)-1],restar_y[len(restar_y)-1]]
        angulo_inicial = round(angulo_inicial%360)
        if x_metrica in ["cm",""] and y_metrica in ["cm",""]:
            if angulo_inicial >= 0 or angulo_inicial <= 360:
                restar_x_cm, restar_y_cm = restar_cm[angulo_inicial]
        else:
            restar_x_pt, restar_y_pt = [57,29]
        #1.1. Caso unidad metrica "pt"
        if x_metrica == "pt":
            x -= restar_x_pt
        #1.2. Caso unidad metrica "cm"
        else:
            x_original = deepcopy(x)
            if angulo_inicial == 0:
                x -= restar_x_cm
                #Debe de haber una diferencia del X original y el X, cuya diferencia seria la radio.
                x+= (x_original - x) - radio
                x-=radio
            else:
                if radio==1:
                    x -= restar_x_cm
                else:
                    x -= restar_x_cm*radio


        if y_metrica == "pt":
            y -= restar_y_pt
        else:
            y_original = deepcopy(y)
            if angulo_inicial == 0:
                y -= restar_y_cm
                #Debe de haber una diferencia del Y original y el Y, cuya diferencia seria el resultado de (((1 + radio) - (1 - radio))).
                y+= (y_original - y) - ((1 + radio) - (1 - radio))
                y += radio
            else:
                if radio==1:
                    y -= restar_y_cm
                else:
                    y -= restar_y_cm*radio
        posiciones_pytikz = [format(x,"f")+x_metrica,format(y,"f")+y_metrica]
        #Agregar el array modificado del comando_tikz con valores PyTikZ en el array comandos_pytikz_depurado
        draw_posicion[0] = posiciones_pytikz
        comando_tikz[2] = draw_posicion
        return comando_tikz

    def circulo(self,comando_tikz,draw_posicion):
        #Valores TikZ
        x_string,y_string = draw_posicion[0]
        radio_string = draw_posicion[1]
        #Extraer  valores de x y y, separados de la metrica
        x,x_metrica = self.__extraer_valor_metrica(x_string)
        y,y_metrica = self.__extraer_valor_metrica(y_string)
        radio,radio_metrica = self.__extraer_valor_metrica(radio_string)
        #Valores PyTikZ
        #1. Modificar el valor de la posicion
        restar_posiciones_pt = 30
        restar_posiciones_cm = 1
        #1.1. Caso unidad metrica "pt"
        if x_metrica == "pt":
            x -= restar_posiciones_pt
        #1.2. Caso unidad metrica "cm"
        else:
            x -= restar_posiciones_cm
        if y_metrica == "pt":
            y -= restar_posiciones_pt
        else:
            y -= restar_posiciones_cm
        posiciones_pytikz = [str(x)+x_metrica,str(y)+y_metrica]
        #Agregar el array modificado del comando_tikz con valores PyTikZ en el array comandos_pytikz_depurado
        draw_posicion[0] = posiciones_pytikz
        comando_tikz[2] = draw_posicion
        return comando_tikz

    def bezier(self,comando_tikz):
        return comando_tikz

    def linea(self,comando_tikz):
        return comando_tikz

    #Herramienta de las funciones del __tikz_a_pytikz
    def __extraer_valor_metrica(self,valor_metrica):
        """Extrae el valor y la metrica de un valor_metrica como '10cm'.
        Retorna un array de la siguiente manera [numero,metrica]. Donde el "Numero" tiene el tipo de dato Float, y la "metrica" un tipo de dato String"""
        numero = re.compile(r"[\+\-\*\/]*[0-9.]+")
        numero = numero.search(valor_metrica)
        try:
            numero = float(numero.group())
        except:
            numero = 0.0
        metrica = re.compile(r"[A-z]+")
        metrica = metrica.search(valor_metrica)
        try:
            metrica = metrica.group()
        except:
            metrica = ""
        return [numero,metrica]