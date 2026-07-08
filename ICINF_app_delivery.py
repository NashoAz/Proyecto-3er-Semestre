import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os
import random
from abc import ABC, abstractmethod

# Interfaces Segregadas para ISP
class Despachuable(ABC):
    @abstractmethod
    def despachar(self, pedido_contexto):
        pass

class Entregable(ABC):
    @abstractmethod
    def entregar(self, pedido_contexto, codigo_ingresado):
        pass

# Implementación del Patrón State
class EstadoPedido(Despachuable, Entregable):
    pass

class EstadoPendiente(EstadoPedido):
    def despachar(self, pedido_contexto):
        pedido_contexto["Estado"] = "En camino"
        return True, "Pedido despachado con éxito. Ahora está En camino."
    def entregar(self, pedido_contexto, codigo_ingresado):
        return False, "No se puede entregar un pedido que aún está Pendiente."

class EstadoEnCamino(EstadoPedido):
    def despachar(self, pedido_contexto):
        return False, "El pedido ya se encuentra en camino."
    def entregar(self, pedido_contexto, codigo_ingresado):
        if codigo_ingresado == pedido_contexto.get("codigo_entrega"):
            pedido_contexto["Estado"] = "Entregado"
            return True, f"Pedido {pedido_contexto['id_pedido']} verificado y entregado con éxito."
        return False, "El código ingresado de 4 números es incorrecto o inválido."

class EstadoEntregado(EstadoPedido):
    def despachar(self, pedido_contexto):
        return False, "El pedido ya fue entregado de forma conforme."
    def entregar(self, pedido_contexto, codigo_ingresado):
        return False, "El pedido ya fue entregado de forma conforme."

# Registro dinámico para cumplir OCP (Abierto a la extensión, cerrado a la modificación)
REGISTRO_ESTADOS = {
    "Pendiente": EstadoPendiente,
    "En camino": EstadoEnCamino,
    "Entregado": EstadoEntregado
}

def mapear_estado_objeto(str_estado):
    clase_estado = REGISTRO_ESTADOS.get(str_estado, EstadoPendiente)
    return clase_estado()

# Clase Utilitaria para cumplir SRP (Separa la persistencia física de la lógica de negocio)
class GestorPersistenciaJSON:
    def leer_json(self, ruta):
        if os.path.exists(ruta):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def escribir_json(self, ruta, datos):
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            return True
        except IOError:
            return False

# Clase Subsistema Autenticación: Lee y modifica el json de usuarios // Valida usuarios // Reglas de seguridad
class SubsistemaAutenticacion:

    # Inicialización de la clase
    def __init__(self, archivo_usuarios="usuarios_data.json", persistencia=None): # Archivo donde se guardaran los usuarios registrados
        self.archivo = archivo_usuarios # Instancia
        self.persistencia = persistencia if persistencia else GestorPersistenciaJSON() # Inyección de dependencia (DIP)
        self._usuarios = {} # Diccionario vacío
        self._cargar_y_asegurar_usuarios() #Carga de usuarios

    # Busqueda de usuarios ya existentes
    def _cargar_y_asegurar_usuarios(self):
        # Definicion de cuentas iniciales
        self._cuentas_oficiales = {
            "admin": {"password": "123", "rol": "Administrador"},
            "user1": {"password": "123", "rol": "Usuario"},
            "Rep1": {"password": "123", "rol": "Repartidor"}
        }

        # Si encuentra el archivo usuarios
        datos_cargados = self.persistencia.leer_json(self.archivo)
        if datos_cargados is not None:
            # Si alguna de las cuentas iniciales no se encuentra en el archivo
            if not all(usuario in datos_cargados for usuario in self._cuentas_oficiales):
                # Se guardar temporalmente los datos ya existentes de usuarios
                self._usuarios = datos_cargados
                # Recorre la plantilla de las cuentas iniciales
                for k, v in self._cuentas_oficiales.items():
                    # Si alguno de los usuarios iniciales fue borrado reinyecta en memoria con sus credenciales por defecto
                    if k not in self._usuarios:
                        self._usuarios[k] = v
                # Actualizacion del json
                self._guardar_usuarios()
            # Si el archivo no tiene errores
            else:
                # Asigna los datos directamente a la variable global de la clase
                self._usuarios = datos_cargados
        # Si el archivo no existe
        else:
            # Copia las cuentas iniciales y crea el archivo usuarios
            self._usuarios = self._cuentas_oficiales
            self._guardar_usuarios()

    # Guardar usuarios en el json
    def _guardar_usuarios(self):
        # Abre json en escritura
        if not self.persistencia.escribir_json(self.archivo, self._usuarios):
            # Error de entrada o salida
            print("Error al guardar usuarios.")

    # Autenticar identidad de usuario y determinar rol
    def verificar_credenciales(self, usuario, password):
        # Si en usuario guardado existe como key en el diccionario
        if usuario in self._usuarios:
            # Obtiene datos del usuario
            datos = self._usuarios[usuario]
            # Si la contraseña coincide
            if datos["password"] == password:
                # Entrega el rol con el que abrira el programa
                return datos["rol"]
        return None
    
    # Obtener copia actualizada de datos en memoria
    def obtener_todos_los_usuarios(self):
        self._cargar_y_asegurar_usuarios()
        return self._usuarios

    # Creacion de usuario (Admin)
    def crear_usuario(self, usuario, password, rol):
        # Si el usuario ya se encuentra dentro de los datos
        if usuario in self._usuarios:
            # Error
            return False, "El nombre de usuario ya existe."
        # Si no se encuentra guarda los datos
        self._usuarios[usuario] = {"password": password, "rol": rol}
        self._guardar_usuarios()
        # Mensaje de éxito
        return True, "Usuario creado con éxito."

    # Modificacion de datos usuario
    def modificar_usuario(self, usuario, password, rol):
        # Si el usuario no se encuentra dentro de los datos
        if usuario not in self._usuarios:
            # Error
            return False, "El usuario no existe."
        # Si si existe sobreescribe los datos asignados al usuario
        self._usuarios[usuario] = {"password": password, "rol": rol}
        self._guardar_usuarios()
        # Mensaje de éxito
        return True, "Usuario modificado con éxito."
    
    # Eliminar usuario de los datos
    def eliminar_usuario(self, usuario):
        # Si el usuario a querer eliminar es el administrador inicial
        if usuario == "admin":
            # Error
            return False, "No puedes eliminar la cuenta de administrador principal."
        # Si el usuario no existe en los datos
        if usuario not in self._usuarios:
            # Error
            return False, "El usuario no existe."
        # Si sí se encuentra dentro de los datos se eliminan y se guardan los cambios
        del self._usuarios[usuario]
        self._guardar_usuarios()
        # Mensaje de éxito
        return True, "Usuario eliminado con éxito."

