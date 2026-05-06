import tkinter as tk
from tkinter import ttk, messagebox
import uuid
import re

# ===================== MODELO =====================

class Usuario:
    def __init__(self, nombre, telefono):
        self.nombre = nombre
        self.telefono = telefono

class Producto:
    def __init__(self, nombre, precio, categoria):
        self.nombre = nombre
        self.precio = precio
        self.categoria = categoria

class Pedido:
    def __init__(self, usuario):
        self.id = str(uuid.uuid4())
        self.usuario = usuario
        self.items = []
        self.estado = "Pendiente"
        self.total = 0

    def agregar_producto(self, producto, cantidad):
        self.items.append((producto, cantidad))

    def calcular_total(self):
        self.total = sum(p.precio * c for p, c in self.items)
        return self.total

    def confirmar(self):
        self.estado = "Confirmado"

# ===================== PAGOS =====================

class TipoPago:
    def pagar(self, monto):
        raise NotImplementedError

class Efectivo(TipoPago):
    def pagar(self, monto):
        return f"Pago en efectivo: ${monto}"

class Transferencia(TipoPago):
    def pagar(self, monto):
        return f"Transferencia: ${monto}"

class Credito(TipoPago):
    def pagar(self, monto):
        return f"Tarjeta: ${monto}"

class Pago:
    def __init__(self, tipo):
        self.tipo = tipo

    def procesar(self, monto):
        return self.tipo.pagar(monto)

class Restaurante:
    def __init__(self):
        self.productos = []

    def agregar_producto(self, producto):
        self.productos.append(producto)

    def obtener_por_categoria(self, categoria):
        return [p for p in self.productos if p.categoria == categoria]

# ===================== INTERFAZ =====================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("ICINF Delivery")
        self.root.geometry("1100x720")
        self.root.configure(bg="#1e1e2f")

        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TLabel", background="#1e1e2f", foreground="white")

        self.restaurante = Restaurante()
        self.cargar_menu()
        self.pedidos = []

        self.crear_layout()

    def cargar_menu(self):
        datos = [
            ("Hamburguesa", 3000, "Comida"),
            ("Pizza", 5000, "Comida"),
            ("Completo", 2000, "Comida"),
            ("Papas Fritas", 1500, "Snacks"),
            ("Empanada", 1800, "Snacks"),
            ("Pollo Frito", 4500, "Comida"),
            ("Bebida", 1000, "Bebidas"),
            ("Jugo Natural", 2000, "Bebidas"),
            ("Combo Burger", 6000, "Combos"),
            ("Combo Pizza", 8000, "Combos")
        ]
        for n, p, c in datos:
            self.restaurante.agregar_producto(Producto(n, p, c))

    def crear_layout(self):
        header = tk.Frame(self.root, bg="#111122", height=60)
        header.pack(fill="x")

        tk.Label(header, text=" ICINF DELIVERY", fg="white", bg="#111122",
                 font=("Segoe UI", 20, "bold")).pack(pady=10)

        main = tk.Frame(self.root, bg="#1e1e2f")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(main, bg="#2a2a40")
        left.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(left, text="Datos", bg="#2a2a40", fg="white").pack(pady=5)

        self.nombre = self.crear_entry(left, "Nombre")
        self.telefono = self.crear_entry(left, "Teléfono")

        self.categoria = ttk.Combobox(left, values=["Comida", "Snacks", "Bebidas", "Combos"], state="readonly")
        self.categoria.pack(pady=5)
        self.categoria.bind("<<ComboboxSelected>>", self.actualizar_productos)

        self.producto = ttk.Combobox(left, state="readonly")
        self.producto.pack(pady=5)

        self.cantidad = self.crear_entry(left, "Cantidad")

        self.tipo_pago = ttk.Combobox(left, values=["Efectivo", "Transferencia", "Credito"], state="readonly")
        self.tipo_pago.pack(pady=5)

        ttk.Button(left, text="Crear Pedido", command=self.crear_pedido).pack(pady=10)

        right = tk.Frame(main, bg="#2a2a40")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.tabla = ttk.Treeview(right, columns=("Cliente", "Producto", "Cantidad", "Total", "Estado"), show="headings")
        for col in self.tabla["columns"]:
            self.tabla.heading(col, text=col)
        self.tabla.pack(fill="both", expand=True)

    def crear_entry(self, parent, label):
        tk.Label(parent, text=label, bg="#2a2a40", fg="white").pack()
        entry = tk.Entry(parent)
        entry.pack(pady=5)
        return entry

    def actualizar_productos(self, event):
        productos = self.restaurante.obtener_por_categoria(self.categoria.get())
        self.producto['values'] = [p.nombre for p in productos]

    def validar_nombre(self, nombre):
        return bool(re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]{3,}", nombre))

    def validar_telefono(self, telefono):
        return bool(re.fullmatch(r"\d{8,12}", telefono))

    def validar_cantidad(self, cantidad):
        return cantidad.isdigit() and int(cantidad) > 0

    def obtener_producto(self, nombre):
        for p in self.restaurante.productos:
            if p.nombre == nombre:
                return p

    def crear_pedido(self):
        nombre = self.nombre.get()
        telefono = self.telefono.get()
        prod = self.producto.get()
        cantidad = self.cantidad.get()
        tipo = self.tipo_pago.get()

        if not self.validar_nombre(nombre):
            messagebox.showerror("Error", "Nombre inválido")
            return
        if not self.validar_telefono(telefono):
            messagebox.showerror("Error", "Teléfono inválido")
            return
        if not prod or not self.validar_cantidad(cantidad):
            messagebox.showerror("Error", "Producto o cantidad inválida")
            return
        if not tipo:
            messagebox.showerror("Error", "Selecciona método de pago")
            return

        usuario = Usuario(nombre, telefono)
        pedido = Pedido(usuario)
        producto = self.obtener_producto(prod)

        pedido.agregar_producto(producto, int(cantidad))
        total = pedido.calcular_total()

        # confirmación antes de pagar
        if not messagebox.askyesno("Confirmar", f"Total: ${total}\n¿Continuar al pago?"):
            return

        if tipo == "Efectivo":
            pago = Pago(Efectivo())
        elif tipo == "Transferencia":
            pago = Pago(Transferencia())
        else:
            pago = Pago(Credito())

        mensaje = pago.procesar(total)
        pedido.confirmar()

        self.pedidos.append(pedido)

        self.tabla.insert("", "end", values=(nombre, prod, cantidad, f"${total}", pedido.estado))

        messagebox.showinfo("Pago realizado", mensaje)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()