import os
import cv2
import sys
import numpy as np
import pytesseract

# python main.py /path/to/folder/

"""
X
355, 697, 904, 1256, 1447

Y
454, 515, 580, 645, 706, 775, 840, 905, 970, 1035

7363541-1O   Ivan


2554 - 1648


2553 - 1644


2543 - 1644


Ractangle total: 360,462 x 1439,1035

X
355, 697, 904, 1256, 1447

Y
454, 515, 580, 645, 706, 775, 840, 905, 970, 1035


https://computo.oep.org.bo/resul/imgActa/509401.jpg


 Mesa 76814

Cc: 25. En acta: cc=125

Mesa 78533

Cc= 6. En acta: cc=66

Mesa 10514

Cc= 88. Trep: cc=142

Mesa 72228

Cc= 1. En acta cc=54

"""
#(Xinit, Yinit, Xend, Yend)

#DISPLAY_ROI = (355,454,1447,1035)
DISPLAY_ROI = (355,454,904,1035)

PRESIDENT_BOXES = {
    "C.C.":     (697, 454, 904, 515),
    "FPV":      (697, 515, 904, 580),
    "MTS":      (697, 580, 904, 645),
    "UCS":      (697, 645, 904, 706),
    "MAS":      (697, 706, 904, 775),
    "21F":      (697, 775, 904, 840),
    "PDC":      (697, 840, 904, 905),
    "MNR":      (697, 905, 904, 970),
    "PAN":      (697, 970, 904, 1035),
}

DEPUTY_BOXES = {
    "C.C.":     (1256, 454, 1447, 515),
    "FPV":      (1256, 515, 1447, 580),
    "MTS":      (1256, 580, 1447, 645),
    "UCS":      (1256, 645, 1447, 706),
    "MAS":      (1256, 706, 1447, 775),
    "21F":      (1256, 775, 1447, 840),
    "PDC":      (1256, 840, 1447, 905),
    "MNR":      (1256, 905, 1447, 970),
    "PAN":      (1256, 970, 1447, 1035),
}

cv2.namedWindow("Acta",cv2.WINDOW_NORMAL)
cv2.namedWindow("Number",cv2.WINDOW_NORMAL)
cv2.namedWindow("K means",cv2.WINDOW_NORMAL)
#config = ("-l eng --oem 1 --psm 7 -c tessedit_char_whitelist=0123456789")
config = ("-l eng --oem 1 --psm 7 'digits'")
#config = ("--oem 1 --psm 7 -c tessedit_char_whitelist=0123456789")

k = ord("a")

folderPath = sys.argv[1]
files_and_actas = os.listdir(folderPath)
actas = [possible_acta for possible_acta in files_and_actas if ".jpg" in possible_acta]

for acta in actas:
    print("Número de mesa: " + acta.replace(".jpg","")[:-1])
    frame = cv2.imread(folderPath+"/"+acta)
    roi = frame[DISPLAY_ROI[1]:DISPLAY_ROI[3], DISPLAY_ROI[0]:DISPLAY_ROI[2]]
    cv2.imshow("Acta", roi)

    for (key, value) in PRESIDENT_BOXES.items():
        number_roi = frame[value[1]:value[3],value[0]:value[2]]
        #number_roi[:, :, 2] = 255
        cv2.imshow("Number",number_roi)

        pixeles = number_roi.reshape((-1,3))
        
        pixeles = np.float32(pixeles)
        h, w, canales = number_roi.shape
        
        sumDistances, labels, center = cv2.kmeans(pixeles, K = 4, bestLabels = None, criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,15,1.0), attempts = 10, flags = cv2.KMEANS_RANDOM_CENTERS)
        
        print(type(center))
        center_white_black = np.array(())
        index = -1
        min_value = 10000000000

        k = cv2.waitKey()
        
        for ind in range(len(center)):
            #print("Index",ind)
            point = center[ind]
            absvalue = point[0]**2+point[1]**2+point[2]**2
            if absvalue < min_value:
                min_value = absvalue
                index = ind

        for ind in range(len(center)):
            if ind !=index:
                center[ind] = np.array((255,255,255))
            else:
                center[ind] = np.array((0,0,0))

        center = np.uint8(center)
        res = center[labels.flatten()]
        res = np.reshape(res,(h,w,canales))

        cv2.imshow('K means',res)#np.hstack((res,pixeles))
        text = pytesseract.image_to_string(number_roi, config="digits")
        ktext = pytesseract.image_to_string(res, config="digits")

        print(key + " \t " + text + "->" +  ktext)
        k = cv2.waitKey()
        if k == ord("n"):
            break

        if k == ord("s"):
            print("Saving: qcroped_"+acta)
            cv2.imwrite("croped_"+acta, roi)
    print(text)
    k = cv2.waitKey()

    if k == ord("q"):
        break