import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os
import random
from abc import ABC, abstractmethod

# =====================================================================
# PATRÓN STATE: Clases abstractas y concretas para el Estado del Pedido
# =====================================================================
class EstadoPedido(ABC):
    @abstractmethod
    def obtener_nombre(self) -> str:
        pass

    @abstractmethod
    def despachar(self, pedido) -> bool:
        pass

    @abstractmethod
    def entregar(self, pedido, codigo_ingresado: str) -> bool:
        pass

class EstadoPendiente(EstadoPedido):
    def obtener_nombre(self) -> str:
        return "Pendiente"

    def despachar(self, pedido) -> bool:
        pedido["Estado"] = "En camino"
        return True

    def entregar(self, pedido, codigo_ingresado: str) -> bool:
        return False  # No se puede entregar si aún está pendiente

class EstadoEnCamino(EstadoPedido):
    def obtener_nombre(self) -> str:
        return "En camino"

    def despachar(self, pedido) -> bool:
        return False  # Ya está en camino

    def entregar(self, pedido, codigo_ingresado: str) -> bool:
        if codigo_ingresado == pedido.get("codigo_entrega"):
            pedido["Estado"] = "Entregado"
            return True
        return False

class EstadoEntregado(EstadoPedido):
    def obtener_nombre(self) -> str:
        return "Entregado"

    def despachar(self, pedido) -> bool:
        return False

    def entregar(self, pedido, codigo_ingresado: str) -> bool:
        return False

# Factoría simple para mapear el string del JSON a la clase de Estado correspondiente
class EstadoFactory:
    @staticmethod
    def crear_estado(nombre_estado: str) -> EstadoPedido:
        if nombre_estado == "Pendiente":
            return EstadoPendiente()
        elif nombre_estado == "En camino":
            return EstadoEnCamino()
        elif nombre_estado == "Entregado":
            return EstadoEntregado()
        return EstadoPendiente()


# Clase Subsistema Autenticación
class SubsistemaAutenticacion:
    def __init__(self, archivo_usuarios="usuarios_data.json"):
        self.archivo = archivo_usuarios
        self._usuarios = {}
        self._cargar_y_asegurar_usuarios()

    def _cargar_y_asegurar_usuarios(self):
        self._cuentas_oficiales = {
            "admin": {"password": "123", "rol": "Administrador"},
            "user1": {"password": "123", "rol": "Usuario"},
            "Rep1": {"password": "123", "rol": "Repartidor"}
        }

        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, "r", encoding="utf-8") as f:
                    datos_cargados = json.load(f) 
                if not all(usuario in datos_cargados for usuario in self._cuentas_oficiales):
                    self._usuarios = datos_cargados
                    for k, v in self._cuentas_oficiales.items():
                        if k not in self._usuarios:
                            self._usuarios[k] = v
                    self._guardar_usuarios()
                else:
                    self._usuarios = datos_cargados
            except (json.JSONDecodeError, IOError):
                self._usuarios = self._cuentas_oficiales
                self._guardar_usuarios()
        else:
            self._usuarios = self._cuentas_oficiales
            self._guardar_usuarios()

    def _guardar_usuarios(self):
        try:
            with open(self.archivo, "w", encoding="utf-8") as f:
                json.dump(self._usuarios, f, indent=4, ensure_ascii=False)
        except IOError:
            print("Error al guardar usuarios.")

    def verificar_credenciales(self, usuario, password):
        if usuario in self._usuarios:
            datos = self._usuarios[usuario]
            if datos["password"] == password:
                return datos["rol"]
        return None
    
    def obtener_todos_los_usuarios(self):
        self._cargar_y_asegurar_usuarios()
        return self._usuarios

    def crear_usuario(self, usuario, password, rol):
        if usuario in self._usuarios:
            return False, "El nombre de usuario ya existe."
        self._usuarios[usuario] = {"password": password, "rol": rol}
        self._guardar_usuarios()
        return True, "Usuario creado con éxito."

    def modificar_usuario(self, usuario, password, rol):
        if usuario not in self._usuarios:
            return False, "El usuario no existe."
        self._usuarios[usuario] = {"password": password, "rol": rol}
        self._guardar_usuarios()
        return True, "Usuario modificado con éxito."
    
    def eliminar_usuario(self, usuario):
        if usuario == "admin":
            return False, "No puedes eliminar la cuenta de administrador principal."
        if usuario not in self._usuarios:
            return False, "El usuario no existe."
        del self._usuarios[usuario]
        self._guardar_usuarios()
        return True, "Usuario eliminado con éxito."


