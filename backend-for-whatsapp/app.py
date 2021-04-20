''' Import Libraries '''

from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import os
import json
import math
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt 
from twilio.twiml.messaging_response import MessagingResponse
from ibm_watson_machine_learning import APIClient
from twilio.rest import Client
from PIL import Image, ImageDraw, ImageFont

''' Initialize Flask Variables '''

app = Flask(__name__)

app.config["SERVICES"] = 'static/watsonservices/'
app.config["CREDENTIALS"] = 'static/watsoncredentials/'
app.config["DATASET"] = 'static/datasets/'

account_sid = ""
auth_token = ""
wml_credentials = {}
space_id = ""

receivedMsg = ""
sentMsg = ""
area = ""
sqft = ""
bhk = ""


@app.route('/getWmlCredentials')
def getWmlCredentials(): 
    try:
        global wml_credentials, space_id
        with open(app.config["CREDENTIALS"]+'wmlCredentials.json') as wmlCreds:
            wmlcred = json.loads(wmlCreds.read())
            
        wml_credentials = {
            "apikey": wmlcred.get('apikey'),
            "url": wmlcred.get('url')
        }
        
        space_id = wmlcred.get('space_id')
        
        returnablejson = wml_credentials
        returnablejson.update({"status": "Configured"})
        
        return jsonify(returnablejson)
    except:
        return jsonify({"status": "Not Configured"})
    

@app.route('/getWatsonCredentials')
def getWatsonCredentials():
    try:
        x = scanAvailableFiles(app.config['CREDENTIALS'])
        
        returnableObj = {"services": x}        
        
        return jsonify(returnableObj)
    except:
        return jsonify({"services": ["No Service Configured"]})

@app.route('/getTwilioCredentials')
def getTwilioCredentials():
    try:
        global account_sid
        global auth_token
        with open('twiliocredentials.json') as creds:
            twiliocred = json.loads(creds.read())
    
        account_sid = twiliocred.get('account_sid')
        auth_token = twiliocred.get('auth_token')
        return jsonify({"status": "Configured"})
    except:
        return jsonify({"status": "Not Configured"})

@app.route('/getDeploymentState')
def getDeploymentState():
    try:
        with open(app.config["SERVICES"]+'wmlDeployment.json') as temp:
            cred = json.loads(temp.read())
        model_id = cred["entity"]["asset"]["id"]
        model_name = cred["entity"]["name"]
        model_status = cred["entity"]["status"]["state"]
        return jsonify({
            "status": model_status, 
            "modelId": model_id,
            "modelName": model_name,
            })
    except:
        return jsonify({"status": "Model not Deployed"})

@app.route('/storeTwilioCredentials', methods=['GET', 'POST'])
def storeTwilioCredentials():
    receivedPayload = json.loads(request.form['Credentials'])
    
    data = {
        "account_sid": receivedPayload.get('account_sid'),
        "auth_token": receivedPayload.get('auth_token')
    }
    
    with open('twiliocredentials.json', 'w') as fs:
        json.dump(data, fs, indent=2)

    return jsonify({"status": "Configured"})


@app.route('/storeWatsonCredentials', methods=['GET', 'POST'])
def storeWatsonCredentials():
    receivedPayload = json.loads(request.form['Credentials'])
    
    if receivedPayload.get('type') == "wml":
        
        data = receivedPayload
        data.pop("type")

        with open(app.config["CREDENTIALS"]+'wmlCredentials.json', 'w') as fs:
            json.dump(data, fs, indent=2)

        return jsonify({"status": "Configured"})
    
    data = json.loads(receivedPayload.get('apikey'))
    data.update({"cloudfunctionurl": receivedPayload.get('cloudfunctionurl')+'.json'})
    data.update({"windowURL": receivedPayload.get('windowURL')})
    with open(app.config["CREDENTIALS"]+receivedPayload.get('type')+'Credentials.json', 'w') as fs:
        json.dump(data, fs, indent=2)

    return jsonify({"status": "Configured"})


