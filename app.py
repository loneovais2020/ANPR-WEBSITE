#import dependencies
from flask import Flask, render_template,request
import requests
import cv2
from matplotlib import pyplot as plt
import numpy as np
import imutils
import easyocr
import requests



app = Flask(__name__)


@app.route('/',methods=["GET"])
def home():
    return render_template('index.html')

@app.route('/',methods=["POST"])
def upload_image():
    r_num=request.form.get('reg_num')
    if len(r_num)>0 :
        r_num=request.form.get('reg_num')
        print(f'the reg no. is {r_num}')
        find_details(r_num)
        
    else:
        imageFile=request.files['imagefile']
        imagePath=imageFile.filename
        # calling the find_num_plate function 
        find_num_plate(imagePath)
    
    return render_template('show_details.html',results=results)



def find_num_plate(img_path):
    # read in image,grayscale and blur
    img=cv2.imread(img_path)
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # plt.imshow(cv2.cvtColor(gray,cv2.COLOR_BGR2RGB))
    # Apply filter and find     edges for localization
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17) #Noise reduction
    edged = cv2.Canny(bfilter, 30, 200) #Edge detection
    # plt.imshow(cv2.cvtColor(edged, cv2.COLOR_BGR2RGB))
    # Find Contours and Apply Mask
    keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(keypoints)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    location = None
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            location = approx
            break
    
    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [location], 0,255, -1)
    new_image = cv2.bitwise_and(img, img, mask=mask)
    (x,y) = np.where(mask==255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped_image = gray[x1:x2+1, y1:y2+1] 
    # plt.imshow(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))
    # Use Easy OCR To Read Text
    reader = easyocr.Reader(['en'])
    result = reader.readtext(cropped_image)
    # print(result)
    # Render Result
    text = result[0][-2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    res = cv2.putText(img, text=text, org=(approx[0][0][0], approx[1][0][1]+60), fontFace=font, fontScale=1, color=(0,255,0), thickness=2, lineType=cv2.LINE_AA)
    res = cv2.rectangle(img, tuple(approx[0][0]), tuple(approx[2][0]), (0,255,0),3)
    # plt.imshow(cv2.cvtColor(res, cv2.COLOR_BGR2RGB))
    
    # remove spaces from the generated text
    new_text = text.replace(" ","")
    print(f"the plate no. is {new_text}")
    # calling the find details function
    find_details(new_text)




def find_details(plate_num):
    

    url = "https://vehicle-rc-information.p.rapidapi.com/"

    payload = { "VehicleNumber": plate_num }
    headers = {
 "content-type": "application/json",
 "X-RapidAPI-Key": "f5210d201fmsha58c733f838ed9fp1861d1jsn92d6212006d3",
 "X-RapidAPI-Host": "vehicle-rc-information.p.rapidapi.com"
}

    response = requests.post(url, json=payload, headers=headers)

    print(response.json())
    res=response.json()
    global results
    results={"Registration Number":res['result']['registration_number'],
         "Owner Name":res['result']['owner_name'],
         "Father's Name" :res['result']['father_name'],
         "Address":res['result']['current_address'],
         "Vehicle Model":res['result']['manufacturer_model'],
         "Registration Date":res['result']['registration_date'],
         "Chasis Number":res['result']['chassis_number'],
         "Engine Number":res['result']['engine_number'],
         "Fitness Upto":res['result']['fitness_upto']
         
         }
    

    


if __name__=='__main__':
    app.run(port=3000,debug=True)

