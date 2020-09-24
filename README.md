### !Documentation in progress
# Augment IBM Watson Services to WhatsApp

In this code pattern, we will [create something] using [technologies] and [components]. [Explain briefly how things work]. [Give acknowledgements to others if necessary]

When you have completed this code pattern, you will understand how to:

* [goal 1]
* [goal 2]
* [goal 3]
* [goal 4]

<!--add an image in this path-->
![architecture](doc/source/images/architecture.png)

<!--Optionally, add flow steps based on the architecture diagram-->
## Flow

1. Step 1.
2. Step 2.
3. Step 3.
4. Step 4.
5. Step 5.

<!--Optionally, update this section when the video is created-->
# Watch the Video

[![video](http://img.youtube.com/vi/Jxi7U7VOMYg/0.jpg)](https://www.youtube.com/watch?v=Jxi7U7VOMYg)

# Steps

Use the **Deploy to IBM Cloud** button **OR** create the services and run locally.

1. [Clone the repo](#1-clone-the-repo).
2. [Create Watson services](#2-create-watson-services).
3. [Deploy the Server Application on IBM Cloud Foundry](#3-deploy-the-server-application-on-ibm-cloud-foundry).
4. [Create Twilio service](#4-create-twilio-service).
5. [Configure credentials](#5-configure-credentials).
6. [Deploy the House Price Prediction model](#6-deploy-the-house-price-prediction-model).


### 1. Clone the repo

Clone the `augment-watson-services-to-whatsapp` repo locally. In a terminal, run:

```bash
git clone https://github.com/IBM/augment-watson-services-to-whatsapp
```

We’ll be using the file [`data/assistant/workspaces/banking.json`](data/assistant/workspaces/banking.json) and the folder
[`data/assistant/workspaces/`](data/assistant/workspaces/)

### 2. Create Watson services

Create the following services:

#### 2.1. Watson Machine Learning

- Login to IBM Cloud, and create a [**Watson Machine Learning**](https://cloud.ibm.com/catalog/services/machine-learning) service, make a note of the **region** that you select and click on **create** as shown.

![wml](doc/source/images/watsonML.png)

- Once the service is created, click on the **Manage** tab and select **Access (IAM)**, the cloud Identity and Access Management page will be displayed.

![manage-iam](doc/source/images/accessiam.png)

- Click on **API keys** on the left panel as shown.

![iam](doc/source/images/iam.png)

- In **API keys**, click on **Create an IBM Cloud API key** and give a Name and Description Accordingly as shown.

![create-api-key](doc/source/images/createApiKey.png)

- Once the API key is generated Successfully, copy the key as it will be used in [Step 5](#5-configure-credentials). 

>NOTE: The API key will not be visible once the dialog box is dismissed, you can **Download** the API key to keep it handy just in case you loose the copied key.

![api-key-created](doc/source/images/apiKeyCreated.png)

#### 2.2. Watson Studio

- Back to IBM Cloud, create a [**Watson Studio**](https://cloud.ibm.com/catalog/services/watson-studio) service, make sure the **region** that you select is same as the Watson Machine Learning service's region, and finally click on **create** as shown.

![watson-studio](doc/source/images/watsonStudioService.png) 

- Once the service is created, click on **Get Started** to provision an IBM Cloud Pak for Data instance.

![watson-studio-get-started](doc/source/images/watsonStudioGetStarted.png) 

- In Watson Studio / IBM Cloud Pak for Data, click on the hamburger menu on the top left corner and select **Deployment spaces > View all spaces**.

![](doc/source/images/select-deployment-spaces.gif)

- In deployment spaces, click on **New deployment space +**.

- Select **Create an empty space** when prompted.

- Make sure you select the appropriate **Cloud object storage service** as well as **Machine learning service**.

![](doc/source/images/deployment-space.png)

>NOTE: In v4 Machine learning assets are stored in Cloud Object Storage rather than in the Watson Machine Learning repository.

- Once the deployment space is created, click on **View Space** to view the details.

- Click on **Settings** and copy the `space ID` as it is required in [Step 5](#5-configure-credentials).

![](doc/source/images/copy-space-id.gif)

> Learn more about deployment space [here](https://eu-gb.dataplatform.cloud.ibm.com/docs/content/wsj/wmls/wmls-deploy-overview.html).

- At this point, you should have the `API key` and the `Space ID` copied in any notepad as these will be used in [Step 5](#5-configure-credentials).

### 3. Deploy the Server Application on IBM Cloud Foundry

- Before you proceed, make sure you have installed [IBM Cloud CLI](https://cloud.ibm.com/docs/cli?topic=cloud-cli-getting-started&locale=en-US) in your deployment machine.

- From the cloned repo, goto **backend-for-whatsapp** directory in terminal, and run the following commands to deploy the Application to IBM Cloud Foundry.

* Log in to your IBM Cloud account, and select an API endpoint.
```bash
$ ibmcloud login
```

>NOTE: If you have a federated user ID, instead use the following command to log in with your single sign-on ID.
```bash
$ ibmcloud login --sso
```

* Target a Cloud Foundry org and space:
```bash
$ ibmcloud target --cf
```

* From within the _backend-for-whatsapp directory_ push your app to IBM Cloud.
```bash
$ ibmcloud cf push whatsapp-server
```

- The [manifest.yml](backend-for-whatsapp/manifest.yml) file will be used here to deploy the application to IBM Cloud Foundry.

- On Successful deployment of the application you will see something similar on your terminal as shown.

<pre><code>Invoking 'cf push'...

Pushing from manifest to org manoj.jahgirdar@in.ibm.com / space dev as manoj.jahgirdar@in.ibm.com...

...

Waiting for app to start...

name:              whatsapp-server
requested state:   started
routes:            <b>whatsapp-server.xx-xx.mybluemix.net </b>
last uploaded:     Sat 16 May 18:05:16 IST 2020
stack:             cflinuxfs3
buildpacks:        python

type:            web
instances:       1/1
memory usage:    256M
start command:   python app.py
     state     since                  cpu     memory           disk           details
#0   <b>running</b>   2020-05-16T12:36:15Z   25.6%   116.5M of 256M   796.2M of 1
</code></pre>

* Once the app is deployed you can visit the `routes` to launch the application.

>Example: http://whatsapp-server.xx-xx.mybluemix.net

- At this point, along with `API key` and the `Space ID` you should also have the deployed app `URL`.

### 4. Create Twilio service

- Create a free Twilio service here: <https://www.twilio.com/try-twilio>.

- Enter the your details to signup as shown.

![twilio-signup](doc/source/images/createTwilio.png)

- Once you create a twilio service, you will have to verify your email id as well as your phone number.

- To verify your email id, visit your registered email id and you will see a mail from twilio with a verification link, go ahead and verify.

![](doc/source/images/verifyTwilio.png)

- Once email id is verified you will be prompted to enter your phone number, submit that and you will get an OTP on your registered number, enter that back to verify.

![](doc/source/images/verifyMobileTwilio.png)

- On Successful verification you should see a welcome greeting message, additionally you will see a question **Do you write code?**, select **Yes** to proceed.

![](doc/source/images/twilioWelcome.png)

- The second question asked to you would be **What is your preferred language?**, select **Python** to proceed.

![](doc/source/images/twilioWelcome2.png)

- Third question asked to you would be **What is your goal today?**, select **Use Twilio in a project** to proceed.

![](doc/source/images/twilioWelcome3.png)

- The final question asked to you would be **What do you want to do first?**, select **Send WhatsApp messages** to proceed.

![](doc/source/images/twilioWelcome4.png)

- You will then see a popup box requesting you to **Activate Your Sandbox**, click on **I agree** checkbox and click **Confirm**.

![](doc/source/images/allowSandbox.png)

- The sandbox for WhatsApp will appear, make a note of the `Sandbox Name` which will be prefixed with **join**, click on **Settings** on the left panel and select **WhatsApp Sandbox Settings**.

![](doc/source/images/twilioSettings.png) 

- In **WhatsApp Sandbox Settings** page, under **Sandbox Configuration**, there will be a field called **WHEN A MESSAGE COMES IN**, replace the existing URL in that field with the `URL` obtained by deploying the backend application from [Step 3](#3-deploy-the-server-application-on-ibm-cloud-foundry), finally click on **Save** to save the configuration.

![](doc/source/images/whatsappSandbox.png)

>NOTE: Sometimes the changes are not saved in Twilio WhatsApp Sandbox Settings even after clicking on save, reload the page to enusre the `URL` that you have entered in **WHEN A MESSAGE COMES IN** field is reflecting over there. If you still see the old URL over there then enter the `URL` from [Step 3](#3-deploy-the-server-application-on-ibm-cloud-foundry) again and save it.

- Now the Backend server is configured in Twilio, any message that you send from WhatsApp from this point will go to the backend server via Twilio WhatsApp Sandbox. However to reply back to you from WhatsApp the backend server needs to establish connection with Twilio.

- To establish connection between the backend server and Twilio we need to get the `account_sid` and `auth_token` from Twilio. 

- Visit <https://www.twilio.com/console> and expand the **Project Info** tab. You will see the `ACCOUNT ID` and `AUTH TOKEN`, copy it in some notepad as it will be used in [Step 5](#5-configure-credentials).
 
![](doc/source/images/twilio-credentials-from-twilio-console.png)

- At this point, you should have the `Sandbox Name`, `account_sid` and `auth_token` from Twilio service.

### 5. Configure credentials

- Visit the `URL` which was obtained by deploying the backend application in [Step 3](#3-deploy-the-server-application-on-ibm-cloud-foundry).

>Example: http://whatsapp-server.xx-xx.mybluemix.net

- You will now have access to the backend through which you can configure **Twilio** and **Watson services**.

![backend-app](doc/source/images/backendApp.png)

- You will have to configure the backend with Twilio credentials generated in [Step 4](#4-create-twilio-service) and Watson Machine Learning credentials generated in [Step 2](#2-create-watson-services).

- Under **Add Twilio service to the Application**, click on the **Add Twilio Credentials** button and insert the twilio `account_sid` and `auth_token` which were generated from [Step 4](#4-create-twilio-service) and finally click on **Submit**. You will now see the status as `Configured`.

![twilio-credentials-in-backend-app](doc/source/images/addingTwilioCredentials.gif)

- Similarly, under **Add Watson services to the Application**, select the **Watson Machine Learning** radio button and click on **Add Watson Credentials** button, here add the `apikey`, `region` and `space_id` which were generated from [Step 2](#2-create-watson-services) and finally click on **Submit**. You will now see `Watson Machine Learning` under **Configured Services**.

![wml-credentials-in-backend-app](doc/source/images/addingWmlCredentials.gif)

- At this point, you have successfully configured the backend for WhatsApp to communicate with Watson services through Twilio messaging service as Inter-mediator.

### 6. Deploy the House Price Prediction model

- Now that the Twilio service and Backend server both are configured, you can deploy the sample model from the backend application.

- The sample model is a House Price Prediction model built to predict house prices in the city Bengaluru, Karnataka, India. 

>NOTE: The main aim of this code pattern is to demonstrate how IBM Watson Services can be plugged into WhatsApp and not about how to build Machine Learning models for which we already have other code pattens, hence we are limiting the scope to a basic model. With some minor code changes you can use any Machine Learning models.

- In the Application, click on the **Deploy Model** tab, and you will see the details of the model.

>NOTE: The dataset for the sample house price prediction model is taken from Kaggle, credits to [Bengaluru House price data](https://www.kaggle.com/amitabhajoy/bengaluru-house-price-data) from Kaggle.

![](doc/source/images/deployWml.png)

- Click on **Deploy the Model on WML** button and wait for the &**Status** to change.

- Once the model is deployed you will see a **Status** as `Deployed, Model ID: xxx-xxx-xxx`.

- At this point, all the setup is completed and now its time to explore what you just built!

# Sample output

- Once the model is deployed and ready to use, the **View Application in Action** panel will be visible in the Application.

![](doc/source/images/whatsappQR.png)

- Scan the QR code in your Phone to open the WhatsApp chat with Twilio.

- A WhatsApp chat will open up in your phone with a typed code `join <sandbox name>`.

- Replace the `<sandbox name>` with your `Sandbox Name` obtained from [Step 4](#4-create-twilio-service) and send the message.

>NOTE: If you are unable to scan the QR code, save the phone number **+14155238886**, open WhatsApp and send a message to the saved number with code `join <sandbox name>`.

The workflow of the app is as follows:

NOTE: The user has to follow the exact same workflow for the WhatsApp to reply as intended.

Flow 1: Where user gives the Locality manually.

User|Reply|Screenshot
---|---|---
<pre><code>Hi</code></pre> | <pre><code>The message, 'Hi' that you typed on your phone, went through Whatsapp -> Twilio -> Python App hosted on IBM Cloud and returned back to you from Python App hosted on IBM Cloud -> Twilio -> Whatsapp. How Cool is that!! Try asking <b>What can you do?</b> </code></pre> | ![](doc/source/images/whatsappss/2.png)
<pre><code>What can you do?</code></pre> | <pre><code>I am a bot who is connected to watson services on IBM Cloud! Try asking <b>What are the services you are connected to?</b></code></pre> | ![](doc/source/images/whatsappss/3.png)
<pre><code>What are the services you are connected to?</code></pre> | <pre><code>I found the following services associated to me: 1. Watson Machine Learning -> *ready* Enter the number to know more.</code></pre> | ![](doc/source/images/whatsappss/4.png)
<pre><code>1</code></pre> | <pre><code>WML Model id: *xxxx-xxxx-xxxx* WML Model Name: *Deployment of Bangalore House Price Prediction* WML Model Status: *ready* Try asking <b>I want to know house prices</b></code></pre> | ![](doc/source/images/whatsappss/5.png)
<pre><code>I want to know house prices</code></pre> | <pre><code>What do you want to do? A.Check prices in different locality B.Check the prices in your current locality Enter either *A* or *B* to continue...</b></code></pre> | ![](doc/source/images/whatsappss/6.png)
<pre><code>A</code></pre> | <pre><code>Please enter the details with the below format: Predict:`<Place-Name>`,`<Area-sq.ft>`,`<How-many-bhk>` Example: Predict:Thanisandra,1300,2</code></pre> | ![](doc/source/images/whatsappss/7.png)
<pre><code>Predict: Whitefield, 1400, 3</code></pre> | <pre><code>Area: Whitefield, Bengaluru 3 Bhk with 1400 Sq.Ft will cost you approx: <b>89 Lakhs</b></code></pre> | ![](doc/source/images/whatsappss/7.png)

Alternate Flow 2: Where user sends location data and the algorithm will compute nearest locality.

User|Reply|Screenshot
---|---|---
<pre><code>Hi</code></pre> | <pre><code>The message, 'Hi' that you typed on your phone, went through Whatsapp -> Twilio -> Python App hosted on IBM Cloud and returned back to you from Python App hosted on IBM Cloud -> Twilio -> Whatsapp. How Cool is that!! Try asking <b>What can you do?</b> </code></pre> | ![](doc/source/images/whatsappss/2.png)
<pre><code>What can you do?</code></pre> | <pre><code>I am a bot who is connected to watson services on IBM Cloud! Try asking <b>What are the services you are connected to?</b></code></pre> | ![](doc/source/images/whatsappss/3.png)
<pre><code>What are the services you are connected to?</code></pre> | <pre><code>I found the following services associated to me: 1. Watson Machine Learning -> *ready* Enter the number to know more.</code></pre> | ![](doc/source/images/whatsappss/4.png)
<pre><code>1</code></pre> | <pre><code>WML Model id: *xxxx-xxxx-xxxx* WML Model Name: *Deployment of Bangalore House Price Prediction* WML Model Status: *ready* Try asking <b>I want to know house prices</b></code></pre> | ![](doc/source/images/whatsappss/5.png)
<pre><code>I want to know house prices</code></pre> | <pre><code>What do you want to do? A.Check prices in different locality B.Check the prices in your current locality Enter either *A* or *B* to continue...</b></code></pre> | ![](doc/source/images/whatsappss/6.png)
<pre><code>B</code></pre> | <pre><code>Share your current location Tap Attach > Location > Send your current location</code></pre> | ![](doc/source/images/whatsappss/8.png)
<pre><code>*GPS LOCATION*</code></pre> | <pre><code>For Area: XXX, Bengaluru Please enter the details with the below format: Predict:`<Area-sq.ft>`,`<How-many-bhk>` Example: Predict:1300,2</code></pre> | ![](doc/source/images/whatsappss/9.png)
<pre><code>Predict: 1200, 2</code></pre> | <pre><code>Area: XXX, Bengaluru 2 Bhk with 1200 Sq.Ft will cost you approx: <b>67 Lakhs</b></code></pre> | ![](doc/source/images/whatsappss/10.png)

At the end of the code pattern you will have learnt how to Augment IBM Watson services to WhatsApp via Twilio service.

## License

This code pattern is licensed under the Apache License, Version 2. Separate third-party code objects invoked within this code pattern are licensed by their respective providers pursuant to their own separate licenses. Contributions are subject to the [Developer Certificate of Origin, Version 1.1](https://developercertificate.org/) and the [Apache License, Version 2](https://www.apache.org/licenses/LICENSE-2.0.txt).

[Apache License FAQ](https://www.apache.org/foundation/license-faq.html#WhatDoesItMEAN)
