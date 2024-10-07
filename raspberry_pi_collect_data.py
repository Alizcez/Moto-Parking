import cv2
import datetime
import time

cam = cv2.VideoCapture(0)
# cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) # this is the magic!

cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
print("start")

while True:
	ct = str(datetime.datetime.now())
	ret, img = cam.read()
	cv2.imwrite(f"now.png", img)
	if int(ct[11:13]) < 6 or int(ct[11:13]) > 18:
		continue
	if ct[14:16] in ["00", "15", "30", "45"]:
		print(f"cap {ct}")
		for i in range(50):
			ret, image = cam.read()
		cv2.imwrite(f'./img/{ct[:10]}-{ct[11:13]}-{ct[14:16]}.png', image)
		
	ret = 0
	image = 0
cam.release()
