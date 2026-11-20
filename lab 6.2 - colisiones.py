from threading import Thread
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from stl import mesh
import numpy as np
import tkinter as tk
import time

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
escala_norm = 0.25 / max_dim if max_dim > 0 else 1.0
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
#Se calcular esferas q "envuelven" cada pieza
esferas_locales = []
for modelo in modelos:
    vertices = modelo.vectors.reshape(-1, 3)
    centro = (vertices.min(axis=0) + vertices.max(axis=0)) / 2
    radio = np.max(np.linalg.norm(vertices - centro, axis=1))
    esferas_locales.append((centro, radio))

escalar = 1
cam_angle_x = 0
cam_angle_y = 0
rotacion_x = 0
rotacion_y = 0
rotacion_z = 0
pieza_seleccionada = 0
rotaciones_piezas = [[0, 0, 0] for _ in modelos]
listas_opengl = []


def matriz_traslacion(offset):
    matriz = np.eye(4)
    matriz[:3, 3] = offset
    return matriz


def matriz_rotacion(eje, grados):
    angulo = np.radians(grados)
    coseno = np.cos(angulo)
    seno = np.sin(angulo)
    matriz = np.eye(4)

    if eje == 0:
        matriz[1, 1] = coseno
        matriz[1, 2] = -seno
        matriz[2, 1] = seno
        matriz[2, 2] = coseno
    elif eje == 1:
        matriz[0, 0] = coseno
        matriz[0, 2] = seno
        matriz[2, 0] = -seno
        matriz[2, 2] = coseno
    else:
        matriz[0, 0] = coseno
        matriz[0, 1] = -seno
        matriz[1, 0] = seno
        matriz[1, 1] = coseno

    return matriz


def pose_sin_colisiones(rotaciones):
    """Comprueba colisiones aproximadas entre piezas no adyacentes."""
    matriz_ensamble = np.eye(4)
    centros_mundo = []
    radios_mundo = []

    for indice, desplazamiento in enumerate(offsets):
        # Reproduce, en el mismo orden, el glTranslatef y los glRotatef de display().
        matriz_ensamble = np.matmul(
            matriz_ensamble,
            matriz_traslacion(desplazamiento)
        )
        for eje, angulo in enumerate(rotaciones[indice]):
            matriz_giro = matriz_rotacion(eje, angulo)
            matriz_ensamble = np.matmul(matriz_ensamble, matriz_giro)

        centro_local, radio_local = esferas_locales[indice]
        punto_local = np.append(centro_local, 1.0)
        punto_mundo = np.matmul(matriz_ensamble, punto_local)
        centros_mundo.append(punto_mundo[:3] * escalar)
        radios_mundo.append(radio_local * escalar)

    for i in range(len(centros_mundo)):
        for j in range(i + 2, len(centros_mundo)):
            diferencia = centros_mundo[i] - centros_mundo[j]
            distancia = np.linalg.norm(diferencia)
            radio_combinado = radios_mundo[i] + radios_mundo[j]
            if distancia < radio_combinado:
                return False

    return True


# Prepara las geometrias de los modelos para reutilizarlas al dibujar.
def compilar_modelos():
    for modelo in modelos:
        lista = glGenLists(1)
        glNewList(lista, GL_COMPILE)
        glBegin(GL_TRIANGLES)
        v0 = modelo.vectors[:, 0, :]
        v1 = modelo.vectors[:, 1, :]
        v2 = modelo.vectors[:, 2, :]
        normales = np.cross(v1 - v0, v2 - v0)
        normas = np.linalg.norm(normales, axis=1, keepdims=True)
        normas[normas == 0] = 1
        normales /= normas

        for i in range(len(modelo.vectors)):
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
    if key == b'1':
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
    elif key == b'w':
        cam_angle_x += 5
    elif key == b's':
        cam_angle_x -= 5
    elif key == b'a':
        cam_angle_y += 5
    elif key == b'd':
        cam_angle_y -= 5
    glutPostRedisplay()


def sliders():
    global escalar, rotacion_x, rotacion_y, rotacion_z
    time.sleep(0.5)

    root = tk.Tk()
    root.title("Controles:")
    estado = tk.StringVar(value="Listo")

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
        candidata = [rot[:] for rot in rotaciones_piezas]
        candidata[pieza_seleccionada][eje] = float(val)

        if pose_sin_colisiones(candidata):
            rotaciones_piezas[pieza_seleccionada][eje] = float(val)
            estado.set("Movimiento permitido")
        else:
            estado.set("Movimiento rechazado: posible colision")

    def update_piezas_rx(val):
        update_pieza(0, val)

    def update_piezas_ry(val):
        update_pieza(1, val)

    def update_piezas_rz(val):
        update_pieza(2, val)

    tk.Label(root, text="Rota ensamble en X").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_rx).pack()

    tk.Label(root, text="Rota ensamble en Y").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_ry).pack()

    tk.Label(root, text="Rota ensamble en Z").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_rz).pack()

    tk.Label(root, text="Elige articulacion con teclas 1 a 7 (1 es la base)").pack()

    tk.Label(root, text="Rota articulacion en X").pack()
    tk.Scale(root, from_=-180, to=180, orient='horizontal', command=update_piezas_rx).pack()

    tk.Label(root, text="Rota articulacion en Y").pack()
    tk.Scale(root, from_=-180, to=180, orient='horizontal', command=update_piezas_ry).pack()

    tk.Label(root, text="Rota articulacion en Z").pack()
    tk.Scale(root, from_=-180, to=180, orient='horizontal', command=update_piezas_rz).pack()

    tk.Label(root, text="Escala").pack()
    escala_slider = tk.Scale(root, from_=0.2, to=3.0, resolution=0.1, orient='horizontal', command=update_scale)
    escala_slider.set(1)
    escala_slider.pack()

    tk.Label(root, textvariable=estado).pack()
    root.mainloop()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Igus ReBeL 6-DOF")
    init()

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 800 / 600, 0.05, 50.0)
    glMatrixMode(GL_MODELVIEW)

    Thread(target=sliders, daemon=True).start()

    glutDisplayFunc(display)
    glutKeyboardFunc(teclado)
    glutIdleFunc(lambda: glutPostRedisplay())
    glutMainLoop()


if __name__ == "__main__":
    main()
