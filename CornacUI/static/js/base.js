$(document).ready(function(){

    document.getElementById("get_result").addEventListener("click", function(e){
        $(".overlay").css('height', '100%');
        var form_data = new FormData($("#user_form")[0]);
        var file_size = form_data.get("dataset").size/1024/1024;
        file_size = file_size.toFixed(1);
        if (file_size > 20) {
            alert("File size is wayyyyy too big! " + file_size + "MB uploaded (20MB max)");
            $(".overlay").css('height', '0%');
            window.location.href = "/train/pmf";
        }
        form_data.append("model", display);
        var Req = new XMLHttpRequest(); 
        Req.open("POST", "/train/" + display, true);
        Req.onload = function(){
            if (Req.status == 200) {
                if(JSON.parse(Req.response).errors) {
                    $(".overlay").css('height', '0%');
                    var flask_errors = JSON.parse(Req.response).errors;
                    $("#warnings").css("display", "block");
                    var ul = document.getElementById("flask_errors");
                    while (ul.firstChild) {
                        ul.removeChild(ul.firstChild);
                    };

                    for (error of flask_errors) {
                        var li = document.createElement("li");
                        li.appendChild(document.createTextNode(error));
                        ul.appendChild(li);
                    };
                    alert("Please check your form is filled correctly")
                }
                else {
                    alert("Task has been submitted to our server...");
                    window.location.href = "/results";
                }
            }
            else {
                window.location.href = "/train/pmf";
                alert("Error " + Req.status + " has occured. Please try again!");
                
            }
        };
        Req.send(form_data);
        e.preventDefault(); // stops the usual submit function
    }, false);

});