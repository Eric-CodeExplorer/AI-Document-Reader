function hide_input_bar(){
    const input_bar = document.getElementById("input-bar");
    input_bar.classList.add("hide")
}

function unhide_input_bar(){
    const input_bar = document.getElementById("input-bar");
    input_bar.classList.remove("hide")
}

function appendMsg(role,message){
    let source, name;
    const chatBox = document.querySelector('.chat-box');
    if (role === "user"){
        source = "/static/svg/user_icon.svg";
        name = "You";
    }else{
        source = "/static/svg/ai_icon.svg";
        name = "AI Document Reader";
    }
    
    if (chatBox){
        const msgContainer = `
        <div class="msg-container">
            <div class="msg-container-left">
                <img class="icon" src="${source}" alt="icon">
            </div>
            <div class="msg-container-right">
                <h5>${name}</h5>
                <pre>${message}</pre>
            </div>
        </div>
        `;

        chatBox.innerHTML += msgContainer;
    }
}

function appendAllMsg(msgs){
    // console.log("appendAllMsg entered");
    // console.log(msgs);
    const data = msgs.data;
    // console.log(data)
    for (var i = 0; i < data.length; i++){
        var role = data[i].role;
        var valueText = data[i].content[0].text.value;
        appendMsg(role,valueText);
    }
}

function modifyLastMsgContainer(role,message){
    let source, name;
    const lastContainer = document.querySelector('.msg-container:last-child');
    if (role === "user"){
        source = "/static/svg/user_icon.svg";
        name = "You";
    }else{
        source = "/static/svg/ai_icon.svg";
        name = "AI Document Reader";
    }
    lastContainer.innerHTML = `
    
        <div class="msg-container-left">
            <img class="icon" src="${source}" alt="icon">
        </div>
        <div class="msg-container-right">
            <h5>${name}</h5>
            <pre>${message}</pre>
        </div>
    
    `;
}


function getCidByURL(){
    const currentPath = decodeURI(window.location.pathname);
    const pathParts = currentPath.split('/');
    const cid = pathParts[pathParts.length - 1];
    return cid;
}


document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.querySelector('.chat-box');
    const inputForm = document.querySelector('.input-bar');

    inputForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(inputForm);
        const inputData = formData.get("input-msg");
        const cid = getCidByURL();
        const urlString = "/conversation/" + cid;
        inputForm.reset();
        appendMsg("user",inputData);
        appendMsg("assistant","Processing...");
        hide_input_bar();
        const response = await fetch(urlString, {
            method: "POST",
            body: JSON.stringify({ "message": inputData, "cid":cid}),
            headers: {
                "Content-Type": "application/json"
            }
        });
        const result = await response.json();
        modifyLastMsgContainer(result.data[0].role,result.data[0].content[0].text.value);
        unhide_input_bar();
    });
});
