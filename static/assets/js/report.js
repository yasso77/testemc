var socket= new WebSocket('ws://localhost:8000/ws/manager/');

socket.onmessage=function(e){

    var dajangoData=JSON.parse(e.data);
    console.log(dajangoData);

    document.querySelector('#app').innerText=dajangoData.value;
}