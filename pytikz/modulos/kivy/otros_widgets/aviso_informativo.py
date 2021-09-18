#GLOBAL
import globales
#Otras librerias
import os
from functools import partial
#FRAMEWORK KIVYMD
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
class AvisoInformativo():

    """Lanza una ventana informativa.
    
    Atributo:
    - RADIUS = [20,7,20,7], valor constante."""
    
    RADIUS = [20,7,20,7]

    def __init__(self,titulo:str="Aviso informativo",mensaje:str="",tipo:str="alert",contenido_cls:object=None,botones_adicionales:list=[],agregar_boton_salir:bool=False,auto_desaparecer=True,**kwargs):
        """Muestra una ventana informativa.
        
        Parametros:
        - titulo = "Aviso informativo" (str), el titulo de la ventana informativa.
        - mensaje = "" (str), el mensaje de la ventana informativa.
        - contenido_cls = None (object), el contenido cls de la ventana informativa.
        - botones_adicionales = [] (List[any]), widgets de botones. Si no se utiliza, se mostrara el boton de "Volver" por defecto.
        - agregar_boton_salir = False (bool), si es True y hay botones_adicionales, se agregara tambien el boton de salir.
        - auto_desaparecer = True (bool), si es False la ventana informativa no desaparecera, si das clic fuera de ella.
        """

        btn_salir = MDRaisedButton(text='Cancelar', text_color=[0,0,0,1], font_name=os.path.join(globales.ruta_raiz,"media/fonts/OpenSans-SemiBold"))
        
        if not len(botones_adicionales):
            botones_adicionales = [btn_salir]
        else:
            if agregar_boton_salir:
                botones_adicionales.append(btn_salir)

        self.md_dialog = MDDialog(
            title=titulo,
            text=mensaje,
            type=tipo,
            content_cls=contenido_cls,
            radius=self.RADIUS,
            buttons=botones_adicionales,
            auto_dismiss=auto_desaparecer
        )

        self.md_dialog.open()
        
        btn_salir.bind(on_release=partial(self.cerrar_aviso_informativo,self.md_dialog))

    def cerrar_aviso_informativo(self,md_dialog,*args)->None:
        """Cierra la ventana informativa."""
        md_dialog.dismiss()