# Clase Subsistema Negocio: Gestion de la persistencia y la lógica de los restaurantes, el carrito y los pedidos.
class SubsistemaNegocio:
    
    # Inicializacion de la clase
    def __init__(self, persistencia=None):
        # Instancia de los archivos a utilizar
        self.arc_restaurantes = "restaurantes.json"
        self.arc_carrito = "carrito.json"
        self.arc_pedidos = "pedidos.json"
        
        self.persistencia = persistencia if persistencia else GestorPersistenciaJSON() # Inyección de dependencia (DIP)
        
        # Diccionario vacio
        self.restaurantes = {}

        # Lista vacia
        self.carrito = []
        self.pedidos = []
        
        # Inicializacion de las funciones del programa
        self._inicializar_y_asegurar_restantes()
        self._cargar_carrito()
        self._cargar_pedidos()

    # Inicializador de restaurantes
    def _inicializar_y_asegurar_restantes(self):
        # Menú por defecto de los restaurantes
        self._menu_defecto = {
            "Restaurante 1": {
                "Menú": [
                    {"comida": "Churrasco Italiano", "precio": 5500},
                    {"comida": "Papas Fritas Medianas", "precio": 2800},
                    {"comida": "Bebida 500cc", "precio": 1500}
                ]
            },
            "Restaurante 2": {
                "Menú": [
                    {"comida": "Pizza Pepperoni Familiar", "precio": 10990},
                    {"comida": "Palitos de Ajo", "precio": 3500},
                    {"comida": "Nectar Durazno 1.5L", "precio": 2000}
                ]
            },
            "Restaurante 3": {
                "Menú": [
                    {"comida": "Sushi Roll Queso Crema", "precio": 4800},
                    {"comida": "Gyozas de Cerdo (5 un)", "precio": 3200},
                    {"comida": "Té Helado", "precio": 1800}
                ]
            }
        }

        # Si el archivo que contiene los datos de los restaurantes existe
        contenido = self.persistencia.leer_json(self.arc_restaurantes)
        if contenido is not None:
            # Si el contenido del archivo no se encuentra o "Restaurante 1" no esta
            if not contenido or "Restaurante 1" not in contenido:
                # Reparacion gargando el menu por defecto
                self.restaurantes = self._menu_defecto
                self._guardar_json(self.arc_restaurantes, self.restaurantes)
            # Si el archivo esta correcto
            else:
                self.restaurantes = contenido
        # Si el archivo de restaurantes no existe
        else:
            # Establece el menu por defecto y crea el archivo faltante
            self.restaurantes = self._menu_defecto
            self._guardar_json(self.arc_restaurantes, self.restaurantes)

    # Cargar datos de carrito
    def _cargar_carrito(self):
        # Si el archivo existe
        contenido = self.persistencia.read_json(self.arc_carrito) if hasattr(self.persistencia, 'read_json') else self.persistencia.leer_json(self.arc_carrito)
        if contenido is not None:
            self.carrito = contenido
        # Si no existe se crea una lista vacia
        else:
            self.carrito = []

    # Cargar datos de los pedidos
    def _cargar_pedidos(self):
        # Si el archivo existe
        contenido = self.persistencia.leer_json(self.arc_pedidos)
        if contenido is not None:
            # Carga datos
            self.pedidos = contenido
        # Error / Si no existe se crea una lista vacia
        else:
            self.pedidos = []

    # Guardar datos en .json
    def _guardar_json(self, ruta, datos):
        # Abre el archivo en modo escritura
        if not self.persistencia.escribir_json(ruta, datos):
            # Error
            print(f"Error al escribir en {ruta}")

    # Agregar comida al carrito
    def agregar_al_carrito(self, comida, precio):
        # Se guarda informacion de la comida
        item = {"comida": comida, "precio": precio}
        # Se ordena la comida
        self.carrito.append(item)
        # Se guarda en el archivo de carrito
        self._guardar_json(self.arc_carrito, self.carrito)

    # Limpiar elementos de carrito
    def limpiar_carrito(self):
        # Crea lista vacia
        self.carrito = []
        # Si el archivo de carrito existe
        if os.path.exists(self.arc_carrito):
            try:
                # Elimina archivo de carrito
                os.remove(self.arc_carrito)
            # Error
            except OSError:
                pass
    
    # Registro de pedido
    def registrar_pedido(self, usuario, total, direccion, metodo_pago):
        # Generacion de un ID
        id_unico = f"PED-{random.randint(100000, 999999)}"
        # Generacion de numero de verificacion para entrega
        codigo_verificacion = f"{random.randint(1000, 9999)}"
        
        # Se guardan datos del pedido
        nuevo_pedido = {
            "id_pedido": id_unico,
            "Nombre de usuario": usuario,
            "Valor del pedido": total,
            "Direccion": direccion,
            "Metodo de pago": metodo_pago,
            "Estado": "Pendiente",
            "codigo_entrega": codigo_verificacion
        }
        # Organizacion del pedido
        self.pedidos.append(nuevo_pedido)
        # Guardar informacion en archivo de pedidos
        self._guardar_json(self.arc_pedidos, self.pedidos)
        # Llama a funcion de limpiar carrito
        self.limpiar_carrito()

    # Actualizacion de estado del pedido
    def actualizar_estado_pedido(self, id_pedido, nuevo_estado, **kwargs):
        # Se cargan los datos del pedido
        self._cargar_pedidos()
        # Bucle iterativo que recorre los elementos de la lista de pedidos. En cada vuelta la variable p guarda el diccionario con todos los datos un pedido
        for p in self.pedidos:
            if p["id_pedido"] == id_pedido:
                estado_objeto = mapear_estado_objeto(p["Estado"])
                if nuevo_estado == "En camino":
                    exito, msg = estado_objeto.despachar(p)
                elif nuevo_estado == "Entregado":
                    exito, msg = estado_objeto.entregar(p, kwargs.get("codigo_ingresado", ""))
                else:
                    exito, msg = False, "Operación inválida"
                
                if exito:
                    self._guardar_json(self.arc_pedidos, self.pedidos)
                return exito, msg
        return False, "Pedido no encontrado."

