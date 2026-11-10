import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import bd
import security
import datetime

class AplicacionBiblioteca:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de biblioteca")
        self.root.geometry("1200x750")
        self.root.minsize(800, 500)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tab_libros = ttk.Frame(self.notebook)
        self.tab_personas = ttk.Frame(self.notebook)
        self.tab_prestamos = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_libros, text="📚 Gestión de Libros")
        self.notebook.add(self.tab_personas, text="👥 Registro de Personas")
        self.notebook.add(self.tab_prestamos, text="🔄 Préstamos")
        
        self.construir_tab_libros()
        self.construir_tab_personas()
        self.construir_tab_prestamos()

    # =========================================================
    # TAB 1: LIBROS
    # =========================================================
    def construir_tab_libros(self):
        toolbar = ttk.Frame(self.tab_libros)
        toolbar.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(toolbar, text="➕ Dar alta", command=lambda: self.abrir_form_libro()).pack(side='left', padx=5)
        ttk.Button(toolbar, text="📁 Cargar", command=self.evento_carga_lote_libros).pack(side='left', padx=5)
        ttk.Button(toolbar, text="✏️ Modificar", command=self.evento_modificar_libro).pack(side='left', padx=5)
        ttk.Button(toolbar, text="🗑️ Borrar", command=self.evento_borrar_libro).pack(side='left', padx=5)
        ttk.Button(toolbar, text="🔄 Recargar", command=self.evento_mostrar_todos_libros).pack(side='left', padx=5)
        # Búsqueda combinada: ID, título, autor o sinopsis
        self.ent_buscar_libro = ttk.Entry(toolbar, width=60)
        self.ent_buscar_libro.pack(side='left', padx=(15, 5))
        self.ent_buscar_libro.bind("<Return>", lambda e: self.evento_buscar_libro())
        ttk.Button(toolbar, text="🔍 Buscar", command=self.evento_buscar_libro).pack(side='left', padx=5)

        frame_tabla = ttk.Frame(self.tab_libros)
        frame_tabla.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        columnas = ("id", "titulo", "autor", "genero", "disponible")
        self.tree_libros = ttk.Treeview(frame_tabla, columns=columnas, show='headings', selectmode='browse')
        self.tree_libros.heading("id", text="ID")
        self.tree_libros.heading("titulo", text="Título")
        self.tree_libros.heading("autor", text="Autor")
        self.tree_libros.heading("genero", text="Género")
        self.tree_libros.heading("disponible", text="Disponible")
        
        self.tree_libros.column("id", width=100, anchor='center')
        self.tree_libros.column("titulo", width=400)
        self.tree_libros.column("autor", width=250)
        self.tree_libros.column("genero", width=150, anchor='center')
        self.tree_libros.column("disponible", width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree_libros.yview)
        self.tree_libros.configure(yscrollcommand=scrollbar.set)
        self.tree_libros.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Doble clic sobre un libro abre la ventana de modificar (ignora encabezados y espacio vacío)
        def al_doble_clic_libro(event):
            if self.tree_libros.identify_row(event.y):
                self.evento_modificar_libro()
        self.tree_libros.bind("<Double-1>", al_doble_clic_libro)



    def abrir_form_libro(self, libro_data=None):
        ventana = tk.Toplevel(self.root)
        ventana.title("Modificar Libro" if libro_data else "Alta de Libro Nuevo")
        ventana.geometry("1000x500")
        ventana.resizable(False, False)
        ventana.grab_set() 
        
        frame = ttk.LabelFrame(ventana, text="Datos del Libro", padding=15)
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.vars_libro = {}
        campos = [
            ("ID*:", "id"), ("ISBN:", "isbn"), ("Título*:", "titulo"), 
            ("Autor*:", "autor"), ("Año*:", "anio"), ("Editorial:", "editorial"), 
            ("Género*:", "genero", ["ciencia ficcion", "fantasia", "misterio", "terror", "no ficcion", "clasico"]), 
            ("Tema*:", "tema"), ("Idioma:", "idioma"), 
            ("Tipo de Pasta:", "pasta", ["blanda", "dura", "digital"]), 
            ("Páginas:", "paginas")
        ]
        
        fila, columna = 0, 0
        for item in campos:
            ttk.Label(frame, text=item[0]).grid(row=fila, column=columna, sticky='e', padx=5, pady=10)
            if len(item) == 3:
                self.vars_libro[item[1]] = ttk.Combobox(frame, values=item[2], width=22, state="readonly")
            else:
                self.vars_libro[item[1]] = ttk.Entry(frame, width=25)
            self.vars_libro[item[1]].grid(row=fila, column=columna+1, padx=5, pady=10, sticky='w')
            
            # --- LÓGICA DE AUTO-GENERACIÓN DE ID ---
            if item[1] == "id":
                if libro_data: # Si estamos modificando un libro, solo ponemos su ID
                    self.vars_libro["id"].insert(0, libro_data["id"])
                else:
                    # Si es libro nuevo, buscamos el ID máximo en Redis y le sumamos 1
                    todos_libros = bd.obtener_todos_libros()
                    max_id = 0
                    for lib in todos_libros:
                        try:
                            # Filtramos para asegurarnos de leer solo números
                            num_id = int(''.join(filter(str.isdigit, lib.get("id", "0")))) if any(c.isdigit() for c in lib.get("id", "")) else 0
                            if num_id > max_id:
                                max_id = num_id
                        except ValueError:
                            pass
                    self.vars_libro["id"].insert(0, str(max_id + 1))
                    
                # Bloqueamos la caja para que el usuario no pueda escribir en ella
                self.vars_libro["id"].configure(state='disabled')
                
            elif libro_data and item[1] in libro_data:
                if isinstance(self.vars_libro[item[1]], ttk.Combobox): 
                    self.vars_libro[item[1]].set(libro_data[item[1]])
                else: 
                    self.vars_libro[item[1]].insert(0, libro_data[item[1]])
                
            columna += 2
            if columna > 3:
                columna = 0
                fila += 1

        # Fila 5 especial para Calificación y Disponible
        ttk.Label(frame, text="Calificación / Disp.:").grid(row=fila, column=2, sticky='e', padx=5, pady=10)
        frame_mini = ttk.Frame(frame)
        frame_mini.grid(row=fila, column=3, sticky='w', padx=5, pady=10)
        self.vars_libro["calificacion"] = ttk.Entry(frame_mini, width=8)
        self.vars_libro["calificacion"].pack(side="left", padx=(0, 10))
        if libro_data and "calificacion" in libro_data:
            self.vars_libro["calificacion"].insert(0, libro_data["calificacion"])
            
        var_disponible = tk.BooleanVar(value=True)
        # Si estamos editando y no estaba disponible, desmarcamos la casilla
        if libro_data and libro_data.get("disponible") == "False":
            var_disponible.set(False)
            
        ttk.Checkbutton(frame_mini, text="Disponible", variable=var_disponible).pack(side="left")
        
        fila += 1
        ttk.Label(frame, text="Sinopsis*:").grid(row=fila, column=0, sticky='ne', padx=5, pady=10)
        txt_sinopsis = tk.Text(frame, height=5, width=50, wrap="word")
        txt_sinopsis.grid(row=fila, column=1, columnspan=3, padx=5, pady=10, sticky='w')
        # Si estamos modificando, cargamos la sinopsis guardada en ChromaDB
        if libro_data:
            txt_sinopsis.insert("1.0", bd.obtener_sinopsis(libro_data["id"]))

        def guardar():
            id_libro = self.vars_libro["id"].get().strip()
            titulo = self.vars_libro["titulo"].get().strip()
            autor = self.vars_libro["autor"].get().strip()
            anio = self.vars_libro["anio"].get().strip()
            genero = self.vars_libro["genero"].get().strip()
            tema = self.vars_libro["tema"].get().strip()
            sinopsis = txt_sinopsis.get("1.0", tk.END).strip()
            
            # 1. Validación de todos los campos obligatorios (*)
            # Si estamos editando un libro viejo, dejamos que la sinopsis esté vacía para no borrarla de la BD Vectorial.
            if not all([id_libro, titulo, autor, anio, genero, tema]) or (not libro_data and not sinopsis):
                messagebox.showerror("Campos Incompletos", "Por favor, llena todos los campos marcados con asterisco (*).", parent=ventana)
                return
                
            # 2. Validación de que el año sean números enteros
            if not anio.isdigit():
                messagebox.showerror("Error de Formato", "El Año debe ser un número entero (ej. 2024).", parent=ventana)
                return
                
            # 3. Validación opcional: Si pusieron páginas, que sean números
            paginas = self.vars_libro["paginas"].get().strip()
            if paginas and not paginas.isdigit():
                messagebox.showerror("Error de Formato", "Las Páginas deben ser un número entero.", parent=ventana)
                return
                
            # 4. Validación opcional: Si pusieron calificación, que sea un decimal/entero válido
            calif = self.vars_libro["calificacion"].get().strip()
            if calif:
                try:
                    float(calif)
                except ValueError:
                    messagebox.showerror("Error de Formato", "La Calificación debe ser un número (ej. 4.5).", parent=ventana)
                    return

            datos = {key: var.get() for key, var in self.vars_libro.items() if key != "id"}
            datos["disponible"] = "True" if var_disponible.get() else "False"
            
            bd.guardar_libro(id_libro, datos, sinopsis)
            messagebox.showinfo("Éxito", f"Libro '{id_libro}' guardado.", parent=ventana)
            self.evento_mostrar_todos_libros()
            ventana.destroy()
            
        def limpiar():
            for k, v in self.vars_libro.items():
                if k != "id" or not libro_data:
                    if isinstance(v, ttk.Combobox): v.set('')
                    else: v.delete(0, tk.END)
            txt_sinopsis.delete("1.0", tk.END)

        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(fill="x", padx=20, pady=(0, 20))
        ttk.Button(frame_botones, text="Cancelar", command=ventana.destroy).pack(side="right", padx=5)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="right", padx=5)
        ttk.Button(frame_botones, text="Limpiar", command=limpiar).pack(side="right", padx=5)
    # =========================================================
    # TAB 2: PERSONAS 
    # =========================================================
    def construir_tab_personas(self):
        frame_botones = ttk.Frame(self.tab_personas)
        frame_botones.pack(side="top", fill="x", padx=10, pady=10)

        ttk.Button(frame_botones, text="➕ Registrar Persona", command=self.abrir_form_persona).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="✏️ Modificar Datos", command=self.evento_modificar_persona).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="🔄 Refrescar Catálogo", command=self.evento_mostrar_todas_personas).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="📚 Ver con Préstamos", command=lambda: self.notebook.select(self.tab_prestamos)).pack(side="left", padx=5)

        # Búsqueda: ID, nombre, correo, teléfono o tipo de usuario
        self.ent_buscar_persona = ttk.Entry(frame_botones, width=30)
        self.ent_buscar_persona.pack(side="left", padx=(15, 5))
        self.ent_buscar_persona.bind("<Return>", lambda e: self.evento_buscar_persona())
        ttk.Button(frame_botones, text="🔍 Buscar", command=self.evento_buscar_persona).pack(side="left", padx=5)

        frame_tabla = ttk.Frame(self.tab_personas)
        frame_tabla.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

        columnas = ("id", "nombre", "correo", "telefono", "tipo")
        self.tree_personas = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        
        self.tree_personas.heading("id", text="ID")
        self.tree_personas.heading("nombre", text="Nombre Completo")
        self.tree_personas.heading("correo", text="Correo")
        self.tree_personas.heading("telefono", text="Teléfono")
        self.tree_personas.heading("tipo", text="Tipo de Usuario")

        self.tree_personas.column("id", width=120, anchor="center")
        self.tree_personas.column("nombre", width=300)
        self.tree_personas.column("correo", width=250)
        self.tree_personas.column("telefono", width=150, anchor="center")
        self.tree_personas.column("tipo", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree_personas.yview)
        self.tree_personas.configure(yscrollcommand=scrollbar.set)
        self.tree_personas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Doble clic sobre una persona abre la ventana de modificar
        def al_doble_clic_persona(event):
            if self.tree_personas.identify_row(event.y):
                self.evento_modificar_persona()
        self.tree_personas.bind("<Double-1>", al_doble_clic_persona)

    def abrir_form_persona(self, persona_data=None):
        ventana = tk.Toplevel(self.root)
        ventana.title("Modificar Persona" if persona_data else "Registro de Persona Nueva")
        ventana.geometry("800x650")
        ventana.resizable(False, False)
        ventana.grab_set()

        self.vars_per = {}
        
        # ID Inyectado y Automático
        frame_id = ttk.Frame(ventana)
        frame_id.pack(fill="x", padx=15, pady=(10, 0))
        ttk.Label(frame_id, text="ID / Matrícula*:").pack(side='left', padx=5)
        self.vars_per["id"] = ttk.Entry(frame_id, width=25)
        self.vars_per["id"].pack(side='left', padx=5)
        
        # Lógica para autogenerar o cargar ID
        if persona_data:
            self.vars_per["id"].insert(0, persona_data["id"])
        else:
            # Autogenerar ID basado en el máximo existente
            todas_personas = bd.obtener_todas_personas()
            max_id = 0
            for p in todas_personas:
                try:
                    num_id = int(p.get("id", "0"))
                    if num_id > max_id:
                        max_id = num_id
                except ValueError:
                    pass
            nuevo_id = str(max_id + 1)
            self.vars_per["id"].insert(0, nuevo_id)
        
        self.vars_per["id"].configure(state='disabled')

        # SECCIÓN 1: Datos Personales
        frame_personales = ttk.LabelFrame(ventana, text="Datos Personales")
        frame_personales.pack(fill="x", padx=15, pady=10)

        ttk.Label(frame_personales, text="Nombre(s)*:").grid(row=0, column=0, padx=5, pady=10, sticky="e")
        self.vars_per["nombre"] = ttk.Entry(frame_personales, width=25)
        self.vars_per["nombre"].grid(row=0, column=1, padx=5, pady=10, sticky="w")

        ttk.Label(frame_personales, text="Ap. Paterno*:").grid(row=0, column=2, padx=5, pady=10, sticky="e")
        self.vars_per["apellido_paterno"] = ttk.Entry(frame_personales, width=20)
        self.vars_per["apellido_paterno"].grid(row=0, column=3, padx=5, pady=10, sticky="w")

        ttk.Label(frame_personales, text="Ap. Materno:").grid(row=0, column=4, padx=5, pady=10, sticky="e")
        self.vars_per["apellido_materno"] = ttk.Entry(frame_personales, width=20)
        self.vars_per["apellido_materno"].grid(row=0, column=5, padx=5, pady=10, sticky="w")

        ttk.Label(frame_personales, text="Fecha Nac. (YYYY-MM-DD)*:").grid(row=1, column=0, padx=5, pady=10, sticky="e")
        self.vars_per["fecha_nacimiento"] = ttk.Entry(frame_personales, width=25)
        self.vars_per["fecha_nacimiento"].grid(row=1, column=1, padx=5, pady=10, sticky="w")

        ttk.Label(frame_personales, text="Género*:").grid(row=1, column=2, padx=5, pady=10, sticky="e")
        self.vars_per["genero"] = ttk.Combobox(frame_personales, values=["Hombre", "Mujer", "No Binario", "Prefiero no decir"], state="readonly", width=17)
        self.vars_per["genero"].grid(row=1, column=3, padx=5, pady=10, sticky="w")

        # SECCIÓN 2: Contacto
        frame_contacto = ttk.LabelFrame(ventana, text="Contacto (Será Cifrado en Redis)")
        frame_contacto.pack(fill="x", padx=15, pady=10)

        ttk.Label(frame_contacto, text="Correo Electrónico*:").grid(row=0, column=0, padx=5, pady=10, sticky="e")
        self.vars_per["correo"] = ttk.Entry(frame_contacto, width=35)
        self.vars_per["correo"].grid(row=0, column=1, padx=5, pady=10, sticky="w")

        ttk.Label(frame_contacto, text="Teléfono (10 dígitos)*:").grid(row=0, column=2, padx=5, pady=10, sticky="e")
        self.vars_per["telefono"] = ttk.Entry(frame_contacto, width=25)
        self.vars_per["telefono"].grid(row=0, column=3, padx=5, pady=10, sticky="w")

        # SECCIÓN 3: Dirección
        frame_direccion = ttk.LabelFrame(ventana, text="Dirección")
        frame_direccion.pack(fill="x", padx=15, pady=10)

        ttk.Label(frame_direccion, text="Calle y Número:").grid(row=0, column=0, padx=5, pady=10, sticky="e")
        self.vars_per["calle_numero"] = ttk.Entry(frame_direccion, width=25)
        self.vars_per["calle_numero"].grid(row=0, column=1, padx=5, pady=10, sticky="w")

        ttk.Label(frame_direccion, text="Colonia:").grid(row=0, column=2, padx=5, pady=10, sticky="e")
        self.vars_per["colonia"] = ttk.Entry(frame_direccion, width=20)
        self.vars_per["colonia"].grid(row=0, column=3, padx=5, pady=10, sticky="w")

        ttk.Label(frame_direccion, text="Ciudad:").grid(row=1, column=0, padx=5, pady=10, sticky="e")
        self.vars_per["ciudad"] = ttk.Entry(frame_direccion, width=25)
        self.vars_per["ciudad"].grid(row=1, column=1, padx=5, pady=10, sticky="w")

        ttk.Label(frame_direccion, text="C.P.*:").grid(row=1, column=2, padx=5, pady=10, sticky="e")
        self.vars_per["codigo_postal"] = ttk.Entry(frame_direccion, width=20)
        self.vars_per["codigo_postal"].grid(row=1, column=3, padx=5, pady=10, sticky="w")

        ttk.Label(frame_direccion, text="Estado*:").grid(row=1, column=4, padx=5, pady=10, sticky="e")
        estados_mexico = [
            "Aguascalientes", "Baja California", "Baja California Sur", "Campeche", "Chiapas", 
            "Chihuahua", "Ciudad de México", "Coahuila", "Colima", "Durango", "Estado de México", 
            "Guanajuato", "Guerrero", "Hidalgo", "Jalisco", "Michoacán", "Morelos", "Nayarit", 
            "Nuevo León", "Oaxaca", "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí", 
            "Sinaloa", "Sonora", "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas"
        ]
        self.vars_per["estado"] = ttk.Combobox(frame_direccion, values=estados_mexico, state="readonly", width=17)
        self.vars_per["estado"].grid(row=1, column=5, padx=5, pady=10, sticky="w")

        # SECCIÓN 4: Perfil
        frame_perfil = ttk.LabelFrame(ventana, text="Perfil Institucional")
        frame_perfil.pack(fill="x", padx=15, pady=10)

        ttk.Label(frame_perfil, text="Ocupación*:").grid(row=0, column=0, padx=5, pady=10, sticky="e")
        self.vars_per["ocupacion"] = ttk.Combobox(frame_perfil, values=["Estudiante", "Docente", "Empleado", "Otro"], state="readonly", width=20)
        self.vars_per["ocupacion"].grid(row=0, column=1, padx=5, pady=10, sticky="w")

        ttk.Label(frame_perfil, text="Tipo Usuario*:").grid(row=0, column=2, padx=5, pady=10, sticky="e")
        self.vars_per["tipo_usuario"] = ttk.Combobox(frame_perfil, values=["Alumno", "Profesor", "Externo"], state="readonly", width=20)
        self.vars_per["tipo_usuario"].grid(row=0, column=3, padx=5, pady=10, sticky="w")

        if persona_data:
            for k, v in self.vars_per.items():
                if k != "id" and k in persona_data:
                    if isinstance(v, ttk.Combobox): v.set(persona_data[k])
                    else: v.insert(0, persona_data[k])

        # SECCIÓN 5: Privacidad y Botones
        frame_acciones = ttk.Frame(ventana)
        frame_acciones.pack(fill="x", padx=15, pady=15)

        var_priv = tk.BooleanVar(value=True if persona_data else False)
        ttk.Checkbutton(frame_acciones, text="Acepto el Aviso de Privacidad (LFPDPPP) para el tratamiento y cifrado de mis datos*", variable=var_priv).pack(side="top", pady=(0, 15))

        def guardar():
            id_per = self.vars_per["id"].get().strip()
            
            # Validación de campos obligatorios (*)
            nombre = self.vars_per["nombre"].get().strip()
            ap_paterno = self.vars_per["apellido_paterno"].get().strip()
            fecha_nac = self.vars_per["fecha_nacimiento"].get().strip()
            genero = self.vars_per["genero"].get().strip()
            estado = self.vars_per["estado"].get().strip()
            cp = self.vars_per["codigo_postal"].get().strip()
            ocupacion = self.vars_per["ocupacion"].get().strip()
            tipo_usr = self.vars_per["tipo_usuario"].get().strip()
            
            if not all([nombre, ap_paterno, fecha_nac, genero, estado, cp, ocupacion, tipo_usr]):
                messagebox.showerror("Campos Incompletos", "Por favor, llena todos los campos marcados con asterisco (*).", parent=ventana)
                return
                
            # Validación de fecha (básica YYYY-MM-DD)
            if len(fecha_nac) != 10 or not fecha_nac[0:4].isdigit() or not fecha_nac[5:7].isdigit() or not fecha_nac[8:10].isdigit() or fecha_nac[4] != '-' or fecha_nac[7] != '-':
                 messagebox.showerror("Error de Formato", "La Fecha de Nacimiento debe tener el formato YYYY-MM-DD.", parent=ventana)
                 return
                 
            # Validación de Código Postal (5 dígitos)
            if not cp.isdigit() or len(cp) != 5:
                messagebox.showerror("Error de Formato", "El Código Postal debe contener exactamente 5 dígitos numéricos.", parent=ventana)
                return
                
            telefono = self.vars_per["telefono"].get().strip()
            if not telefono.isdigit() or len(telefono) != 10:
                messagebox.showerror("Error de Formato", "El teléfono debe contener exactamente 10 dígitos numéricos.", parent=ventana)
                return
                
            correo = self.vars_per["correo"].get().strip()
            if "@" not in correo or "." not in correo:
                messagebox.showerror("Error de Formato", "Ingresa un correo electrónico válido (debe contener '@' y '.').", parent=ventana)
                return

            if not var_priv.get():
                messagebox.showerror("Error Legal", "Debe aceptar el Aviso de Privacidad.", parent=ventana)
                return
            
            datos_seguros = {}
            for k, v in self.vars_per.items():
                if k != "id":
                    datos_seguros[k] = security.encriptar_texto(v.get())
                    
            bd.guardar_persona(id_per, datos_seguros)
            messagebox.showinfo("Éxito", "Usuario guardado exitosamente en Redis.", parent=ventana)
            self.evento_mostrar_todas_personas()
            ventana.destroy()

        def limpiar():
            for k, v in self.vars_per.items():
                if k != "id" or not persona_data:
                    if isinstance(v, ttk.Combobox): v.set('')
                    else: v.delete(0, tk.END)

        ttk.Button(frame_acciones, text="Limpiar", command=limpiar).pack(side="right", padx=5)
        ttk.Button(frame_acciones, text="❌ Cancelar", command=ventana.destroy).pack(side="right", padx=5)
        ttk.Button(frame_acciones, text="💾 Actualizar Persona", command=guardar).pack(side="right", padx=5)

    # =========================================================
    # TAB 3: PRÉSTAMOS 
    # =========================================================
    def construir_tab_prestamos(self):
        frame_tabla = ttk.LabelFrame(self.tab_prestamos, text="Préstamos Activos (Catálogo)")
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

        # Barra superior: búsqueda + botones que abren las ventanas + actualizar
        frame_barra = ttk.Frame(frame_tabla)
        frame_barra.pack(side="top", fill="x", padx=10, pady=5)
        self.ent_buscar_prestamo = ttk.Entry(frame_barra, width=30)
        self.ent_buscar_prestamo.pack(side="left", padx=(0, 5))
        self.ent_buscar_prestamo.bind("<Return>", lambda e: self.evento_buscar_prestamo())
        ttk.Button(frame_barra, text="🔍 Buscar", command=self.evento_buscar_prestamo).pack(side="left", padx=5)
        ttk.Button(frame_barra, text="☑ Registrar Préstamo", command=self.abrir_ventana_prestamo).pack(side="left", padx=5)
        ttk.Button(frame_barra, text="↩ Registrar Devolución", command=self.abrir_ventana_devolucion).pack(side="left", padx=5)
        ttk.Button(frame_barra, text="🔄 Actualizar Lista de Préstamos", command=self.evento_mostrar_personas_prestamos).pack(side="right")

        columnas = ("usuario", "libro", "fecha")
        self.tabla_prestamos = ttk.Treeview(frame_tabla, columns=columnas, show="headings", selectmode="browse")
        self.tabla_prestamos.heading("usuario", text="Usuario (ID)")
        self.tabla_prestamos.heading("libro", text="ID del Libro Prestado")
        self.tabla_prestamos.heading("fecha", text="Fecha de Préstamo")

        self.tabla_prestamos.column("usuario", width=150, anchor="center")
        self.tabla_prestamos.column("libro", width=250)
        self.tabla_prestamos.column("fecha", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_prestamos.yview)
        self.tabla_prestamos.configure(yscrollcommand=scrollbar.set)
        self.tabla_prestamos.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

        # Doble clic: muestra el usuario y los libros que tiene prestados
        def al_doble_clic_prestamo(event):
            fila = self.tabla_prestamos.identify_row(event.y)
            if fila:
                self.abrir_detalle_prestamo(str(self.tabla_prestamos.item(fila)['values'][0]))
        self.tabla_prestamos.bind("<Double-1>", al_doble_clic_prestamo)

    def _datos_usuario_descifrados(self, id_per):
        # Nombre completo, correo, teléfono y tipo de usuario ya descifrados
        p = bd.obtener_persona(id_per)
        if not p:
            return None
        d = lambda k: security.desencriptar_texto(p.get(k, "")).strip()
        nombre = " ".join(x for x in [d("nombre"), d("apellido_paterno"), d("apellido_materno")] if x)
        return {"nombre": nombre, "correo": d("correo"), "telefono": d("telefono"), "tipo": d("tipo_usuario")}

    def abrir_ventana_prestamo(self, id_usuario=""):
        ventana = tk.Toplevel(self.root)
        ventana.title("Registrar Préstamo")
        ventana.geometry("380x380")
        ventana.resizable(False, False)
        ventana.grab_set()

        frame = ttk.LabelFrame(ventana, text="Datos del Préstamo", padding=10)
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(frame, text="ID del Usuario*:").pack(anchor="w", pady=(5, 2))
        ent_usuario = ttk.Entry(frame, width=40)
        ent_usuario.pack(pady=(0, 10))
        ent_usuario.insert(0, id_usuario)

        cajas = []
        for i, etiqueta in enumerate(["ID del Libro 1 (Obligatorio):", "ID del Libro 2 (Opcional):", "ID del Libro 3 (Opcional):"]):
            ttk.Label(frame, text=etiqueta).pack(anchor="w", pady=(5, 2))
            caja = ttk.Entry(frame, width=40)
            caja.pack(pady=(0, 5))
            cajas.append(caja)

        def confirmar():
            id_per = ent_usuario.get().strip()
            # Separamos por comas por si meten varios libros en una sola caja
            libros = []
            for caja in cajas:
                libros.extend([l.strip() for l in caja.get().split(",") if l.strip()])

            if not id_per or not libros:
                messagebox.showwarning("Faltan datos", "Ingresa el ID del usuario y al menos el ID de un libro.", parent=ventana)
                return
            if not bd.existe_persona(id_per):
                messagebox.showerror("Usuario no encontrado", f"No existe ninguna persona registrada con el ID '{id_per}'.", parent=ventana)
                return
            # Regla de negocio frontal (máximo 3)
            if len(libros) > 3:
                messagebox.showerror("Regla de Negocio", "No puedes procesar más de 3 libros en una sola operación.", parent=ventana)
                return

            exito, msj = bd.realizar_prestamo(id_per, libros)
            if exito:
                messagebox.showinfo("Éxito", msj, parent=ventana)
                self.evento_mostrar_personas_prestamos()
                self.evento_mostrar_todos_libros()
                ventana.destroy()
            else:
                messagebox.showerror("Error", msj, parent=ventana)

        def limpiar():
            for e in [ent_usuario] + cajas:
                e.delete(0, tk.END)

        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(fill="x", padx=15, pady=(0, 15))
        ttk.Button(frame_botones, text="Cancelar", command=ventana.destroy).pack(side="right", padx=5)
        ttk.Button(frame_botones, text="☑ Confirmar Préstamo", command=confirmar).pack(side="right", padx=5)
        ttk.Button(frame_botones, text="Limpiar", command=limpiar).pack(side="right", padx=5)
        (cajas[0] if id_usuario else ent_usuario).focus_set()

    def abrir_ventana_devolucion(self, id_usuario=""):
        ventana = tk.Toplevel(self.root)
        ventana.title("Registrar Devolución")
        ventana.geometry("420x400")
        ventana.resizable(False, False)
        ventana.grab_set()

        frame = ttk.LabelFrame(ventana, text="Datos de la Devolución", padding=10)
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(frame, text="ID del Usuario*:").pack(anchor="w", pady=(5, 2))
        frame_usr = ttk.Frame(frame)
        frame_usr.pack(fill="x", pady=(0, 10))
        ent_usuario = ttk.Entry(frame_usr, width=25)
        ent_usuario.pack(side="left")
        ent_usuario.insert(0, id_usuario)

        lbl_nombre = ttk.Label(frame, text="", foreground="gray")
        lbl_nombre.pack(anchor="w")
        ttk.Label(frame, text="Marca los libros que se devuelven:").pack(anchor="w", pady=(10, 2))
        frame_libros = ttk.Frame(frame)
        frame_libros.pack(fill="both", expand=True)
        vars_libros = {}

        def cargar_libros(event=None):
            for w in frame_libros.winfo_children():
                w.destroy()
            vars_libros.clear()
            lbl_nombre.configure(text="")

            id_per = ent_usuario.get().strip()
            if not id_per:
                return
            usuario = self._datos_usuario_descifrados(id_per)
            lbl_nombre.configure(text=f"Usuario: {usuario['nombre']}" if usuario else "Usuario no registrado")
            libros = bd.obtener_libros_prestados(id_per)
            if not libros:
                ttk.Label(frame_libros, text="Este usuario no tiene libros prestados.").pack(anchor="w")
                return
            for lib in libros:
                var = tk.BooleanVar(value=False)
                vars_libros[lib["id"]] = var
                ttk.Checkbutton(frame_libros, text=f"{lib['id']} - {lib['titulo']}", variable=var).pack(anchor="w", pady=2)

        ent_usuario.bind("<Return>", cargar_libros)
        ttk.Button(frame_usr, text="📖 Ver libros prestados", command=cargar_libros).pack(side="left", padx=5)

        def confirmar():
            id_per = ent_usuario.get().strip()
            if not id_per:
                messagebox.showwarning("Atención", "Ingresa el ID del usuario y presiona 'Ver libros prestados'.", parent=ventana)
                return
            seleccionados = [id_lib for id_lib, var in vars_libros.items() if var.get()]
            if not seleccionados:
                messagebox.showwarning("Atención", "Marca al menos un libro para devolver.", parent=ventana)
                return

            errores = []
            for id_lib in seleccionados:
                exito, msj = bd.devolver_prestamo(id_per, id_lib)
                if not exito:
                    errores.append(f"{id_lib}: {msj}")

            self.evento_mostrar_personas_prestamos()
            self.evento_mostrar_todos_libros()
            if errores:
                messagebox.showerror("Error", "No se pudieron devolver algunos libros:\n" + "\n".join(errores), parent=ventana)
                cargar_libros()
            else:
                messagebox.showinfo("Éxito", f"Se devolvieron {len(seleccionados)} libro(s) al catálogo.", parent=ventana)
                ventana.destroy()

        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(fill="x", padx=15, pady=(0, 15))
        ttk.Button(frame_botones, text="Cancelar", command=ventana.destroy).pack(side="right", padx=5)
        ttk.Button(frame_botones, text="↩ Confirmar Devolución", command=confirmar).pack(side="right", padx=5)

        if id_usuario:
            cargar_libros()
        else:
            ent_usuario.focus_set()

    def abrir_detalle_prestamo(self, id_per):
        # Ventana de solo lectura: datos del usuario y sus libros prestados
        ventana = tk.Toplevel(self.root)
        ventana.title(f"Préstamo del usuario {id_per}")
        ventana.geometry("600x400")
        ventana.grab_set()

        frame_usr = ttk.LabelFrame(ventana, text="Usuario", padding=10)
        frame_usr.pack(fill="x", padx=15, pady=(15, 5))
        usuario = self._datos_usuario_descifrados(id_per)
        filas = [("ID:", id_per)]
        if usuario:
            filas += [("Nombre:", usuario["nombre"]), ("Correo:", usuario["correo"]),
                      ("Teléfono:", usuario["telefono"]), ("Tipo:", usuario["tipo"])]
        else:
            filas.append(("Nombre:", "(usuario no registrado)"))
        for i, (etq, valor) in enumerate(filas):
            ttk.Label(frame_usr, text=etq).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            ttk.Label(frame_usr, text=valor).grid(row=i, column=1, sticky="w", padx=5, pady=2)

        frame_lib = ttk.LabelFrame(ventana, text="Libros Prestados", padding=10)
        frame_lib.pack(fill="both", expand=True, padx=15, pady=5)
        tabla = ttk.Treeview(frame_lib, columns=("id", "titulo", "autor"), show="headings", height=4)
        tabla.heading("id", text="ID")
        tabla.heading("titulo", text="Título")
        tabla.heading("autor", text="Autor")
        tabla.column("id", width=60, anchor="center")
        tabla.column("titulo", width=260)
        tabla.column("autor", width=180)
        tabla.pack(fill="both", expand=True)
        for lib in bd.obtener_libros_prestados(id_per):
            tabla.insert("", tk.END, values=(lib["id"], lib["titulo"], lib["autor"]))

        def ir_a_devolucion():
            ventana.destroy()
            self.abrir_ventana_devolucion(id_per)

        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(fill="x", padx=15, pady=(5, 15))
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="right", padx=5)
        ttk.Button(frame_botones, text="↩ Registrar Devolución", command=ir_a_devolucion).pack(side="right", padx=5)

    # =========================================================
    # EVENTOS LÓGICOS GLOBALES (Conectados a BD)
    # =========================================================
    def limpiar_treeview(self, tree):
        for item in tree.get_children(): tree.delete(item)

    # --- LÓGICA DE LIBROS ---
   # --- LÓGICA DE LIBROS ---
    def evento_mostrar_todos_libros(self):
        self.limpiar_treeview(self.tree_libros)
        
        # 1. Obtenemos los libros de la base de datos
        libros = bd.obtener_todos_libros()
        
        # 2. Los ordenamos por su ID. 
        # Usamos una función lambda que extrae el número del ID (ej. de 'libro01' saca el 1)
        # Si un ID no tiene números (ej. 'HarryPotter'), lo manda al final.
        libros_ordenados = sorted(
            libros, 
            key=lambda x: int(''.join(filter(str.isdigit, x.get("id", "0")))) if any(c.isdigit() for c in x.get("id", "")) else float('inf')
        )
        
        # 3. Pintamos los libros ya ordenados en la tabla
        for lib in libros_ordenados:
            self.tree_libros.insert("", tk.END, values=(lib.get("id"), lib.get("titulo"), lib.get("autor"), lib.get("genero"), "SÍ" if lib.get("disponible") == "True" else "NO"))

    def evento_buscar_libro(self):
        # Búsqueda combinada desde la barra superior: ID, título, autor o sinopsis
        texto = self.ent_buscar_libro.get().strip()
        if not texto:
            messagebox.showwarning("Atención", "Escribe un ID, título, autor o tema de la sinopsis para buscar.")
            return

        try:
            resultados = bd.buscar_libros_general(texto)
        except Exception:
            messagebox.showerror("Error", "Problema al buscar en la base de datos.")
            return

        if not resultados:
            messagebox.showinfo("Sin resultados", f"No se encontró ningún libro con '{texto}'.")
            return

        self.limpiar_treeview(self.tree_libros)
        for lib in resultados:
            self.tree_libros.insert("", tk.END, values=(lib.get("id"), lib.get("titulo"), lib.get("autor"), lib.get("genero"), "SÍ" if lib.get("disponible") == "True" else "NO"))

    def evento_modificar_libro(self):
        sel = self.tree_libros.selection()
        if not sel: return
        id_lib = self.tree_libros.item(sel[0])['values'][0]
        datos = bd.obtener_libro(str(id_lib))
        if datos:
            datos["id"] = id_lib
            self.abrir_form_libro(datos)

    def evento_borrar_libro(self):
        sel = self.tree_libros.selection()
        if not sel: return
        id_lib = self.tree_libros.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirmar", f"¿Borrar {id_lib}?"):
            bd.borrar_libro(str(id_lib))
            self.evento_mostrar_todos_libros()

    def evento_carga_lote_libros(self):
        archivo = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not archivo: return
        try:
            import csv
            c = 0
            with open(archivo, mode='r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    id_lib = row.pop('id', '').strip()
                    sinopsis = row.pop('sinopsis', '').strip()
                    if id_lib:
                        row['disponible'] = "True"
                        bd.guardar_libro(id_lib, dict(row), sinopsis)
                        c += 1
            messagebox.showinfo("Éxito", f"Cargados {c} libros.")
            self.evento_mostrar_todos_libros()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- LÓGICA DE PERSONAS ---
    def evento_buscar_persona(self):
        texto = self.ent_buscar_persona.get().strip()
        if not texto:
            messagebox.showwarning("Atención", "Escribe un ID, nombre, correo, teléfono o tipo de usuario para buscar.")
            return
        encontrados = self.evento_mostrar_todas_personas(filtro=texto)
        if encontrados == 0:
            messagebox.showinfo("Sin resultados", f"No se encontró ninguna persona con '{texto}'.")
            self.evento_mostrar_todas_personas()

    def evento_mostrar_todas_personas(self, filtro=""):
        # Si se pasa un filtro, solo se muestran las personas que coinciden (sin distinguir mayúsculas)
        filtro = filtro.strip().lower()
        encontrados = 0
        self.limpiar_treeview(self.tree_personas)
        
        personas = bd.obtener_todas_personas()
        
        # Ordenamos las personas por su ID numéricamente
        personas_ordenadas = sorted(
            personas, 
            key=lambda x: int(x.get("id", "0")) if x.get("id", "0").isdigit() else 0
        )
        
        for p in personas_ordenadas:
            # Desencriptar las 3 partes del nombre
            nombre_pila = security.desencriptar_texto(p.get("nombre", "")).strip()
            ap_paterno = security.desencriptar_texto(p.get("apellido_paterno", "")).strip()
            ap_materno = security.desencriptar_texto(p.get("apellido_materno", "")).strip()
            
            # Concatenar el nombre completo ignorando los campos vacíos
            partes_nombre = [nombre_pila, ap_paterno, ap_materno]
            nombre_completo = " ".join([parte for parte in partes_nombre if parte])
            
            correo = security.desencriptar_texto(p.get("correo", ""))
            tel = security.desencriptar_texto(p.get("telefono", ""))
            tipo = security.desencriptar_texto(p.get("tipo_usuario", ""))
            
            fila = (p.get("id"), nombre_completo, correo, tel, tipo)
            if filtro:
                if filtro != str(p.get("id", "")).lower() and not any(filtro in str(campo).lower() for campo in fila[1:]):
                    continue
            self.tree_personas.insert("", tk.END, values=fila)
            encontrados += 1
        return encontrados

    def evento_modificar_persona(self):
        sel = self.tree_personas.selection()
        if not sel: return
        id_per = str(self.tree_personas.item(sel[0])['values'][0])
        for p in bd.obtener_todas_personas():
            if p.get("id") == id_per:
                datos_descifrados = {"id": id_per}
                for k, v in p.items():
                    if k != "id": datos_descifrados[k] = security.desencriptar_texto(v)
                self.abrir_form_persona(datos_descifrados)
                break

    # --- LÓGICA DE PRÉSTAMOS ---
    def evento_buscar_prestamo(self):
        texto = self.ent_buscar_prestamo.get().strip()
        if not texto:
            messagebox.showwarning("Atención", "Escribe un ID de usuario, nombre o ID de libro para buscar.")
            return
        encontrados = self.evento_mostrar_personas_prestamos(filtro=texto)
        if encontrados == 0:
            messagebox.showinfo("Sin resultados", f"No se encontró ningún préstamo con '{texto}'.")
            self.evento_mostrar_personas_prestamos()

    def evento_mostrar_personas_prestamos(self, filtro=""):
        # Con filtro: ID de usuario o libro exacto, o parte del nombre del usuario
        filtro = filtro.strip().lower()
        encontrados = 0
        self.limpiar_treeview(self.tabla_prestamos)
        fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
        for r in bd.obtener_personas_con_prestamos():
            if filtro:
                nombre = ""
                if r.get("nombre_encriptado"):
                    try:
                        nombre = security.desencriptar_texto(r["nombre_encriptado"]).lower()
                    except Exception:
                        pass
                ids_libros = [str(l).lower() for l in r["libros"]]
                if filtro != str(r["id_persona"]).lower() and filtro not in ids_libros and filtro not in nombre:
                    continue
            # Mostramos el ID del usuario en la primera columna tal cual lo hace tu compañero
            self.tabla_prestamos.insert("", tk.END, values=(r["id_persona"], ", ".join(r["libros"]), fecha_hoy))
            encontrados += 1
        return encontrados
