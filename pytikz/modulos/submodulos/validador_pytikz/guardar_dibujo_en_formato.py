import os
from kivy.utils import platform
if platform == 'android':
    os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"
import moviepy.editor as mpy
import glob, uuid, threading
from PIL import Image
from kivy.core.window import Window
from proglog import ProgressBarLogger
from math import floor
from functools import partial

#Globales
import globales

#KIVY
from kivy.lang import Builder
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color,Rectangle,Ellipse,Line

#FRAMEWORK KIVYMD
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton

#Librerias propias
from modulos.limpiar_recursos import limpiar_recursos

class InfoProgreso(MDBoxLayout):
    pass

#PROGRESS BAR - CÓDIGO KIVY
Builder.load_string('''
<InfoProgreso>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(100)
    MDLabel:
        id: porcentaje_de_realizacion
        font_name: "media/fonts/OpenSans-ExtraBold"
        font_style: "H6"
        halign: "center"
        size_hint: (1.0, .15)
    MDLabel:
        id: info
        font_name: "media/fonts/OpenSans-ExtraBold"
        font_style: "Body1"
        halign: "center"
        size_hint: (1.0, .75)
    MDProgressBar:
        id: porcentaje_actual
        size_hint: (1.0, .1)
''')

#PROGRESS BAR - API DEL MOVIEPY
class ProgresoCreacionImagen(ProgressBarLogger):
    # `window` is the class where all the gui widgets are held
    def __init__(self,clase_generar_archivo):
        super().__init__(init_state=None, bars=None, ignored_bars=None,
                 logged_bars='all', min_time_interval=0, ignore_bars_under=0)
        self.clase_generar_archivo = clase_generar_archivo
    def callback(self, **changes):
        # Every time the logger is updated, this function is called with
        # the `changes` dictionnary of the form `parameter: new value`.
        # the `try` is to avoid KeyErrors before moviepy generates a `'t'` dict 
        try:
            index = self.state['bars']['t']['index']
            total = self.state['bars']['t']['total']
            porcentaje_de_realizacion = index / total * 100
            if porcentaje_de_realizacion < 0:
                porcentaje_de_realizacion = 0
            if porcentaje_de_realizacion > 100:
                porcentaje_de_realizacion = 100
            self.clase_generar_archivo.actualizar_wid(porcentaje_de_realizacion, index=index, total=total,generar_dibujo_en_formato=True)
        except KeyError as e:
            print("ERROR")
            print(e)

