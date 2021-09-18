from kivy.app import App
from kivy.uix.widget import Widget

from pytikzgenerate.pytikzgenerate import PytikzGenerate

class MyPaintApp(App):
    title="Test PytikzGenerate"
    def build(self):
        main_widget = Widget()
        PytikzGenerate(r"""%Estilos globales
\tikzset{estilo_sin_parametros global/.style = {draw=red}}
\tikzset{estilo_con_parametros global/.style n args = {3}{line width=#3, fill = #2, #1}, estilo global/.default = {cyan}{red}{50pt}}
\definecolor{ColorA}{RGB}{255,0,0}
\definecolor{ColorB}{RGB}{255,0,255}
\definecolor{ColorC}{RGB}{255,255,0}

%Mostrar regla, recomendamos que si desea tener el tamaño de la regla abarcando todo el lienzo de dibujo, utilices las medidas del tamaño de pantalla indicadas en el lienzo de dibujo%
\draw[style=help lines] (0,0) grid (20.25,14.16);

%Circulo que emite ondas%
\draw[estilo_con_parametros global={red}{blue}{1.5pt}] (3cm,1.5cm) circle (1cm);
\draw[estilo_sin_parametros global,line width=5pt] (5,2.5) arc (0:90:1cm);
\draw[draw=red, line width= 5pt] (4.5,2) arc[start angle=0, end angle=90, radius=1];

%Un controls%
\draw (0,0) .. controls (0,1)  and (1,2)  .. (2,3);

%Con mas de un controls%
%Borde con un color RGB%
\draw[draw=cyan!75!green] (100pt,140pt) .. controls (100pt,165pt) and (150pt,240pt) .. (200pt,240pt) .. controls (200pt,225pt) and (250pt,140pt) .. (300pt,140pt);

%Shade, degradado gris por defecto%
\shade (10pt,220pt) rectangle (60pt, 270pt);

%Fill, relleno negro y borde blanco por defecto%
%Relleno con un color RGB%
\fill (12,12) arc (90:360:1) arc (360:380:1);
\draw[fill=red!50!blue] (8,12) arc (90:360:1) arc (0:0:1);

%Filldraw, relleno negro y borde negro por defecto%
\filldraw[line width=5pt] (320pt,50pt) arc (0:90:3cm);""",main_widget)
        return main_widget

if __name__ == '__main__':
    MyPaintApp().run()