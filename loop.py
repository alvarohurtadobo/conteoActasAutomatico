#Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#PDX-License-Identifier: MIT-0 (For details, see https://github.com/awsdocs/amazon-rekognition-developer-guide/blob/master/LICENSE-SAMPLECODE.)

import re
import os
import cv2
import boto3
import base64
import urllib
import numpy as np

ROI_CC  = (355, 454, 904, 515)        #355
ROI_MAS = (355, 706, 904, 775)

DISPLAY_ROI = (355,454,904,1035)
HAND_WRITTEN_DIGITS = (355,454,904,1035)

font = cv2.FONT_HERSHEY_SIMPLEX

#Range in excel 22 octubre: 1001,90389
#actaCount = range(10001,90389)
actaCount = range(10005,10222)

def purgeNotDigitsAndConvertToInt(my_string):
    my_string = my_string.replace(" ","")
    my_string = my_string.replace("q","9")
    my_string = my_string.replace("A","1")
    my_string = my_string.replace("O","0")
    my_string = my_string.replace("o","0")
    my_string = my_string.replace("y","4")
    my_string = re.sub("[^0-9]", "", my_string)
    # Eliminar repetidos
    # Eliminar sobras del nombre
    if my_string == "":
        return 0
    return int(my_string)

def purgeDigitToInt(my_string,exp = 0):
    my_string = my_string.replace(" ","")
    my_string = my_string.replace("q","9")
    my_string = my_string.replace("A","1")
    my_string = my_string.replace("O","0")
    my_string = my_string.replace("o","0")
    my_string = my_string.replace("y","4")
    my_string = re.sub("[^0-9]", "", my_string)
    # Eliminar repetidos
    # Eliminar sobras del nombre
        
    if my_string == "":
        return 0
    else:
        digito = int(my_string)
        if exp == 2:
            if digito >3:
                return 0
    return digito

def validateCCData(results):
    validated = ""
    new_result = []
    for result in results:
        if ("C" in result['DetectedText']) and ("." in result['DetectedText']):
            validated = result['DetectedText']
        else:
            new_result.append(result)
    return validated, new_result

def validateMASData(results):
    validated = ""
    new_result = []
    for result in results:
        if (("M" in result['DetectedText']) and ("S" in result['DetectedText']) and ("P" in result['DetectedText'])) or (("M" in result['DetectedText']) and ("A" in result['DetectedText']) and ("S" in result['DetectedText']))or (("I" in result['DetectedText']) and ("P" in result['DetectedText']) and ("S" in result['DetectedText'])):
            validated = result['DetectedText']
        else:
            new_result.append(result)
    return validated, new_result

def getNumberFromResults(results,width,heigth):
    # If all results are small pieces:
    # all_text_one_character = True
    # concatenated = ""
    # for result in results:
    #     all_text_one_character = all_text_one_character and len(result['DetectedText']) == 1
    #     concatenated += result['DetectedText']
    #     long_string_conc = len(concatenated)
    #     if long_string_conc%2 == 0:
    #         print("Even length string detected {},{}".format(concatenated[:long_string_conc//2], concatenated[long_string_conc//2:]))
    #         if concatenated[:long_string_conc//2] == concatenated[long_string_conc//2:]:
    #             print("Concatenating half")
    #             concatenated = concatenated[:long_string_conc//2]
    #         else:
    #             print("Concatenating all")
    # if all_text_one_character:
    #     return purgeNotDigitsAndConvertToInt(concatenated)
    # else:
    #     length = 0
    #     longest_string = ""
    #     for result in results:
    #         result_digit = re.sub("[^0-9]", "", result['DetectedText'])
    #         if len(result_digit)>length:
    #             length = len(result_digit)
    #             longest_string = result['DetectedText']
    #             print("\tLongest digit string selected: {}".format(longest_string))
    #     return purgeNotDigitsAndConvertToInt(longest_string)
    digits = [0,0,0]
    for result in results:
        if len(result['DetectedText']) == 1:
            getPositionDigitValue(digits, result, width, heigth)

    return digits[2] + digits[1]*10 + digits[0]*100
            

def getPositionDigitValue(digits, result, width, heigth):
    poly_dict = result["Geometry"]["Polygon"]
    x_min = 0
    x_max = 0
    x_min_u = 482
    x_min_d = 428
    x_max_d = 482
    x_min_c = 369
    x_max_c = 428

    average_x = 0
    cantidad = 0

    for point in poly_dict:
        average_x += point['X']*width
        cantidad += 1

    average_x = average_x/cantidad

    if average_x > x_min_u:
        digits[2] = purgeDigitToInt(result['DetectedText'])
        print(x_min_u, average_x)
        print("Unidad: {}".format(digits[2]))
        return
    if (average_x > x_min_d) and (average_x < x_max_d):
        digits[1] = purgeDigitToInt(result['DetectedText'])
        print(x_min_d, x_max_d, average_x)
        print("Decena: {}".format(digits[1]))
        return
    if (average_x > x_min_c) and (average_x < x_max_c):
        digits[0] = purgeDigitToInt(result['DetectedText'])
        print(x_min_c, x_max_c, average_x)
        print("Centena: {}".format(digits[0]))
        return


