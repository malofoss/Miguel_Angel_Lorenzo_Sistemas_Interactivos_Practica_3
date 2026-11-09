import math
import time

import cv2
import mediapipe as mp


class Button:
    def __init__(self, pos, width, height, value):
        self.pos = pos
        self.width = width
        self.height = height
        self.value = value

    # he añadido el parámetro color para poder pintar el botón de otro color
    # cuando el cursor está encima o cuando se pulsa
    def draw(self, img, color=(225, 225, 225)):
        s = self.height / 100
        cv2.rectangle(img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height),
                      color, cv2.FILLED)
        cv2.rectangle(img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height),
                      (50, 50, 50), 3)

        text_x = self.pos[0] + self.width // 2 - int(15 * s)
        text_y = self.pos[1] + self.height // 2 + int(15 * s)

        cv2.putText(img, self.value, (text_x, text_y), cv2.FONT_HERSHEY_PLAIN,
                    3 * s, (50, 50, 50), max(1, round(3 * s)))

    # compruebo si un punto (el cursor) está dentro del botón
    def is_inside(self, point):
        x, y = point
        return (self.pos[0] <= x <= self.pos[0] + self.width and
                self.pos[1] <= y <= self.pos[1] + self.height)


# distancia entre dos puntos, la uso para saber si los dedos están juntos
def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# MUST be configured for each system
cap = cv2.VideoCapture(0)

#input image size, based on your webcam
WIDTH = 1920
HEIGHT = 1080
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

success, img = cap.read()
if not success:
    print("Failed to read frame")
    exit(1)
HEIGHT, WIDTH = img.shape[:2]
scale = HEIGHT / 1080
size = int(100 * scale)

# basic list of buttons, may be changed (changes must be justified)
buttonListValues = [['C', '<'],
                    ['7', '8', '9', '/'],  # ÷ cant be rendered, so well have to do with / :/
                    ['4', '5', '6', '*'],
                    ['1', '2', '3', '-'],
                    ['0', '.', '=', '+']]

buttonlist = []
for y in range(5):
    for x in range(4):
        if y == 0 and x >= 2:  # first row only has 2 buttons (C and <), so kinda special case
            break

        xpos = int(WIDTH - 5 * size + x * size)
        ypos = int(HEIGHT * 0.15 + y * size)

        # first row special case, second button needs to be shifted
        if y == 0 and x == 1: #not the most elegant
            xpos += size

        if y == 0:
            width = 2 * size
            buttonlist.append(Button((xpos, ypos), width, size, buttonListValues[y][x]))
        else:
            buttonlist.append(Button((xpos, ypos), size, size, buttonListValues[y][x]))

operation = ""

# uso MediaPipe Hands para detectar la mano.
# Solo detecto una mano para que haya un único cursor y no haya confusiones.
# Uso el modelo ligero (model_complexity=0) para que vaya más rápido y haya menos retraso.
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1,
                       model_complexity=0,
                       min_detection_confidence=0.7,
                       min_tracking_confidence=0.6)
mp_draw = mp.solutions.drawing_utils

# ajustes de mi gesto de "pinza" (juntar índice y pulgar)
PINCH_CLOSE = 0.25  # si la distancia entre los dedos baja de esto, considero que he cerrado la pinza
PINCH_OPEN = 0.40   # y solo la considero abierta otra vez cuando pasa de esto (así no parpadea)
HOLD_TIME = 0.3     # segundos que tengo que mantener la pinza para que la pulsación cuente

# Colores que uso para que el usuario sepa qué está pasando (en formato BGR)
COLOR_HOVER = (255, 210, 150)    # azul claro: el cursor está encima del botón
COLOR_PRESSING = (150, 220, 150) # verde claro: estoy manteniendo la pinza
COLOR_DONE = (80, 200, 80)       # verde: la tecla se ha aceptado

# variables para controlar las pulsaciones
pinched = False      # si ahora mismo tengo los dedos juntos
armed = True         # si puedo hacer una pulsación nueva (tengo que abrir los dedos entre pulsaciones)
target = None        # el botón que estoy pulsando
pinch_start = 0      # cuándo empecé a hacer la pinza
done_button = None   # el último botón aceptado, para iluminarlo un momento
done_until = 0

