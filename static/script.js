function populateOptions(element, options) {
    const elementdiv = document.getElementById(element + 'div');
    var selects = document.getElementById(element + 'options');
    selects.innerHTML = "";
    selects.add(document.createElement("option"));
    options.forEach(option => {
        newOption = document.createElement("option");
        newOption.text = option.text;
        newOption.value = option.value;
        selects.add(newOption);
    });
    elementdiv.hidden = false;
}

async function fetchjson(url, data) {
    const response = await fetch(url,
        {
            headers: { "Content-Type": "application/json" },
            method: "POST",
            body: JSON.stringify(data)
        }
    );
    return await response.json();
}

async function getSchools(form) {
    formdata = new FormData(form);
    var cdomain = document.getElementById('cdomain');
    cdomain.value = formdata.get("domain");
    const data = { domain: formdata.get("domain") };
    jsonresponse = await fetchjson("/getSchools/", data);
    populateOptions("school", jsonresponse.map(x => ({ text: x["unitId"], value: x["unitGuid"] })))
};

async function getClasses(form) {
    formdata = new FormData(form);
    const data = { domain: formdata.get("cdomain"), unitguid: formdata.get("schooloptions") };
    var udomain = document.getElementById('udomain');
    var uclass = document.getElementById('uschool');
    udomain.value = formdata.get("cdomain");
    uclass.value = formdata.get("schooloptions");
    const jsonresponse = await fetchjson("/getClasses/", data);
    populateOptions("classes", jsonresponse.map(x => ({ text: x["groupName"], value: x["groupGuid"] })))
};

function buildUrl(form) {
    formdata = new FormData(form);
    const data = { domain: formdata.get("udomain"), unitguid: formdata.get("uschool"), groupguid: formdata.get("classesoptions") };
    const url = new URL("/ical/"+data.domain+"/"+data.unitguid+"/"+data.groupguid, window.location.origin);
    createdurl = document.getElementById("createdurl");
    createdurl.innerHTML = url.href;
    urldiv = document.getElementById("urldiv");
    urldiv.hidden = false;
}