@app.route('/deployWMLModel')
def deployWMLModel():
    ''' Step 1: Build the Linear Regression Model '''
    #importing the dataset
    df1 = pd.read_csv(app.config["DATASET"]+'Bengaluru_House_Data.csv')
    df2 = df1.drop(['area_type', 'society', 'balcony',
                    'availability'], axis='columns')
    df3 = df2.dropna()
    df3['bhk'] = df3['size'].apply(lambda x: int(x.split(' ')[0]))
    df3[df3.bhk > 20]

    def is_float(x):
        try:
            float(x)
        except:
            return False
        return True

    df3[~df3['total_sqft'].apply(is_float)]

    def convert_sqft_to_num(x):
        tokens = x.split('-')
        if len(tokens) == 2:
            return(float(tokens[0])+float(tokens[1]))/2
        try:
            return float(x)
        except:
            return None

    convert_sqft_to_num('2166')
    convert_sqft_to_num('2100-3000')

    df4 = df3.copy()
    df4['total_sqft'] = df4['total_sqft'].apply(convert_sqft_to_num)

    #now we will start with feature engineering techniques and dimensionality reduction techniques
    df5 = df4.copy()
    #now we will create price per sqft
    df5['price_per_sqft'] = df5['price']*100000/df5['total_sqft']

    df5.location = df5.location.apply(lambda x: x.strip())
    location_stats = df5.groupby('location')['location'].agg(
        'count').sort_values(ascending=False)
    location_stats_less_than_10 = location_stats[location_stats <= 10]
    df5.location = df5.location.apply(
        lambda x: 'other'if x in location_stats_less_than_10 else x)

    df6 = df5[~(df5.total_sqft/df5.bhk < 300)]

    def remove_pps_outliers(df):
        df_out = pd.DataFrame()
        for key, subdf in df.groupby('location'):
            m = np.mean(subdf.price_per_sqft)
            st = np.std(subdf.price_per_sqft)
            reduced_df = subdf[(subdf.price_per_sqft > (m-st))
                               & (subdf.price_per_sqft <= (m+st))]
            df_out = pd.concat([df_out, reduced_df], ignore_index=True)
        return df_out

    df7 = remove_pps_outliers(df6)

    def remove_bhk_outliers(df):
        exclude_indices = np.array([])
        for location, location_df in df.groupby('location'):
            bhk_stats = {}
            for bhk, bhk_df in location_df.groupby('bhk'):
                bhk_stats[bhk] = {
                    'mean': np.mean(bhk_df.price_per_sqft),
                    'std': np.std(bhk_df.price_per_sqft),
                    'count': bhk_df.shape[0]
                }
            for bhk, bhk_df in location_df.groupby('bhk'):
                stats = bhk_stats.get(bhk-1)
                if stats and stats['count'] > 5:
                    exclude_indices = np.append(
                        exclude_indices, bhk_df[bhk_df.price_per_sqft < (stats['mean'])].index.values)
        return df.drop(exclude_indices, axis='index')
    df8 = remove_bhk_outliers(df7)

    df9 = df8[df8.bath < df8.bhk+2]
    df10 = df9.drop(['size', 'price_per_sqft'], axis='columns')

    dummies = pd.get_dummies(df10.location)
    df11 = pd.concat([df10, dummies], axis='columns')

    df11 = df11.drop(['other'], axis='columns')
    df12 = df11.drop('location', axis='columns')

    #will define dependent variable for training
    X = df12.drop('price', axis='columns')
    y = df12.price

    from sklearn.model_selection import train_test_split
    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=10)

    from sklearn.linear_model import LinearRegression
    lr_clf = LinearRegression()
    lr_clf.fit(x_train, y_train)
    lr_clf.score(x_test, y_test)
    print("Model Built Successfully")

    ''' Deploy the Model to Watson Machine Learning '''
    getWmlCredentials()

    client = APIClient(wml_credentials)
    
    client.set.default_space(space_id)
    
    sofware_spec_uid = client.software_specifications.get_id_by_name(
        "scikit-learn_0.20-py3.6")

    metadata = {
        client.repository.ModelMetaNames.NAME: 'Bangalore House Price Prediction',
        client.repository.ModelMetaNames.TYPE: "default_py-3.7",
        client.repository.ModelMetaNames.SOFTWARE_SPEC_UID: sofware_spec_uid
    }

    published_model = client.repository.store_model(
        lr_clf, meta_props=metadata)

    published_model_uid = client.repository.get_model_uid(published_model)
    model_details = client.repository.get_details(published_model_uid)

    # print(json.dumps(model_details, indent=2))

    models_details = client.repository.list_models()

    loaded_model = client.repository.load(published_model_uid)
    test_predictions = loaded_model.predict(x_test[:10])

    deploy_meta = {
        client.deployments.ConfigurationMetaNames.NAME: 'Deployment of Bangalore House Price Prediction',
        client.deployments.ConfigurationMetaNames.ONLINE: {}
    }
    created_deployment = client.deployments.create(
        published_model_uid, meta_props=deploy_meta)

    with open(app.config["SERVICES"]+'wmlDeployment.json', 'w') as fp:
        json.dump(created_deployment, fp,  indent=2)

    print(json.dumps(created_deployment, indent=2))
    print("Model Successfully Deployed..")
    with open(app.config["SERVICES"]+'wmlDeployment.json') as temp:
        cred = json.loads(temp.read())
    model_id = cred["entity"]["asset"]["id"]
    return jsonify({"status": "Deployed, Model ID: "+model_id})

