#Otras librerias
import os
#KIVY
from kivy.core.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, BindTexture, Rectangle, Ellipse, InstructionGroup
from kivy.graphics.texture import Texture
#Globales
from pytikzgenerate import globales

#Relleno con degradado para figuras cerradas (Excluyendo la figura de lineas(Line) y bezier (Line(bezier=coordenadas)).
class Relleno():
    def __init__(self,area_dibujar,name_figure,degradado,pos,size,angle_start=0,angle_end=0,habilitado_generar_figura_en_formato=False):
        figura_wid = InstructionGroup()
        if not habilitado_generar_figura_en_formato:
            figura_wid.add(Color(1, 1, 1))
        else:
            wid_img = RelativeLayout(size=size)
            figura_wid.add(Color(1, 1, 1))
        if name_figure == "rectangle":
            if not habilitado_generar_figura_en_formato:
                figura = Rectangle(pos=pos,size=size)
            else:
                figura = Rectangle(pos=wid_img.pos,size=wid_img.size)
        elif name_figure == "arc":
            if not habilitado_generar_figura_en_formato:
                figura = Ellipse(pos=pos,size=size,angle_start=angle_start,angle_end=angle_end)
            else:
                figura = Ellipse(pos=wid_img.pos,size=wid_img.size,angle_start=angle_start,angle_end=angle_end)
        elif name_figure == "circle":
            if not habilitado_generar_figura_en_formato:
                figura = Ellipse(pos=pos,size=size)
            else:
                figura = Ellipse(pos=wid_img.pos,size=wid_img.size)
        id_figura = figura_wid.uid
        url_texture_degradado = self.__aplicar_degradado(id_figura,**degradado)
        if not habilitado_generar_figura_en_formato:
            # aqui, nosotros estamos enlazando una textura personalizada en el index 1
            # esto seria usado como texture1 en el shader.
            # Los nombres de los archivos son engañosos: no corresponden al
            # index aqui o en el shader.
            # establecer la texture1 para usar la textura en el index 1
            figura_wid.add(BindTexture(source=url_texture_degradado, index=1))
            figura_wid.add(figura)
            area_dibujar.canvas.add(figura_wid)
            area_dibujar.canvas['texture1'] = 1
        else:
            texture = Image(url_texture_degradado).texture
            figura.texture = texture
            figura_wid.add(figura)
            #Dibujar canvas...
            wid_img.canvas.add(figura_wid)
            ruta = os.path.join(globales.ruta_raiz,'recursos/animacion/figura_cerrado_'+str(figura.uid)+".png")
            wid_img.export_to_png(ruta)
                
    def __aplicar_degradado(self,id_figura,left_color=(),right_color=(),top_color=(),middle_color=(),bottom_color=(),inner_color=(),outer_color=(),ball_color=()):
        #left color, right color, top color, middle color, bottom color, inner color, outer color, ball color
        if len(right_color) and len(left_color) and not len(middle_color):
            #Colores Origen - Destino
            color_origen = right_color
            color_destino = left_color
            #Color Origen
            c1 = [color*255 for color in color_origen]+[255]
            c1_trans = [color*255 for color in color_origen]+[128]
            #Color Destino
            c2_trans = [color*255 for color in color_destino]+[128]
            c2 = [color*255 for color in color_destino]+[255]
            #Crear degradiente
            degradient = c1+c1_trans+c2_trans+c2
            degradient = [int(degra) for degra in degradient]
            #Textura de 4 columnas, 1 fila.
            texture = Texture.create(size=(4,1), colorfmt='rgba')
        elif len(right_color) and len(left_color) and len(middle_color):
            #Colores Origen - Destino
            color_origen = right_color
            color_intermedio = middle_color
            color_destino = left_color
            #Color Origen
            c1 = [color*255 for color in color_origen]+[255]
            c1_trans = [color*255 for color in color_origen]+[128]
            #Color Intermediario
            c2_trans = [color*255 for color in color_intermedio]+[128]
            c2 = [color*255 for color in color_intermedio]+[255]
            #Color Destino
            c3_trans = [color*255 for color in color_destino]+[128]
            c3 = [color*255 for color in color_destino]+[255]
            #Crear degradiente
            degradient = c1+c1_trans+c2_trans+c2+c2_trans+c3_trans+c3
            degradient = [int(degra) for degra in degradient]
            #Textura de 7 columnas, 1 fila.
            texture = Texture.create(size=(7,1), colorfmt='rgba')
        elif len(top_color) and len(bottom_color) and not len(middle_color):
            #Colores Origen - Destino
            color_origen = bottom_color
            color_destino = top_color
            #Color Oriden
            c1 = [color*255 for color in color_origen]+[255]
            c1_trans = [color*255 for color in color_origen]+[128]
            #Color Destino
            c2_trans = [color*255 for color in color_destino]+[128]
            c2 = [color*255 for color in color_destino]+[255]
            #Crear degradiente
            fila_1 = c1+c1+c1+c1
            fila_2 = c1_trans+c1_trans+c1_trans+c1_trans
            fila_3 = c2_trans+c2_trans+c2_trans+c2_trans
            fila_4 = c2+c2+c2+c2
            degradient = fila_1+fila_2+fila_3+fila_4
            degradient = [int(degra) for degra in degradient]
            #Textura de 4 columnas, 4 fila.
            texture = Texture.create(size=(4,4), colorfmt='rgba')
        elif len(top_color) and len(bottom_color) and len(middle_color):
            #Colores Origen - Destino
            color_origen = bottom_color
            color_intermedio = middle_color
            color_destino = top_color
            #Color Origen
            c1 = [color*255 for color in color_origen]+[255]
            c1_trans = [color*255 for color in color_origen]+[128]
            #Color Intermediario
            c2_trans = [color*255 for color in color_intermedio]+[128]
            c2 = [color*255 for color in color_intermedio]+[255]
            #Color Destino
            c3_trans = [color*255 for color in color_destino]+[128]
            c3 = [color*255 for color in color_destino]+[255]
            #Crear degradiente
            fila_1 = c1+c1+c1+c1+c1+c1+c1
            fila_2 = c1_trans+c1_trans+c1_trans+c1_trans+c1_trans+c1_trans+c1_trans
            fila_3 = c2_trans+c2_trans+c2_trans+c2_trans+c2_trans+c2_trans+c2_trans
            fila_4 = c2+c2+c2+c2+c2+c2+c2
            fila_5 = c2_trans+c2_trans+c2_trans+c2_trans+c2_trans+c2_trans+c2_trans
            fila_6 = c3_trans+c3_trans+c3_trans+c3_trans+c3_trans+c3_trans+c3_trans
            fila_7 = c3+c3+c3+c3+c3+c3+c3
            degradient = fila_1+fila_2+fila_3+fila_4+fila_5+fila_6+fila_7
            degradient = [int(degra) for degra in degradient]
            #Textura de 7 columnas, 7 fila.
            texture = Texture.create(size=(7,7), colorfmt='rgba')
        else:
            degradient = 0
            texture = Texture.create(size=(4,1), colorfmt='rgba')
        texture.blit_buffer(bytes(degradient),colorfmt='rgba', bufferfmt='ubyte')
        url_texture = os.path.join(globales.ruta_raiz,"recursos/relleno/figura_relleno_"+str(id_figura)+".png")
        texture.save(url_texture)
        return url_texture