# Clase Subsistema Negocio
class SubsistemaNegocio:
    def __init__(self):
        self.arc_restaurantes = "restaurantes.json"
        self.arc_carrito = "carrito.json"
        self.arc_pedidos = "pedidos.json"
        self.restaurantes = {}
        self.carrito = []
        self.pedidos = []
        self._inicializar_y_asegurar_restantes()
        self._cargar_carrito()
        self._cargar_pedidos()

    def _inicializar_y_asegurar_restantes(self):
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

        if os.path.exists(self.arc_restaurantes):
            try:
                with open(self.arc_restaurantes, "r", encoding="utf-8") as f:
                    contenido = json.load(f)
                if not contenido or "Restaurante 1" not in contenido:
                    self.restaurantes = self._menu_defecto
                    self._guardar_json(self.arc_restaurantes, self.restaurantes)
                else:
                    self.restaurantes = contenido
            except (json.JSONDecodeError, IOError):
                self.restaurantes = self._menu_defecto
                self._guardar_json(self.arc_restaurantes, self.restaurantes)
        else:
            self.restaurantes = self._menu_defecto
            self._guardar_json(self.arc_restaurantes, self.restaurantes)

    def _cargar_carrito(self):
        if os.path.exists(self.arc_carrito):
            try:
                with open(self.arc_carrito, "r", encoding="utf-8") as f:
                    self.carrito = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.carrito = []
        else:
            self.carrito = []

    def _cargar_pedidos(self):
        if os.path.exists(self.arc_pedidos):
            try:
                with open(self.arc_pedidos, "r", encoding="utf-8") as f:
                    self.pedidos = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.pedidos = []

    def _guardar_json(self, ruta, datos):
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
        except IOError:
            print(f"Error al escribir en {ruta}")

    def agregar_al_carrito(self, comida, precio):
        item = {"comida": comida, "precio": precio}
        self.carrito.append(item)
        self._guardar_json(self.arc_carrito, self.carrito)

    def limpiar_carrito(self):
        self.carrito = []
        if os.path.exists(self.arc_carrito):
            try:
                os.remove(self.arc_carrito)
            except OSError:
                pass
    
    def registrar_pedido(self, usuario, total, direccion, metodo_pago):
        id_unico = f"PED-{random.randint(100000, 999999)}"
        codigo_verificacion = f"{random.randint(1000, 9999)}"
        
        nuevo_pedido = {
            "id_pedido": id_unico,
            "Nombre de usuario": usuario,
            "Valor del pedido": total,
            "Direccion": direccion,
            "Metodo de pago": metodo_pago,
            "Estado": "Pendiente",
            "codigo_entrega": codigo_verificacion
        }
        self.pedidos.append(nuevo_pedido)
        self._guardar_json(self.arc_pedidos, self.pedidos)
        self.limpiar_carrito()

    # Adaptación con el patrón State para transicionar de estado
    def intentar_despachar_pedido(self, id_pedido) -> bool:
        self._cargar_pedidos()
        for p in self.pedidos:
            if p["id_pedido"] == id_pedido:
                estado_actual = EstadoFactory.crear_estado(p["Estado"])
                if estado_actual.despachar(p): # Modifica internamente el string si es válido
                    self._guardar_json(self.arc_pedidos, self.pedidos)
                    return True
        return False

    def intentar_entregar_pedido(self, id_pedido, codigo_ingresado) -> bool:
        self._cargar_pedidos()
        for p in self.pedidos:
            if p["id_pedido"] == id_pedido:
                estado_actual = EstadoFactory.crear_estado(p["Estado"])
                if estado_actual.entregar(p, codigo_ingresado): # Modifica internamente si coincide token
                    self._guardar_json(self.arc_pedidos, self.pedidos)
                    return True
        return False


