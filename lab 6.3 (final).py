from threading import Event, Thread
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from stl import mesh
import numpy as np
import tkinter as tk
import sys

modelos = [
    mesh.Mesh.from_file("Joint0.STL"),
    mesh.Mesh.from_file("Joint1.STL"),
    mesh.Mesh.from_file("Joint2.STL"),
    mesh.Mesh.from_file("Joint3.STL"),
    mesh.Mesh.from_file("Joint4.STL"),
    mesh.Mesh.from_file("Joint5.STL"),
    mesh.Mesh.from_file("Joint6.STL")
]
# Normalizar escala para que todo el robot mida ~1 metro de alto
max_dim = max(np.max(np.abs(m.vectors)) for m in modelos)
escala_norm = 0.3/ max_dim if max_dim > 0 else 1.0
for m in modelos:
    m.vectors *= escala_norm
# Alturas de apilamiento basadas en la geometria real de las mallas STL de igus
offsets = [
    [0.0, 0.0, 0.0],     # Joint0 (Base)
    [0.0, 0.0, 0.086],   # Joint1
    [0.0, 0.0, 0.173],   # Joint2
    [0.0, 0.0, 0.250],   # Joint3
    [0.0, 0.0, 0.128],   # Joint4
    [0.0, 0.0, 0.181],   # Joint5
    [0.0, 0.0, 0.104],   # Joint6
]

escalar = 1
cam_angle_x = 0
cam_angle_y = 0
x = 0
y = 0
rotacion_x = 0
rotacion_y = 0
rotacion_z = 0
pieza_seleccionada = 0
rotaciones_piezas = []
for modelo in modelos:
    rotaciones_piezas.append([0, 0, 0])

limites_piezas = [
    [(-90, 90), (-90, 90), (-180, 180)],  # Joint0: X, Y, Z
    [(-1, 1), (-1, 1), (-180, 180)],    # Joint1
    [(-1, 1), (-180, 180), (-1, 1)],    # Joint2
    [(-1, 1), (-90, 120), (-1, 1)],    # Joint3
    [(-1, 1), (-1, 1), (-180, 180)],    # Joint4
    [(-1, 1), (-90, 90), (-1, 1)],    # Joint5
    [(-90, 90), (-90, 90), (-90, 90)],    # Joint6
]
listas_opengl = []
reinicio_pendiente = Event()

# Prepara las geometrias de los modelos para reutilizarlas al dibujar.
def compilar_modelos():
    for modelo in modelos:
        lista = glGenLists(1) #guarda el modelo en una lista para dibujarlo mas rapido
        glNewList(lista, GL_COMPILE)
        glBegin(GL_TRIANGLES)
        v0 = modelo.vectors[:, 0, :] # : "todos los elementos (triangulos)"
        v1 = modelo.vectors[:, 1, :]
        v2 = modelo.vectors[:, 2, :]
        normales = np.cross(v1 - v0, v2 - v0) # Calcular el vector normal de cada cara
        normas = np.linalg.norm(normales, axis=1, keepdims=True) #indica lado al q mira la cara, para iluminacion
        normas[normas == 0] = 1 #igual a 1 para evitar division por cero
        normales /= normas

        for i in range(len(modelo.vectors)): #guardo los vertices y normales de cada triangulo
            glNormal3fv(normales[i])
            glVertex3fv(v0[i])
            glVertex3fv(v1[i])
            glVertex3fv(v2[i])
        glEnd()
        glEndList()
        listas_opengl.append(lista)

def init():
    glClearColor(0.15, 0.15, 0.18, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_NORMALIZE)

    # Posicion e intensidad de la luz
    glLightfv(GL_LIGHT0, GL_POSITION, [2.0, -3.0, 4.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.85, 0.85, 0.85, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])

    # Material de la pieza
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.25, 0.25, 0.3, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.7, 0.75, 0.85, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 30.0)
    glShadeModel(GL_SMOOTH)
    compilar_modelos()

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    #camara
    gluLookAt(0.0, -1.5, 0.3, 0.0, 0.0, 0.3, 0.0, 0.0, 1.0)
    glTranslatef(x, 0, y)
    glRotatef(cam_angle_x, 1, 0, 0)
    glRotatef(cam_angle_y, 0, 0, 1)
    glRotatef(rotacion_x, 1, 0, 0)
    glRotatef(rotacion_y, 0, 1, 0)
    glRotatef(rotacion_z, 0, 0, 1)
    glScalef(escalar, escalar, escalar)
    glPushMatrix()

    # Las transformaciones se acumulan para que cada articulacion siga a la anterior.
    for i in range(len(modelos)):
        xyz = offsets[i]
        rot = rotaciones_piezas[i]

        glTranslatef(xyz[0], xyz[1], xyz[2])
        glRotatef(rot[0], 1, 0, 0)
        glRotatef(rot[1], 0, 1, 0)
        glRotatef(rot[2], 0, 0, 1)

        if i < len(listas_opengl):
            glCallList(listas_opengl[i])

    glPopMatrix()
    glutSwapBuffers()

