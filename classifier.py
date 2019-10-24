import re
import os
import csv
import cv2
import boto3
import base64
import urllib
import numpy as np
from datetime import datetime

"""
X
355, 720, 890, 1256, 1447

Y
454, 515, 580, 645, 706, 775, 840, 905, 970, 1035
   CC                 MAS

White ROI:
"""


DISPLAY_ROI = (355,454,890,775)#1035)
#WHITE_ROI_DOUBLE = (0, 515-454, 890-355, 706-454)
WHITE_ROI               = (720-720, 515-454, 890-720, 706-454)
HAND_WRITTEN_DIGITS_ONE = (720,     454,     890,     775)#1035)
HAND_WRITTEN_DIGITS_TWO = (1256,    454,     1447,    775)#1035)

relative_centena = (0,   57)
relative_decena  = (57,  111)
relative_unidad  = (111, 1000000)

relative_range_cc_vote  = (0,58)
relative_range_mas_vote = (256,312)

#casilla_centena_cc = (720-720,,720-720,)

font = cv2.FONT_HERSHEY_SIMPLEX

#Range in excel 22 octubre: 1001,90389
actaCount = range(10005, 10222)
actaCount = range(10001, 76814)

client=boto3.client('rekognition', region_name='us-west-2')

def isWhitinBox(point, range_list_x, range_list_y):
    if (point[0]>range_list_x[0]) and (point[0]<range_list_x[1]) and (point[1]>range_list_y[0]) and (point[1]<range_list_y[1]):
        return True
    return False

def validateResults(list_of_results):
    isValid = True
    resultadoCC = 0
    resultadoMAS = 0
    # Centena, decena, unidad
    cc = [-1,-1,-1]
    mas = [-1,-1,-1]
    
    for result in results:    
        # Here we will purge some obvious values:
        result["value"].replace("O","0")
        result["value"].replace("o","0")

        print("Analice: {}".format(result["value"]))

        # Drop low accuracy and letters
        if not result["value"] in ("0","1","2","3","4","5","6","7","8","9"):
            print("Not digit, dropping value")
            isValid = False
            result["value"] = "0"

        if result["accuracy"]<75:
            print("Low accuracy")
            isValid = False

        # Centenas CC
        if(isWhitinBox(result["center"], relative_centena,relative_range_cc_vote)):
            cc[0] = int(result["value"])
            print("{} es Centena para CC".format(result["value"]))
            continue
        # Decenas CC
        if(isWhitinBox(result["center"], relative_decena,relative_range_cc_vote)):
            cc[1] = int(result["value"])
            print("{} es Decena para CC".format(result["value"]))
            continue
        # Unid CC
        if(isWhitinBox(result["center"], relative_unidad,relative_range_cc_vote)):
            cc[2] = int(result["value"])
            print("{} es Unidad para CC".format(result["value"]))
            continue
        # Centenas MAS
        if(isWhitinBox(result["center"], relative_centena,relative_range_mas_vote)):
            mas[0] = int(result["value"])
            print("{} es Centena para MAS".format(result["value"]))
            continue
        # Decenas MAS
        if(isWhitinBox(result["center"], relative_decena,relative_range_mas_vote)):
            mas[1] = int(result["value"])
            print("{} es Decena para MAS".format(result["value"]))
            continue
        # Unid MAS
        if(isWhitinBox(result["center"], relative_unidad,relative_range_mas_vote)):
            mas[2] = int(result["value"])
            print("{} es Unidad para MAS".format(result["value"]))
            continue

    print("Resultado CC: {}".format(cc))
    print("Resultado MAS: {}".format(mas))

    if((-1 in cc) or (-1 in mas)):
        # All values must have been set
        print("Missing value, exiting")
        isValid = False
    
    if cc[2]!=-1:
        resultadoCC += cc[2]
    if cc[1]!=-1:
        resultadoCC += cc[1]*10
    if cc[0]!=-1:
        resultadoCC += cc[0]*100

    if mas[2]!=-1:
        resultadoMAS += mas[2]
    if mas[1]!=-1:
        resultadoMAS += mas[1]*10
    if mas[0]!=-1:
        resultadoMAS += mas[0]*100

    print("Success: {}, CC: {}, MAS: {}".format(isValid, resultadoCC, resultadoMAS))

    return isValid, resultadoCC, resultadoMAS

def detect_text(photo, size):
    answers = []
    """[{
        "value":"1",
        "accuracy":0.9,
        "poly": np.array()
    }]
    """
    global client
    heigth, width = size
    
    response=client.detect_text(Image = {"Bytes":photo})
    #Image={'S3Object':{'Bucket':bucket,'Name':photo}}
    numpy_list = []

    textDetections=response['TextDetections']

    for text in textDetections:
        new_value = {   "value"     : "",
                        "accuracy"  : 0,
                        "poly"      : [],
                        "poly_glob" : [],
                        "list"      : [],
                        "center"    : (0,0)
                    }
        # Solo se aceptan dígitos
        if(len(text['DetectedText'])==1):
            new_value["value"] = text['DetectedText']
            print ('\tDetected text:' + new_value["value"])
            #print ('Confidence: ' + "{:.2f}".format(text['Confidence']) + "%")
            poly_dict = text["Geometry"]["Polygon"]
            # [{'X': 0.05282331630587578, 'Y': 0.7882960438728333}, {'X': 0.17850637435913086, 'Y': 0.7882960438728333}, {'X': 0.17850637435913086, 'Y': 0.8313252925872803}, {'X': 0.05282331630587578, 'Y': 0.8313252925872803}]
            point_list = []
            point_list_global = []
            cantidad = 0
            average_x = 0
            average_y = 0
            for point in poly_dict:
                point_list.append([point['X']*width,point['Y']*heigth])
                point_list_global.append([point['X']*width+720,point['Y']*heigth+454])
                average_x += point['X']*width
                average_y += point['Y']*heigth
                cantidad += 1
            average_x = average_x/cantidad
            average_y = average_y/cantidad

            new_value["list"]      = point_list
            new_value["center"]    = (average_x,average_y)
            new_value["poly"]      = np.int32([point_list])
            new_value["poly_glob"] = np.int32([point_list_global])
            new_value["accuracy"]  = text['Confidence']
            answers.append(new_value)
            
    return answers