# =====================================================================
# PATRÓN SINGLETON + FACADE: Intermediario único del sistema
# =====================================================================
class DeliveryFacade:
    _instancia = None

    def __new__(cls, *args, **kwargs):
        if not cls._instancia:
            cls._instancia = super(DeliveryFacade, cls).__new__(cls, *args, **kwargs)
        return cls._instancia

    def __init__(self):
        # Evitar doble inicialización debido al Singleton
        if not hasattr(self, '_inicializado'):
            self.auth = SubsistemaAutenticacion()
            self.negocio = SubsistemaNegocio()
            self._inicializado = True

    def autenticar_credenciales(self, usuario, password):
        return self.auth.verificar_credenciales(usuario, password)

    def obtener_usuarios_sistema(self):
        return self.auth.obtener_todos_los_usuarios()
    
    def registrar_nuevo_usuario(self, usuario, password, rol):
        return self.auth.crear_usuario(usuario, password, rol)

    def actualizar_datos_usuario(self, usuario, password, rol):
        return self.auth.modificar_usuario(usuario, password, rol)

    def remover_usuario_sistema(self, usuario):
        return self.auth.eliminar_usuario(usuario)

    def obtener_restaurantes(self):
        return self.negocio.restaurantes

    def añadir_item_carrito(self, comida, precio):
        self.negocio.agregar_al_carrito(comida, precio)

    def obtener_carrito(self):
        self.negocio._cargar_carrito()
        return self.negocio.carrito

    def obtener_total_carrito(self):
        return sum(item["precio"] for item in self.obtener_carrito())

    def vaciar_carrito_local(self):
        self.negocio.limpiar_carrito()

    def procesar_finalizar_pedido(self, usuario, total, direccion, metodo_pago):
        self.negocio.registrar_pedido(usuario, total, direccion, metodo_pago)

    def obtener_todos_los_pedidos(self):
        self.negocio._cargar_pedidos()
        return self.negocio.pedidos

    # Métodos delegados adaptados al patrón State
    def despachar_pedido(self, id_pedido):
        return self.negocio.intentar_despachar_pedido(id_pedido)

    def entregar_pedido(self, id_pedido, codigo_ingresado):
        return self.negocio.intentar_entregar_pedido(id_pedido, codigo_ingresado)


