class BasePytikz():
    """Clase padre, que tiene los atributos actualmente compatibles con Pytikz.
    Atributos:
    - COMANDOS_ANIDADORES(List[str]), tiene el nombre de los comandos anidadodres.
    - DELIMITADORES_PARAMETROS_COMANDO_PERSONALIZADO(List[str]), tiene los delimitadores del valor de los parametros. se utiliza en el caso de que se tratase de un estilo con delimitadores, por ejemplo en el caso de un color RGB que tenga como delimitador "#7!70!black", solo se extrae el "#7" y posteriormente se devuelve solo el "7". Actualmente solo utilizado en los parametros de un comando personalizado invocado.
    """
    #Utilizados en la clase "DepuradorTikz"
    COMANDOS_ANIDADORES = ("foreach", "newcommand","animarPytikz","guardarPytikz")
    DELIMITADORES_PARAMETROS_COMANDO_PERSONALIZADO = ("!")
    #Utilizados en la clase "ValidadorPytikz"
    COMANDOS_DIBUJAR_PYTIKZ = ("draw","fill","filldraw","shade")
    COMANDOS_VARIABLES_PYTIKZ = ("tikzset","definecolor","foreach","animarPytikz","guardarPytikz")
    #Utilizados en la clase "Validadores"
    TIPO_DE_LINEAS_VALIDOS = ("dotted")
    COLORES_VALIDOS = ("red","blue","green","cyan","black","yellow","white","purple")
    ESTILOS_VALIDOS = ("help lines")
    METRICA_VALIDOS = ("pt","cm")

    #Todos los nombres de las llaves de parametro - Agregar, todos los entornos actualmente disponible para las variables...