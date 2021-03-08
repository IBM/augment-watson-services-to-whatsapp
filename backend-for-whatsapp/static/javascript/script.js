const setupButton = document.getElementById('setupButton');
const deployModelButton = document.getElementById('deployModelButton');
const nextBtn = document.getElementById('next-btn');
const viewAction = document.getElementById('viewAction');
const addwatsoncreds = document.getElementById('addwatsoncreds');

const twilioStatus = document.getElementById('twilioStatus');
const modal_credentials = document.getElementById('modal-credentials-heading');
const wStatus = document.getElementById('wStatus');
const wmlDeploymentStatus = document.getElementById('wmlDeploymentStatus');
const wmlDeploymentStatus2 = document.getElementById('wmlDeploymentStatus2');
const wmlDeploymentStatus3 = document.getElementById('wmlDeploymentStatus3');

const modelexists = document.getElementById('modelexists');
const modelexists2 = document.getElementById('modelexists2');

const twilioCredSubmit = document.getElementById('twilio-cred-submit');
const wmlCredSubmit = document.getElementById('wml-cred-submit');
const CredSubmit = document.getElementById('cred-submit');

const deployModeltoWML = document.getElementById('deployModeltoWML');

const receivedMsg = document.getElementById('receivedMsg');
const sentMsg = document.getElementById('sentMsg');

const debuggerr = document.getElementById('debugger');

var flag = false;

$(document).ready(() => {
    getTwilioCredentials();
    getWatsonCredentials();
    getDeploymentState();
    document.getElementById("deployModelTab").className = "bx--tabs__nav-item";
});

const changeMode = () => {
    if (twilioStatus.innerHTML == "Configured" && wStatus.innerHTML == "Configured") {
        document.getElementById("deployModelTab").className = "bx--tabs__nav-item";
        nextBtn.style.display = "block";
    }
};

addwatsoncreds.onclick = () => {
    if (document.getElementById('radio-wml').checked) {
        $('#addwatsoncreds').attr('data-modal-target', '#modal-credentials-wml');
        modal_credentials.innerHTML = "Watson Machine Learning Credentials";
    } else if (document.getElementById('radio-wa').checked) {
        $('#addwatsoncreds').attr('data-modal-target', '#modal-credentials');
        modal_credentials.innerHTML = "Watson Assistant Credentials";
    } else if (document.getElementById('radio-wnlu').checked) {
        $('#addwatsoncreds').attr('data-modal-target', '#modal-credentials');
        modal_credentials.innerHTML = "Watson Natural Language Understanding Credentials";
    } else if (document.getElementById('radio-wvr').checked) {
        $('#addwatsoncreds').attr('data-modal-target', '#modal-credentials');
        modal_credentials.innerHTML = "Watson Visual Recognition Credentials";
    }
};

viewAction.onclick = () => {
    flag = ~flag;
    getMessages(flag);
};

const getTwilioCredentials = async () => {
    await fetch('/getTwilioCredentials').then(async(response) => {
        data = await response.json();
        twilioStatus.innerHTML = data.status;
    });
};

const getWatsonCredentials = async () => {
    await fetch('/getWatsonCredentials').then(async(response) => {
        data = await response.json();
        wStatus.innerHTML = "";
        data.services.forEach(element => {
            if (element == 'wmlCredentials.json')
                wStatus.innerHTML += "<li>" + "<code>Watson Machine Learning</code>" + "</li><br>";
            else if (element == 'waCredentials.json')
                wStatus.innerHTML += "<li>" + "<code>Watson Assistant</code>" + "</li><br>";
            else if (element == 'wnluCredentials.json')
                wStatus.innerHTML += "<li>" + "<code>Watson Natural Language Understanding</code>" + "</li><br>";
            else if (element == 'wvrCredentials.json')
                wStatus.innerHTML += "<li>" + "<code>Watson Visual Recognition</code>" + "</li><br>";
            else
                console.log(element);
        });

        changeMode();
    });
};

const getDeploymentState = async () => {
    await fetch('/getDeploymentState').then(async(response) => {
        data = await response.json();
        console.log(data);
        if (data.status == 'ready') {
            debuggerr.click();
            modelexists.style.display = "block";
            modelexists2.style.display = "block";
            wmlDeploymentStatus.innerHTML = data.status;
            wmlDeploymentStatus2.innerHTML = data.modelId;
            wmlDeploymentStatus3.innerHTML = data.modelName;
        } else {
            wmlDeploymentStatus.innerHTML = data.status;
        }
    });
};

const getMessages = async (flag) => {
    if (flag) {
        setTimeout(async function() {
            await fetch('/getMessages').then(async(response) => {
                data = await response.json();
                receivedMsg.innerHTML = data.receivedMsg;
                sentMsg.innerHTML = data.sentMsg;
                getMessages(flag);
            });
        }, 5000);
    }
};

var saveData = (function() {
    var a = document.createElement("a");
    document.body.appendChild(a);
    a.style = "display: none";
    return function(data, fileName) {
        var json = JSON.stringify(data),
            blob = new Blob([json], { type: "octet/stream" }),
            url = window.URL.createObjectURL(blob);
        a.href = url;
        a.download = fileName;
        a.click();
        window.URL.revokeObjectURL(url);
    };
}());

twilioCredSubmit.onclick = () => {
    SaveCredentials("twilio");
};

CredSubmit.onclick = () => {
    console.log("-> CredSubmit Function");
    var wtype = "";
    if (document.getElementById('radio-wa').checked) {
        wtype = "wa";
    } else if (document.getElementById('radio-wnlu').checked) {
        wtype = "wnlu";
    } else if (document.getElementById('radio-wvr').checked) {
        wtype = "wvr";
    }
    SaveCredentials(wtype);
};

wmlCredSubmit.onclick = () => {
    console.log("-> wmlCredSubmit Function");
    var wtype = "wml";
    SaveCredentials(wtype);
};

const SaveCredentials = async (type) => {

    if (type == "twilio") {
        var url = '/storeTwilioCredentials';
        var payload = {
            account_sid: document.getElementById('account_sid').value,
            auth_token: document.getElementById('auth_token').value
        }
    } else {
        var url = '/storeWatsonCredentials';

        if (type == "wml") {
            var payload = {
                apikey: document.getElementById('wml_apikey').value,
                url: document.getElementById('wml_url').value,
                space_id: document.getElementById('wml_space_id').value,
                type: type,
                windowURL: location.href
            }
            console.log(payload);
        } else {
            var payload = {
                apikey: document.getElementById('apikey').value,
                cloudfunctionurl: document.getElementById('cloudfunctionurl').value,
                type: type,
                windowURL: location.href
            }
            console.log(payload);
        }
    }

    let formData = new FormData();
    formData.append(`Credentials`, JSON.stringify(payload));

    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
        success: function(response) {
            if (type == "twilio")
                twilioStatus.innerHTML = response.status;
            else {
                if (response.status == "Configured") {
                    getWatsonCredentials();
                    changeMode();
                }
            }
        }
    });
};

deployModeltoWML.onclick = () => {
    wmlDeploymentStatus.innerHTML = "deploying model please wait ...";
    deployWML();
};

const deployWML = async () => {
    await fetch('/deployWMLModel').then(async(response) => {
        data = await response.json();
        wmlDeploymentStatus.innerHTML = data.status;
        debuggerr.click();
    });
}