def teclado(key, _x, _y):
    global cam_angle_x, cam_angle_y, pieza_seleccionada
    key = key.lower()
    if key in (b'\x08', b'\x7f'):
        reinicio_pendiente.set()
    #numero de la pieza
    elif key == b'1':
        pieza_seleccionada = int(key) - 1
    elif key == b'2':
        pieza_seleccionada = int(key) - 1
    elif key == b'3':
        pieza_seleccionada = int(key) - 1
    elif key == b'4':
        pieza_seleccionada = int(key) - 1
    elif key == b'5':
        pieza_seleccionada = int(key) - 1
    elif key == b'6':
        pieza_seleccionada = int(key) - 1
    elif key == b'7':
        pieza_seleccionada = int(key) - 1
    #vistas del ensamble
    elif key == b'w':
        cam_angle_x = 0
        cam_angle_y = 0
    elif key == b's':
        cam_angle_x = 90
        cam_angle_y = 0
    elif key == b'a':
        cam_angle_x = 0
        cam_angle_y = 90
    elif key == b'd':
        cam_angle_x = 90
        cam_angle_y = 90
    elif key == b'z':
        cam_angle_x = -90
        cam_angle_y = 0
    elif key == b'f':
        cam_angle_x = 0
        cam_angle_y = -90
    elif key == b' ':
        cam_angle_x = 45
        cam_angle_y = 45
    glutPostRedisplay()

def teclas_especiales(key, _x, _y):
    global x, y

    if key == GLUT_KEY_RIGHT:
        x += 0.05
    elif key == GLUT_KEY_LEFT:
        x -= 0.05
    elif key == GLUT_KEY_UP:
        y += 0.05
    elif key == GLUT_KEY_DOWN:
        y -= 0.05
    glutPostRedisplay()

def sliders():
    global escalar, rotacion_x, rotacion_y, rotacion_z
    root = tk.Tk()
    root.title("Controles:")
    estado = tk.StringVar(value="Listo")
    controles = []
    def restablecer(): #debuelve todas las variables a su estado inicial
        global escalar, cam_angle_x, cam_angle_y
        global x, y, rotacion_x, rotacion_y, rotacion_z, pieza_seleccionada
        escalar = 1
        cam_angle_x = 0
        cam_angle_y = 0
        x = 0
        y = 0
        rotacion_x = 0
        rotacion_y = 0
        rotacion_z = 0
        pieza_seleccionada = 0
        for rotacion in rotaciones_piezas:
            rotacion[:] = [0, 0, 0]
        for control, valor_inicial in controles:
            control.set(valor_inicial)
        estado.set("Listo")

    def revisar_reinicio():
        if reinicio_pendiente.is_set():
            reinicio_pendiente.clear()
            restablecer()
        root.after(50, revisar_reinicio)

    def agregar_slider(minimo, maximo, comando, inicial=0, resolucion=1):
        control = tk.Scale(
            root, from_=minimo, to=maximo, resolution=resolucion,
            orient='horizontal', command=comando
        )
        control.set(inicial)
        control.pack()
        controles.append((control, inicial))

    def update_rx(val):
        global rotacion_x
        rotacion_x = float(val)

    def update_ry(val):
        global rotacion_y
        rotacion_y = float(val)

    def update_rz(val):
        global rotacion_z
        rotacion_z = float(val)

    def update_scale(val):
        global escalar
        escalar = float(val)

    def update_pieza(eje, val):
        angulo = float(val)
        minimo, maximo = limites_piezas[pieza_seleccionada][eje]

        if minimo <= angulo <= maximo:
            rotaciones_piezas[pieza_seleccionada][eje] = angulo
            estado.set("Rotacion actualizada")
        else:
            estado.set("Fuera del limite")

    def update_piezas_rx(val):
        update_pieza(0, val)

    def update_piezas_ry(val):
        update_pieza(1, val)

    def update_piezas_rz(val):
        update_pieza(2, val)

    tk.Label(root, text="Rota ensamble en X").pack()
    agregar_slider(0, 360, update_rx)

    tk.Label(root, text="Rota ensamble en Y").pack()
    agregar_slider(0, 360, update_ry)

    tk.Label(root, text="Rota ensamble en Z").pack()
    agregar_slider(0, 360, update_rz)

    tk.Label(root, text="\nElige articulacion con teclas 1 a 7 (1 es la base)").pack()
   
    tk.Label(root, text="Rota articulacion en X").pack()
    agregar_slider(-180, 180, update_piezas_rx)

    tk.Label(root, text="Rota articulacion en Y").pack()
    agregar_slider(-180, 180, update_piezas_ry)

    tk.Label(root, text="Rota articulacion en Z").pack()
    agregar_slider(-180, 180, update_piezas_rz)

    tk.Label(root, text="Escala").pack()
    agregar_slider(0.2, 3.0, update_scale, inicial=1, resolucion=0.1)
    tk.Label(root, text="\nPresiona letras (w,a,s,d,f,z) para las vistas.").pack()
    tk.Label(root, text="Presiona flechas (↑ ↓ → ←) para desplazar el ensamble. ").pack()
    tk.Label(root, text="Presiona Backspace para restablecer todo").pack()

    root.after(50, revisar_reinicio)
    root.mainloop()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(900, 600)
    glutCreateWindow(b"Simulacion del Igus ReBeL 6-DOF")
    init() 

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 900 / 600, 0.05, 50.0)
    glMatrixMode(GL_MODELVIEW)

    Thread(target=sliders, daemon=True).start()
    glutDisplayFunc(display)
    glutKeyboardFunc(teclado)
    glutSpecialFunc(teclas_especiales)
    glutIdleFunc(lambda: glutPostRedisplay())  #lambda para que se refresque la pantalla constantemente
    glutMainLoop()

if __name__ == "__main__":
    main()
