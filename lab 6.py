from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from stl import mesh
import numpy as np
import tkinter as tk

modelo = mesh.Mesh.from_file("Pieza1.stl")

escala_modelo = 0.001
modelo.vectors *= escala_modelo

x = 0
y = 0
angulo = 0
escalar = 1

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


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    #camara
    gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0) # Posición de la cámara
    glTranslatef(x,y,0)    # Translación
    glRotatef(angulo,1,1,0) #rotación
    glScalef(escalar,escalar,escalar) #escalar

    glBegin(GL_TRIANGLES)
    for cara in modelo.vectors: # recorrer las caras trinagulares del archivo stl
        v0,v1,v2 = cara # descomponer cada cara en sus 3 vertices
        normal = np.cross(v1 - v0, v2 - v0) # calcular
        normal = normal / np.linalg.norm(normal) # normalizar
        glNormal3fv(normal) # asignar la normal a la cara
        for vertice in cara: # recorrer cada vertice de cada triangulo
            glVertex3fv(vertice)  # dibuja cada vertice del modelo
    glEnd()
    glFlush()


def teclado( key,a,b):
    global x, y,angulo,escalar
    paso=0.05
    if key == b'a':
        x -= paso
    elif key == b's':
        x += paso
    elif key == b'w':
        y += paso
    elif key == b'z':
        y -= paso
    elif key == b'm':
        angulo += 1
    elif key == b'p':
        escalar += paso
    elif key == b'o':
        escalar -= paso 

    glutPostRedisplay()


def sliders():
    global rot_x, rot_y, rot_z, scale

    def update_rx(val):
        global rot_x
        rot_x = float(val)

    def update_ry(val):
        global rot_y
        rot_y = float(val)

    def update_rz(val):
        global rot_z
        rot_z = float(val)

    def update_scale(val):
        global scale
        scale = float(val)

    root = tk.Tk()
    root.title("Controles")

    tk.Label(root, text="Rotación X").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_rx).pack()

    tk.Label(root, text="Rotación Y").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_ry).pack()

    tk.Label(root, text="Rotación Z").pack()
    tk.Scale(root, from_=0, to=360, orient='horizontal', command=update_rz).pack()

    tk.Label(root, text="Escala").pack()
    tk.Scale(root, from_=0.1, to=3, resolution=0.1, orient='horizontal', command=update_scale).pack()

    root.mainloop()


glutInit()
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(800, 600)
glutCreateWindow(b"mi primer modelo3D")
init()
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(45, 800/600, 0.1, 100)
glMatrixMode(GL_MODELVIEW)

glutDisplayFunc(display)
glutKeyboardFunc(teclado)
glutMainLoop()