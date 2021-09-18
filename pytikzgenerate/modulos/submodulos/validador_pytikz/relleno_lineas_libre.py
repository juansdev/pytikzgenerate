#Otras librerias
import numpy as np
import cv2, imutils, copy, os
from kivy.graphics import Rectangle, BindTexture, Color, InstructionGroup
from PIL import Image

#Globales
import globales

#Relleno con o sin degradado para figuras dibujadas con Lineas. (Line)
class RellenoLineasLibre():
    
    def __init__(self,area_dibujar,coordenadas_figura,colores,relleno=True,degradado=False,habilitado_generar_figura_en_formato=False):
        #SI ES LISTA
        #RGB A BGR
        if isinstance(colores, list):
            colores = [colores[2],colores[1],colores[0]]
        #Convertir numeros flotantes a INT.
        coordenadas_figura = [int(coordenada) for coordenada in coordenadas_figura]
        #Sacar valores Width y Height Minimos...
        indice = 1
        coordenada_individual_arr = []
        min_width = []
        min_height = []
        for coordenada in coordenadas_figura:
            coordenada_individual_arr.append(coordenada)
            if not indice%2:
                min_width.append(coordenada_individual_arr[0])
                min_height.append(coordenada_individual_arr[1])
                coordenada_individual_arr = []
            indice+=1
        min_width = np.array(min_width).min()
        min_height = np.array(min_height).min()
        #Modificar coordenadas originales, convirtiendolos a coordenadas que dibujen desde las coordenadas 0,0
        indice = 1
        coordenada_np = []
        for coordenada in coordenadas_figura:
            if indice%2:
                coordenada_np.append(coordenada-min_width)
            else:
                coordenada_np.append(coordenada-min_height)
            indice+=1
        #Sacar valores maximos de Height y Width usando las coordenadas nuevas.
        #Coordenadas nuevas transformados a unas coordenadas divididas por matrices [[0,0],[100,100],etc]
        coordenada_individual_arr = []
        height = []
        width = []
        coordenada_np_new = []
        for coordenada in coordenada_np:
            coordenada_individual_arr.append(coordenada)
            if not indice%2:
                width.append(coordenada_individual_arr[0])
                height.append(coordenada_individual_arr[1])
                coordenada_np_new.append(coordenada_individual_arr)
                coordenada_individual_arr = []
            indice+=1
        self.max_width = np.array(width).max()
        self.max_height = np.array(height).max()
        #Crear imagen a partir de coordenadas...
        contours = np.array(coordenada_np_new)
        img = np.zeros( (self.max_height,self.max_width) ) #Ancho y alto dependiendo del ancho y alto que ocupe la figura...
        cv2.fillPoly(img, pts =[contours], color=[255,255,255])#Relleno blanco...
        error_x_y = False
        try:
            img = imutils.rotate(img, 180)
        except:
            error_x_y = True
            print("La imagen que tratas de renderizar tiene una anchura o altura igual a 0. No se aplicara degradado...")
        if not error_x_y:
            self.img = cv2.flip(img, 1)
            pos_graphic = [float(min_width),float(min_height)]
            size_graphic = [float(self.max_width),float(self.max_height)]
            figura_wid = InstructionGroup()
            if not habilitado_generar_figura_en_formato:    
                #Dibujar rectangulo en "Area de dibujar"
                figura = Rectangle(pos=pos_graphic,size=size_graphic)
                figura_wid.add(Color(1, 1, 1))
                self.ruta = os.path.join(globales.ruta_raiz,'recursos/relleno_lineas_libre/figura_relleno_'+str(figura.uid)+".png")
            else:
                figura = Rectangle()
                self.ruta = os.path.join(globales.ruta_raiz,'recursos/relleno_lineas_libre/figura_relleno_'+str(figura.uid)+".png")
            cv2.imwrite(self.ruta, self.img)
            #Pasar imagen de color blanco a COLOR definido por el usuario...
            if relleno:
                self.__convertir_a_color(colores,relleno=True)
                if colores != (0,0,0):
                    self.__convertir_a_png()
                else:
                    self.__convertir_a_png(True)
            elif degradado:
                self.__convertir_a_color([1,1,1],relleno=True)
                self.__convertir_a_png()
                self.__convertir_a_color(colores,degradado=True)
                self.__convertir_a_png()
            if not habilitado_generar_figura_en_formato:
                #Añadir la imagen del degradado o imagen al Rectangulo.
                figura_wid.add(BindTexture(source=self.ruta, index=1))
                figura_wid.add(figura)
                # establecer la texture1 para usar la textura en el index 1
                area_dibujar.canvas.add(figura_wid)
                area_dibujar.canvas['texture1'] = 1
    #Convertir pixeles blanco a X color...
    def __convertir_a_color(self,colores,relleno=False,degradado=False):
        self.img = cv2.imread(self.ruta)
        def aplicar_relleno(colores):
            Conv_hsv_Gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(Conv_hsv_Gray, 0, 255,cv2.THRESH_BINARY_INV |cv2.THRESH_OTSU)
            if colores != (0,0,0):
                indices = np.where(mask==0)#Ignorar color Negro...
                self.img[indices[0], indices[1], :] = [color*255 for color in colores[::-1]]#Convierte pixeles sobrantes (En este seria solo blanco) al color deseado..
            else:
                indices = np.where(mask==255)#Ignorar color Blanco...
                self.img[indices[0], indices[1], :] = [color*255 for color in colores[::-1]]#Convierte pixeles sobrantes (En este seria solo negro) al color deseado..
        def aplicar_degradado(left_color=(),right_color=(),top_color=(),middle_color=(),bottom_color=(),inner_color=(),outer_color=(),ball_color=()): 
            def gradient_3d(start_list, stop_list):
                result = self.img
                for i, (start, stop) in enumerate(zip(start_list, stop_list)):
                    for f in range(result.shape[0]):
                        degradado_raw = copy.copy(result)
                        degradado_raw[f,:, i] = np.linspace(start, stop, self.max_width).T
                        for c in range(result[f,:,i].shape[0]):
                            if result[f,c,i]:
                                result[f,c,i] = degradado_raw[f, c, i]
                Image.fromarray(np.uint8(result)).save(self.ruta, quality=95)
            if top_color and bottom_color:
                gradient_3d([color*255 for color in top_color],[color*255 for color in bottom_color])
        if relleno:
            aplicar_relleno(colores)
        elif degradado:
            aplicar_degradado(**colores)

    def __convertir_a_png(self,figura_solo_negra=False):
        img = self.img
        #Eliminar pixeles negros (Resultado de pasar pixeles transparentes a un formato PNG, se convierte en color negro)...
        h, w, c = img.shape#Se obtiene la dimencion de la imagen (h,w,c)
        # Añadido canal Alpha -- requerido para BGRA (B, G, R, A)
        image_bgra = np.concatenate([img, np.full((h, w, 1), 255, dtype=np.uint8)], axis=-1)
        # Crear una mask donde pixeles negros ([0, 0, 0]) son True
        white = np.all(img == [0, 0, 0], axis=-1)
        # Cambiar valores de Alpha a 0 para todos los pixeles negros
        image_bgra[white, -1] = 0
        if figura_solo_negra:
            image_without_alpha = image_bgra[:,:,:3]
            image_without_alpha[image_without_alpha == 255] = 0#Convertir todos los pixeles blancos a negro (Imagen sin transparencia).
            image_bgra[:,:,:3] = image_without_alpha
        cv2.imwrite(self.ruta, image_bgra)