class GuardarDibujoEnImagen():
    def __init__(self,area_de_dibujar):
        # CONFIGURACIÓN DEL WID A DESCARGAR COMO IMG
        w,h = Window.size
        print("Window.size")
        print(Window.size)
        self.wid_gif = RelativeLayout(size=(w,h))
        with self.wid_gif.canvas:
            Color(1,1,1,0)
            Rectangle(pos=self.wid_gif.pos,size=self.wid_gif.size)
    
    def figura_a_png(self,generar_dibujo_en_formato,name_figure,size,pos,color_relleno,tipo_de_linea,coords_borde,color_borde,line_width,angle_start=0,angle_end=0): 
        #APLICAR RELLENO
        with self.wid_gif.canvas:
            Color(*color_relleno)
        if name_figure == "rectangle":
            with self.wid_gif.canvas:
                figura = Rectangle(pos=pos,size=size)
        elif name_figure == "arc":
            with self.wid_gif.canvas:
                figura = Ellipse(pos=pos,size=size,angle_start=angle_start,angle_end=angle_end)
        elif name_figure == "circle":
            with self.wid_gif.canvas:
                figura = Ellipse(pos=pos,size=size)
        #APLICAR BORDE
        if tipo_de_linea:
            with self.wid_gif.canvas:
                Color(*color_borde)
            if name_figure == "rectangle":
                with self.wid_gif.canvas:
                    #BORDE RECTANGULO CON LINEAS DISCONTINUADAS
                    Line(points=coords_borde, dash_offset=10, dash_length=5)
            elif name_figure == "arc":
                with self.wid_gif.canvas:
                    Line(circle=coords_borde, dash_offset=10, dash_length=5)
        else:
            if name_figure == "rectangle":
                with self.wid_gif.canvas:
                    #BORDE RECTANGULO
                    Line(points=coords_borde,width=line_width)
            elif name_figure == "arc":
                with self.wid_gif.canvas:
                    Line(circle=coords_borde,width=line_width)
        if generar_dibujo_en_formato:
            #ESTE PROCESO TMB TOMA TIEMPO PERO NO SE COMO REFLEJARLO EN UN PROGRESSBAR
            #1. Guardar imagenes con transparencia, con el proposito de que la imagen sea lo unico sin transparencia...
            id_figura = str(figura.uid)
            nombre_img = 'figura_estandar_'+id_figura+".png"
            ruta = os.path.join(globales.ruta_raiz,'recursos/crear_imagen/grafica_original/'+nombre_img)
            self.wid_gif.export_to_png(ruta)

            #2. Quitar transparencia de la imagen para solo conservar la figura
            image_png = Image.open(ruta)
            image_png.getbbox()
            image_png = image_png.crop(image_png.getbbox())
            
            #3. Convertir PNG a JPG para ser compatible como secuencia de imagenes de un .GIF (Si es requerido)
            image_png.load()
            background = Image.new("RGB", image_png.size, (255, 255, 255))
            background.paste(image_png, mask=image_png.split()[3])
            nombre_img = 'figura_estandar_'+id_figura+".jpg"
            ruta = os.path.join(globales.ruta_raiz,'recursos/crear_imagen/grafica_recortada/'+nombre_img)
            background.save(ruta, 'JPEG', quality=80)

    def crear_imagen(self):
        #1. CONFIGURACIÓN - PROGRESS BAR
        self.old_value = 0#IMPORTANTE - ANTERIOR VALOR DEJADO POR EL ANTERIOR IMPULSO DE CARGA ILUSTRADO  [PROGRESS BAR]

        #2. DESPLIEGUE DEL POP UP, CONEXIÓN AL API Logger del MoviePy Y CREAR UN GIF ANIMADO...
        self.contenido_progreso_wid = InfoProgreso()
        btn_salir = MDRaisedButton(text="Vale",font_name=os.path.join(globales.ruta_raiz,"media/fonts/OpenSans-SemiBold"))
        self.md_dialog = MDDialog(
            title="Información del progreso de generación",
            type="custom",
            radius=[20, 7, 20, 7],
            content_cls=self.contenido_progreso_wid,
            buttons=[
                btn_salir
            ]
        )
        #Agregar los comportamientos correspondientes
        def cerrar_md_dialog(md_dialog,*args):
            md_dialog.dismiss()
        btn_salir.bind(on_release=partial(cerrar_md_dialog,self.md_dialog))
        self.md_dialog.open()
        #Genera GIF a partir de una lista de secuencia de imagenes
        threading.Thread(target=self.__crear_imagen).start()#En este caso la función por la cual el Progress Bar llenara hasta ser terminado es el "self.onMul"

    def __crear_imagen(self):
        #CONEXIÓN AL API Logger del MoviePy
        my_bar_logger = ProgresoCreacionImagen(self)
        #GENERAR ARCHIVO
        id = str(uuid.uuid4())
        #Ordenar los archivos de forma ascendente
        input_png_list = glob.glob(os.path.join(globales.ruta_raiz,"recursos/crear_imagen/grafica_recortada/*.jpg"))
        input_png_list.sort()
        clips = [mpy.ImageClip(i).set_duration(.1)
                    for i in input_png_list]
        #¿Hay secuencia de imagenes o almenos una imagen?
        if (len(clips) > 0):
            concat_clip = mpy.concatenate_videoclips(clips, method="compose")
            #No es una secuencia de imagenes - GENERAR JPG
            if len(clips) == 1:
                self.ruta_imagen_creado = os.path.join(globales.ruta_imagen,'Pytikz/imagen_generado_id-'+id+'.jpg').replace("/","\\")
                concat_clip.write_gif(self.ruta_imagen_creado,fps=2, logger=my_bar_logger)
            #Es una secuencia de imagenes - GENERAR GIF
            else:
                self.ruta_imagen_creado = os.path.join(globales.ruta_imagen,'Pytikz/imagen_generado_id-'+id+'.gif').replace("/","\\")
                concat_clip.write_gif(self.ruta_imagen_creado,fps=2, logger=my_bar_logger)
        
        #Si no lo hay es un error...
        else:
            self.md_dialog.title = "¡ERROR!"
            self.contenido_progreso_wid.ids.info.text = f"Ocurrio un error al momento de crear la imagen"
        
        #Limpiar recursos
        limpiar_recursos()

    def actualizar_wid(self, porcentaje_de_realizacion, info="",index=0, total=0, generar_dibujo_en_formato=False,*args):
        porcentaje_actual = floor(porcentaje_de_realizacion)
        if porcentaje_actual != self.old_value and porcentaje_actual % 5 == 0:
            self.contenido_progreso_wid.ids.porcentaje_actual.value = porcentaje_actual#IMPORTANTE - [PROGRESS BAR]
            self.contenido_progreso_wid.ids.porcentaje_de_realizacion.text = "PROGRESO: "+str(porcentaje_actual)
            if generar_dibujo_en_formato:
                self.contenido_progreso_wid.ids.info.text = f"{index} de {total} frames de la imagen completados... ({floor(porcentaje_de_realizacion)}%)"
            else:
                self.contenido_progreso_wid.ids.info.text = info
            if(porcentaje_actual == 100):
                self.md_dialog.title = "¡EXITO!"
                self.contenido_progreso_wid.ids.porcentaje_de_realizacion.text = "La imagen se creo satisfactoriamente"
                self.contenido_progreso_wid.ids.info.text = "Ruta: "+self.ruta_imagen_creado