def detect_text(photo, img, size, cc = True):

    heigth, width = size

    client=boto3.client('rekognition', region_name='us-west-2')

    response=client.detect_text(Image = {"Bytes":photo})
    #Image={'S3Object':{'Bucket':bucket,'Name':photo}}
    numpy_list = []
                        
    textDetections=response['TextDetections']
    print("Detected items: {} \n----------".format(len(textDetections)))
    if cc:
        validated, textDetectionsFiltered = validateCCData(textDetections)
    else:
        validated, textDetectionsFiltered = validateMASData(textDetections)

    if validated != "":
        print ('\Validated with String: [{}] '.format(validated))
        for text in textDetectionsFiltered:
            value = text['DetectedText']
            print ('\tDetected text:' + value)
            #print ('Confidence: ' + "{:.2f}".format(text['Confidence']) + "%")
            poly_dict = text["Geometry"]["Polygon"]
            # [{'X': 0.05282331630587578, 'Y': 0.7882960438728333}, {'X': 0.17850637435913086, 'Y': 0.7882960438728333}, {'X': 0.17850637435913086, 'Y': 0.8313252925872803}, {'X': 0.05282331630587578, 'Y': 0.8313252925872803}]
            point_list = []
            for point in poly_dict:
                point_list.append([point['X']*width,point['Y']*heigth])

            org = (int(point_list[3][0]), int(point_list[3][1]))
            #print(point_list)
            point_list = np.array(point_list, dtype = np.uint32)
            #point_list = point_list.reshape((-1,1,2))
            #print(point_list)
            #print ("Bounding: "+str(text["Geometry"]["Polygon"]))
            #print ('Id: {}'.format(text['Id']))
            #if 'ParentId' in text:
            #    print ('Parent Id: {}'.format(text['ParentId']))
            #print ('Type:' + text['Type'])
            #print(point_list)
            if cc:
                img = cv2.polylines(img, np.int32([point_list]), 1, (0,255,0)) 
            else:
                img = cv2.polylines(img, np.int32([point_list]), 1, (0,0,255)) 
            numpy_list.append(np.int32([point_list]))
            #cv2.putText(img,value , org, font, 1, (0,255,0),2)#color[, thickness[, lineType[, bottomLeftOrigin]]])

        #print("All detections:")
        #print(textDetections)
        return getNumberFromResults(textDetectionsFiltered, width, heigth), numpy_list
    else:
        return -1, []


if __name__ == "__main__":
    archivoLocal = "croped_785331_resizedWidth.jpg"

    with open(archivoLocal, "rb") as img_file:
        my_photo_string = img_file.read()
        my_photo_string_encoded = base64.b64encode(my_photo_string).decode('UTF-8')

    if not os.path.isdir("./output/"):
        os.makedirs("./output/")
    
    for count in actaCount:
        url = "https://computo.oep.org.bo/resul/imgActa/{}1.jpg".format(count)
        print("Requested URL:")
        print(url)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        url_response = urllib.request.urlopen(req)
        
        img_array = np.array(bytearray(url_response.read()),dtype=np.uint8)
        img = cv2.imdecode(img_array, -1)

        print("Received image size: {}".format(img.shape))
        roi_cc = img[ROI_CC[1]:ROI_CC[3], ROI_CC[0]:ROI_CC[2]]
        roi_mas = img[ROI_MAS[1]:ROI_MAS[3], ROI_MAS[0]:ROI_MAS[2]]

        is_success, im_buf_arr = cv2.imencode(".jpg", roi_cc)
        byte_im = im_buf_arr.tobytes()

        result_cc, numpy_list_cc = detect_text(byte_im, roi_cc, roi_cc.shape[:2],cc = True)

        is_success, im_buf_arr = cv2.imencode(".jpg", roi_mas)
        byte_im = im_buf_arr.tobytes()

        result_mas, numpy_list_mas = detect_text(byte_im, roi_mas, roi_cc.shape[:2],cc = False)

        cv2.putText(img, str(result_cc)  , (ROI_CC[2], ROI_CC[3]), font, 1, (0,255,0), 2)#color[, thickness[, lineType[, bottomLeftOrigin]]])
        cv2.putText(img, str(result_mas) , (ROI_MAS[2], ROI_MAS[3]), font, 1, (0,255,0), 2)#color[, thickness[, lineType[, bottomLeftOrigin]]])

        for plot in numpy_list_cc:
            img = cv2.polylines(img, plot, 1, (0, 255, 0)) 
        for plot in numpy_list_cc:
            img = cv2.polylines(img, plot, 1, (0, 0, 255)) 

        cv2.imwrite("./output/mesa_{}.jpg".format(count),img)


        print("C.C.: {}\tMAS: {}".format(result_cc,result_mas))

        #cv2.imshow("C.C.", roi_cc)
        #cv2.imshow("MAS.", roi_mas)
        k = cv2.waitKey()
        if k == ord("q"):
            break

    #print(my_photo_string)
    #text_count = detect_text(my_photo_string)
    #print("Text detected: " + str(text_count))