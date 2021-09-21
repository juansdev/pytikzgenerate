import re
from typing import List,Dict,Union
from kivy.metrics import pt, cm
# Librerias propias
from .base_pytikz import BasePytikz

class Validadores(BasePytikz):

    def __init__(self,estilos_predeterminados:Dict[str,str]={}):
        #Estilos predeterminados
        for estilo in estilos_predeterminados.keys():
            if estilo == "degradients":
                self.degradients = estilos_predeterminados["degradients"]
            elif estilo == "fill":
                self.fill = estilos_predeterminados["fill"]
            elif estilo == "draw":
                self.draw = estilos_predeterminados["draw"]
            elif estilo == "tipo_de_linea":
                self.tipo_de_linea = estilos_predeterminados["tipo_de_linea"]
            elif estilo == "line_width":
                self.line_width = estilos_predeterminados["line_width"]
            elif estilo == "style":
                self.style = estilos_predeterminados["style"]
        self.mensajes_de_error = []

    #Se utiliza las metricas
    def validar_metrica(self,metrica_a_validar:str,medida_pt_por_default:bool=False,no_error:bool=False)->Union[bool,float,List[str]]:
        """Recibe una metrica_a_validar(str) y se valida si esta correctamente escrito, las validaciones que se realiza son las siguientes:
        
        1. Se verifica si hay letras en la "metrica_a_validar", si es asi se verifica si esta correctamente escrito, de forma que sea EJ: "1cm".
        1.1. Se valida si el valor de la unidad metrica, sea de tipo FLOAT|INT. 
        1.2. Se valida si la unidad metrica es compatible con las unidades metricas de PyTikZ.
        2. Si no hay letras, se valida si el valor es de tipo FLOAT|INT. 
        2.1. Si "medida_pt_por_default", es False se convierte el valor a "CM". Caso contrario si es True, se convierte en "PT".
        
        Parametros:
        - metrica_a_validar(str), es la unidad metrica junto a su valor, EJ: "5cm".
        - medida_pt_por_default=False(bool), si la "metrica_a_validar" no dispone de unidad metrica. Se convertira el valor a "PT" en el caso de TRUE, caso contrario se convierte a "CM".
        - no_error=False(bool), en el caso de False se devuelve un Array con todos los errores, en el caso de que los haya, si es True, se devuelve "False", en el caso de error.
        
        Retorna:
        - En el caso de error, se devuelve un Array[str] con los mensajes de error, o si "no_error" es True, se devuelve un booleano "False".
        - Si se pasa todas las validaciones, se retorna un FLOAT, con el valor ya convertido a su unidad metrica."""
        unidad_metrica = re.compile("[a-z]")
        metrica = []
        distanciamiento_metrica = []
        for unidad in unidad_metrica.finditer(metrica_a_validar):
            distanciamiento_metrica.append(unidad.start())
            metrica.append(unidad.group())
        #VALIDAR METRICA.
        #Si se cuenta con unidad de medida...
        if len(distanciamiento_metrica)>1:
            distanciamiento_original = ""
            for distanciamiento in distanciamiento_metrica:
                if not distanciamiento_original:
                    distanciamiento_original = distanciamiento
                else:
                    if not distanciamiento_original+1==distanciamiento:
                        if not no_error:
                            self.mensajes_de_error.append("Error cerca de "+metrica_a_validar+" no es una metrica valida")
                        else:
                            return False
            if not len(self.mensajes_de_error):
                try:
                    float(metrica_a_validar[:distanciamiento_metrica[0]])
                except:
                    if not no_error:
                        self.mensajes_de_error.append("Error cerca de "+str(metrica_a_validar[:distanciamiento_metrica[0]])+" se esperaba un valor FLOAT O INTEGER")
                    else:
                        return False
                if not self.mensajes_de_error:
                    #Validar unidad de metrica
                    unidad_metrica = "".join(metrica) 
                    if unidad_metrica in self.METRICA_VALIDOS:
                        valor_metrica = float(metrica_a_validar[:distanciamiento_metrica[0]])
                        if unidad_metrica == "pt":
                            return pt(valor_metrica)
                        elif unidad_metrica == "cm":
                            return cm(valor_metrica)
                    else:
                        if not no_error:
                            self.mensajes_de_error.append("Error cerca de "+unidad_metrica+" no se reconoce la unidad metrica")
                        else:
                            return False
        #Si no se cuenta con unidad de medida, utilizar el cm como unidad de medida por defecto
        else:
            try:
                float(metrica_a_validar)
            except:
                if not no_error:
                    self.mensajes_de_error.append("Error cerca de "+metrica_a_validar)
                else:
                    return False
            if not len(self.mensajes_de_error):
                if medida_pt_por_default:
                    return pt(float(metrica_a_validar))
                else:
                    return cm(float(metrica_a_validar))
        return self.mensajes_de_error
    
    #Se utiliza los degradients[middle color, top color, left color, right color, bottom color], fill, draw, tipo_de_linea, line_width, style=[help lines]
    def validar_estilos(self,tipo_dato,valor,valor_diccionario=None):
        def draw_tupla(valor,tupla=False):
            if tupla:
                valor = valor.strip()
            color_porcentaje = valor.split("!")
            if valor in self.COLORES_VALIDOS:
                self.draw = self.__color_a_rgb(valor)
            elif valor in self.TIPO_DE_LINEAS_VALIDOS:
                self.tipo_de_linea = valor
            elif len(color_porcentaje)==3:#green!70!blue
                self.draw = self.__validar_color_porcentaje(color_porcentaje)
            else:
                self.mensajes_de_error.append("Error cerca de '"+valor+"'. No es un valor valido.")
        def draw_diccionario(valor,valor_diccionario,diccionario=False):
            if diccionario:
                key_original = valor
                valor_diccionario = valor_diccionario[key_original]
            key = valor.strip()
            if key.find("line width")!=-1:
                #Validar si es correcta la unidad de medida utilizada...
                self.line_width = self.validar_metrica(valor_diccionario,True)
            elif key.find("fill")!=-1:
                #Validar si es correcto el color utilizado...
                relleno = ""
                #Si es un codgio RGB
                if type(valor_diccionario) is list:
                    relleno = [int(num)/255 for num in valor_diccionario if int(num)>=0]
                    if len(relleno) == 3:
                        self.fill = relleno
                    else:
                        relleno = "("+",".join([str(elem) for elem in valor_diccionario])+")"
                        self.mensajes_de_error.append("Error cerca de '"+relleno+"'. No es un valor valido.")
                else:
                    relleno = valor_diccionario.strip()
                    color_porcentaje = relleno.split("!")
                    if relleno in self.COLORES_VALIDOS:
                        self.fill = self.__color_a_rgb(relleno)
                    elif len(color_porcentaje)==3:#green!70!blue
                        self.fill = self.__validar_color_porcentaje(color_porcentaje)
                    else:
                        self.mensajes_de_error.append("Error cerca de '"+relleno+"'. No es un valor valido.")
            elif key.find("draw")!=-1 or key.find("color")!=-1 and key.find(" color")==-1:
                borde_color = ""
                #Si es un codigo RGB...
                if type(valor_diccionario) is list:
                    borde_color = [int(num)/255 for num in valor_diccionario if int(num)>=0]
                    if len(borde_color) == 3:
                        self.draw = borde_color
                    else:
                        borde_color = "("+",".join([str(elem) for elem in valor_diccionario])+")"
                        self.mensajes_de_error.append("Error cerca de '"+borde_color+"'. No es un valor valido.")
                else: 
                    #Validar si es correcto el color utilizado...
                    borde_color = valor_diccionario.strip()
                    color_porcentaje = borde_color.split("!")
                    if borde_color in self.COLORES_VALIDOS:
                        self.draw = self.__color_a_rgb(borde_color)
                    elif len(color_porcentaje)==3:#green!70!blue
                        self.draw = self.__validar_color_porcentaje(color_porcentaje)
                    else:
                        self.mensajes_de_error.append("Error cerca de '"+borde_color+"'. No es un valor valido.")
            #degradients = [left color, right color, top color, middle color, bottom color, inner color, outer color, ball color]
            elif key.find("left color")!=-1:
                #Validar si es correcto el color utilizado...
                left_color = valor_diccionario.strip()
                color_porcentaje = left_color.split("!")
                if left_color in self.COLORES_VALIDOS:
                    self.degradients["left_color"] = self.__color_a_rgb(left_color)
                elif len(color_porcentaje)==3:#green!70!blue
                    self.degradients["left_color"] = self.__validar_color_porcentaje(color_porcentaje)
                else:
                    self.mensajes_de_error.append("Error cerca de '"+left_color+"'. No es un valor valido.")
            elif key.find("right color")!=-1:
                #Validar si es correcto el color utilizado...
                right_color = valor_diccionario.strip()
                color_porcentaje = right_color.split("!")
                if right_color in self.COLORES_VALIDOS:
                    self.degradients["right_color"] = self.__color_a_rgb(right_color)
                elif len(color_porcentaje)==3:#green!70!blue
                    self.degradients["right_color"] = self.__validar_color_porcentaje(color_porcentaje)
                else:
                    self.mensajes_de_error.append("Error cerca de '"+right_color+"'. No es un valor valido.")
            elif key.find("top color")!=-1:
                #Validar si es correcto el color utilizado...
                top_color = valor_diccionario.strip()
                color_porcentaje = top_color.split("!")
                if top_color in self.COLORES_VALIDOS:
                    self.degradients["top_color"] = self.__color_a_rgb(top_color)
                elif len(color_porcentaje)==3:#green!70!blue
                    self.degradients["top_color"] = self.__validar_color_porcentaje(color_porcentaje)
                else:
                    self.mensajes_de_error.append("Error cerca de '"+top_color+"'. No es un valor valido.")
            elif key.find("middle color")!=-1:
                #Validar si es correcto el color utilizado...
                middle_color = valor_diccionario.strip()
                color_porcentaje = middle_color.split("!")
                if middle_color in self.COLORES_VALIDOS:
                    self.degradients["middle_color"] = self.__color_a_rgb(middle_color)
                elif len(color_porcentaje)==3:#green!70!blue
                    self.degradients["middle_color"] = self.__validar_color_porcentaje(color_porcentaje)
                else:
                    self.mensajes_de_error.append("Error cerca de '"+middle_color+"'. No es un valor valido.")
            elif key.find("bottom color")!=-1:
                #Validar si es correcto el color utilizado...
                bottom_color = valor_diccionario.strip()
                color_porcentaje = bottom_color.split("!")
                if bottom_color in self.COLORES_VALIDOS:
                    self.degradients["bottom_color"] = self.__color_a_rgb(bottom_color)
                elif len(color_porcentaje)==3:#green!70!blue
                    self.degradients["bottom_color"] = self.__validar_color_porcentaje(color_porcentaje)
                else:
                    self.mensajes_de_error.append("Error cerca de '"+bottom_color+"'. No es un valor valido.")
            elif key.find("inner color")!=-1:
                #Validar si es correcto el color utilizado...
                inner_color = valor_diccionario.strip()
                color_porcentaje = inner_color.split("!")
                if inner_color in self.COLORES_VALIDOS:
                    self.degradients["inner_color"] = self.__color_a_rgb(inner_color)
                elif len(color_porcentaje)==3:#green!70!blue
                    self.degradients["inner_color"] = self.__validar_color_porcentaje(color_porcentaje)
                else:
                    self.mensajes_de_error.append("Error cerca de '"+inner_color+"'. No es un valor valido.")
            elif key.find("outer color")!=-1:
                #Validar si es correcto el color utilizado...
                outer_color = valor_diccionario.strip()
                color_porcentaje = outer_color.split("!")
                if outer_color in self.COLORES_VALIDOS:
                    self.degradients["outer_color"] = self.__color_a_rgb(outer_color)
                elif len(color_porcentaje)==3:#green!70!blue
                    self.degradients["outer_color"] = self.__validar_color_porcentaje(color_porcentaje)
                else:
                    self.mensajes_de_error.append("Error cerca de '"+outer_color+"'. No es un valor valido.")
            elif key.find("ball color")!=-1:
                #Validar si es correcto el color utilizado...
                ball_color = valor_diccionario.strip()
                color_porcentaje = ball_color.split("!")
                if ball_color in self.COLORES_VALIDOS:
                    self.degradients["ball_color"] = self.__color_a_rgb(ball_color)
                elif len(color_porcentaje)==3:#green!70!blue
                    self.degradients["ball_color"] = self.__validar_color_porcentaje(color_porcentaje)
                else:
                    self.mensajes_de_error.append("Error cerca de '"+ball_color+"'. No es un valor valido.")
            #style = [help lines]
            elif key.find("style")!=-1:
                #Guardar los estilos indicados en un diccionario
                estilo = valor_diccionario.strip()
                if estilo in self.ESTILOS_VALIDOS:
                    self.style["help lines"] = {
                        "line width":.5,
                        "draw":self.__validar_color_porcentaje(["black",20,"white"])
                    }
                else:
                    self.mensajes_de_error.append("Error cerca de '"+estilo+"'. No es un estilo valido.")
        if tipo_dato == "tupla":
            #VARIABLE SIN PARAMETROS O NORMAL
            if isinstance(valor,list):
                for estilo in valor:
                    draw_tupla(estilo,tupla=True)
            #VARIABLE CON PARAMETROS
            else:
                draw_tupla(valor)
        elif tipo_dato == "diccionario":
            #VARIABLE SIN PARAMETROS O NORMAL
            if isinstance(valor,list):
                keys_diccionario = valor
                for key in keys_diccionario:
                    draw_diccionario(key,valor_diccionario,True)
            #VARIABLE CON PARAMETROS
            else:
                draw_diccionario(valor,valor_diccionario)
            #Validacion orden del degradient middle color, debe de estar de ultimas...
            try:
                index_middle_color = list(self.degradients.keys()).index("middle_color")
            except:
                index_middle_color = -1
            if(index_middle_color != -1 and len(self.degradients.keys())-1!=index_middle_color):
                self.mensajes_de_error.append("El 'middle color' debe de estar posicionado al final de los parametros.")
        return (self.degradients,self.fill,self.draw,self.tipo_de_linea,self.line_width,self.style,self.mensajes_de_error)

    def __validar_color_porcentaje(self,color_porcentaje):
        """Funcion que recibe un array llamado "color_porcentaje", donde se espera la siguiente estructura:
        ["nombre_color",porcentaje,"nombre_color"].
        Porcentaje debe de tener un valor INTEGER.
        Se retorna un valor RGB compatible con Kivy EJ: [1,0,1]"""
        porcentaje = color_porcentaje[1]
        try:
            porcentaje = int(porcentaje)
        except:
            self.mensajes_de_error.append("El porcentaje debe de tener un valor INTEGER")
        if not len(self.mensajes_de_error):
            if porcentaje > 100 or porcentaje < 0:
                self.mensajes_de_error.append("El porcentaje debe de tener un valor entre 0-100")
            elif not len(self.mensajes_de_error):
                color_1 = color_porcentaje[0].lower().strip()
                color_2 = color_porcentaje[2].lower().strip()
                color_1 = self.__color_a_rgb(color_1)
                color_2 = self.__color_a_rgb(color_2)
                if len(color_1) == 3 and len(color_2) == 3:
                    color_elegido = []
                    indice = 0
                    #color RGB
                    for color in color_2:
                        if color != color_1[indice]:
                            #0
                            if not color:
                                color_elegido.append((color+(porcentaje/100)))
                            #1
                            elif color:
                                color_elegido.append((color-(porcentaje/100)))
                        else:
                            color_elegido.append(color)
                        indice+=1
                    return color_elegido
    
    def __color_a_rgb(self,color):
        #["red","blue","green","cyan","black","yellow"]
        #RGB
        if color == "red":
            return (1,0,0)
        elif color == "blue":
            return (0,0,1)
        elif color == "green":
            return (0,1,0)
        elif color == "cyan":
            return (0,.7254901960784314,.9490196078431373)
        elif color == "black":
            return (0,0,0)
        elif color == "yellow":
            return (1,.9215686274509804,.2392156862745098)
        elif color == "white":
            return (1,1,1)
        elif color == "purple":
            return (.7490196078431373,0,.2509803921568627)
        else:
            self.mensajes_de_error.append("El color "+color+" no esta disponible.")
            return ()
