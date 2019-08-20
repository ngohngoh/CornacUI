$(document).ready(function(){

    // let current_run;

    document.getElementById("get_result").addEventListener("click", function(e){
        $(".overlay").css('height', '100%');
        console.log("display:", display);
        var form_data = new FormData($("#user_form")[0]);
        form_data.append("model", display);
        console.log("form data:", form_data);
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
                    $(".overlay").css('height', '0%');
                    $("#warnings").css("display", "none");
                    $("#user_check").show();
                    var user_check = document.getElementById("user_check");
                    var output = JSON.parse(Req.response).output;
                    var result_table = document.getElementById("result_table");

                    while (result_table.firstChild) {
                        result_table.removeChild(result_table.firstChild);
                    };

                    for (data of output[0]) {
                        var new_header = document.createElement("th");
                        new_header.innerHTML = data;
                        result_table.appendChild(new_header);
                    };

                    for (i=1; i < output.length; i++) {
                        var new_row = result_table.insertRow(-1);
                        for (data of output[i]) {
                            var cell = new_row.insertCell(-1);
                            cell.innerHTML = data
                        };
                    };            
                    // current_run = JSON.parse(Req.response).current_run;
                    alert("Model ran successfully!");
                    user_check.scrollIntoView();
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
    
    
    // document.getElementById("user_check_btn").addEventListener("click", function(e){
    //     var reco_data = new FormData($("#reco_form")[0]);
    //     reco_data.append("current_run", current_run);
    //     console.log("reco_data: ", reco_data);
    //     var Req = new XMLHttpRequest();
    //     Req.open("POST", "/recommendations", true);
    //     Req.onload = function(){
    //         if (Req.status == 200) {
    //             console.log("returned reco_data: ", JSON.parse(Req.responseText));
    //             $("#user_check").show();
    //             document.getElementById("ranking").innerHTML = JSON.parse(Req.response).ranking;
    //             document.getElementById("scores").innerHTML = JSON.parse(Req.response).scores;
    //             alert("User checked!");
    //         }
    //         else {
    //             alert("Error " + Req.status + " has occured");
    //         }
    //     };
    //     Req.send(reco_data);
    //     e.preventDefault(); // stops the usual submit function
    // }, false);

});