# Clase ICINF App Delivery: Interfaz Gráfica (Se mantiene prácticamente idéntica)
class ICINFAppDelivery:
    def __init__(self, root):
        self.root = root
        self.root.title("ICINF App Delivery")
        self.root.state('zoomed')
        
        # Ahora llamamos a la instancia Singleton de la Facade
        self.sistema = DeliveryFacade()
        
        self.usuario_actual = None
        self.rol_actual = None
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)
        
        self.mostrar_pantalla_login()

    def limpiar_contenedor(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def mostrar_pantalla_login(self):
        self.limpiar_contenedor()
        
        login_frame = ttk.Frame(self.main_container, padding=40)
        login_frame.pack(fill="both", expand=True)
        
        ttk.Label(login_frame, text="ICINF App Delivery", font=("Helvetica", 32, "bold"), foreground="#1F618D").pack(pady=30)
        
        form_panel = ttk.LabelFrame(login_frame, text=" Control de Acceso ", padding=40)
        form_panel.pack(pady=20, ipadx=20)
        
        ttk.Label(form_panel, text="Nombre de Usuario:", font=("Helvetica", 13)).grid(row=0, column=0, sticky="w", pady=15)
        entry_user = ttk.Entry(form_panel, font=("Helvetica", 13), width=35)
        entry_user.grid(row=0, column=1, pady=15, padx=15)
        entry_user.focus()
        
        ttk.Label(form_panel, text="Contraseña de Acceso:", font=("Helvetica", 13)).grid(row=1, column=0, sticky="w", pady=15)
        entry_pass = ttk.Entry(form_panel, font=("Helvetica", 13), show="*", width=35)
        entry_pass.grid(row=1, column=1, pady=15, padx=15)
        
        def ejecutar_login():
            user = entry_user.get().strip()
            password = entry_pass.get()
            
            if not user or not password:
                messagebox.showwarning("Campos Requeridos", "Por favor, complete todas las credenciales.")
                return
            
            rol_detectado = self.sistema.autenticar_credenciales(user, password)

            if rol_detectado:
                self.usuario_actual = user
                self.rol_actual = rol_detectado
                self.mostrar_sistema_pestanas()
            else:
                messagebox.showerror("Fallo de Autenticación", "Las credenciales ingresadas son incorrectas.")

        btn_ingresar = ttk.Button(form_panel, text="Iniciar Sesión", command=ejecutar_login)
        btn_ingresar.grid(row=2, column=0, columnspan=2, pady=25, sticky="ew", ipady=10)
        
        btn_salir = ttk.Button(login_frame, text="Salir de la Aplicación", command=self.root.quit)
        btn_salir.pack(pady=20, ipadx=25, ipady=8)

    def mostrar_sistema_pestanas(self):
        self.limpiar_contenedor()
        
        app_frame = ttk.Frame(self.main_container, padding=20)
        app_frame.pack(fill="both", expand=True)
        
        top_bar = ttk.Frame(app_frame)
        top_bar.pack(fill="x", pady=(0, 15))
        
        lbl_welcome = ttk.Label(top_bar, text=f"Conectado: {self.usuario_actual} ({self.rol_actual})", font=("Helvetica", 14, "bold"))
        lbl_welcome.pack(side="left")
        
        btn_logout = ttk.Button(top_bar, text="Cerrar Sesión", command=self.cerrar_sesion)
        btn_logout.pack(side="right", ipady=5)
        
        self.notebook = ttk.Notebook(app_frame)
        self.notebook.pack(fill="both", expand=True)
        
        if self.rol_actual == "Usuario":
            self.crear_pestaña_usuario()
        elif self.rol_actual == "Repartidor":
            self.crear_pestaña_repartidor()
        elif self.rol_actual == "Administrador":
            self.crear_pestaña_usuario()
            self.crear_pestaña_repartidor()
            self.crear_pestaña_administrador()

    def crear_pestaña_usuario(self):
        self.frame_tab_usuario = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(self.frame_tab_usuario, text=" Vista de Usuario ")
        
        self.sub_notebook_usuario = ttk.Notebook(self.frame_tab_usuario)
        self.sub_notebook_usuario.pack(fill="both", expand=True)
        
        self.pane_catalogo = ttk.Frame(self.sub_notebook_usuario, padding=10)
        self.pane_mis_pedidos = ttk.Frame(self.sub_notebook_usuario, padding=10)
        
        self.sub_notebook_usuario.add(self.pane_catalogo, text=" Catálogo y Tiendas ")
        self.sub_notebook_usuario.add(self.pane_mis_pedidos, text=" Mis Pedidos Activos ")
        
        self.sub_notebook_usuario.bind("<<NotebookTabChanged>>", self._al_cambiar_subpestaña_usuario)
        self.cargar_vista_restaurantes()

    def _al_cambiar_subpestaña_usuario(self, event):
        pestaña_seleccionada = self.sub_notebook_usuario.index(self.sub_notebook_usuario.select())
        if pestaña_seleccionada == 1:
            self.cargar_historial_pedidos_usuario()

    def cargar_vista_restaurantes(self):
        for widget in self.pane_catalogo.winfo_children():
            widget.destroy()
            
        content_view = ttk.Frame(self.pane_catalogo)
        content_view.pack(fill="both", expand=True)
        
        nav_bar = ttk.Frame(content_view)
        nav_bar.pack(fill="x", pady=10)
        
        cant_items = len(self.sistema.obtener_carrito())
        btn_ir_carrito = ttk.Button(nav_bar, text=f"Ver mi Carrito ({cant_items} items)", command=self.cargar_vista_carrito_aislado)
        btn_ir_carrito.pack(side="right", padx=20, ipady=5)
        
        ttk.Label(content_view, text="Selecciona un Restaurante para ver su menú", font=("Helvetica", 18, "bold"), foreground="#2C3E50").pack(pady=10)
        
        cards_container = ttk.Frame(content_view)
        cards_container.pack(fill="x", expand=True, padx=40)
        
        dict_restaurantes = self.sistema.obtener_restaurantes()

        calificaciones_rest = {
            "Restaurante 1": "★ ★ ★ ★ ☆ (4 Estrellas)",
            "Restaurante 2": "★ ★ ★ ★ ★ (5 Estrellas)",
            "Restaurante 3": "★ ★ ★ ☆ ☆ (3 Estrellas)"
        }
        
        for indice, (nombre_rest, datos) in enumerate(dict_restaurantes.items()):
            cards_container.columnconfigure(indice, weight=1)
            card = ttk.LabelFrame(cards_container, text=f" {nombre_rest} ", padding=20)
            card.grid(row=0, column=indice, padx=20, pady=20, sticky="nsew")
            
            texto_rating = calificaciones_rest.get(nombre_rest, "★ ★ ★ ★ ☆")
            color_rating = "#F39C12" if "3" not in texto_rating else "#E67E22"
            
            ttk.Label(card, text=texto_rating, font=("Helvetica", 13, "bold"), foreground=color_rating).pack(pady=10)
            
            btn_menu = ttk.Button(card, text="Ver Menú", command=lambda name=nombre_rest: self.cargar_vista_menu(name))
            btn_menu.pack(pady=10, fill="x", ipady=8)

    def cargar_vista_menu(self, nombre_restaurante):
        for widget in self.pane_catalogo.winfo_children():
            widget.destroy()
            
        content_view = ttk.Frame(self.pane_catalogo)
        content_view.pack(fill="both", expand=True)
        
        top_nav = ttk.Frame(content_view)
        top_nav.pack(fill="x", padx=20, pady=10)
        
        btn_back = ttk.Button(top_nav, text="Volver a Restaurantes", command=self.cargar_vista_restaurantes)
        btn_back.pack(side="left")
        
        cant_items = len(self.sistema.obtener_carrito())
        btn_ir_carrito = ttk.Button(top_nav, text=f"Ir al Carrito ({cant_items})", command=self.cargar_vista_carrito_aislado)
        btn_ir_carrito.pack(side="right", ipady=5)
        
        menu_panel = ttk.LabelFrame(content_view, text=f" Menú de {nombre_restaurante} ", padding=25)
        menu_panel.pack(fill="both", expand=True, padx=40, pady=20)
        
        lista_comidas = self.sistema.obtener_restaurantes()[nombre_restaurante]["Menú"]
        
        for item in lista_comidas:
            row_frame = ttk.Frame(menu_panel, padding=10)
            row_frame.pack(fill="x", pady=5)
            lbl_info = ttk.Label(row_frame, text=f"{item['comida']} — ${item['precio']:,}".replace(",", "."), font=("Helvetica", 12, "bold"))
            lbl_info.pack(side="left")
            btn_add = ttk.Button(row_frame, text="Añadir al carrito", command=lambda c=item['comida'], p=item['precio']: [self.sistema.añadir_item_carrito(c, p), self.cargar_vista_menu(nombre_restaurante)])
            btn_add.pack(side="right", padx=10)

    def cargar_vista_carrito_aislado(self):
        for widget in self.pane_catalogo.winfo_children():
            widget.destroy()
            
        content_view = ttk.Frame(self.pane_catalogo, padding=20)
        content_view.pack(fill="both", expand=True)
        
        btn_back = ttk.Button(content_view, text="Seguir Comprando (Inicio)", command=self.cargar_vista_restaurantes)
        btn_back.pack(anchor="w", pady=10)
        
        cart_panel = ttk.LabelFrame(content_view, text=" Revisión de tu Carrito de Compras ", padding=30)
        cart_panel.pack(fill="both", expand=True, padx=50, pady=10)
        
        items_carrito = self.sistema.obtener_carrito()

        txt_area = tk.Text(cart_panel, font=("Helvetica", 12), height=12)
        txt_area.pack(fill="both", expand=True, pady=10)
        
        if not items_carrito:
            txt_area.insert("1.0", "Tu carrito actual se encuentra vacío.\n¡Vuelve al catálogo para agregar alimentos!")
            txt_area.config(state="disabled")
            btn_empty = ttk.Button(cart_panel, text="Vaciar Carrito", state="disabled")
            btn_empty.pack(side="left", pady=10)
        else:
            for item in items_carrito:
                txt_area.insert("end", f"• {item['comida']} (${item['precio']:,})\n".replace(",", "."))
            txt_area.config(state="disabled")
            
            total = self.sistema.obtener_total_carrito()
            ttk.Label(cart_panel, text=f"Subtotal a pagar: ${total:,}".replace(",", "."), font=("Helvetica", 15, "bold"), foreground="#27AE60").pack(pady=10)
            
            actions_frame = ttk.Frame(cart_panel)
            actions_frame.pack(fill="x", pady=10)
            
            def vaciar():
                self.sistema.vaciar_carrito_local()
                self.cargar_vista_carrito_aislado()
                
            btn_empty = ttk.Button(actions_frame, text="Vaciar Carrito", command=vaciar)
            btn_empty.pack(side="left", padx=10, ipady=5)
            
            btn_order = ttk.Button(actions_frame, text="Realizar pedido / Ir a Pagar", command=self.cargar_vista_pagos)
            btn_order.pack(side="right", padx=10, ipady=5)

    def cargar_vista_pagos(self):
        for widget in self.pane_catalogo.winfo_children():
            widget.destroy()
            
        pay_panel = ttk.LabelFrame(self.pane_catalogo, text=" Checkout — Formulario de Pago Pasarela Redcompra ", padding=30)
        pay_panel.pack(pady=40, padx=100)
        
        total_pagar = self.sistema.obtener_total_carrito()
        ttk.Label(pay_panel, text=f"Monto Total a Pagar: ${total_pagar:,} CLP".replace(",", "."), font=("Helvetica", 16, "bold"), foreground="#C0392B").pack(pady=15)
        
        form_grid = ttk.Frame(pay_panel)
        form_grid.pack(pady=10)
        
        def validar_calle(texto_entrante):
            if texto_entrante == "": return True
            for char in texto_entrante:
                if not (char.isalnum() or char in "  áéíóúÁÉÍÓÚñÑüÜ"): return False
            return True

        def validar_numero(texto_entrante):
            if texto_entrante == "": return True
            return texto_entrante.isdigit()

        reg_calle = self.root.register(validar_calle)
        reg_numero = self.root.register(validar_numero)
        
        ttk.Label(form_grid, text="Método de Pago:", font=("Helvetica", 12)).grid(row=0, column=0, sticky="w", pady=10)
        combo_metodo = ttk.Combobox(form_grid, values=["Tarjeta de Débito (Redcompra)", "Efectivo"], state="readonly", font=("Helvetica", 11))
        combo_metodo.current(0)
        combo_metodo.grid(row=0, column=1, pady=10, padx=10, sticky="w")
        
        lbl_tarjeta_titulo = ttk.Label(form_grid, text="Tarjeta:", font=("Helvetica", 11))
        lbl_tarjeta_titulo.grid(row=1, column=0, sticky="w", pady=5)
        
        lbl_tarjeta_valor = tk.Label(
            form_grid, text="Cuenta Rut (1)", font=("Helvetica", 11, "bold"), 
            bg="#EAECEE", fg="#2C3E50", relief="sunken", anchor="w", padx=10, width=26
        )
        lbl_tarjeta_valor.grid(row=1, column=1, pady=5, padx=10, sticky="w")
        
        ttk.Label(form_grid, text="Calle de Despacho:", font=("Helvetica", 12)).grid(row=2, column=0, sticky="w", pady=10)
        entry_calle = ttk.Entry(form_grid, font=("Helvetica", 12), width=30, validate="key", validatecommand=(reg_calle, "%P"))
        entry_calle.grid(row=2, column=1, pady=10, padx=10, sticky="w")
        entry_calle.focus()
        
        ttk.Label(form_grid, text="Número / Depto:", font=("Helvetica", 12)).grid(row=3, column=0, sticky="w", pady=10)
        entry_numero = ttk.Entry(form_grid, font=("Helvetica", 12), width=15, validate="key", validatecommand=(reg_numero, "%P"))
        entry_numero.grid(row=3, column=1, pady=10, padx=10, sticky="w")

        def cambiar_metodo_pago(event):
            if combo_metodo.get() == "Efectivo":
                lbl_tarjeta_titulo.grid_remove()
                lbl_tarjeta_valor.grid_remove()
            else:
                lbl_tarjeta_titulo.grid(row=1, column=0, sticky="w", pady=5)
                lbl_tarjeta_valor.grid(row=1, column=1, pady=5, padx=10, sticky="w")

        combo_metodo.bind("<<ComboboxSelected>>", cambiar_metodo_pago)
        
        def procesar_pago():
            calle = entry_calle.get().strip()
            numero = entry_numero.get().strip()
            metodo_elegido = combo_metodo.get()
            
            if not calle or not numero:
                messagebox.showwarning("Campos Requeridos", "Por favor, complete la Calle y el Número para realizar el despacho.")
                return
            
            direccion_completa = f"{calle} #{numero}"
            self.sistema.procesar_finalizar_pedido(self.usuario_actual, total_pagar, direccion_completa, metodo_elegido)
            
            messagebox.showinfo("Transacción Exitosa", "Pago Realizado con Éxito. Revisa su código en la pestaña 'Mis Pedidos Activos'.")
            self.cargar_vista_restaurantes()
            self.sub_notebook_usuario.select(1)

        btn_confirmar = ttk.Button(pay_panel, text="Proceder al pago", command=procesar_pago)
        btn_confirmar.pack(fill="x", pady=20, ipady=8)
        
        btn_abort = ttk.Button(pay_panel, text="Cancelar y Volver al Carrito", command=self.cargar_vista_carrito_aislado)
        btn_abort.pack()

    def cargar_historial_pedidos_usuario(self):
        for widget in self.pane_mis_pedidos.winfo_children():
            widget.destroy()
            
        ttk.Label(self.pane_mis_pedidos, text="Tus Pedidos en Curso y Códigos de Verificación", font=("Helvetica", 16, "bold"), foreground="#2E4053").pack(pady=10)

        color_fondo_sistema = self.style.lookup("TFrame", "background")
        canvas = tk.Canvas(self.pane_mis_pedidos, borderwidth=0, highlightthickness=0, bg=color_fondo_sistema)
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

    def crear_pestaña_repartidor(self):
        self.frame_tab_repartidor = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.frame_tab_repartidor, text=" Vista Repartidor ")
        self.actualizar_vista_repartidor()

    def actualizar_vista_repartidor(self):
        for widget in self.frame_tab_repartidor.winfo_children():
            widget.destroy()

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

        if not pedidos_activos:
            lbl_no_pedidos = ttk.Label(scrollable_frame, text="No hay pedidos pendientes ni en camino en el sistema actualmente.", font=("Helvetica", 12, "italic"), foreground="gray")
            lbl_no_pedidos.pack(pady=30)
            return

        for idx, pedido in enumerate(pedidos_activos):
            id_p = pedido["id_pedido"]
            estado_p = pedido["Estado"]
            codigo_correcto = pedido.get("codigo_entrega", "0000")

            row = ttk.Frame(scrollable_frame, padding=5, relief="solid", borderwidth=1)
            row.pack(fill="x", pady=4)

            ttk.Label(row, text=id_p, font=("Helvetica", 10, "bold"), width=12, anchor="center").grid(row=0, column=0)
            ttk.Label(row, text=pedido["Nombre de usuario"], font=("Helvetica", 10), width=15, anchor="w").grid(row=0, column=1)
            ttk.Label(row, text=f"${pedido['Valor del pedido']:,}".replace(",", "."), font=("Helvetica", 10), width=12, anchor="center").grid(row=0, column=2)
            ttk.Label(row, text=pedido["Direccion"], font=("Helvetica", 10), width=25, anchor="w").grid(row=0, column=3)
            ttk.Label(row, text=pedido["Metodo de pago"], font=("Helvetica", 10), width=12, anchor="center").grid(row=0, column=4)
            
            color_estado = "#E67E22" if estado_p == "Pendiente" else "#2980B9"
            lbl_est = ttk.Label(row, text=estado_p, font=("Helvetica", 10, "bold"), width=15, anchor="center", foreground=color_estado)
            lbl_est.grid(row=0, column=5)

            btn_despachar = ttk.Button(row, text="Despachar")
            btn_despachar.grid(row=0, column=6, padx=5)

            def ejecutar_despacho(b=btn_despachar, mid=id_p):
                # Uso del nuevo método State mediante la Facade
                if self.sistema.despachar_pedido(mid):
                    b.config(state="disabled")
                    def reactivar_boton():
                        try: b.config(state="normal")
                        except: pass
                    self.root.after(5000, reactivar_boton)
                    self.actualizar_vista_repartidor()

            btn_despachar.config(command=ejecutar_despacho)

            if estado_p == "En camino":
                btn_despachar.config(state="disabled")

            ttk.Label(row, text="Código:", font=("Helvetica", 9, "bold")).grid(row=0, column=7, padx=(10, 2))
            el_cod = ttk.Entry(row, width=6, font=("Helvetica", 10, "bold"), justify="center")
            el_cod.grid(row=0, column=8, padx=2)

            btn_entregar = ttk.Button(row, text="Entregar")
            btn_entregar.grid(row=0, column=9, padx=5)

            def ejecutar_entrega(ent=el_cod, mid=id_p):
                codigo_ingresado = ent.get().strip()
                # Uso del nuevo método State mediante la Facade
                if self.sistema.entregar_pedido(mid, codigo_ingresado):
                    messagebox.showinfo("Verificación Correcta", f"Pedido {mid} verificado y entregado con éxito.")
                    self.actualizar_vista_repartidor()
                else:
                    messagebox.showerror("Error de Código", "El código ingresado es incorrecto o la transición no es válida.")

            btn_entregar.config(command=lambda e=el_cod, m=id_p: ejecutar_entrega(e, m))

    def crear_pestaña_administrador(self):
        self.frame_tab_admin = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(self.frame_tab_admin, text=" Panel de Control Admin ")
        
        ttk.Label(
            self.frame_tab_admin, 
            text="Sistema de Gestión Global de Cuentas (CRUD)", 
            font=("Helvetica", 16, "bold"), 
            foreground="#2E4053"
        ).pack(anchor="w", pady=(0, 15))

        main_crud_frame = ttk.Frame(self.frame_tab_admin)
        main_crud_frame.pack(fill="both", expand=True)
        
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

    def actualizar_tabla_usuarios_admin(self):
        for item in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(item)
            
        diccionario_usuarios = self.sistema.obtener_usuarios_sistema()
        for username, info in diccionario_usuarios.items():
            self.tree_usuarios.insert("", "end", values=(username, info["password"], info["rol"]))

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

    def _crud_añadir_cuenta(self):
        user = self.ent_crud_user.get().strip()
        password = self.ent_crud_pass.get().strip()
        rol = self.combo_crud_rol.get()
        
        if not user or not password:
            messagebox.showwarning("Campos Vacíos", "Se requiere ingresar un usuario y una contraseña válida.")
            return
        
        exito, msg = self.sistema.registrar_nuevo_usuario(user, password, rol)

        if exito:
            messagebox.showinfo("Operación Exitosa", msg)
            self.actualizar_tabla_usuarios_admin()
            self._limpiar_formulario_crud()
        else:
            messagebox.showerror("Error de Registro", msg)

    def _crud_modificar_cuenta(self):
        user = self.ent_crud_user.get().strip()
        password = self.ent_crud_pass.get().strip()
        rol = self.combo_crud_rol.get()
        
        if not user or not password:
            messagebox.showwarning("Campos Vacíos", "Seleccione un usuario de la lista e ingrese los nuevos datos.")
            return
        
        exito, msg = self.sistema.actualizar_datos_usuario(user, password, rol)
        
        if exito:
            messagebox.showinfo("Operación Exitosa", msg)
            self.actualizar_tabla_usuarios_admin()
            self._limpiar_formulario_crud()
        else:
            messagebox.showerror("Error de Modificación", msg)

    def _crud_eliminar_cuenta(self):
        user = self.ent_crud_user.get().strip()
        
        if not user:
            messagebox.showwarning("Sin Selección", "Escriba o seleccione el usuario que desea eliminar de la base de datos.")
            return
            
        confirmacion = messagebox.askyesno("Confirmar Eliminación", f"¿Está completamente seguro de eliminar permanentemente la cuenta '{user}'?")
        if not confirmacion:
            return
            
        exito, msg = self.sistema.remover_usuario_sistema(user)

        if exito:
            messagebox.showinfo("Operación Exitosa", msg)
            self.actualizar_tabla_usuarios_admin()
            self._limpiar_formulario_crud()
        else:
            messagebox.showerror("Error de Eliminación", msg)

    def _limpiar_formulario_crud(self):
        self.ent_crud_user.delete(0, tk.END)
        self.ent_crud_pass.delete(0, tk.END)
        self.combo_crud_rol.current(0)

    def cerrar_sesion(self):
        self.usuario_actual = None
        self.rol_actual = None
        self.mostrar_pantalla_login()


if __name__ == "__main__":
    root = tk.Tk()
    app = ICINFAppDelivery(root)
    root.mainloop()