if __name__ == "__main__":
    name = datetime.now().strftime("%Y%m%d_%H%M%S")
    print('prueba_{}.csv'.format(name))
    with open('prueba_{}.csv'.format(name), 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow(['Acta', 'resultado aceptable', 'Digitos', 'Precision', 'Caja', 'Votos CC', 'Votos MAS'])
    cv2.namedWindow("Acta", cv2.WINDOW_NORMAL)
    cv2.namedWindow("ROI",  cv2.WINDOW_NORMAL)

    # Lets create the directories for storing the information
    if not os.path.isdir("./goodones/"):
        os.makedirs("./goodones/")
    if not os.path.isdir("./badones/"):
        os.makedirs("./badones/")
    if not os.path.isdir("./original/"):
        os.makedirs("./original/")
    
    for count in actaCount:
        url = "https://computo.oep.org.bo/resul/imgActa/{}1.jpg".format(count)
        print("Requested URL:")
        print(url)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        url_response = urllib.request.urlopen(req)
        
        img_array = np.array(bytearray(url_response.read()),dtype=np.uint8)
        img = cv2.imdecode(img_array, -1)
        copy = img.copy()

        print("Received image size: {}".format(img.shape))
        roi_one = img[HAND_WRITTEN_DIGITS_ONE[1]:HAND_WRITTEN_DIGITS_ONE[3], HAND_WRITTEN_DIGITS_ONE[0]:HAND_WRITTEN_DIGITS_ONE[2]]
        #roi_two = img[HAND_WRITTEN_DIGITS_TWO[1]:HAND_WRITTEN_DIGITS_TWO[3], HAND_WRITTEN_DIGITS_TWO[0]:HAND_WRITTEN_DIGITS_TWO[2]]

        #hand_roi = np.hstack((roi_one,roi_two))
        hand_roi = roi_one.copy()
        print(WHITE_ROI)
        print(hand_roi[WHITE_ROI[1]:WHITE_ROI[3], WHITE_ROI[0]:WHITE_ROI[2]].shape)
        #cv2.imshow("WHITE_ROI",hand_roi[WHITE_ROI[1]:WHITE_ROI[3], WHITE_ROI[0]:WHITE_ROI[2]])
        hand_roi[WHITE_ROI[1]:WHITE_ROI[3], WHITE_ROI[0]:WHITE_ROI[2]] = np.zeros((WHITE_ROI[3]-WHITE_ROI[1],WHITE_ROI[2]-WHITE_ROI[0], 3))
        is_success, im_buf_arr = cv2.imencode(".jpg", hand_roi)
        byte_im = im_buf_arr.tobytes()

        results = detect_text(byte_im, hand_roi.shape[:2])
        #print(results)

        validated = True

        # for result in results:
        #     if 
        digitos = []
        accuracies = []
        polys = []


        for result in results:
            digitos.append(result["value"])
            accuracies.append(result["accuracy"])
            polys.append(result["poly"].tolist())
            hand_roi = cv2.putText(hand_roi,   result["value"],        (result["poly"][0][3][0], result["poly"][0][3][1]), font, 1,   (0,255,0),2)
            accuracy = result["accuracy"]
            if accuracy>75:
                hand_roi = cv2.putText(hand_roi,   str(int(accuracy)), (result["poly"][0][2][0], result["poly"][0][2][1]), font, 0.5, (255,0,0),2)
            else:
                hand_roi = cv2.putText(hand_roi,   str(int(accuracy)), (result["poly"][0][2][0], result["poly"][0][2][1]), font, 0.5, (0,0,255),2)
            hand_roi = cv2.polylines(hand_roi, result["poly"], 1, (0, 255, 0)) 
            img = cv2.polylines(img, result["poly_glob"],      1, (0, 255, 0)) 

        isValid, result_cc, result_mas = validateResults(results)

        if isValid:
            folder = "goodones"
            color = (0,255,0)
            aceptable = "Si"
        else:
            folder = "badones"
            color = (0,0,0)
            aceptable = "No"

        with open('prueba_{}.csv'.format(name), 'a') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            filewriter.writerow([str(count), aceptable, str(digitos), str(accuracies), str(polys), result_cc, result_mas])

        img = cv2.putText(img, str(result_cc),  (890,515), font, 2, color, 2)
        img = cv2.putText(img, str(result_mas), (890,775), font, 2, color, 2) 

        cv2.imshow("ROI", hand_roi)
        cv2.imshow("Acta", img)
        k = cv2.waitKey(1)

        
        cv2.imwrite("./{}/mesa_{}_process.jpg".format(folder, count),img)
        cv2.imwrite("./{}/mesa_{}_original.jpg".format(folder, count),copy)
        cv2.imwrite("./{}/mesa_{}_roi.jpg".format(folder, count),hand_roi)
        cv2.imwrite("./original/mesa_{}.jpg".format(count),copy)

        if k == ord("q"):
            break
        

        