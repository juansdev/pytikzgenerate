import numpy as np
import re, math
from copy import deepcopy 
from functools import partial
from kivy.uix.widget import Widget
from kivy.properties import ListProperty
from kivy.graphics import Color, Line, Rectangle, Ellipse, InstructionGroup
from kivy.clock import Clock
from bisect import bisect, insort
# Librerias propias
from pytikzgenerate.modulos.submodulos.base_pytikz import BasePytikz
from pytikzgenerate.modulos.submodulos.validadores import Validadores
from pytikzgenerate.modulos.submodulos.validador_pytikz.relleno import Relleno
from pytikzgenerate.modulos.submodulos.validador_pytikz.relleno_lineas_libre import RellenoLineasLibre
from pytikzgenerate.modulos.submodulos.validador_pytikz.guardar_dibujo_en_formato import GuardarDibujoEnImagen
from pytikzgenerate.modulos.submodulos.evaluar import Evaluar
from .transpilador import Transpilador

class ValidadorPytikz(BasePytikz):
    
    def __init__(self,area_de_dibujar):
        self.area_de_dibujar = area_de_dibujar
        self.guardar_dibujo_en_imagen = GuardarDibujoEnImagen(self.area_de_dibujar)
        self.comandos_pytikz_depurado = []
        self.mensajes_de_error = []
        self.estilo_global_local = {}
        self.comandos_global = {}
        #Utilizado para las animaciones
        self.index_animacion = 0
        #Utilizado para identificar que numero de comando segun orden tiene error.
        self.linea_de_comando = 1
        #Instanciar clases modulos.submodulos
        self.evaluar = Evaluar()

    def validar_pytikz(self):
        for comando_pytikz in self.comandos_pytikz_depurado:
            if(len(self.mensajes_de_error)>0):
                error = {"error":self.mensajes_de_error}
                return error
            nombre_comando = comando_pytikz[0]
            if nombre_comando in self.COMANDOS_DIBUJAR_PYTIKZ:
                parametros_comando = comando_pytikz[1]
                draw_posicion = comando_pytikz[2]
                figuras = comando_pytikz[3]
                funcion_de_figura = comando_pytikz[4]
                self.__validar_dibujar(nombre_comando,parametros_comando,draw_posicion,figuras,funcion_de_figura,self.area_de_dibujar)
            elif nombre_comando in self.COMANDOS_VARIABLES_PYTIKZ:
                funcion_de_comando = comando_pytikz[1]
                parametros_comando = comando_pytikz[2]
                self.__validar_variables_tikz(nombre_comando,funcion_de_comando,parametros_comando)
            else:
                self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": El comando '"+nombre_comando+"' no esta registrado en el sistema o no existe.")
            self.linea_de_comando+=1
        if(len(self.mensajes_de_error)>0):
            error = {"error":self.mensajes_de_error}
            return error

    def __validar_dibujar(self,nombre_comando,parametros_comando,draw_posicion,figuras,funcion_de_figura,area_de_dibujar,habilitado_generar_figura_en_formato={}):
        #Estilos predeterminados
        self.degradients = {}
        self.style = {}
        self.fill = (1,1,1) if nombre_comando == "draw" or nombre_comando == "shade" else (0,0,0) if nombre_comando == "fill" else (0,0,0)
        self.draw = (0,0,0) if nombre_comando == "draw" or nombre_comando == "shade" else (1,1,1) if nombre_comando == "fill" else (0,0,0)
        self.tipo_de_linea = ""
        self.line_width = 1.0
        #Estilos sujeto a cambio debido a parametros definidos en comando.
        estilos_predeterminados = {
            "fill":self.fill,
            "draw":self.draw,
            "degradients":self.degradients,
            "tipo_de_linea":self.tipo_de_linea,
            "line_width":self.line_width,
            "style":self.style
        }
        self.validadores = Validadores(estilos_predeterminados)
        indice = 0

        #VALIDA LOS ESTILOS DEL COMANDO, SI TIENE UNIDADES METRICAS VALIDOS LO CONVIERTE A FLOAT, LOS COLORES SON TRANSFORMADOS AL CODIGO DE COLOR QUE MANEJA KIVY.
        for parametro in parametros_comando:
            tupla_validada = False
            diccionario_validada = False
            #Explorar por []
            if indice == 0:
                for estilo in parametro:
                    estilo = estilo.strip()
                    #Si el estilo coincide con el nombre de una variable, utilizar los estilos de esa variable en la figura en cuestion...
                    if estilo in list(self.estilo_global_local.keys()):
                        parametros_estilo_global_local = self.estilo_global_local[estilo]
                        indice_estilo_global_local = 0
                        for parametro_estilo_global_local in parametros_estilo_global_local:
                            #Explorar por []
                            if indice_estilo_global_local == 0:
                                array_estilos_validados = self.validadores.validar_estilos("tupla",parametro_estilo_global_local)
                                mensajes_de_error_generados = array_estilos_validados[len(array_estilos_validados)-1]
                                if not len(mensajes_de_error_generados):
                                    self.degradients = array_estilos_validados[0]
                                    self.fill = array_estilos_validados[1]
                                    self.draw = array_estilos_validados[2]
                                    self.tipo_de_linea = array_estilos_validados[3]
                                    self.line_width = array_estilos_validados[4]
                                    self.style = array_estilos_validados[5]
                                else:
                                    indice = 0
                                    for mensaje_de_error_generado in mensajes_de_error_generados:
                                        mensajes_de_error_generados[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                                    self.mensajes_de_error.extend(mensajes_de_error_generados)
                            #Explorar por {}
                            elif indice_estilo_global_local == 1:
                                #Recorrer keys de {}
                                keys_diccionario = list(parametro_estilo_global_local.keys())
                                array_estilos_validados = self.validadores.validar_estilos("diccionario",keys_diccionario,parametro_estilo_global_local)
                                mensajes_de_error_generados = array_estilos_validados[len(array_estilos_validados)-1]
                                if not len(mensajes_de_error_generados):
                                    self.degradients = array_estilos_validados[0]
                                    self.fill = array_estilos_validados[1]
                                    self.draw = array_estilos_validados[2]
                                    self.tipo_de_linea = array_estilos_validados[3]
                                    self.line_width = array_estilos_validados[4]
                                    self.style = array_estilos_validados[5]
                                else:
                                    indice = 0
                                    for mensaje_de_error_generado in mensajes_de_error_generados:
                                        mensajes_de_error_generados[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                                    self.mensajes_de_error.extend(mensajes_de_error_generados)
                            indice_estilo_global_local+=1
                    #Si no es el caso
                    elif not tupla_validada:
                        array_estilos_validados = self.validadores.validar_estilos("tupla",parametro)
                        mensajes_de_error_generados = array_estilos_validados[len(array_estilos_validados)-1]
                        if not len(mensajes_de_error_generados):
                            self.degradients = array_estilos_validados[0]
                            self.fill = array_estilos_validados[1]
                            self.draw = array_estilos_validados[2]
                            self.tipo_de_linea = array_estilos_validados[3]
                            self.line_width = array_estilos_validados[4]
                            self.style = array_estilos_validados[5]
                        else:
                            indice = 0
                            for mensaje_de_error_generado in mensajes_de_error_generados:
                                mensajes_de_error_generados[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                            self.mensajes_de_error.extend(mensajes_de_error_generados)
                        tupla_validada = True
            #Explorar por {}
            elif indice == 1:
                #Recorrer keys de {}
                keys_diccionario = list(parametro.keys())
                for key in keys_diccionario:
                    key_original = key
                    key = key.strip()
                    #Si se quiere establecer los parametros a una variable global o local, para aplicar luego los estilos de la variable a la figura en cuestion.
                    if key in list(self.estilo_global_local.keys()):
                        # print("DETECTADO ESTILO GLOBAL O LOCAL CON PARAMETROS")
                        # print("key")
                        # print(key)
                        #\draw[estilo global = {red}{solid}] (0,0) rectangle (2.5, 2.5);
                        #{'estilo global ': ' {red}{solid}'}
                        variable_valores_definido = parametro[key_original].strip()
                        variable_valores_definido = [valor for valor in variable_valores_definido.split("}") if valor]
                        variable_valores_definido_limpio = []
                        for e in variable_valores_definido:
                            if e.find("{")!=-1:
                                variable_valores_definido_limpio.append(e[e.find("{")+1::])
                            else:
                                variable_valores_definido_limpio.append(e)
                        variable_valores_definido = variable_valores_definido_limpio
                        variable_valores_indefinidos = self.estilo_global_local[key]
                        key_variable_indefinido = list(variable_valores_indefinidos.keys())[0]
                        parametros_estilo_global_local = variable_valores_indefinidos[key_variable_indefinido]
                        #[[['#2'], {'line width': '1.25pt', 'draw ': ' #1'}], [[], {'estilo global/.default ': '[cyan,dotted]'}]]
                        indice_estilo_global_local = 0
                        indice_estilo_global_local_parametro = 0
                        for parametro_estilo_global_local in parametros_estilo_global_local:
                            indice_estilo_global_local_parametro = 1 if indice_estilo_global_local > 1 else 0
                            indice_estilo_global_local = indice_estilo_global_local if indice_estilo_global_local <2 else 0
                            parametro_estilo_global_local = parametros_estilo_global_local[indice_estilo_global_local_parametro][indice_estilo_global_local]
                            #Solo recorre por [['#2'], {'line width': '1.25pt', 'draw ': ' #1'}]
                            if not indice_estilo_global_local_parametro:
                                #Explorar por []
                                if indice_estilo_global_local == 0:
                                    for key in parametro_estilo_global_local:
                                        key = key.strip()
                                        if key.find("#") != -1:
                                            # print("variable_valores_definido")
                                            # print(variable_valores_definido)
                                            indice = int(key[key.find("#")+1::])-1 #EJ #2 -> 
                                            # print("indice a utilizar en variable_valores_definido")
                                            # print(indice)
                                            try:
                                                estilo = variable_valores_definido[indice] #Red, Solid etc...
                                            except:
                                                #{'estilo global/.default ': '[cyan,5pt]'}
                                                parametro_estilo_global_local_1 = parametros_estilo_global_local[1][1]
                                                str1 = list(parametro_estilo_global_local_1.values())[0]#'[cyan,5pt]'
                                                str2 = str1.replace(']','').replace('[','')
                                                valores_predeterminado = str2.replace('"','').split(",")#['cyan', '5pt']
                                                estilo = valores_predeterminado[indice]
                                                # print("Estilo predeterminado seleccionado "+estilo)
                                            array_estilos_validados = self.validadores.validar_estilos("tupla",estilo)
                                            mensajes_de_error_generados = array_estilos_validados[len(array_estilos_validados)-1]
                                            if not len(mensajes_de_error_generados):
                                                self.degradients = array_estilos_validados[0]
                                                self.fill = array_estilos_validados[1]
                                                self.draw = array_estilos_validados[2]
                                                self.tipo_de_linea = array_estilos_validados[3]
                                                self.line_width = array_estilos_validados[4]
                                                self.style = array_estilos_validados[5]
                                            else:
                                                indice = 0
                                                for mensaje_de_error_generado in mensajes_de_error_generados:
                                                    mensajes_de_error_generados[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                                                self.mensajes_de_error.extend(mensajes_de_error_generados)
                                #Explorar por {}
                                elif indice_estilo_global_local == 1:
                                    #Recorrer keys de {}
                                    values_diccionario = list(parametro_estilo_global_local.values())
                                    indice_key_seleccionado = 0
                                    for value in values_diccionario:
                                        if value.find("#")!=-1:
                                            # print("variable_valores_definido")
                                            # print(variable_valores_definido)
                                            indice = int(value[value.find("#")+1::])-1 #EJ #2 -> 1
                                            # print("indice a utilizar en variable_valores_definido")
                                            # print(indice)
                                            try:
                                                estilo = variable_valores_definido[indice] #Red, Solid etc...
                                            except:
                                                #{'estilo global/.default ': '[cyan,5pt]'}
                                                parametro_estilo_global_local_1 = parametros_estilo_global_local[1][1]
                                                str1 = list(parametro_estilo_global_local_1.values())[0]#'[cyan,5pt]'
                                                str2 = str1.replace(']','').replace('[','')
                                                valores_predeterminado = str1.replace('"','').split(",")#['cyan', '5pt']
                                                estilo = valores_predeterminado[indice]
                                                # print("Estilo predeterminado seleccionado "+estilo)
                                            indice_key = 0
                                            for key in list(parametro_estilo_global_local.keys()):
                                                if indice_key == indice_key_seleccionado:
                                                    key = key.strip()
                                                    array_estilos_validados = self.validadores.validar_estilos("diccionario",key,estilo)
                                                    mensajes_de_error_generados = array_estilos_validados[len(array_estilos_validados)-1]
                                                    if not len(mensajes_de_error_generados):
                                                        self.degradients = array_estilos_validados[0]
                                                        self.fill = array_estilos_validados[1]
                                                        self.draw = array_estilos_validados[2]
                                                        self.tipo_de_linea = array_estilos_validados[3]
                                                        self.line_width = array_estilos_validados[4]
                                                        self.style = array_estilos_validados[5]
                                                    else:
                                                        indice = 0
                                                        for mensaje_de_error_generado in mensajes_de_error_generados:
                                                            mensajes_de_error_generados[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                                                        self.mensajes_de_error.extend(mensajes_de_error_generados)
                                                indice_key+=1
                                        indice_key_seleccionado+=1
                            else:
                                break
                            indice_estilo_global_local+=1
                    #Si no es el caso...
                    elif not diccionario_validada:
                        #Codigos COLOR
                        keys_color = [estilo_global for estilo_global in self.estilo_global_local.keys()]
                        keys_color_invocados = list(parametro.values())
                        # print("Colores globales existentes")
                        # print(keys_color)
                        # print("Parametros establecidos")
                        # print(keys_color_invocados)
                        #Si el comando tiene estilos con codigos RGB..
                        if True in np.in1d(keys_color_invocados,keys_color):
                            index_keys_color = []
                            for index,value in enumerate(keys_color):
                                if value in keys_color_invocados:
                                    index_keys_color.append(index)
                            # print("Index donde el Color fue invocado...")
                            # print(index_keys_color)
                            keys_color_invocados = []
                            codigos_color_invocados = []
                            for index,value in enumerate(self.estilo_global_local.values()):
                                if index in index_keys_color:
                                    keys_color_invocados.append(keys_color[index])
                                    codigos_color_invocados.append(value)
                            codigos_color = [codigo_color for codigo_color in codigos_color_invocados]
                            #Si existe codigos rgb...
                            codigos_rgb = [{index:list(color[1].values())[0]} for index,color in enumerate(codigos_color) if list(color[1].keys())[0].find("RGB") != -1]
                            # print(codigos_rgb)
                            # print("Antes de actualizar")
                            # print(parametro)
                            i = 0
                            for key in parametro:
                                if parametro[key] in keys_color:
                                    #Corresponde a un valor RGB?
                                    for codigo in codigos_rgb:
                                        if list(codigo.keys())[0] == i:
                                            for k in parametro:
                                                if parametro[k] == keys_color_invocados[i]:
                                                    # print("La key...")
                                                    # print(parametro[k])
                                                    # print("Corresponde a un codigo RGB, en el Index: ",i)
                                                    # print(list(codigo.values())[0])
                                                    parametro[k] = list(codigo.values())[0]
                                    i+=1
                        array_estilos_validados = self.validadores.validar_estilos("diccionario",keys_diccionario,parametro)
                        mensajes_de_error_generados = array_estilos_validados[len(array_estilos_validados)-1]
                        if not len(mensajes_de_error_generados):
                            self.degradients = array_estilos_validados[0]
                            self.fill = array_estilos_validados[1]
                            self.draw = array_estilos_validados[2]
                            self.tipo_de_linea = array_estilos_validados[3]
                            self.line_width = array_estilos_validados[4]
                            self.style = array_estilos_validados[5]
                        else:
                            indice = 0
                            for mensaje_de_error_generado in mensajes_de_error_generados:
                                mensajes_de_error_generados[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                            self.mensajes_de_error.extend(mensajes_de_error_generados)
                        diccionario_validada = True
            indice+=1

        #VALIDAR - FIGURA SIN PARAMETROS
        if(len(funcion_de_figura[0]) == 0 and len(list(funcion_de_figura[1].keys())) == 0):
            if not len(self.mensajes_de_error):
                for figura in figuras:
                    #Dibujar rectangulo
                    #\draw[color=black] (10pt,10pt) rectangle (100pt,100pt); WORKS.
                    #\draw[color=black] (100pt,100pt) rectangle (10pt,10pt); WORKS. Y es lo mismo que lo anterior.
                    #\draw[color=black] (100pt,10pt) rectangle (100pt,100pt); WORKS.
                    if(figura=="rectangle"):
                        punto_inicial_x_y = self.validadores.validar_metrica(draw_posicion[0][0])
                        punto_final_x_y = self.validadores.validar_metrica(draw_posicion[0][1])
                        ancho = self.validadores.validar_metrica(draw_posicion[1][0])
                        alto = self.validadores.validar_metrica(draw_posicion[1][1])
                        #Si ocurre un error de validacion...
                        if(isinstance(punto_inicial_x_y,list) or isinstance(punto_final_x_y,list) or isinstance(ancho,list) or isinstance(alto,list)):
                            indice = 0
                            for mensaje_de_error_generado in self.validadores.mensajes_de_error:
                                self.validadores.mensajes_de_error[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                                indice += 1
                            self.mensajes_de_error.extend(self.validadores.mensajes_de_error)
                        #Si todo esta correcto...
                        else:
                            if punto_inicial_x_y >= ancho:
                                punto_inicial_x_y_original = deepcopy(punto_inicial_x_y)
                                punto_inicial_x_y = deepcopy(ancho)
                                ancho = punto_inicial_x_y_original - ancho
                            else:
                                ancho = ancho - punto_inicial_x_y
                            if punto_final_x_y >= alto:
                                punto_final_x_y_original = deepcopy(punto_final_x_y)
                                punto_final_x_y = deepcopy(alto)
                                alto = punto_final_x_y_original - alto
                            else:
                                alto = alto - punto_final_x_y
                            rectangulo_dibujado_lineas = [punto_inicial_x_y, punto_final_x_y, punto_inicial_x_y, punto_final_x_y+alto, punto_inicial_x_y+ancho, punto_final_x_y+alto, punto_inicial_x_y+ancho, punto_final_x_y, punto_inicial_x_y, punto_final_x_y]
                            #Dibujar contenido rectangulo
                            #DEGRADADO RECTANGULO
                            if self.degradients:
                                Relleno(area_de_dibujar,figura,self.degradients,(punto_inicial_x_y,punto_final_x_y),(ancho,alto),habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                            #RELLENO RECTANGULO
                            else:
                                if not habilitado_generar_figura_en_formato:
                                    figura = InstructionGroup()
                                    figura.add(Color(self.fill[0], self.fill[1], self.fill[2]))
                                    figura.add(Rectangle(pos=(punto_inicial_x_y,punto_final_x_y),size=(ancho,alto)))
                                    area_de_dibujar.canvas.add(figura)
                                else:
                                    self.guardar_dibujo_en_imagen.figura_a_png(habilitado_generar_figura_en_formato["generar_dibujo_en_formato"],"rectangle",(ancho,alto),(punto_inicial_x_y,punto_final_x_y),(self.fill[0], self.fill[1], self.fill[2]),self.tipo_de_linea,rectangulo_dibujado_lineas,(self.draw[0], self.draw[1], self.draw[2]),self.line_width)
                            #Dibujar borde rectangulo
                            #Si hay separacion de lineas...
                            if self.tipo_de_linea:
                                if not habilitado_generar_figura_en_formato:
                                    figura = InstructionGroup()
                                    figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                    figura.add(Line(points=rectangulo_dibujado_lineas, dash_offset=10, dash_length=5))
                                    area_de_dibujar.canvas.add(figura)
                            #Si no hay...
                            else:
                                if not habilitado_generar_figura_en_formato:
                                    figura = InstructionGroup()
                                    figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                    figura.add(Line(points=rectangulo_dibujado_lineas,width=self.line_width))
                                    area_de_dibujar.canvas.add(figura)
                    #DIBUJAR ARCO
                    #\draw[color=ColorA,line width=0.1cm,rounded corners=2ex] (100,100) arc (0:90:5cm);
                    elif(figura=="arc"):
                        
                        posicion_x = None
                        posicion_y = None
                        indice_angulo_inicial_final_radio = None
                        indice = 0

                        for posicion in draw_posicion:
                            if type(posicion) is list and len(posicion) == 2:
                                #Si las posiciones de origen se rigen segun dos valores (X,Y)
                                posicion_x = self.validadores.validar_metrica(draw_posicion[indice][0])
                                posicion_y = self.validadores.validar_metrica(draw_posicion[indice][1])
                            #Indice del angulo inicial, angulo final, y radio del Arc...
                            elif type(posicion) is list and len(posicion)==3:
                                if indice_angulo_inicial_final_radio == None:
                                    indice_angulo_inicial_final_radio = deepcopy(indice)
                                    radio = self.validadores.validar_metrica(draw_posicion[indice_angulo_inicial_final_radio][2])
                            indice+=1

                        #Si ocurre un error de validacion...
                        if(isinstance(posicion_x,list) or isinstance(posicion_y,list) or isinstance(radio,list)):
                            indice = 0
                            for mensaje_de_error_generado in self.validadores.mensajes_de_error:
                                self.validadores.mensajes_de_error[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                                indice += 1
                            self.mensajes_de_error.extend(self.validadores.mensajes_de_error)
                        else:
                            #Si existe un posicion_x, posicion_y y radio
                            if(posicion_x != None and posicion_y != None and indice_angulo_inicial_final_radio != None):
                                angulo_inicial = float(450) if float(draw_posicion[indice_angulo_inicial_final_radio][0]) == 0.0 else float(450-(float(draw_posicion[indice_angulo_inicial_final_radio][0])))
                                angulo_final = float(450) if float(draw_posicion[indice_angulo_inicial_final_radio][1]) == 0.0 else float(450-(float(draw_posicion[indice_angulo_inicial_final_radio][1])))
                                #Eliminar parametro Arc utilizado
                                self.angulo_final_arc = draw_posicion[indice_angulo_inicial_final_radio][1]
                                self.longitud_arc = radio
                                del draw_posicion[indice_angulo_inicial_final_radio:indice_angulo_inicial_final_radio+1]
                                #DIBUJAR CONTENIDO ARC
                                #Si aplica relleno o degradado...
                                if self.fill != (1,1,1) or self.degradients:
                                    if self.degradients:
                                        #Aplicar degradado a la figura...
                                        Relleno(area_de_dibujar,figura,self.degradients,(posicion_x,posicion_y),(radio*2,radio*2),angulo_inicial, angulo_final,habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                                    else:
                                        #Aplicar relleno a la figura...
                                        if not habilitado_generar_figura_en_formato:
                                            figura = InstructionGroup()
                                            figura.add(Color(self.fill[0],self.fill[1],self.fill[2]))
                                            figura.add(Ellipse(pos=(posicion_x,posicion_y),size=(radio*2,radio*2),angle_start=angulo_inicial, angle_end=angulo_final))
                                            area_de_dibujar.canvas.add(figura)
                                        else:
                                            self.guardar_dibujo_en_imagen.figura_a_png(habilitado_generar_figura_en_formato["generar_dibujo_en_formato"],"arc",(radio*2,radio*2),(posicion_x,posicion_y),(self.fill[0], self.fill[1], self.fill[2]),self.tipo_de_linea,[posicion_x,posicion_y,radio,angulo_inicial,angulo_final],(self.draw[0], self.draw[1], self.draw[2]),self.line_width,angle_start=angulo_inicial, angle_end=angulo_final)
                                posicion_x+=radio
                                posicion_y+=radio
                                #DIBUJAR ARC
                                #ARCO CON LINEAS DISCONTINUADAS
                                if self.tipo_de_linea:
                                    if not habilitado_generar_figura_en_formato:
                                        figura = InstructionGroup()
                                        figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                        figura.add(Line(circle=[posicion_x,posicion_y,radio,angulo_inicial,angulo_final], dash_offset=10, dash_length=5))
                                        area_de_dibujar.canvas.add(figura)
                                #Si no hay...
                                #ARCO SIN LINEAS DISCONTINUADAS
                                else:
                                    if not habilitado_generar_figura_en_formato:
                                        figura = InstructionGroup()
                                        figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                        figura.add(Line(circle=[posicion_x,posicion_y,radio,angulo_inicial,angulo_final],width=self.line_width))
                                        area_de_dibujar.canvas.add(figura)
                            else:
                                if(posicion_x == None or posicion_y == None):
                                    self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Se esperaba posiciones de Origen y de Destino")
                                else:
                                    self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Se esperaba Angulo de Inicio, Final y de Radio")
                    
                    #DIBUJAR CIRCULO
                    #\draw[draw=red,fill=yellow] (0,0) circle (1cm);
                    elif(figura=="circle"):
                        posicion_x = self.validadores.validar_metrica(draw_posicion[0][0])
                        posicion_y = self.validadores.validar_metrica(draw_posicion[0][1])
                        posiciones_validas = True
                        try:
                            radio = self.validadores.validar_metrica(draw_posicion[1])
                        except:
                            self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Error cerca de "+figura+" se esperaba un valor de Radio o de posicion X y Y validos.")
                            posiciones_validas = False
                        #Si ocurre un error de validacion...
                        if(isinstance(posicion_x,list) or isinstance(posicion_y,list) or isinstance(radio,list)):
                            indice = 0
                            for mensaje_de_error_generado in self.validadores.mensajes_de_error:
                                self.validadores.mensajes_de_error[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                                indice += 1
                            self.mensajes_de_error.extend(self.validadores.mensajes_de_error)
                            posiciones_validas = False
                        #Line:
                        # circle: (60,60,60,90,180)#CIRCULO CERRADO, 40 DE RADIO
                        if posiciones_validas:
                            #DIBUJAR CONTENIDO CIRCULO
                            ancho = radio*2
                            alto = radio*2
                            if self.degradients:
                                #APLICAR DEGRADADO AL CIRCULO
                                Relleno(area_de_dibujar,figura,self.degradients,(posicion_x,posicion_y),(ancho,alto),habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                            else:
                                #RELLENO CIRCULO
                                if not habilitado_generar_figura_en_formato:
                                    figura = InstructionGroup()
                                    figura.add(Color(self.fill[0], self.fill[1], self.fill[2]))
                                    figura.add(Ellipse(pos=(posicion_x,posicion_y),size=(ancho,alto)))
                                    area_de_dibujar.canvas.add(figura)
                                else:
                                    self.guardar_dibujo_en_imagen.figura_a_png(habilitado_generar_figura_en_formato["generar_dibujo_en_formato"],"circle",(ancho,alto),(posicion_x,posicion_y),(self.fill[0], self.fill[1], self.fill[2]),self.tipo_de_linea,[posicion_x,posicion_y,radio],(self.draw[0], self.draw[1], self.draw[2]),self.line_width)
                            #DIBUJAR BORDE CIRCULO
                            posicion_x+=radio
                            posicion_y+=radio
                            if self.tipo_de_linea:
                                if not habilitado_generar_figura_en_formato:
                                    figura = InstructionGroup()
                                    figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                    figura.add(Line(circle=[posicion_x,posicion_y,radio], dash_offset=10, dash_length=self.line_width))
                                    area_de_dibujar.canvas.add(figura)
                            #Si no hay...
                            else:
                                if not habilitado_generar_figura_en_formato:
                                    figura = InstructionGroup()
                                    figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                    figura.add(Line(circle=[posicion_x,posicion_y,radio], width=self.line_width))
                                    area_de_dibujar.canvas.add(figura)
                    #DIBUJAR LINEAS BEZIER
                    #\draw[left color=yellow, bottom color=orange, right color=red,rounded] (0,100) .. controls (100,200) and (200,300) .. (300,400) .. (200,100) .. (300,200);
                    elif(figura=="controls"):
                        #Estas variables son necesarias para reunir coordenadas
                        coordenadas = []
                        #Extraer figura del array "figuras"
                        indice = 0
                        figuras_control = []
                        for figura in figuras:
                            if figura == "controls":
                                figuras_control.append(figura)
                        posiciones_controls = 0
                        
                        #Estas variables son necesarias cuando se trabaja con mas de 1 controls.
                        cantidad_de_posiciones_valido = False
                        conjunto_de_coordenadas = []

                        for posicion in draw_posicion:
                            coordenadas_x1y1_a_validar = None
                            coordenadas_x2y2_a_validar = None
                            if len(figuras_control)>1:
                                #Maximo-Minimo 3 posiciones
                                #Avanzando hacia el siguiente control (Termina en 4, luego inicia en 0 hasta 3, y pasa al proximo control en 4)...
                                if (posiciones_controls == 4):
                                    conjunto_de_coordenadas.append(coordenadas)
                                    coordenadas = []
                                    posiciones_controls = 0
                                    cantidad_de_posiciones_valido = True
                                if(posiciones_controls < 4):
                                    #Posiciones Control
                                    if(posiciones_controls == 0) and len(conjunto_de_coordenadas):
                                        ultimo_conjunto_de_coordenadas = conjunto_de_coordenadas[len(conjunto_de_coordenadas)-1]
                                        posicion_x_anterior = ultimo_conjunto_de_coordenadas[len(ultimo_conjunto_de_coordenadas)-2]
                                        posicion_y_anterior = ultimo_conjunto_de_coordenadas[len(ultimo_conjunto_de_coordenadas)-1]
                                        coordenadas.append(posicion_x_anterior)
                                        coordenadas.append(posicion_y_anterior)
                                    coordenadas_x1y1_a_validar = self.validadores.validar_metrica(posicion[0])
                                    coordenadas_x2y2_a_validar = self.validadores.validar_metrica(posicion[1])
                                posiciones_controls+=1
                            else:
                                #Solo hay un control...
                                #Posiciones Control
                                coordenadas_x1y1_a_validar = self.validadores.validar_metrica(posicion[0])
                                coordenadas_x2y2_a_validar = self.validadores.validar_metrica(posicion[1])
                            if(coordenadas_x1y1_a_validar != None and coordenadas_x2y2_a_validar != None):
                                #Si ocurre un error de validacion...
                                if(isinstance(coordenadas_x1y1_a_validar,list) or isinstance(coordenadas_x2y2_a_validar,list)):
                                    coordenadas = []
                                    conjunto_de_coordenadas = []
                                    break
                                else:
                                    coordenadas.append(coordenadas_x1y1_a_validar)
                                    coordenadas.append(coordenadas_x2y2_a_validar)
                            indice += 1
                        
                        #Añadir las ultimas posiciones del ultimo control
                        if(cantidad_de_posiciones_valido):
                            if(posiciones_controls == 3):
                                conjunto_de_coordenadas.append(coordenadas)
                            else:
                                cantidad_de_posiciones_valido = False
                            coordenadas = []
                        
                        #Eliminar figuras Controls (Si hay mas de uno)
                        if len(figuras_control)>1:
                            while(True):
                                try:
                                    index_control = figuras.index("controls")
                                except:
                                    break
                                del figuras[index_control]
                        
                        if len(coordenadas)>=4 or len(conjunto_de_coordenadas) > 1:
                            if not habilitado_generar_figura_en_formato:
                                #Dibujar en el area de dibujado...
                                indice = 0
                                es_conjunto_de_coordenadas = True
                                while(es_conjunto_de_coordenadas):
                                    if indice < len(conjunto_de_coordenadas):
                                        coordenadas = conjunto_de_coordenadas[indice]
                                    else:
                                        es_conjunto_de_coordenadas = False
                                    #Si hay separacion de lineas...
                                    if self.tipo_de_linea:
                                        figura = InstructionGroup()
                                        figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                        figura.add(Line(bezier=coordenadas, dash_offset=10, dash_length=5))
                                        area_de_dibujar.canvas.add(figura)
                                    #Si no hay...
                                    else:
                                        figura = InstructionGroup()
                                        figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                        figura.add(Line(bezier=coordenadas, width=self.line_width))
                                        area_de_dibujar.canvas.add(figura)
                                    indice+=1
   
                        else:
                            if(not cantidad_de_posiciones_valido):
                                self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Se esperaba 3 posiciones por 'controls' (Sin contar posicion inicial).")
                            #Si ocurre un error de validacion...
                            elif(isinstance(coordenadas_x1y1_a_validar,list) or isinstance(coordenadas_x2y2_a_validar,list)):
                                indice = 0
                                for mensaje_de_error_generado in self.validadores.mensajes_de_error:
                                    self.validadores.mensajes_de_error[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                                    indice += 1
                                self.mensajes_de_error.extend(self.validadores.mensajes_de_error)
                            else:    
                                self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Error cerca de "+str(coordenadas[len(coordenadas)-1])+" se esperaba posiciones de Origen y de Destino")
                    #Si hay figura (--)...
                    #\draw[line width= 1.5pt, fill = yellow, draw  = black](100,100) -- (200,0) -- (50,300) -- (40,200) -- cycle;
                    elif(figura=="--"):
                        coordenadas = []
                        draw_posicion_valido = []
                        
                        for posicion in draw_posicion:
                            if type(posicion) is list and len(posicion) == 2:
                                draw_posicion_valido.append(posicion)
                        
                        indice = 0
                        for posicion in draw_posicion_valido:
                            coordenadas_x_a_validar = None
                            coordenadas_y_a_validar = None
                            if posicion != "cycle":
                                coordenadas_x_a_validar = self.validadores.validar_metrica(posicion[0])
                                coordenadas_y_a_validar = self.validadores.validar_metrica(posicion[1])
                            #Si es Cycle...
                            else:
                                if posicion=="cycle":
                                    #HASTA COORDENADA ORIGEN X,Y
                                    coordenadas.append(coordenadas[0])
                                    coordenadas.append(coordenadas[1])
                            if(coordenadas_x_a_validar != None and coordenadas_y_a_validar != None):
                                #Si ocurre un error de validacion...
                                if(isinstance(coordenadas_x_a_validar,list) or isinstance(coordenadas_y_a_validar,list)):
                                    indice = 0
                                    for mensaje_de_error_generado in self.validadores.mensajes_de_error:
                                        self.validadores.mensajes_de_error[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                                        indice += 1
                                    self.mensajes_de_error.extend(self.validadores.mensajes_de_error)
                                    break
                                else:
                                    coordenadas.append(coordenadas_x_a_validar)
                                    coordenadas.append(coordenadas_y_a_validar)
                            indice+=1
                        if not len(self.mensajes_de_error):
                            if len(coordenadas)>=4:
                                # print("coordenadas")
                                # print(coordenadas)
                                #DIBUJAR LINEAS CON CONTENIDO
                                #Si aplica relleno o degradado...
                                if self.fill != (1,1,1) or self.degradients:
                                    if self.fill != (1,1,1):
                                        #Crear Imagen con relleno y aplicarlo en el Source de un Rectangle para luego dibujarlo en el Area_de_dibujar
                                        RellenoLineasLibre(area_de_dibujar,coordenadas,self.fill,habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                                    else:
                                        RellenoLineasLibre(area_de_dibujar,coordenadas,self.degradients,False,True,habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                                #DIBUJAR LINEAS
                                #Si hay separacion de lineas...
                                if self.tipo_de_linea:
                                    if not habilitado_generar_figura_en_formato:
                                        figura = InstructionGroup()
                                        figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                        figura.add(Line(points=coordenadas, dash_offset=10, dash_length=5))
                                        area_de_dibujar.canvas.add(figura)
                                #Si no hay...
                                else:
                                    if not habilitado_generar_figura_en_formato:
                                        figura = InstructionGroup()
                                        figura.add(Color(self.draw[0], self.draw[1],self.draw[2]))
                                        figura.add(Line(points=coordenadas, width=self.line_width))
                                        area_de_dibujar.canvas.add(figura)
                            else:
                                self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Error cerca de "+str(coordenadas[len(coordenadas)-1])+" se esperaba posiciones de Origen y de Destino")
                    #Si hay figura (grid)...
                    #\draw[style=help lines] (0,0) grid (21,29.7);
                    elif(figura=="grid"):
                        coordenadas = []
                        draw_posicion_valido = []
                        
                        #Validar las posiciones, solo aceptan de esta manera: [21,29.7] (Valores varian), las posiciones se redondean a la unidad inferior.
                        for conjunto_de_posiciones in draw_posicion:
                            if type(conjunto_de_posiciones) is list and len(conjunto_de_posiciones) == 2:
                                posiciones_validas = [self.validadores.validar_metrica(posicion) for posicion in conjunto_de_posiciones]
                                posiciones_invalidas = [posicion for posicion in posiciones_validas if isinstance(posicion,list)]
                                if not len(posiciones_invalidas):
                                    posiciones_con_cm = [posicion for posicion in conjunto_de_posiciones if posicion.find("pt") == -1]
                                    posiciones_con_pt = [self.validadores.validar_metrica(posicion) for posicion in conjunto_de_posiciones if posicion.find("pt") != -1]
                                    # print("posiciones_con_cm")
                                    # print(posiciones_con_cm)
                                    # print("posiciones_con_pt")
                                    # print(posiciones_con_pt)
                                    conjunto_de_posiciones = list(map(lambda x: x.replace("cm",""), posiciones_con_cm))+posiciones_con_pt
                                    conjunto_de_posiciones = [str(math.floor(float(posicion))) for posicion in conjunto_de_posiciones]
                                    draw_posicion_valido.append(conjunto_de_posiciones)
                                else:
                                    for indice,mensaje_de_error_generado in enumerate(self.validadores.mensajes_de_error,0):
                                        self.validadores.mensajes_de_error[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado    
                                    self.mensajes_de_error.extend(self.validadores.mensajes_de_error)
                                    break
                        
                        #Añadir las posiciones al array de coordenadas, si su unidad metrica es valida y se guarda como float.
                        if not len(self.mensajes_de_error):
                            # print("draw_posicion_valido")
                            # print(draw_posicion_valido)
                            for indice,posicion in enumerate(draw_posicion_valido,0):
                                coordenadas_x_a_validar = None
                                coordenadas_y_a_validar = None
                                coordenadas_x_a_validar = self.validadores.validar_metrica(posicion[0])
                                coordenadas_y_a_validar = self.validadores.validar_metrica(posicion[1])
                                if(coordenadas_x_a_validar != None and coordenadas_y_a_validar != None):
                                    #Si ocurre un error de validacion...
                                    if(isinstance(coordenadas_x_a_validar,list) or isinstance(coordenadas_y_a_validar,list)):
                                        indice = 0
                                        for mensaje_de_error_generado in self.validadores.mensajes_de_error:
                                            self.validadores.mensajes_de_error[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                                            indice += 1
                                        self.mensajes_de_error.extend(self.validadores.mensajes_de_error)
                                        break
                                    else:
                                        coordenadas.append(coordenadas_x_a_validar)
                                        coordenadas.append(coordenadas_y_a_validar)
                                        if(len(coordenadas) == 2):
                                            unidad_metrica_desde_x = posicion[0]
                                            unidad_metrica_desde_y = posicion[1]
                                        if(len(coordenadas) == 4):
                                            unidad_metrica_hasta_y = posicion[1]
                                            string_unidades_metricas = str(unidad_metrica_desde_y)+","+str(unidad_metrica_hasta_y)
                                            numeros_ordenados = self.evaluar.resivar_metricas(string_unidades_metricas)
                                            unidades_metricas_desde_hasta_y_validas = False
                                            if(len(numeros_ordenados)<=1):
                                                unidades_metricas_desde_hasta_y_validas = True
                                                unidad_metrica_utilizado = list(filter(None,re.findall(r"[A-z]*",numeros_ordenados[0][0])))[0]
                            
                            if not len(self.mensajes_de_error):
                                #Las coordenadas deben de ser si o si 4 en longitud (X1,X2)(Y1,Y2)
                                if len(coordenadas)==4:
                                    if unidades_metricas_desde_hasta_y_validas:
                                        #Coordenadas (X1,Y1,X2,Y2) iniciales...
                                        desde_x,desde_y,hasta_x,hasta_y = coordenadas
                                        #1. Empezar dibujando los renglones horizontales...
                                        coordenadas = [desde_x,desde_y,hasta_x,desde_y]
                                        renglones_horizontales_verticales = [coordenadas]
                                        #1.1. Se actualizaran las coordendas, partiendo desde las coordenadas Y, se iran sumando de 1 en 1 hasta alcanzar las coordanadas hasta Y.
                                        desde_y_subir = self.evaluar.evaluar_metrica(unidad_metrica_desde_y,True)
                                        step = self.validadores.validar_metrica("1"+unidad_metrica_utilizado)
                                        hasta_y_destino=hasta_y + step
                                        coordenadas = []
                                        for y_up in np.arange(desde_y_subir,hasta_y_destino,step):
                                            coordenadas_x1 = desde_x
                                            coordenadas_y1 = desde_y_subir+y_up
                                            coordenadas_x2 = hasta_x
                                            coordenadas_y2 = desde_y_subir+y_up
                                            coordenadas.append(coordenadas_x1)
                                            coordenadas.append(coordenadas_y1)
                                            coordenadas.append(coordenadas_x2)
                                            coordenadas.append(coordenadas_y2)
                                            #1.2. Añadir coordenadas a renglones_horizontales_verticales, despues limpiarlo para el siguiente renglon
                                            renglones_horizontales_verticales.append(coordenadas)
                                            coordenadas = []
                                        
                                        #2. Luego dibujar los renglones verticales...
                                        coordenadas = [desde_x,desde_y,desde_x,hasta_y]
                                        renglones_horizontales_verticales.append(coordenadas)
                                        #2.1. Se actualizaran las coordendas, partiendo desde las coordenadas X, se iran sumando de 1 en 1 hasta alcanzar las coordanadas hasta X.
                                        desde_x_derecha = self.evaluar.evaluar_metrica(unidad_metrica_desde_x,True)
                                        step = self.validadores.validar_metrica("1"+unidad_metrica_utilizado)
                                        hasta_x_destino=hasta_x + step
                                        coordenadas = []
                                        for x_right in np.arange(desde_x_derecha,hasta_x_destino,step):
                                            coordenadas_x1 = desde_x_derecha+x_right
                                            coordenadas_y1 = desde_y
                                            coordenadas_x2 = desde_x_derecha+x_right
                                            coordenadas_y2 = hasta_y
                                            coordenadas.append(coordenadas_x1)
                                            coordenadas.append(coordenadas_y1)
                                            coordenadas.append(coordenadas_x2)
                                            coordenadas.append(coordenadas_y2)
                                            #2.2. Añadir coordenadas a renglones_horizontales_verticales, despues limpiarlo para el siguiente renglon
                                            renglones_horizontales_verticales.append(coordenadas)
                                            coordenadas = []

                                        #Antes de dibujar, actualizar valores de los estilos, si hay un estilo predeterminado definido.
                                        if self.style:
                                            for _, conjunto_de_estilos in self.style.items():
                                                nombres_estilos = list(conjunto_de_estilos.keys())
                                                for nombre_estilo in nombres_estilos:
                                                    if nombre_estilo == "degradients":
                                                        self.degradients = conjunto_de_estilos[nombre_estilo]
                                                    if nombre_estilo == "fill":
                                                        self.fill = conjunto_de_estilos[nombre_estilo]
                                                    if nombre_estilo == "draw":
                                                        self.draw = conjunto_de_estilos[nombre_estilo]
                                                    if nombre_estilo == "tipo_de_linea":
                                                        self.tipo_de_linea = conjunto_de_estilos[nombre_estilo]
                                                    if nombre_estilo == "line_width":
                                                        self.line_width = conjunto_de_estilos[nombre_estilo]
                                        for coordenadas in renglones_horizontales_verticales:
                                            #DIBUJAR LINEAS CON CONTENIDO
                                            #Si aplica relleno o degradado...
                                            if self.fill != (1,1,1) or self.degradients:
                                                if self.fill != (1,1,1):
                                                    #Crear Imagen con relleno y aplicarlo en el Source de un Rectangle para luego dibujarlo en el Area_de_dibujar
                                                    RellenoLineasLibre(area_de_dibujar,coordenadas,self.fill,habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                                                else:
                                                    RellenoLineasLibre(area_de_dibujar,coordenadas,self.degradients,False,True,habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                                            #DIBUJAR LINEAS
                                            #Si hay separacion de lineas...
                                            if self.tipo_de_linea:
                                                if not habilitado_generar_figura_en_formato:
                                                    figura = InstructionGroup()
                                                    figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                                    figura.add(Line(points=coordenadas, dash_offset=10, dash_length=5))
                                                    area_de_dibujar.canvas.add(figura)
                                            #Si no hay...
                                            else:
                                                if not habilitado_generar_figura_en_formato:
                                                    figura = InstructionGroup()
                                                    figura.add(Color(self.draw[0], self.draw[1],self.draw[2]))
                                                    figura.add(Line(points=coordenadas, width=self.line_width))
                                                    area_de_dibujar.canvas.add(figura)
                                    else:
                                        self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Error cerca de "+str(coordenadas[len(coordenadas)-1])+" se esperaba que las coordenadas Y1 y Y2 utilicen la misma unidad metrica.")
                                else:
                                    self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Error cerca de "+str(coordenadas[len(coordenadas)-1])+" se esperaba solo 4 coordenadas.")
                    #No tiene figura
                    else:
                        self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Error el comando PyTikZ '"+nombre_comando+"' no tiene una figura valida.")
                
        #VALIDAR - FIGURA CON PARAMETROS
        else:
            if not len(self.mensajes_de_error):
                for figura in figuras:
                    #DIBUJAR ARCO
                    #\draw[bottom color=cyan!60!black, top color=red, middle color = blue!20!white] (100,100) arc[start angle=0, end angle=90, radius=5cm];
                    if(figura=="arc"):
            
                        posicion_x = self.validadores.validar_metrica(draw_posicion[0][0])
                        posicion_y = self.validadores.validar_metrica(draw_posicion[0][1])
                        diccionario_funcion_figura = {}
                        for key in list(funcion_de_figura[1].keys()):
                            key_nueva = key.strip()
                            diccionario_funcion_figura[key_nueva] = funcion_de_figura[1][key]
                        radius = diccionario_funcion_figura["radius"] if "radius" in list(diccionario_funcion_figura.keys()) else "10.0"
                        radio = self.validadores.validar_metrica(radius)
                        #Si ocurre un error de validacion...
                        if(isinstance(posicion_x,list) or isinstance(posicion_y,list) or isinstance(radio,list)):
                            indice = 0
                            for mensaje_de_error_generado in self.validadores.mensajes_de_error:
                                self.validadores.mensajes_de_error[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                                indice +=1
                            self.mensajes_de_error.extend(self.validadores.mensajes_de_error)
                        else:
                            start_angle = diccionario_funcion_figura["start angle"] if "start angle" in list(diccionario_funcion_figura.keys()) else "0.0"
                            end_angle = diccionario_funcion_figura["end angle"] if "end angle" in list(diccionario_funcion_figura.keys()) else "360.0"
                            angulo_inicial = 450.0 if float(start_angle) == 0.0 else 450-float(start_angle)
                            angulo_final = 450.0 if float(end_angle) == 0.0 else 450-float(end_angle)

                            #DIBUJAR CONTENIDO ARC
                            #Si aplica relleno o degradado...
                            if self.fill != (1,1,1) or self.degradients:
                                if self.degradients:
                                    #Aplicar degradado a la figura...
                                    Relleno(area_de_dibujar,figura,self.degradients,(posicion_x,posicion_y),(radio*2,radio*2),angulo_inicial,angulo_final,habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                                else:
                                    #Aplicar relleno a la figura...
                                    if not habilitado_generar_figura_en_formato:
                                        figura = InstructionGroup()
                                        figura.add(Color(self.fill[0],self.fill[1],self.fill[2]))
                                        figura.add(Ellipse(pos=(posicion_x,posicion_y),size=(radio*2,radio*2),angle_start=angulo_inicial, angle_end=angulo_final))
                                        area_de_dibujar.canvas.add(figura)
                                    else:
                                        self.guardar_dibujo_en_imagen.figura_a_png(habilitado_generar_figura_en_formato["generar_dibujo_en_formato"],"arc",(radio*2,radio*2),(posicion_x,posicion_y),(self.fill[0],self.fill[1],self.fill[2]),self.tipo_de_linea,[posicion_x,posicion_y,radio,angulo_inicial,angulo_final],(self.draw[0], self.draw[1], self.draw[2]),self.line_width,angle_start=angulo_inicial, angle_end=angulo_final)
                            #DIBUJAR ARC
                            posicion_x+=radio
                            posicion_y+=radio
                            #BORDE CON LINEAS DISCONTINUADAS
                            if self.tipo_de_linea:
                                if not habilitado_generar_figura_en_formato:
                                    figura = InstructionGroup()
                                    figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                    figura.add(Line(circle=[posicion_x,posicion_y,radio,angulo_inicial,angulo_final], dash_offset=10, dash_length=5))
                                    area_de_dibujar.canvas.add(figura)
                            #Si no hay...
                            else:
                                if not habilitado_generar_figura_en_formato:
                                    figura = InstructionGroup()
                                    figura.add(Color(self.draw[0], self.draw[1], self.draw[2]))
                                    figura.add(Line(circle=[posicion_x,posicion_y,radio,angulo_inicial,angulo_final],width=self.line_width))
                                    area_de_dibujar.canvas.add(figura)
                    #No tiene figura
                    else:
                        self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Error el comando PyTikZ '"+nombre_comando+"' no tiene una figura valida.")

    def __validar_variables_tikz(self,nombre_comando,funcion_de_comando,parametros_comando,habilitado_generar_figura_en_formato={}):

        def animar(comandos_tikz_depurado_anidado,canvas_no_animar,schedule_animate,*args):
            try:
                codigo_a_dibujar = deepcopy(comandos_tikz_depurado_anidado[self.index_animacion])
                # print("ANIMAR")
                # print(codigo_a_dibujar)
                animacion_valido = True
            except:
                # print("DETENER ANIMACIÓN")
                Clock.unschedule(schedule_animate)
                animacion_valido = False
            if(animacion_valido):
                if(len(canvas_no_animar) == len(self.area_de_dibujar.canvas.children)):
                    for canvas in canvas_no_animar:#Añadir Figuras no animadas...
                        self.area_de_dibujar.canvas.add(canvas)
                else:
                    #Elimina todos los canvas del widget "area de dibujar"
                    canvas_no_animar_arr = []
                    for canva in canvas_no_animar:
                        canvas_no_animar_arr.append(canva)
                    self.area_de_dibujar.canvas.children = canvas_no_animar_arr
                    #Añade los canvas no animados...
                    for canvas in canvas_no_animar:#Añadir Figuras no animadas...
                        self.area_de_dibujar.canvas.add(canvas)
                #Dibujar la figura elegida de la lista
                if(isinstance(codigo_a_dibujar,tuple)):
                    for codigo in codigo_a_dibujar:
                        self.__validar_dibujar(codigo[0],codigo[1],codigo[2],
                        codigo[3],codigo[4],self.area_de_dibujar)
                else:
                    self.__validar_dibujar(codigo_a_dibujar[0],codigo_a_dibujar[1],codigo_a_dibujar[2],
                    codigo_a_dibujar[3],codigo_a_dibujar[4],self.area_de_dibujar)
                #Continuar con la siguiente figura en la lista
                self.index_animacion+=1
            else:
                self.index_animacion = 0

        def validarSecuenciaNumerica(cantidad_parametros,array_secuencia_numerica):
            # print("Parametros_sin_definir_ordenado")
            # print(parametros_sin_definir_ordenado)
            #Los parametros deben ser secuenciales #1,#2,#3. ETC
            parametros_sin_definir_ordenado = []
            indice = 0
            for e in array_secuencia_numerica:
                _ = bisect(parametros_sin_definir_ordenado, e)
                insort(parametros_sin_definir_ordenado, e)
                indice+=1
            indice = 0
            for _ in parametros_sin_definir_ordenado:
                if indice>0:
                    if parametros_sin_definir_ordenado[indice-1]+1 != parametros_sin_definir_ordenado[indice]:
                        parametros_sin_definir_ordenado = []
                        break
                indice+=1
            if not len(parametros_sin_definir_ordenado):
                return[{"error":"Error cerca de '#' se esperaba una secuencia numerica de parametros, ej: #1,#2,#3"}]
            else:
                try:
                    int(cantidad_parametros)
                except:
                    return[{"error":"Error cerca de la cantidad de parametros '#' se esperaba un numero INTEGER."}]
                if not len(self.mensajes_de_error):
                    cantidad_parametros = int(cantidad_parametros)
                    if len(array_secuencia_numerica) != cantidad_parametros:
                        return[{"error":str(cantidad_parametros)+" es diferente a la cantidad de parametros definidos (#) "+str(len(array_secuencia_numerica))}]
                    else:
                        return True

        if nombre_comando == "tikzset":
            #\tikzset{estilo global/.style = {line width=1.25pt, draw = cyan!75!gray,dashed}}
            nombre_variable_entorno = [nombre for nombre in list(funcion_de_comando[1].keys())[0].split(" ") if nombre]
            key_original = list(funcion_de_comando[1].keys())[0]
            nombre_variable = nombre_variable_entorno[0]
            entorno = nombre_variable_entorno[1]
            if entorno == "global/.style":
                entorno = entorno.split("/")[0]
                #NO TIENE PARAMETROS
                if isinstance(funcion_de_comando[1][key_original], list):
                    self.estilo_global_local[nombre_variable+" "+entorno] = funcion_de_comando[1][key_original]
                #TIENE PARAMETROS -> EVALUAR VALIDES PARAMETROS
                else:
                    cantidad_parametros = list(funcion_de_comando[1][key_original].keys())[0]
                    parametros_estilo_global_local = funcion_de_comando[1][key_original][cantidad_parametros]
                    parametros_sin_definir = []
                    indice_estilo_global_local = 0
                    indice_estilo_global_local_parametro = 0
                    for parametro_estilo_global_local in parametros_estilo_global_local:
                        indice_estilo_global_local_parametro = 1 if indice_estilo_global_local > 1 else 0
                        indice_estilo_global_local = indice_estilo_global_local if indice_estilo_global_local <2 else 0
                        parametro_estilo_global_local = parametros_estilo_global_local[indice_estilo_global_local_parametro][indice_estilo_global_local]
                        #Explorar por []
                        if indice_estilo_global_local == 0:
                            for key in parametro_estilo_global_local:
                                key = key.strip()
                                #Aqui se espera Parametros #2
                                if key.find("#") != -1:
                                    try:
                                        int(key[key.find("#")+1::])
                                        parametros_sin_definir.append(int(key[key.find("#")+1::]))
                                    except:
                                        self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Error cerca de "+key+" se esperaba un parametro valido. '#'")
                                        break
                                else:
                                    self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Error cerca de "+key+" se esperaba un parametro valido. '#'")
                        #Explorar por {}
                        elif indice_estilo_global_local == 1:
                            #Recorrer keys de {}
                            keys_diccionario = list(parametro_estilo_global_local.values())
                            for key in keys_diccionario:
                                if key.find("#")!=-1:
                                    try:
                                        int(key[key.find("#")+1::])
                                        parametros_sin_definir.append(int(key[key.find("#")+1::]))
                                    except:
                                        self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": Error cerca de "+key+" se esperaba un parametro valido. '#'")
                                        break
                        indice_estilo_global_local+=1
                    if not len(self.mensajes_de_error): 
                        result_validacion_secuencia = validarSecuenciaNumerica(cantidad_parametros,parametros_sin_definir)
                        if type(result_validacion_secuencia) is dict:
                            self.mensajes_de_error.append("Error en la linea del comando "+str(self.linea_de_comando)+": "+result_validacion_secuencia["error"])
                        else:
                            #Si todas las validaciones son correctas...
                            self.estilo_global_local[nombre_variable+" "+entorno] = funcion_de_comando[1][key_original]

        elif nombre_comando == "definecolor":
            nombre_variable_entorno = [nombre for nombre in list(funcion_de_comando[1].keys())[0].split(" ") if nombre]
            nombre_variable = nombre_variable_entorno[0]
            key_original = list(funcion_de_comando[1].keys())[0]
            self.estilo_global_local[nombre_variable] = funcion_de_comando[1][key_original]

        elif nombre_comando == "animarPytikz":
            codigo_tikz_anidado = funcion_de_comando[1]["ejecutar"]
            conjunto_de_comandos = []

            #Si es para generar GIF, entonces se va a generar imagenes a partir de cada código dentro del comando animarPytikz que se utilizara para generar GIF, y luego se animara el mismo resultado pero en el aplicativo.
            if("save" in parametros_comando[0]):
                habilitado_generar_figura_en_formato = {"generar_dibujo_en_formato":True, "retornar_conjunto_de_codigos":True}
            #Caso contrario, entonces se animara en la misma aplicación
            else:
                habilitado_generar_figura_en_formato = {"generar_dibujo_en_formato":False, "retornar_conjunto_de_codigos":True}
            for comando_tikz_anidado in codigo_tikz_anidado:
                if(len(self.mensajes_de_error)>0):
                    break
                #Comandos preexistentes...
                if type(comando_tikz_anidado) is list:
                    if comando_tikz_anidado[0] in self.COMANDOS_DIBUJAR_PYTIKZ:
                        #Generar figuras en formato para la creacion de un GIF o JPG
                        self.__validar_dibujar(comando_tikz_anidado[0],comando_tikz_anidado[1],comando_tikz_anidado[2],comando_tikz_anidado[3],comando_tikz_anidado[4],self.area_de_dibujar,habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                    elif comando_tikz_anidado[0] in self.COMANDOS_VARIABLES_PYTIKZ:
                        #Generar figuras en formato para la creacion de un GIF o JPG
                        frames_foraech = self.__validar_variables_tikz(comando_tikz_anidado[0],comando_tikz_anidado[1],comando_tikz_anidado[2],habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                        if len(frames_foraech):
                            conjunto_de_comandos.append(frames_foraech)
                #Comandos del usuario...
                elif type(comando_tikz_anidado) is dict:
                    for comando_personalizado in comando_tikz_anidado.values():
                        for comando in comando_personalizado:
                            if comando[0] in self.COMANDOS_DIBUJAR_PYTIKZ:
                                #Generar figuras en formato para la creacion de un GIF o JPG
                                self.__validar_dibujar(comando[0],comando[1],comando[2],comando[3],comando[4],self.area_de_dibujar,habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                            elif comando[0] in self.COMANDOS_VARIABLES_PYTIKZ:
                                #Generar figuras en formato para la creacion de un GIF o JPG
                                frames_foraech = self.__validar_variables_tikz(comando[0],comando[1],comando[2],habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                                if len(frames_foraech):
                                    conjunto_de_comandos.append(frames_foraech)
                        #Cada conjunto de comando estara dentro de una TUPLA, cada indice de conjunto_de_comandos, pertenece a los comandos anidados en un comando.
                        conjunto_de_comandos.append([tuple(comando_personalizado)])

            #Generar GIF
            if(habilitado_generar_figura_en_formato["generar_dibujo_en_formato"]):
                self.guardar_dibujo_en_imagen.crear_imagen()

            #Generar animación en aplicativo...
            index_lista_de_comandos = 0
            for index,comando_tikz_anidado in enumerate(codigo_tikz_anidado):
                if type(comando_tikz_anidado) is list:
                    if comando_tikz_anidado[0] == "foreach":
                        del codigo_tikz_anidado[index]
                        for frames in conjunto_de_comandos[index_lista_de_comandos]:
                            codigo_tikz_anidado.insert(0,frames)
                        index_lista_de_comandos+=1
                elif type(comando_tikz_anidado) is dict:
                    #Eliminar el diccionario del comandos de usuario personalizado
                    del codigo_tikz_anidado[index]
                    #Añadir todos los comandos en conjunto del comando personalizado al array codigo_tikz_anidado
                    for frames_comando_personalizado in conjunto_de_comandos[index_lista_de_comandos]:
                        codigo_tikz_anidado.insert(0,frames_comando_personalizado)
                    index_lista_de_comandos+=1
            
            class MyWidget(Widget):
                my_list = ListProperty([])

            print("__________________________________________________________")
            print("CODIGO ANIDADO A ANIMAR")
            print(codigo_tikz_anidado)
            print("__________________________________________________________")

            canvas_no_animar = MyWidget()
            canvas_no_animar.my_list = self.area_de_dibujar.canvas.children
            schedule_animate = partial(animar,codigo_tikz_anidado,canvas_no_animar.my_list)
            schedule_animate(schedule_animate)
            Clock.schedule_interval(schedule_animate,1)
        
        elif nombre_comando == "guardarPytikz":
            print("__________________________________________________________")
            print("CODIGO ANIDADO A EJECUTAR")
            print(funcion_de_comando[1]["ejecutar"])
            print("__________________________________________________________")
            codigo_tikz_anidado = funcion_de_comando[1]["ejecutar"]

            habilitado_generar_figura_en_formato = {"generar_dibujo_en_formato":True, "retornar_conjunto_de_codigos":False}
            
            for comando_tikz_anidado in codigo_tikz_anidado:
                if(len(self.mensajes_de_error)>0):
                    break
                #Comandos preexistentes...
                if type(comando_tikz_anidado) is list:
                    if comando_tikz_anidado[0] in self.COMANDOS_DIBUJAR_PYTIKZ:
                        #Dibujar comandos
                        self.__validar_dibujar(comando_tikz_anidado[0],comando_tikz_anidado[1],comando_tikz_anidado[2],comando_tikz_anidado[3],comando_tikz_anidado[4],self.area_de_dibujar)
                        #Generar figuras en formato para la creacion de un GIF o JPG
                        self.__validar_dibujar(comando_tikz_anidado[0],comando_tikz_anidado[1],comando_tikz_anidado[2],comando_tikz_anidado[3],comando_tikz_anidado[4],self.area_de_dibujar,habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                    elif comando_tikz_anidado[0] in self.COMANDOS_VARIABLES_PYTIKZ:
                        #Dibujar comandos
                        self.__validar_variables_tikz(comando_tikz_anidado[0],comando_tikz_anidado[1],comando_tikz_anidado[2])
                        #Generar figuras en formato para la creacion de un GIF o JPG
                        self.__validar_variables_tikz(comando_tikz_anidado[0],comando_tikz_anidado[1],comando_tikz_anidado[2],habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                #Comandos del usuario...
                elif type(comando_tikz_anidado) is dict:
                    for comando_personalizado in comando_tikz_anidado.values():
                        for comando in comando_personalizado:
                            if comando[0] in self.COMANDOS_DIBUJAR_PYTIKZ:
                                #Dibujar comandos
                                self.__validar_dibujar(comando[0],comando[1],comando[2],comando[3],comando[4],self.area_de_dibujar)
                                #Generar figuras en formato para la creacion de un GIF o JPG
                                self.__validar_dibujar(comando[0],comando[1],comando[2],comando[3],comando[4],self.area_de_dibujar,habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                            elif comando[0] in self.COMANDOS_VARIABLES_PYTIKZ:
                                #Dibujar comandos
                                self.__validar_variables_tikz(comando[0],comando[1],comando[2])
                                #Generar figuras en formato para la creacion de un GIF o JPG
                                self.__validar_variables_tikz(comando[0],comando[1],comando[2],habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)

            #Generar ARCHIVO
            if(habilitado_generar_figura_en_formato["generar_dibujo_en_formato"]):
                self.guardar_dibujo_en_imagen.crear_imagen()
        
        elif nombre_comando == "foreach":
            #Generar valores según Foreach
            
            #Variables Foreach
            each = parametros_comando[0]
            codigo_tikz_anidado = funcion_de_comando[1]["ejecutar"]
            variables = parametros_comando[1]["variables"]

            #Variables del generador_valores mediante Foreach
            index = 0
            index_tipo = 0
            index_interior = 0

            comandos_tikz_depurado_anidado = []
            index_nuevo_codigo_tikz = 0
            generado_comandos_tikz_depurado_anidado = False

            def reemplazar_valores(codigo_tikz_anidado,var,valor_original,valor_a_reemplazar,index,index_tipo=None,index_interior=None):
                if isinstance(var,dict):
                    var = var["variable"]

                if re.search(r"\\"+var,valor_original):#Si hay variables...
                    #Cambiar valor correspondiente por el asignado en el Foreach
                    variables_anidado = valor_original[
                        re.search(r"\\"+var,valor_original).start():
                        re.search(r"\\"+var,valor_original).end()
                    ]
                    if(index_tipo!=None):
                        if(index_interior!=None):
                            valor_original_str = codigo_tikz_anidado[index][index_tipo][index_interior]
                        else:
                            valor_original_str = codigo_tikz_anidado[index][index_tipo]
                    #Comprobar si se trata de una ecuación
                    #Donde valor_a_reemplazar: Es el valor de una variable, es decir \y (variables_anidado) -> 6pt (valor_a_reemplazar) 
                    resultado = valor_original_str.replace(variables_anidado,valor_a_reemplazar)
                    resultado = self.evaluar.evaluar_metrica(resultado)
                    if(resultado==None):
                        indice = 0
                        for mensaje_de_error_generado in self.evaluar.mensajes_de_error:
                            self.evaluar.mensajes_de_error[indice] = "Error en la linea del comando "+str(self.linea_de_comando)+": "+mensaje_de_error_generado
                            indice += 1
                        self.mensajes_de_error.extend(self.evaluar.mensajes_de_error)
                    return resultado
                else:
                    return valor_original
            
            def generar_valores(codigo_tikz_anidado,var,valor,index_nuevo_codigo_tikz,index,index_tipo=None,index_interior=None):
                for codigo in codigo_tikz_anidado:
                    if(isinstance(codigo,list)): #[[], {}], [('\\i', '0'), '1cm'], ['circle'], [[], {}]]
                        for object in codigo:#
                            if(isinstance(object,list) or isinstance(object,tuple)):#Recorrer [] o ()
                                for string in object:
                                    #Comprobar si se trata de una ecuación
                                    validar_ecuacion = reemplazar_valores(codigo_tikz_anidado,var,string,valor,index,index_tipo,index_interior)
                                    if(validar_ecuacion != None):
                                        comandos_tikz_depurado_anidado[index_nuevo_codigo_tikz][index][index_tipo][index_interior] = validar_ecuacion
                                    else:
                                        return False
                                    index_interior += 1
                                index_interior = 0
                            elif(isinstance(object,str)):
                                validar_ecuacion = reemplazar_valores(codigo_tikz_anidado,var,object,valor,index,index_tipo)
                                if(validar_ecuacion != None):
                                    comandos_tikz_depurado_anidado[index_nuevo_codigo_tikz][index][index_tipo] = validar_ecuacion
                                else:
                                    return False
                            index_tipo+=1
                        index_tipo = 0
                    index+=1
                return True

            #Extraer valor each (Si son 2 variables)
            valor_primario = []
            valor_secundario = []
            for valor in each[0]:
                if len(valor.split("/"))>0:
                    index_valor_primari = 0
                    for valor_split in valor.split("/"):
                        if(index_valor_primari==0 or not index_valor_primari%2):
                            valor_primario.append(valor_split)
                        else:
                            valor_secundario.append(valor_split)
                        index_valor_primari+=1
                else:
                    # self.message_error.append("ERROR: DEBE DE TENER VALORES EACH PARA DOS VARIABLES")
                    valor_primario.append(valor)
            if(len(valor_secundario)>0):
                variables[0] = {"variable":variables[0],"each":valor_primario}
                variables[1] = {"variable":variables[1],"each":valor_secundario}
            #Generar valores Foreach
            for var in variables:
                if(isinstance(var,dict)):
                    valor_each = var["each"]
                    var = var["variable"]
                    for codigo_arr in codigo_tikz_anidado:
                        for valor in valor_each:
                            if not generado_comandos_tikz_depurado_anidado:
                                comandos_tikz_depurado_anidado.append(deepcopy(codigo_arr))
                                valores_validos = generar_valores(codigo_arr,var,valor,index_nuevo_codigo_tikz,index,index_tipo,index_interior)
                                if(not valores_validos):
                                    return False
                            else:
                                valores_validos = generar_valores(comandos_tikz_depurado_anidado[index_nuevo_codigo_tikz],var,valor,index_nuevo_codigo_tikz,index,index_tipo,index_interior)
                                if(not valores_validos):
                                    return False
                            index_nuevo_codigo_tikz+=1
                            index=0
                else:
                    for codigo_arr in codigo_tikz_anidado:
                        for valor in each[0]:
                            if not generado_comandos_tikz_depurado_anidado:
                                comandos_tikz_depurado_anidado.append(deepcopy(codigo_arr))
                                valores_validos = generar_valores(codigo_arr,var,valor,index_nuevo_codigo_tikz,index,index_tipo,index_interior)
                                if(not valores_validos):
                                    return False
                            else:
                                valores_validos = generar_valores(comandos_tikz_depurado_anidado[index_nuevo_codigo_tikz],var,valor,index_nuevo_codigo_tikz,index,index_tipo,index_interior)
                                if(not valores_validos):
                                    return False
                            index_nuevo_codigo_tikz+=1
                            index=0
                index_nuevo_codigo_tikz=0
                generado_comandos_tikz_depurado_anidado=True

            #Transpilacion de TikZ a codigo PyTiZ
            transpilador = Transpilador()
            comandos_pytikz_depurado_anidado = transpilador.tikz_a_pytikz(comandos_tikz_depurado_anidado)

            print("_____________________________________________-")
            print("CONTENIDO FOREACH A EJECUTAR")
            print(comandos_pytikz_depurado_anidado)#Y estos son los que se pasarán a dibujar...
            print("_____________________________________________-")

            #Retornar lista de comandos si es para animar, no para generar GIF
            dibujar_comandos = False if "generar_dibujo_en_formato" in habilitado_generar_figura_en_formato.keys() else True
            generar_archivo = habilitado_generar_figura_en_formato["generar_dibujo_en_formato"] if not dibujar_comandos else False
            retornar_conjunto_de_codigos = habilitado_generar_figura_en_formato["retornar_conjunto_de_codigos"] if not dibujar_comandos else False
            if(not dibujar_comandos):
                def retornar_codigos(each,comandos_pytikz_depurado_anidado):
                    #Dividir valores del foreach según Each, para facilitar la animación
                    codigo_pytikz_por_frame = []
                    total_frames = len(each[0])
                    for _ in range(total_frames):
                        codigo_pytikz_por_frame.append([])
                    index = 0
                    for codigo in comandos_pytikz_depurado_anidado:
                        codigo_pytikz_por_frame[index].append(codigo)
                        if(index == total_frames-1):
                            index = 0
                        else:
                            index+=1
                    nuevo_codigo_pytikz_por_frame = []
                    for frame in codigo_pytikz_por_frame:
                        nuevo_codigo_pytikz_por_frame.append(tuple(frame))
                    return nuevo_codigo_pytikz_por_frame
                if(generar_archivo and retornar_conjunto_de_codigos):
                    #Generar imagenes mediante comandos generados por foreach, para luego convertirlos a GIF y retornar conjunto de codigo tikz para animarse.
                    for comando_pytikz_anidado in comandos_pytikz_depurado_anidado:
                        self.__validar_dibujar(comando_pytikz_anidado[0],comando_pytikz_anidado[1],comando_pytikz_anidado[2],comando_pytikz_anidado[3],comando_pytikz_anidado[4],self.area_de_dibujar,habilitado_generar_figura_en_formato=habilitado_generar_figura_en_formato)
                    return retornar_codigos(each,comandos_pytikz_depurado_anidado)
                if(not generar_archivo and retornar_conjunto_de_codigos):
                    return retornar_codigos(each,comandos_pytikz_depurado_anidado)
            #Dibujar según comandos de Foreach
            elif(dibujar_comandos):
                for comando_pytikz_anidado in comandos_pytikz_depurado_anidado:
                    self.__validar_dibujar(comando_pytikz_anidado[0],comando_pytikz_anidado[1],comando_pytikz_anidado[2],comando_pytikz_anidado[3],comando_pytikz_anidado[4],self.area_de_dibujar)