# Clase Delivery Facade: Intermediario entre la interfaz gráfica y los motores del programa
class DeliveryFacade:
    _instancia = None

    def __new__(cls, *args, **kwargs):
        if not cls._instancia:
            cls._instancia = super(DeliveryFacade, cls).__new__(cls, *args, **kwargs)
        return cls._instancia

    # Inicializacion de Clase
    def __init__(self, auth_subsystem=None, negocio_subsystem=None):
        if hasattr(self, "_inicializado") and self._inicializado:
            return
        # Instancia el SubsistemaAuntenticacion (Aplica DIP recibiendo abstracciones)
        self.auth = auth_subsystem if auth_subsystem else SubsistemaAutenticacion()
        # Instancia el SubsistemaNegocio (Aplica DIP recibiendo abstracciones)
        self.negocio = negocio_subsystem if negocio_subsystem else SubsistemaNegocio()
        self._inicializado = True

    # Conexion de pantalla login con validador de seguridad
    def autenticar_credenciales(self, usuario, password):
        return self.auth.verificar_credenciales(usuario, password)

    # Solicitud de listado completo de las cuentas para el panel de admin
    def obtener_usuarios_sistema(self):
        return self.auth.obtener_todos_los_usuarios()
    
    # Permite al administrador añadir una nueva cuenta de forma visual
    def registrar_nuevo_usuario(self, usuario, password, rol):
        return self.auth.crear_usuario(usuario, password, rol)

    # Permite modificar los datos de una cuenta para admin
    def actualizar_datos_usuario(self, usuario, password, rol):
        return self.auth.modificar_usuario(usuario, password, rol)

    # Eliminiar cuenta de sistema de registros
    def remover_usuario_sistema(self, usuario):
        return self.auth.eliminar_usuario(usuario)

    # Entrega catalogo de los restuaurantes disponibles
    def obtener_restaurantes(self):
        return self.negocio.restaurantes

    # Agrega comida seleccionda al carrito
    def añadir_item_carrito(self, comida, precio):
        self.negocio.agregar_al_carrito(comida, precio)

    # Obtiene la lista de comidas seleccionadas en el carrito
    def obtener_carrito(self):
        self.negocio._cargar_carrito()
        return self.negocio.carrito

    # Calculates el monto total a pagar del pedido
    def obtener_total_carrito(self):
        return sum(item["precio"] for item in self.obtener_carrito())

    # Borra los elementos seleccionados del carrito
    def vaciar_carrito_local(self):
        self.negocio.limpiar_carrito()

    # Transforma los elementos del carro en una orden despues de finalizar el pago
    def procesar_finalizar_pedido(self, usuario, total, direccion, metodo_pago):
        self.negocio.registrar_pedido(usuario, total, direccion, metodo_pago)

    # Obtiene el listado global de las compras para la pestala "Mis pedidos"
    def obtener_todos_los_pedidos(self):
        self.negocio._cargar_pedidos()
        return self.negocio.pedidos

    # Permite al repartidor cambiar la etapa del envio
    def modificar_estado_pedido(self, id_pedido, nuevo_estado, **kwargs):
        return self.negocio.actualizar_estado_pedido(id_pedido, nuevo_estado, **kwargs)

