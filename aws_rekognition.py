#Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#PDX-License-Identifier: MIT-0 (For details, see https://github.com/awsdocs/amazon-rekognition-developer-guide/blob/master/LICENSE-SAMPLECODE.)

import boto3
import base64


def detect_text(photo):

    client=boto3.client('rekognition', region_name='us-west-2')

    response=client.detect_text(Image = {"Bytes":photo})
    #Image={'S3Object':{'Bucket':bucket,'Name':photo}}
                        
    textDetections=response['TextDetections']
    print ('Detected text\n----------')
    for text in textDetections:
            print ('Detected text:' + text['DetectedText'])
            print ('Confidence: ' + "{:.2f}".format(text['Confidence']) + "%")
            print ("Bounding: "+text["BoundingBox"])
            print ('Id: {}'.format(text['Id']))
            if 'ParentId' in text:
                print ('Parent Id: {}'.format(text['ParentId']))
            print ('Type:' + text['Type'])
            print()

    #print("All detections:")
    #print(textDetections)
    return len(textDetections)


if __name__ == "__main__":
    archivoLocal = "croped_785331_resizedWidth.jpg"

    with open(archivoLocal, "rb") as img_file:
        my_photo_string = img_file.read()
        my_photo_string_encoded = base64.b64encode(my_photo_string).decode('UTF-8')

    #print(my_photo_string)
    text_count = detect_text(my_photo_string)
    #print("Text detected: " + str(text_count))