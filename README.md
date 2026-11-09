# Práctica 3: calculadora basada en gestos

Miguel Ángel Lorenzo Fossati, Sistemas Interactivos Inteligentes (UIE)

## Sistema operativo y cómo ejecutarla

He hecho la práctica en **Windows**, así que la ejecuto con **uv**, sin Docker (en Windows Docker no puede usar la cámara).

Desde la carpeta `p3-gest-calc`:

```
uv venv
uv pip install -r requirements.txt
uv run python src/gest-calc/webcam_test.py
uv run python src/gest-calc/sample_main.py
```

Uso la cámara 0. Si hay que usar otra, se cambia el número en `cv2.VideoCapture(0)` dentro de `sample_main.py`.

No he cambiado `requirements.txt` ni las versiones de las librerías.

## Cómo se usa

- Muevo la mano delante de la cámara. El cursor (el círculo naranja) está entre las puntas del índice y del pulgar.
- Para pulsar un botón, junto el índice y el pulgar (una "pinza") encima de él y lo mantengo un momento. Se llena una barra verde y, cuando se acepta, el botón se pone verde.
- Para pulsar otro botón, primero tengo que separar los dedos.
- `C` borra todo, `<` borra el último carácter y `=` calcula.
- Con la tecla `q` se cierra el programa.

## Qué he cambiado respecto al código dado

He mantenido el código que nos dieron y solo he añadido la parte de los gestos en `sample_main.py`. Todo lo que he añadido o cambiado está marcado en el código con comentarios.

- **Detección de la mano** con MediaPipe Hands (una sola mano y el modelo ligero, para que vaya más rápido).
- **Gesto de pinza** (juntar índice y pulgar) para pulsar. Lo elegí porque es parecido a "pulsar" o "agarrar", se aprende enseguida y no se hace sin querer con la mano abierta.
- **Cursor en el punto medio entre pulgar e índice**, para que no se mueva a otro botón al cerrar la pinza.
- **Distancia de la pinza dividida por el tamaño de la mano**, para que funcione igual cerca o lejos de la cámara.
- **Dos umbrales (histéresis)** para que la pinza no parpadee cerca del límite.
- **Para evitar pulsaciones sin querer**: el botón se elige al empezar la pinza, hay que mantenerla 0,3 s, cada pinza solo pulsa una vez, y si empiezo la pinza fuera de los botones no cuenta.
- **Feedback visual**: el botón se pone azul cuando el cursor está encima y aparece una barra verde mientras mantengo la pinza. El botón se pone verde cuando la pulsación se acepta, y el cursor cambia de color con la pinza cerrada.
- **Imagen en espejo**, para que el cursor se mueva hacia el mismo lado que mi mano.
- Si sale `Error`, la siguiente tecla empieza una operación nueva.
- Al salir, cierro la cámara y la ventana.
- La ventana es redimensionable y empieza a 1280x720, porque a 1920x1080 con el escalado de Windows la calculadora se salía de la pantalla.