# Clase ICINF App Delivery: Interfaz Gráfica
class ICINFAppDelivery:
    # Inicializacion de Clase
    def __init__(self, root, sistema_facade=None):
        # Guarda ventana base en instancia
        self.root = root
        # Titulo de la ventana
        self.root.title("ICINF App Delivery")
        # Pantalla Completa
        self.root.state('zoomed')
        
        # Instancia para contectar funcinoes con la clase Fachada (DIP mediante inyección)
        self.sistema = sistema_facade if sistema_facade else DeliveryFacade()
        
        # Variables nulas
        self.usuario_actual = None
        self.rol_actual = None
        
        # Motor ttk
        self.style = ttk.Style()
        # Tema "clam"
        self.style.theme_use("clam")
        
        # Frame que utiliza toda la ventana
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)
        
        # Inicializa la ventana en el Login
        self.mostrar_pantalla_login()

    # Elimina la ventana anterior a la que se utilizara
    def limpiar_contenedor(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # Pantalla de Login
    def mostrar_pantalla_login(self):
        self.limpiar_contenedor()
        
        # Frame para login
        login_frame = ttk.Frame(self.main_container, padding=40)
        login_frame.pack(fill="both", expand=True)
        
        # Label de Titulo
        ttk.Label(login_frame, text="ICINF App Delivery", font=("Helvetica", 32, "bold"), foreground="#1F618D").pack(pady=30)
        
        # Label para el frame de las casillas
        form_panel = ttk.LabelFrame(login_frame, text=" Control de Acceso ", padding=40)
        form_panel.pack(pady=20, ipadx=20)
        
        # Label Nombre de usuario
        ttk.Label(form_panel, text="Nombre de Usuario:", font=("Helvetica", 13)).grid(row=0, column=0, sticky="w", pady=15)
        entry_user = ttk.Entry(form_panel, font=("Helvetica", 13), width=35)
        entry_user.grid(row=0, column=1, pady=15, padx=15)
        entry_user.focus()
        
        # Label Contraseña de Acceso
        ttk.Label(form_panel, text="Contraseña de Acceso:", font=("Helvetica", 13)).grid(row=1, column=0, sticky="w", pady=15)
        entry_pass = ttk.Entry(form_panel, font=("Helvetica", 13), show="*", width=35)
        entry_pass.grid(row=1, column=1, pady=15, padx=15)
        
        # Metodo para ejecutar las funciones de login
        def ejecutar_login():
            # Obtiene lo que se escribio en las casillas
            user = entry_user.get().strip()
            password = entry_pass.get()
            
            # Si no hay nada escrito
            if not user or not password:
                messagebox.showwarning("Campos Requeridos", "Por favor, complete todas las credenciales.")
                return
            
            # Deteccion de rol a partir de usuario y contraseña
            rol_detectado = self.sistema.autenticar_credenciales(user, password)

            # Si se volvio un rol valido
            if rol_detectado:
                self.usuario_actual = user
                self.rol_actual = rol_detectado
                self.mostrar_sistema_pestanas()
            # No se volvio un rol valido
            else:
                messagebox.showerror("Fallo de Autenticación", "Las credenciales ingresadas son incorrectas.")

        # Boton de Iniciar Sesion
        btn_ingresar = ttk.Button(form_panel, text="Iniciar Sesión", command=ejecutar_login)
        btn_ingresar.grid(row=2, column=0, columnspan=2, pady=25, sticky="ew", ipady=10)
        
        # Boton Exit
        btn_salir = ttk.Button(login_frame, text="Salir de la Aplicación", command=self.root.quit)
        btn_salir.pack(pady=20, ipadx=25, ipady=8)

    # Ventana Principal
    def mostrar_sistema_pestanas(self):
        self.limpiar_contenedor()
        
        # Frame que utiliza toda la ventana
        app_frame = ttk.Frame(self.main_container, padding=20)
        app_frame.pack(fill="both", expand=True)
        
        # Topbar
        top_bar = ttk.Frame(app_frame)
        top_bar.pack(fill="x", pady=(0, 15))
        
        # Label indicador de usuario
        lbl_welcome = ttk.Label(top_bar, text=f"Conectado: {self.usuario_actual} ({self.rol_actual})", font=("Helvetica", 14, "bold"))
        lbl_welcome.pack(side="left")
        
        # Boton para cerrar sesion
        btn_logout = ttk.Button(top_bar, text="Cerrar Sesión", command=self.cerrar_sesion)
        btn_logout.pack(side="right", ipady=5)
        
        # Pestañas
        self.notebook = ttk.Notebook(app_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Cuantas pesañas se muestran segun el rol
        if self.rol_actual == "Usuario":
            self.crear_pestaña_usuario()
        elif self.rol_actual == "Repartidor":
            self.crear_pestaña_repartidor()
        elif self.rol_actual == "Administrador":
            self.crear_pestaña_usuario()
            self.crear_pestaña_repartidor()
            self.crear_pestaña_administrador()

    # Pestaña Vista de Usuario
    def crear_pestaña_usuario(self):
        # Frame para vista usuario
        self.frame_tab_usuario = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(self.frame_tab_usuario, text=" Vista de Usuario ")
        
        # Segunda pestaña
        self.sub_notebook_usuario = ttk.Notebook(self.frame_tab_usuario)
        self.sub_notebook_usuario.pack(fill="both", expand=True)
        
        # 2 Frames para vista usuario
        self.pane_catalogo = ttk.Frame(self.sub_notebook_usuario, padding=10)
        self.pane_mis_pedidos = ttk.Frame(self.sub_notebook_usuario, padding=10)
        
        # Monta los 2 Frames dentro de la pestaña
        self.sub_notebook_usuario.add(self.pane_catalogo, text=" Catálogo y Tiendas ")
        self.sub_notebook_usuario.add(self.pane_mis_pedidos, text=" Mis Pedidos Activos ")
        
        # Llama a cargar nuevamente los datos del Frame cada que sea seleccionado
        self.sub_notebook_usuario.bind("<<NotebookTabChanged>>", self._al_cambiar_subpestaña_usuario)
        self.cargar_vista_restaurantes()

    # Actualizacion de la informacion al hacer un cambio de pestaña
    def _al_cambiar_subpestaña_usuario(self, event):
        # Obtiene en que pestaña se encuentra el usuario
        pestaña_seleccionada = self.sub_notebook_usuario.index(self.sub_notebook_usuario.select())
        # Si se situa en la pestaña del historial de pedidos
        if pestaña_seleccionada == 1:
            self.cargar_historial_pedidos_usuario()

    # Vista principal de usuario (Restaurantes)
    def cargar_vista_restaurantes(self):
        for widget in self.pane_catalogo.winfo_children():
            widget.destroy()
            
        # Frame para la pestaña
        content_view = ttk.Frame(self.pane_catalogo)
        content_view.pack(fill="both", expand=True)
        
        # Barra de navegacion
        nav_bar = ttk.Frame(content_view)
        nav_bar.pack(fill="x", pady=10)
        
        # Obtiene cantidad de elementos dentro del carrito
        cant_items = len(self.sistema.obtener_carrito())
        # Boton ver carrito
        btn_ir_carrito = ttk.Button(nav_bar, text=f"Ver mi Carrito ({cant_items} items)", command=self.cargar_vista_carrito_aislado)
        btn_ir_carrito.pack(side="right", padx=20, ipady=5)
        
        # Etiqueta para seleccionar restaurante
        ttk.Label(content_view, text="Selecciona un Restaurante para ver su menú", font=("Helvetica", 18, "bold"), foreground="#2C3E50").pack(pady=10)
        
        # Frame Restaurantes
        cards_container = ttk.Frame(content_view)
        cards_container.pack(fill="x", expand=True, padx=40)
        
        # Obtener informacion de restaurantes
        dict_restaurantes = self.sistema.obtener_restaurantes()

        # Calificaciones de restaurantes
        calificaciones_rest = {
            "Restaurante 1": "★ ★ ★ ★ ☆ (4 Estrellas)",
            "Restaurante 2": "★ ★ ★ ★ ★ (5 Estrellas)",
            "Restaurante 3": "★ ★ ★ ☆ ☆ (3 Estrellas)"
        }
        
        # 
        for indice, (nombre_rest, datos) in enumerate(dict_restaurantes.items()):
            cards_container.columnconfigure(indice, weight=1)
            card = ttk.LabelFrame(cards_container, text=f" {nombre_rest} ", padding=20)
            card.grid(row=0, column=indice, padx=20, pady=20, sticky="nsew")
            
            texto_rating = calificaciones_rest.get(nombre_rest, "★ ★ ★ ★ ☆")
            color_rating = "#F39C12" if "3" not in texto_rating else "#E67E22"
            
            ttk.Label(card, text=texto_rating, font=("Helvetica", 13, "bold"), foreground=color_rating).pack(pady=10)
            
            btn_menu = ttk.Button(card, text="Ver Menú", command=lambda name=nombre_rest: self.cargar_vista_menu(name))
            btn_menu.pack(pady=10, fill="x", ipady=8)


    # Actualizacion de info frames menu
    def cargar_vista_menu(self, nombre_restaurante):
        for widget in self.pane_catalogo.winfo_children():
            widget.destroy()
            
        # Frame para el catalogo
        content_view = ttk.Frame(self.pane_catalogo)
        content_view.pack(fill="both", expand=True)
        
        # Frame para navegacion
        top_nav = ttk.Frame(content_view)
        top_nav.pack(fill="x", padx=20, pady=10)
        
        # Boton para volver
        btn_back = ttk.Button(top_nav, text="Volver a Restaurantes", command=self.cargar_vista_restaurantes)
        btn_back.pack(side="left")
        
        # Carrito
        cant_items = len(self.sistema.obtener_carrito())
        btn_ir_carrito = ttk.Button(top_nav, text=f"Ir al Carrito ({cant_items})", command=self.cargar_vista_carrito_aislado)
        btn_ir_carrito.pack(side="right", ipady=5)
        
        # Menu Label
        menu_panel = ttk.LabelFrame(content_view, text=f" Menú de {nombre_restaurante} ", padding=25)
        menu_panel.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Info comidas
        lista_comidas = self.sistema.obtener_restaurantes()[nombre_restaurante]["Menú"]
        
        # For para obtener la informacion de todas las comidas
        for item in lista_comidas:
            row_frame = ttk.Frame(menu_panel, padding=10)
            row_frame.pack(fill="x", pady=5)
            lbl_info = ttk.Label(row_frame, text=f"{item['comida']} — ${item['precio']:,}".replace(",", "."), font=("Helvetica", 12, "bold"))
            lbl_info.pack(side="left")
            btn_add = ttk.Button(row_frame, text="Añadir al carrito", command=lambda c=item['comida'], p=item['precio']: [self.sistema.añadir_item_carrito(c, p), self.cargar_vista_menu(nombre_restaurante)])
            btn_add.pack(side="right", padx=10)

    # Vista de carrito
    def cargar_vista_carrito_aislado(self):
        for widget in self.pane_catalogo.winfo_children():
            widget.destroy()
            
        # Frame Ventana completa
        content_view = ttk.Frame(self.pane_catalogo, padding=20)
        content_view.pack(fill="both", expand=True)
        
        # Boton volver
        btn_back = ttk.Button(content_view, text="Seguir Comprando (Inicio)", command=self.cargar_vista_restaurantes)
        btn_back.pack(anchor="w", pady=10)
        
        # Label Frame
        cart_panel = ttk.LabelFrame(content_view, text=" Revisión de tu Carrito de Compras ", padding=30)
        cart_panel.pack(fill="both", expand=True, padx=50, pady=10)
        
        # Info carrito
        items_carrito = self.sistema.obtener_carrito()

        txt_area = tk.Text(cart_panel, font=("Helvetica", 12), height=12)
        txt_area.pack(fill="both", expand=True, pady=10)
        
        # Si no hay items en el carrito
        if not items_carrito:
            txt_area.insert("1.0", "Tu carrito actual se encuentra vacío.\n¡Vuelve al catálogo para agregar alimentos!")
            txt_area.config(state="disabled")
            btn_empty = ttk.Button(cart_panel, text="Vaciar Carrito", state="disabled")
            btn_empty.pack(side="left", pady=10)
        # Si sí hay
        else:
            # Por cada item dentro del carrito
            for item in items_carrito:
                # Info en texto
                txt_area.insert("end", f"• {item['comida']} (${item['precio']:,})\n".replace(",", "."))
            txt_area.config(state="disabled")
            
            # Total de plata
            total = self.sistema.obtener_total_carrito()
            # Label de pago
            ttk.Label(cart_panel, text=f"Subtotal a pagar: ${total:,}".replace(",", "."), font=("Helvetica", 15, "bold"), foreground="#27AE60").pack(pady=10)
            
            actions_frame = ttk.Frame(cart_panel)
            actions_frame.pack(fill="x", pady=10)
            
            # Vaciar Carrito y actualizar vista de carrito
            def vaciar():
                self.sistema.vaciar_carrito_local()
                self.cargar_vista_carrito_aislado()
                
            btn_empty = ttk.Button(actions_frame, text="Vaciar Carrito", command=vaciar)
            btn_empty.pack(side="left", padx=10, ipady=5)
            
            btn_order = ttk.Button(actions_frame, text="Realizar pedido / Ir a Pagar", command=self.cargar_vista_pagos)
            btn_order.pack(side="right", padx=10, ipady=5)

    # Cargar ventana de pagos
    def cargar_vista_pagos(self):
        for widget in self.pane_catalogo.winfo_children():
            widget.destroy()
            
        # LabelFrame para Frame de pago
        pay_panel = ttk.LabelFrame(self.pane_catalogo, text=" Checkout — Formulario de Pago Pasarela Redcompra ", padding=30)
        pay_panel.pack(pady=40, padx=100)
        
        # Informacion de total a pagar
        total_pagar = self.sistema.obtener_total_carrito()
        ttk.Label(pay_panel, text=f"Monto Total a Pagar: ${total_pagar:,} CLP".replace(",", "."), font=("Helvetica", 16, "bold"), foreground="#C0392B").pack(pady=15)
        
        # Frame de pago
        form_grid = ttk.Frame(pay_panel)
        form_grid.pack(pady=10)
        
        # Valdacion de Calle (Solo abecedario y números)
        def validar_calle(texto_entrante):
            if texto_entrante == "": return True
            for char in texto_entrante:
                if not (char.isalnum() or char in "  áéíóúÁÉÍÓÚñÑüÜ"): return False
            return True

        # Validacion numero de casa/dpto (Solo numeros)
        def validar_numero(texto_entrante):
            if texto_entrante == "": return True
            return texto_entrante.isdigit()

        # Obtencion de calle y numero
        reg_calle = self.root.register(validar_calle)
        reg_numero = self.root.register(validar_numero)
        
        # Label Forma de pago
        ttk.Label(form_grid, text="Método de Pago:", font=("Helvetica", 12)).grid(row=0, column=0, sticky="w", pady=10)
        # Combobox para seleccionar metoodo de pago
        combo_metodo = ttk.Combobox(form_grid, values=["Tarjeta de Débito (Redcompra)", "Efectivo"], state="readonly", font=("Helvetica", 11))
        combo_metodo.current(0)
        combo_metodo.grid(row=0, column=1, pady=10, padx=10, sticky="w")
        
        # label Tarketa
        lbl_tarjeta_titulo = ttk.Label(form_grid, text="Tarjeta:", font=("Helvetica", 11))
        lbl_tarjeta_titulo.grid(row=1, column=0, sticky="w", pady=5)
        
        # Label CuentaRut
        lbl_tarjeta_valor = tk.Label(
            form_grid, text="Cuenta Rut (1)", font=("Helvetica", 11, "bold"), 
            bg="#EAECEE", fg="#2C3E50", relief="sunken", anchor="w", padx=10, width=26
        )
        lbl_tarjeta_valor.grid(row=1, column=1, pady=5, padx=10, sticky="w")
        
        # Label Calle
        ttk.Label(form_grid, text="Calle de Despacho:", font=("Helvetica", 12)).grid(row=2, column=0, sticky="w", pady=10)
        entry_calle = ttk.Entry(form_grid, font=("Helvetica", 12), width=30, validate="key", validatecommand=(reg_calle, "%P"))
        entry_calle.grid(row=2, column=1, pady=10, padx=10, sticky="w")
        entry_calle.focus()
        
        # label Numero
        ttk.Label(form_grid, text="Número / Depto:", font=("Helvetica", 12)).grid(row=3, column=0, sticky="w", pady=10)
        entry_numero = ttk.Entry(form_grid, font=("Helvetica", 12), width=15, validate="key", validatecommand=(reg_numero, "%P"))
        entry_numero.grid(row=3, column=1, pady=10, padx=10, sticky="w")

        # Metodo de pago
        def cambiar_metodo_pago(event):
            # Si es Efectivo
            if combo_metodo.get() == "Efectivo":
                # Se elimina la tarjeta
                lbl_tarjeta_titulo.grid_remove()
                lbl_tarjeta_valor.grid_remove()
            # Si es Tarjeta
            else:
                # Se muestra Tarjeta
                lbl_tarjeta_titulo.grid(row=1, column=0, sticky="w", pady=5)
                lbl_tarjeta_valor.grid(row=1, column=1, pady=5, padx=10, sticky="w")

        # Selección de metodo
        combo_metodo.bind("<<ComboboxSelected>>", cambiar_metodo_pago)
        
        # Procesar pago
        def procesar_pago():
            # Informacion de pedido
            calle = entry_calle.get().strip()
            numero = entry_numero.get().strip()
            metodo_elegido = combo_metodo.get()
            
            # Si no hay calle ni numero
            if not calle or not numero:
                messagebox.showwarning("Campos Requeridos", "Por favor, complete la Calle y el Número para realizar el despacho.")
                return
            
            # Direccion en solo una variable
            direccion_completa = f"{calle} #{numero}"
            # Finalizar pedido
            self.sistema.procesar_finalizar_pedido(self.usuario_actual, total_pagar, direccion_completa, metodo_elegido)
            
            # Éxito
            messagebox.showinfo("Transacción Exitosa", "Pago Realizado con Éxito. Revisa su código en la pestaña 'Mis Pedidos Activos'.")
            self.cargar_vista_restaurantes()
            self.sub_notebook_usuario.select(1)

        # Confirmar pago
        btn_confirmar = ttk.Button(pay_panel, text="Proceder al pago", command=procesar_pago)
        btn_confirmar.pack(fill="x", pady=20, ipady=8)
        
        # Cancelar pago
        btn_abort = ttk.Button(pay_panel, text="Cancelar y Volver al Carrito", command=self.cargar_vista_carrito_aislado)
        btn_abort.pack()

    # Historial de pagos actualizar info
    def cargar_historial_pedidos_usuario(self):
        for widget in self.pane_mis_pedidos.winfo_children():
            widget.destroy()
            
        # Label Pedidos
        ttk.Label(self.pane_mis_pedidos, text="Tus Pedidos en Curso y Códigos de Verificación", font=("Helvetica", 16, "bold"), foreground="#2E4053").pack(pady=10)

        # Fondo
        color_fondo_sistema = self.style.lookup("TFrame", "background")
        # Canvas
        canvas = tk.Canvas(self.pane_mis_pedidos, borderwidth=0, highlightthickness=0, bg=color_fondo_sistema)
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.pane_mis_pedidos, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")

        header_frame = ttk.Frame(scrollable_frame, padding=5)
        header_frame.pack(fill="x", pady=5)
        
        titulos = [("ID Pedido", 15), ("Monto", 12), ("Dirección de Despacho", 30), ("Estado Actual", 15), ("CÓDIGO DE ENTREGA", 22)]
        for col_idx, (texto, ancho) in enumerate(titulos):
            lbl = ttk.Label(header_frame, text=texto, font=("Helvetica", 11, "bold"), width=ancho, anchor="center", relief="groove", padding=5)
            lbl.grid(row=0, column=col_idx, padx=2)

        todos_pedidos = self.sistema.obtener_todos_los_pedidos()
        mis_pedidos = [p for p in todos_pedidos if p.get("Nombre de usuario") == self.usuario_actual]

        if not mis_pedidos:
            ttk.Label(scrollable_frame, text="Aún no has realizado pedidos con esta cuenta.\n¡Ve al catálogo para realizar tu primera orden!", font=("Helvetica", 12, "italic"), foreground="gray", justify="center").pack(pady=40)
            return

        for pedido in mis_pedidos:
            row = ttk.Frame(scrollable_frame, padding=8, relief="solid", borderwidth=1)
            row.pack(fill="x", pady=4)

            id_p = pedido["id_pedido"]
            estado_p = pedido["Estado"]
            token = pedido.get("codigo_entrega", "N/A")

            ttk.Label(row, text=id_p, font=("Helvetica", 10, "bold"), width=15, anchor="center").grid(row=0, column=0)
            ttk.Label(row, text=f"${pedido['Valor del pedido']:,}".replace(",", "."), font=("Helvetica", 10), width=12, anchor="center").grid(row=0, column=2)
            ttk.Label(row, text=pedido["Direccion"], font=("Helvetica", 10), width=30, anchor="w").grid(row=0, column=3)
            
            if estado_p == "Pendiente": color_est = "#E67E22"
            elif estado_p == "En camino": color_est = "#2980B9"
            else: color_est = "#27AE60"

            ttk.Label(row, text=estado_p, font=("Helvetica", 10, "bold"), width=15, anchor="center", foreground=color_est).grid(row=0, column=4)
            
            lbl_codigo = tk.Label(
                row, text=f" {token} ", font=("Courier New", 12, "bold"), 
                bg="#FADBD8" if estado_p != "Entregado" else "#D4EFDF", 
                fg="#78281F" if estado_p != "Entregado" else "#145A32", 
                relief="ridge", width=18, pady=3
            )
            lbl_codigo.grid(row=0, column=5, padx=10)


    # Pestaña repartidor
    def crear_pestaña_repartidor(self):
        # Pestaña Vista repartidor
        self.frame_tab_repartidor = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.frame_tab_repartidor, text=" Vista Repartidor ")
        self.actualizar_vista_repartidor()

    # Actualizar info de pestaña vista repartidor
    def actualizar_vista_repartidor(self):
        for widget in self.frame_tab_repartidor.winfo_children():
            widget.destroy()

        # Label Envios
        ttk.Label(self.frame_tab_repartidor, text="Panel de Control de Envíos (Fila de Pedidos Activos)", font=("Helvetica", 16, "bold"), foreground="#2E4053").pack(pady=10)

        color_fondo_sistema = self.style.lookup("TFrame", "background")
        canvas = tk.Canvas(self.frame_tab_repartidor, borderwidth=0, highlightthickness=0, bg=color_fondo_sistema)
        scrollbar = ttk.Scrollbar(self.frame_tab_repartidor, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")

        header_frame = ttk.Frame(scrollable_frame, padding=5)
        header_frame.pack(fill="x", pady=5)
        
        labels_titulos = [
            ("ID Pedido", 12), ("Cliente", 15), ("Monto Total", 12), 
            ("Dirección de Despacho", 25), ("Método", 12), ("Estado Actual", 15)
        ]
        for col_idx, (texto, ancho) in enumerate(labels_titulos):
            lbl = ttk.Label(header_frame, text=texto, font=("Helvetica", 11, "bold"), width=ancho, anchor="center", relief="groove", padding=5)
            lbl.grid(row=0, column=col_idx, padx=2)

        todos_pedidos = self.sistema.obtener_todos_los_pedidos()
        pedidos_activos = [p for p in todos_pedidos if p.get("Estado") != "Entregado"]

        # Si no hay pedidos
        if not pedidos_activos:
            lbl_no_pedidos = ttk.Label(scrollable_frame, text="No hay pedidos pendientes ni en camino en el sistema actualmente.", font=("Helvetica", 12, "italic"), foreground="gray")
            lbl_no_pedidos.pack(pady=30)
            return

        # Para cada pedido
        for idx, pedido in enumerate(pedidos_activos):
            # Obtener info de pedido
            id_p = pedido["id_pedido"]
            estado_p = pedido["Estado"]
            codigo_correcto = pedido.get("codigo_entrega", "0000")

            # Frame para mostrar pedidos
            row = ttk.Frame(scrollable_frame, padding=5, relief="solid", borderwidth=1)
            row.pack(fill="x", pady=4)

            # Labels info de pedido
            ttk.Label(row, text=id_p, font=("Helvetica", 10, "bold"), width=12, anchor="center").grid(row=0, column=0)
            ttk.Label(row, text=pedido["Nombre de usuario"], font=("Helvetica", 10), width=15, anchor="w").grid(row=0, column=1)
            ttk.Label(row, text=f"${pedido['Valor del pedido']:,}".replace(",", "."), font=("Helvetica", 10), width=12, anchor="center").grid(row=0, column=2)
            ttk.Label(row, text=pedido["Direccion"], font=("Helvetica", 10), width=25, anchor="w").grid(row=0, column=3)
            ttk.Label(row, text=pedido["Metodo de pago"], font=("Helvetica", 10), width=12, anchor="center").grid(row=0, column=4)
            
            # Mas info de pedido
            color_estado = "#E67E22" if estado_p == "Pendiente" else "#2980B9"
            lbl_est = ttk.Label(row, text=estado_p, font=("Helvetica", 10, "bold"), width=15, anchor="center", foreground=color_estado)
            lbl_est.grid(row=0, column=5)

            # Boton despacho
            btn_despachar = ttk.Button(row, text="Despachar")
            btn_despachar.grid(row=0, column=6, padx=5)

            # Ejecucion de boton despacho
            def ejecutar_despacho(b=btn_despachar, mid=id_p):
                # Modificacion de estado a "En camino"
                exito, msg = self.sistema.modificar_estado_pedido(mid, "En camino")
                if exito:
                    messagebox.showinfo("Despacho", msg)
                else:
                    messagebox.showwarning("Atención", msg)
                b.config(state="disabled")
                
                #  Cambio de estado a "Normal"
                def reactivar_boton():
                    try: b.config(state="normal")
                    except: pass
                
                # Cooldown
                self.root.after(5000, reactivar_boton)
                self.actualizar_vista_repartidor()

            # Boton despachar ejecuta metodo
            btn_despachar.config(command=ejecutar_despacho)

            # Si el pedido esta en camino
            if estado_p == "En camino":
                # No funciona el boton despachar
                btn_despachar.config(state="disabled")

            # Label para codigo
            ttk.Label(row, text="Código:", font=("Helvetica", 9, "bold")).grid(row=0, column=7, padx=(10, 2))
            # Entry para el codigo
            el_cod = ttk.Entry(row, width=6, font=("Helvetica", 10, "bold"), justify="center")
            el_cod.grid(row=0, column=8, padx=2)

            # Boton para entregar
            btn_entregar = ttk.Button(row, text="Entregar")
            btn_entregar.grid(row=0, column=9, padx=5)

            # Marcar entregado
            def ejecutar_entrega(ent=el_cod, mid=id_p):
                codigo_ingresado = ent.get().strip()
                # Si el codigo ingresado es correcto
                exito, msg = self.sistema.modificar_estado_pedido(mid, "Entregado", codigo_ingresado=codigo_ingresado)
                if exito:
                    messagebox.showinfo("Verificación Correcta", msg)
                    self.actualizar_vista_repartidor()
                else:
                    messagebox.showerror("Error de Código", msg)

            btn_entregar.config(command=lambda e=el_cod, m=id_p: ejecutar_entrega(e, m))

    # Pestaña administrador
    def crear_pestaña_administrador(self):
        # Frame para admin
        self.frame_tab_admin = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(self.frame_tab_admin, text=" Panel de Control Admin ")
        
        # Label principal
        ttk.Label(
            self.frame_tab_admin, 
            text="Sistema de Gestión Global de Cuentas (CRUD)", 
            font=("Helvetica", 16, "bold"), 
            foreground="#2E4053"
        ).pack(anchor="w", pady=(0, 15))

        # Frame principal de pestaña
        main_crud_frame = ttk.Frame(self.frame_tab_admin)
        main_crud_frame.pack(fill="both", expand=True)
        
        # Panel izquierdo de pestaña
        left_panel = ttk.LabelFrame(main_crud_frame, text=" Cuentas Registradas en el Archivo ", padding=15)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        columnas = ("usuario", "password", "rol")
        self.tree_usuarios = ttk.Treeview(left_panel, columns=columnas, show="headings", selectmode="browse")
        
        self.tree_usuarios.heading("usuario", text="Nombre de Usuario")
        self.tree_usuarios.heading("password", text="Contraseña Guardada")
        self.tree_usuarios.heading("rol", text="Rol del Sistema")
        
        self.tree_usuarios.column("usuario", minwidth=150, width=180, anchor="w")
        self.tree_usuarios.column("password", minwidth=120, width=150, anchor="center")
        self.tree_usuarios.column("rol", minwidth=130, width=160, anchor="center")
        
        scrollbar_tree = ttk.Scrollbar(left_panel, orient="vertical", command=self.tree_usuarios.yview)
        self.tree_usuarios.configure(yscrollcommand=scrollbar_tree.set)
        
        self.tree_usuarios.pack(side="left", fill="both", expand=True)
        scrollbar_tree.pack(side="right", fill="y")
        
        self.tree_usuarios.bind("<<TreeviewSelect>>", self._al_seleccionar_usuario_tree)

        # --- PANEL DERECHO: FORMULARIO INTERACTIVO ---
        right_panel = ttk.LabelFrame(main_crud_frame, text=" Operaciones de Registro ", padding=20)
        right_panel.pack(side="right", fill="both", padx=10, ipadx=10)
        
        ttk.Label(right_panel, text="Nombre de Usuario:", font=("Helvetica", 11, "bold")).pack(anchor="w", pady=5)
        self.ent_crud_user = ttk.Entry(right_panel, font=("Helvetica", 11), width=28)
        self.ent_crud_user.pack(fill="x", pady=5)
        
        ttk.Label(right_panel, text="Contraseña de Acceso:", font=("Helvetica", 11, "bold")).pack(anchor="w", pady=5)
        self.ent_crud_pass = ttk.Entry(right_panel, font=("Helvetica", 11), width=28)
        self.ent_crud_pass.pack(fill="x", pady=5)
        
        ttk.Label(right_panel, text="Rol Asignado:", font=("Helvetica", 11, "bold")).pack(anchor="w", pady=5)
        self.combo_crud_rol = ttk.Combobox(right_panel, values=["Usuario", "Repartidor", "Administrador"], state="readonly", font=("Helvetica", 11))
        self.combo_crud_rol.current(0)
        self.combo_crud_rol.pack(fill="x", pady=5)
        
        ttk.Separator(right_panel, orient="horizontal").pack(fill="x", pady=15)
        
        btn_add = ttk.Button(right_panel, text="Añadir Nueva Cuenta", command=self._crud_añadir_cuenta)
        btn_add.pack(fill="x", pady=4, ipady=4)
        
        btn_mod = ttk.Button(right_panel, text="Modificar Cuenta Seleccionada", command=self._crud_modificar_cuenta)
        btn_mod.pack(fill="x", pady=4, ipady=4)
        
        btn_del = ttk.Button(right_panel, text="Eliminar Cuenta", command=self._crud_eliminar_cuenta)
        btn_del.pack(fill="x", pady=4, ipady=4)
        
        btn_clear = ttk.Button(right_panel, text="Limpiar Formulario", command=self._limpiar_formulario_crud)
        btn_clear.pack(fill="x", pady=(15, 0))
        
        self.actualizar_tabla_usuarios_admin()

    # Actualizacion info usuarios
    def actualizar_tabla_usuarios_admin(self):
        for item in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(item)
            
        diccionario_usuarios = self.sistema.obtener_usuarios_sistema()
        for username, info in diccionario_usuarios.items():
            self.tree_usuarios.insert("", "end", values=(username, info["password"], info["rol"]))

    # Seleccion de usuarios
    def _al_seleccionar_usuario_tree(self, event):
        seleccion = self.tree_usuarios.selection()
        if not seleccion:
            return
        
        valores = self.tree_usuarios.item(seleccion[0], "values")
        if valores:
            self._limpiar_formulario_crud()
            self.ent_crud_user.insert(0, valores[0])
            self.ent_crud_pass.insert(0, valores[1])
            self.combo_crud_rol.set(valores[2])

    # Añadir cuenta
    def _crud_añadir_cuenta(self):
        # Informacion de campos
        user = self.ent_crud_user.get().strip()
        password = self.ent_crud_pass.get().strip()
        rol = self.combo_crud_rol.get()
        
        # Si no hay ni usuario ni contraseña
        if not user or not password:
            messagebox.showwarning("Campos Vacíos", "Se requiere ingresar un usuario y una contraseña válida.")
            return
        
        # Situacion de exito
        exito, msg = self.sistema.registrar_nuevo_usuario(user, password, rol)

        # Si hubo exito mensaje
        if exito:
            messagebox.showinfo("Operación Exitosa", msg)
            self.actualizar_tabla_usuarios_admin()
            self._limpiar_formulario_crud()
        # Si no hubo error
        else:
            messagebox.showerror("Error de Registro", msg)

    # Modificacion de cuenta
    def _crud_modificar_cuenta(self):
        # Informacion de campos
        user = self.ent_crud_user.get().strip()
        password = self.ent_crud_pass.get().strip()
        rol = self.combo_crud_rol.get()
        
        # Si no habia ni usuario ni contraseña
        if not user or not password:
            messagebox.showwarning("Campos Vacíos", "Seleccione un usuario de la lista e ingrese los nuevos datos.")
            return
        
        # Situacion Exito
        exito, msg = self.sistema.actualizar_datos_usuario(user, password, rol)
        
        # Mensajes
        if exito:
            messagebox.showinfo("Operación Exitosa", msg)
            self.actualizar_tabla_usuarios_admin()
            self._limpiar_formulario_crud()
        else:
            messagebox.showerror("Error de Modificación", msg)

    # Eliminar cuenta
    def _crud_eliminar_cuenta(self):
        # informacion usuario
        user = self.ent_crud_user.get().strip()
        
        # Si no hay usuario
        if not user:
            messagebox.showwarning("Sin Selección", "Escriba o seleccione el usuario que desea eliminar de la base de datos.")
            return
            
        # Mensaje de confirmacion
        confirmacion = messagebox.askyesno("Confirmar Eliminación", f"¿Está completamente seguro de eliminar permanentemente la cuenta '{user}'?")
        if not confirmacion:
            return
            
        # Situacion de exito
        exito, msg = self.sistema.remover_usuario_sistema(user)

        # Mensajes
        if exito:
            messagebox.showinfo("Operación Exitosa", msg)
            self.actualizar_tabla_usuarios_admin()
            self._limpiar_formulario_crud()
        else:
            messagebox.showerror("Error de Eliminación", msg)

    # Limpiar formulario admin
    def _limpiar_formulario_crud(self):
        self.ent_crud_user.delete(0, tk.END)
        self.ent_crud_pass.delete(0, tk.END)
        self.combo_crud_rol.current(0)

    # Cerrar sesion
    def cerrar_sesion(self):
        self.usuario_actual = None
        self.rol_actual = None
        self.mostrar_pantalla_login()


if __name__ == "__main__":##
    root = tk.Tk()
    
    # Inyección de Dependencias (DIP) desde la raíz del sistema
    persistencia_global = GestorPersistenciaJSON()
    auth_sub = SubsistemaAutenticacion(persistencia=persistencia_global)
    negocio_sub = SubsistemaNegocio(persistencia=persistencia_global)
    facade_sistema = DeliveryFacade(auth_subsystem=auth_sub, negocio_subsystem=negocio_sub)
    
    app = ICINFAppDelivery(root, sistema_facade=facade_sistema)
    root.mainloop()