def predict_price_wml(location,sqft,bath,bhk):
    getWmlCredentials()
    
    client = APIClient(wml_credentials)
    client.set.default_space(space_id)
    deployments = client.deployments.get_details()

    with open(app.config["SERVICES"]+'wmlDeployment.json', 'r') as wmlDeployment:
        cred = json.loads(wmlDeployment.read())

    scoring_endpoint = client.deployments.get_scoring_href(cred)
    X = pd.read_csv(app.config['DATASET']+'intermediate.csv')
    loc_index=np.where(X.columns==location)[0][0]
    x=np.zeros(len(X.columns), dtype=int)
    x[0]=sqft
    x[1]=bath
    x[2]=bhk
    if loc_index >=0:
        x[loc_index]=1
    
    y = [x.tolist()]
    z = list(list(y))
    did = client.deployments.get_uid(cred)

    job_payload = {
    client.deployments.ScoringMetaNames.INPUT_DATA: [{
     'values': z
    }]
    }
    scoring_response = client.deployments.score(did, job_payload)
    return math.ceil(scoring_response['predictions'][0]['values'][0][0])
    

def createImagePrediction(area, bhk, sqft, price):
    image = Image.open('static/images/DarkOcean.png')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('static/fonts/Roboto.ttf', size=55)

    (x, y) = (115, 300)
    message = "House Price for {0}bhk, {1}sq.ft".format(bhk, sqft)
    color = 'rgb(255, 255, 255)'
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (115, 400)
    message = "in "
    color = 'rgb(255, 255, 255)'
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (165, 400)
    message = "{0}".format(area)
    color = 'rgb(255,165,0)'
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (115, 500)
    message = "is "
    color = 'rgb(255, 255, 255)'
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (165, 500)
    name = '~{0} Lakhs'.format(price)
    color = 'rgb(0, 255, 0)'  # white color
    draw.text((x, y), name, fill=color, font=font)

    image.save('static/images/predicted.png', optimize=True, quality=20)


def createImageVisual(class_, accuracy):
    image = Image.open('static/images/Bighead.png')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('static/fonts/Roboto.ttf', size=55)

    (x, y) = (115, 300)
    message = "The image was classified as".format(bhk, sqft)
    color = 'rgb(255, 255, 255)'
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (115, 400)
    message = "{0}".format(class_)
    color = 'rgb(255,165,0)'
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (115, 500)
    message = "with an accuracy of"
    color = 'rgb(255, 255, 255)'
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (115, 600)
    name = '{0}'.format(accuracy)
    color = 'rgb(0, 255, 0)'  # white color
    draw.text((x, y), name, fill=color, font=font)

    image.save('static/images/visualclass.png', optimize=True, quality=20)

