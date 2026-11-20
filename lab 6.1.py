from threading import Thread
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from stl import mesh
import numpy as np
import tkinter as tk

modelos = [
    mesh.Mesh.from_file("Porta - Pieza1 porta esfero-1.STL"),
    mesh.Mesh.from_file("Porta - Pieza2-1.STL"),
    mesh.Mesh.from_file("Porta - Pieza3-1.STL"),
    mesh.Mesh.from_file("Porta - Pieza4.1-1.STL"),  
]

escala_modelo = 0.001
for modelo in modelos:
    modelo.vectors *= escala_modelo

#centra el ensambre en el origen (0,0,0)
vertices = np.concatenate([modelo.vectors.reshape(-1, 3) for modelo in modelos])   #junta todos los vertices un arreglo
centro_ensamble = (vertices.min(axis=0) + vertices.max(axis=0)) / 2   #calcula el centro del ensamble tomando el promedio de vertices
for modelo in modelos:   #resta el centro del ensamble a cada vertice para centrar el ensamble en el origen
    modelo.vectors -= centro_ensamble

centros_modelos = [
    (modelo.vectors.min(axis=(0, 1)) + modelo.vectors.max(axis=(0, 1))) / 2
    for modelo in modelos
]

escalar = 1
cam_angle_x = 0
cam_angle_y = 0
rotacion_x = 0
rotacion_y = 0
rotacion_z = 0
pieza_seleccionada = 0
rotaciones_piezas = []
for modelo in modelos:
    rotaciones_piezas.append([0, 0, 0])


def init():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_NORMALIZE)

    # Posición de la luz
    glLightfv(GL_LIGHT0, GL_POSITION, [2.0, 3.0, 5.0, 1.0])

    # Intensidad
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.9, 0.9, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])

    # Material de la pieza
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.7, 0.7, 0.8, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.6, 0.6, 0.6, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 30.0)

    glShadeModel(GL_SMOOTH)

def dibujar_pieza(modelo, centro, rotaciones):
    glPushMatrix()
    glTranslatef(*centro)
    glRotatef(rotaciones[0], 1, 0, 0)
    glRotatef(rotaciones[1], 0, 1, 0)
    glRotatef(rotaciones[2], 0, 0, 1)
    glTranslatef(*(-centro))

    glBegin(GL_TRIANGLES)
    for cara in modelo.vectors:
        v0, v1, v2 = cara
        normal = np.cross(v1 - v0, v2 - v0) # Calcular el vector normal de la cara
        normal = normal / np.linalg.norm(normal) #Normalizar el vector (longitud 1)
        glNormal3fv(normal)
        for vertice in cara:
            glVertex3fv(vertice)
    glEnd()
    glPopMatrix()

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    #camara
    gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0) # Posición de la cámara
    glRotatef(cam_angle_x, 1, 0, 0)
    glRotatef(cam_angle_y, 0, 1, 0)
    glRotatef(rotacion_x, 1, 0, 0)
    glRotatef(rotacion_y, 0, 1, 0)
    glRotatef(rotacion_z, 0, 0, 1)
    glScalef(escalar,escalar,escalar) #escalar

    for i in range(len(modelos)): #guarda el modelo, centro y rotacion de cada pieza
        modelo = modelos[i]
        centro = centros_modelos[i]
        rotaciones = rotaciones_piezas[i]
        dibujar_pieza(modelo, centro, rotaciones) #crea cada pieza(modelo) con su respectiva rotacion y centro
    glFlush()


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
    elif key == b'w':
        cam_angle_x += 0.2
    elif key == b's':
        cam_angle_x -= 0.2
    elif key == b'a':
        cam_angle_y += 5
    elif key == b'd':
        cam_angle_y -= 5

    glutPostRedisplay()

def sliders():
    global rotacion_x, rotacion_y, rotacion_z, escalar

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

    def update_piezas_rx(val):
        rotaciones_piezas[pieza_seleccionada][0] = float(val)

    def update_piezas_ry(val):
        rotaciones_piezas[pieza_seleccionada][1] = float(val)

    def update_piezas_rz(val):
        rotaciones_piezas[pieza_seleccionada][2] = float(val)

    root = tk.Tk()
    root.title("Controles")

    tk.Label(root, text="Rota ensamble en X").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_rx).pack()

    tk.Label(root, text="Rota ensamble en Y").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_ry).pack()

    tk.Label(root, text="Rota ensamble en Z").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_rz).pack()

    tk.Label(root, text="Elige la pieza con 1, 2, 3 o 4 ").pack()

    tk.Label(root, text="Rota pieza en X").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_piezas_rx).pack()

    tk.Label(root, text="Rota pieza en Y").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_piezas_ry).pack()

    tk.Label(root, text="Rota pieza en Z").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_piezas_rz).pack()

    tk.Label(root, text="Escala").pack()
    escala_slider = tk.Scale(root, from_=0.1, to=10, resolution=0.1, orient='horizontal', command=update_scale)
    escala_slider.set(1)
    escala_slider.pack()

    root.mainloop()

def main():
# Hilo para sliders
    Thread(target=sliders).start()

    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Mi primer modelo3D")
    init()
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 800/600, 0.1, 100)
    glMatrixMode(GL_MODELVIEW)

    glutDisplayFunc(display)
    glutKeyboardFunc(teclado)
    glutIdleFunc(lambda: glutPostRedisplay()) #actualiza la pantalla constantemente
    glutMainLoop()

if __name__ == "__main__":
    main()