# creo la ventana redimensionable y le doy un tamaño que cabe en la pantalla.
# Sin esto, con la imagen a 1920x1080 y el escalado de Windows, la calculadora
# (que está a la derecha) se quedaba fuera de la pantalla.
cv2.namedWindow('Calculator', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Calculator', 1280, 720)

while True:
    success, img = cap.read()
    if not success:
        print("Failed to read frame")
        break

    # giro la imagen como un espejo para que, si muevo la mano a la derecha,
    # el cursor también vaya a la derecha
    img = cv2.flip(img, 1)

    operation_x = int(WIDTH - 5 * size)
    operation_y = int(HEIGHT * 0.05)

    cv2.rectangle(img, (operation_x, operation_y), (operation_x + 4 * size, operation_y + int(1.2 * size)),
                  (225, 225, 225), cv2.FILLED)
    cv2.rectangle(img, (operation_x, operation_y), (operation_x + 4 * size, operation_y + int(1.2 * size)),
                  (50, 50, 50), 3)

    # busco la mano en la imagen (MediaPipe necesita la imagen en RGB)
    result = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    cursor = None
    if result.multi_hand_landmarks:
        hand = result.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(img, hand, mp_hands.HAND_CONNECTIONS)

        # Paso los 21 puntos de la mano a píxeles
        points = [(int(p.x * WIDTH), int(p.y * HEIGHT)) for p in hand.landmark]
        thumb = points[4]   # punta del pulgar
        index = points[8]   # punta del índice

        # El cursor es el punto medio entre el pulgar y el índice. Al cerrar la pinza
        # los dos dedos se acercan entre sí, así que el cursor casi no se mueve y no
        # cambia de botón justo al pulsar.
        cursor = ((thumb[0] + index[0]) // 2, (thumb[1] + index[1]) // 2)

        # Divido la distancia entre los dedos por el tamaño de la mano (muñeca -> nudillo
        # del dedo corazón). Así el gesto funciona igual si estoy cerca o lejos de la cámara.
        hand_size = max(distance(points[0], points[9]), 1)
        ratio = distance(thumb, index) / hand_size

        # Uso dos umbrales distintos (histéresis) para que, cerca del límite,
        # la pinza no se abra y se cierre sola en cada fotograma
        if pinched and ratio > PINCH_OPEN:
            pinched = False
        elif not pinched and ratio < PINCH_CLOSE:
            pinched = True
    else:
        pinched = False  # si no veo la mano, no hay pinza

    # miro qué botón está debajo del cursor
    hovered = None
    if cursor is not None:
        for button in buttonlist:
            if button.is_inside(cursor):
                hovered = button

    # when something triggers, the calculator should actually calculate
    # the something should be programmed by you, of course
    something = False
    received_val = ""

    # decido si hay una pulsación. Para que un movimiento cualquiera no cuente:
    # 1. el botón se elige en el momento en que empiezo la pinza,
    # 2. tengo que mantener la pinza HOLD_TIME segundos,
    # 3. después de pulsar tengo que abrir los dedos para poder pulsar otra vez,
    # 4. si empiezo la pinza fuera de los botones, no cuenta.
    now = time.time()
    if not pinched:
        armed = True
        target = None
    elif armed:
        if target is None:
            if hovered is None:
                armed = False
            else:
                target = hovered
                pinch_start = now
        elif now - pinch_start >= HOLD_TIME:
            something = True
            received_val = target.value
            done_button = target
            done_until = now + 0.3
            target = None
            armed = False

    # pinto los botones aquí, con un color según lo que esté pasando
    for button in buttonlist:
        if button is done_button and now < done_until:
            button.draw(img, COLOR_DONE)
        elif button is target:
            button.draw(img, COLOR_PRESSING)
        elif button is hovered:
            button.draw(img, COLOR_HOVER)
        else:
            button.draw(img)

    # barra que se va llenando mientras mantengo la pinza
    if target is not None:
        progress = min(1, (now - pinch_start) / HOLD_TIME)
        x, y = target.pos
        cv2.rectangle(img, (x, y + target.height - 10),
                      (x + int(target.width * progress), y + target.height),
                      COLOR_DONE, cv2.FILLED)

    if something:
        if operation == "Error":  # si había un error, empiezo de cero
            operation = ""
        if received_val == "=":
            try:
                operation = str(eval(operation))
            except:
                operation = "Error"
        elif received_val == "C":  # Reset
            operation = ""
        elif received_val == "<":  # remove char
            operation = operation[:-1]
        else:
            operation += received_val
        delayCounter = 1

    cv2.putText(img, operation, (operation_x + int(0.1 * size), operation_y + int(0.75 * size)),
                cv2.FONT_HERSHEY_PLAIN, 3 * scale, (50, 50, 50), max(1, round(3 * scale)))

    # dibujo el cursor (naranja con la mano abierta, verde con la pinza cerrada)
    if cursor is not None:
        cv2.circle(img, cursor, 12, (80, 200, 80) if pinched else (0, 140, 255), cv2.FILLED)

    # texto de ayuda para que el usuario sepa cómo usarla
    cv2.putText(img, "Junta indice y pulgar sobre un boton para pulsarlo. q: salir",
                (20, 40), cv2.FONT_HERSHEY_PLAIN, 2 * scale, (255, 255, 255), 2)

    cv2.imshow('Calculator', img)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break

# libero la cámara y cierro la ventana al salir
hands.close()
cap.release()
cv2.destroyAllWindows()