def distance(lat1, lat2, lon1, lon2): 
    lon1 = radians(lon1) 
    lon2 = radians(lon2) 
    lat1 = radians(lat1) 
    lat2 = radians(lat2) 
    dlon = lon2 - lon1  
    dlat = lat2 - lat1 
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))  
    r = 6371
    return(c * r) 

def location(lat, longg):
    shortest = -1.0
    nearest_place = ""
    lat1 = float(lat)
    lon1 = float(longg)
    df_compare = pd.read_csv(app.config["DATASET"]+'areas_with_lat_long.csv')
    for ind in df_compare.index: 
        lat2 = df_compare['Latitude'][ind]
        lon2 = df_compare['Longitude'][ind]
        dist = distance(lat1, lat2, lon1, lon2)
        if shortest == -1.0:
            shortest = dist
            nearest_place = df_compare['location'][ind]
        elif shortest > dist:
            shortest = dist
            nearest_place = df_compare['location'][ind]
    return nearest_place
    
def checkServices(to_, from_, client):
    try:
        files = scanAvailableFiles(app.config["CREDENTIALS"])
        print(files)
        idx = 0
        inx = 1
        for i in files:
            if i == "wmlCredentials.json":
                x = scanAvailableFiles(app.config["SERVICES"])
                print(x)
                for j in x:
                    if j == "wmlDeployment.json":
                        with open(app.config["SERVICES"]+j) as temp:
                            cred = json.loads(temp.read())
                        files[idx] = "{0}. Watson Machine Learning -> *{1}*".format(
                            inx, cred["entity"]["status"]["state"])
                        inx += 1
                    else:
                        files[idx] = "{0}. Watson Machine Learning -> *No Model Deployed*".format(
                            inx)
                        inx += 1
            if i == "waCredentials.json":
                x = scanAvailableFiles(app.config["SERVICES"])
                print(x)
                for j in x:
                    if j == "waDeployment.json":
                        with open(app.config["SERVICES"]+j) as temp:
                            cred = json.loads(temp.read())
                        files[idx] = "{0}. Watson Assistant -> *{1}*".format(
                            inx, cred["entity"]["status"]["state"])
                        inx += 1
                    else:
                        files[idx] = "{0}. Watson Assistant -> *No Skills*".format(
                            inx)
                        inx += 1
            if i == "wnluCredentials.json":
                x = scanAvailableFiles(app.config["SERVICES"])
                print(x)
                for j in x:
                    if j == "wmlDeployment.json":
                        with open(app.config["SERVICES"]+j) as temp:
                            cred = json.loads(temp.read())
                        files[idx] = "{0}. Watson Natural Language Understanding -> *{1}*".format(
                            inx, cred["entity"]["status"]["state"])
                        inx += 1
                    else:
                        files[idx] = "{0}. Watson Natural Language Understanding -> *No Custom Model Deployed*".format(
                            inx)
                        inx += 1
            if i == "wvrCredentials.json":
                x = scanAvailableFiles(app.config["SERVICES"])
                print(x)
                for j in x:
                    if j == "wvrDeployment.json":
                        with open(app.config["SERVICES"]+j) as temp:
                            cred = json.loads(temp.read())
                        files[idx] = "{0}. Watson Visual Recognition -> *{1}*".format(
                            inx, cred["entity"]["status"]["state"])
                        inx += 1
                    else:
                        files[idx] = "{0}. Watson Visual Recognition -> *No Custom Model Deployed*".format(
                            inx)
                        inx += 1
            idx += 1
        services = "\n".join(files)

        msg = "I found the following services associated to me: \n\n" + \
            services + "\n\nEnter the number to know more."
        
        message = client.messages.create(
            from_=from_,
            body=msg,
            to=to_
        )
        global sentMsg
        sentMsg = "I am a bot who is connected to watson services on IBM Cloud! \nTry asking *What are the services you are connected to?*"
        return(message.sid)
    except Exception as e:
        files = "no service associated, please configure the application on IBM Cloud"
        print(e)
        message = client.messages.create(
            from_=from_,
            body=files,
            to=to_
        )
        return(message.sid)
                
