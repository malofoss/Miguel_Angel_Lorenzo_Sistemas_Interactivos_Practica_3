import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Failed to open capture")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

print("Video capture started at {}x{}".format(
    int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
    int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
))

# igual que en sample_main.py, hago la ventana redimensionable y le doy
# un tamaño que cabe en la pantalla (a 1920x1080 con el escalado de Windows se salía)
cv2.namedWindow("Webcam", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Webcam", 1280, 720)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame")
        break
    cv2.imshow("Webcam", frame)
    # Escape
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