def scanAvailableFiles(path):
    availableFiles = os.listdir(path)
    return availableFiles

@app.route('/getMessages')
def getMessages():
    global receivedMsg
    global sentMsg
    
    return jsonify({"sentMsg": sentMsg, "receivedMsg": receivedMsg})

''' Default Route '''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        global area
        global sqft
        global bhk
        
        getTwilioCredentials()
        
        ResponseMsg = json.dumps(request.form.to_dict(), indent=2)
        respo = json.loads(ResponseMsg)
        print(respo)
        global receivedMsg
        global sentMsg
        receivedMsg = respo.get('Body')
        
        if respo.get('Body') == 'What can you do?':
            client = Client(account_sid, auth_token)
            to_ = respo.get('From')
            from_ = respo.get('To')
            message = client.messages.create(
                from_=from_,
                body="I am a bot who is connected to watson services on IBM Cloud! \nTry asking *What are the services you are connected to?*",
                media_url="https://whatsapp-server-reliable-kangaroo.eu-gb.mybluemix.net/static/images/architecture.png",
                to=to_
            )
            sentMsg = "I am a bot who is connected to watson services on IBM Cloud! \nTry asking *What are the services you are connected to?*"
            return(message.sid)
        
        if respo.get('Body') == 'What are the services you are connected to?':
            
            to_ = respo.get('From')
            from_ = respo.get('To')
            client = Client(account_sid, auth_token)
            checkServices(to_, from_, client)
            
            return str("ok")
        
        if respo.get('Body') == '1':
            message = "Watson Machine Learning Details"
            resp = MessagingResponse()
            resp.message(message)
            sentMsg = message
            x = scanAvailableFiles(app.config["SERVICES"])
            for j in x:
                if j == "wmlDeployment.json":
                    with open(app.config["SERVICES"]+j) as temp:
                        cred = json.loads(temp.read())
                    model_id = cred["entity"]["asset"]["id"]
                    model_name = cred["entity"]["name"]
                    model_status = cred["entity"]["status"]["state"]
                    
                    if model_status == "ready":
                        message = "WML Model id: *{0}*".format(model_id) + \
                            "\nWML Model Name: *{0}*".format(model_name) + \
                            "\nWML Model Status: *{0}*".format(
                                model_status) + "\n\nTry asking *I want to know house prices*"
                    else:
                        message = "Model id: *{0}*".format(model_id) + \
                            "\nModel Name: *{0}*".format(model_name) + \
                            "\nModel Status: *{0}*".format(model_status)
                    resp.message(message)
                    sentMsg = message
                    return str(resp)
                else:
                    message = "Service configured, but no model deployed!\nType *Deploy* to deploy a test model"
                    resp.message(message)
                    sentMsg = message
                    return str(resp)
        
        if respo.get('Body') == '2':
            message = "Watson Visual Recognition"
            resp = MessagingResponse()
            resp.message(message)
            sentMsg = message
            
            message = "Send any food image from your Camera or Gallery to classify the food with Watson Visual Recognition"
            resp.message(message)
            sentMsg = message
            
            return str(resp)
        
        if respo.get('Body') == 'I want to know house prices':
            message = "What do you want to do?\nA.Check prices in different locality\nB.Check the prices in your current locality\n\nEnter either *A* or *B* to continue..."
            resp = MessagingResponse()
            resp.message(message)
            sentMsg = message
            return str(resp)
        
        if respo.get('Body') == 'A':
            message = "Please enter the details with the below format:\n\n*Predict:<Place-Name>,<Area-sq.ft>,<How-many-bhk>*\n\nExample: *Predict:Thanisandra,1300,2*"
            resp = MessagingResponse()
            resp.message(message)
            sentMsg = message
            return str(resp)
        
        if respo.get('Body') == 'B':
            message = "Share your current location\n\nTap *Attach* > *Location* > *Send your current location*"
            resp = MessagingResponse()
            resp.message(message)
            sentMsg = message
            return str(resp)
        
        if respo.get('Body')[:7] == 'Predict':
            
            temp = respo.get('Body').split(':')[1].split(',')
            length = len(temp)
            
            if(length == 3):
                print("Its in 3")
                area = respo.get('Body').split(':')[1].split(',')[0].strip()
                sqft = respo.get('Body').split(':')[1].split(',')[1].strip()
                bhk = respo.get('Body').split(':')[1].split(',')[2].strip()
            
            elif(length == 2):
                print("Its in 2")
                sqft = respo.get('Body').split(':')[1].split(',')[0].strip()
                bhk = respo.get('Body').split(':')[1].split(',')[1].strip()
            
            elif(length == 1):
                print("Its in 1")
                area = respo.get('Body').split(':')[1].split(',')[0].strip()
                sqft = 1200
                bhk = 2
                
            price = predict_price_wml(area,sqft,bhk,bhk)
            
            with open(app.config["CREDENTIALS"]+'wmlCredentials.json') as wmlCreds:
                wmlcred = json.loads(wmlCreds.read())
            
            messageTxt = "Area: *{0}, Bengaluru*\n\n{1} Bhk with {2} Sq.Ft will cost you approx: {3} Lakhs".format(area, bhk, sqft, price)
            createImagePrediction(area, bhk, sqft, price)
            client = Client(account_sid, auth_token)
            to_ = respo.get('From')
            from_ = respo.get('To')
            message = client.messages.create(
                from_=from_,
                body=messageTxt,
                media_url=wmlcred.get('windowURL')+"static/images/predicted.png",
                to=to_
            )
            sentMsg = messageTxt
            return(message.sid)
        
        if respo.get('MediaUrl0') != None:
            imageURL = respo.get('MediaUrl0')
            
            with open(app.config["CREDENTIALS"]+'wvrCredentials.json') as wmlCreds:
                wvrcred = json.loads(wmlCreds.read())
            
            payload = {
                "apikey": wvrcred.get('apikey'),
                "url": wvrcred.get('url'),
                "imageURL": imageURL
                }

            r = requests.post(wvrcred.get('cloudfunctionurl'), data=payload)
            response = r.json()
            
            messageTxt = "Classified as *{0}*\nwith an accuracy of *{1}*".format(response.get('class'), response.get('score'))
            
            createImageVisual(response.get('class'), response.get('score'))
            client = Client(account_sid, auth_token)
            to_ = respo.get('From')
            from_ = respo.get('To')
            message = client.messages.create(
                from_=from_,
                body=messageTxt,
                media_url=wvrcred.get('windowURL')+"static/images/visualclass.png",
                to=to_
            )
            sentMsg = messageTxt
            return(message.sid)
        
        if respo.get('Latitude') != None and respo.get('Longitude') != None:
            Latitude = respo.get('Latitude')
            Longitude = respo.get('Longitude')
        
            msg = "Lat: {0} \nLong: {1}".format(Latitude, Longitude)
            resp = MessagingResponse()
            resp.message(msg)
            sentMsg = msg
            
            area = location(Latitude, Longitude)
            
            message = "For Area: *{0}, Bengaluru*\n\nPlease enter the details with the below format:\n\n*Predict:<Area-sq.ft>,<How-many-bhk>*\n\nExample: *Predict:1300,2*".format(area)
            resp = MessagingResponse()
            resp.message(message)
            sentMsg = message
            return str(resp)
            
        msg = "The message,\n'_{0}_'\nthat you typed on your phone, went through\nWhatsapp -> Twilio -> Python App hosted on IBM Cloud and returned back to you from\nPython App hosted on IBM Cloud -> Twilio -> Whatsapp.\n\n*How Cool is that!!*\n\n Try asking *What can you do?*".format(respo.get('Body'))
        resp = MessagingResponse()
        resp.message(msg)
        sentMsg = msg
        return str(resp)

    return render_template('index.html')

''' Start the Server '''

port = os.getenv('VCAP_APP_PORT', '8080')
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True, host='0.0.0.0', port=port)


