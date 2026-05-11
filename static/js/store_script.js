//const QrScanner = require('qr-scanner');

document.addEventListener('DOMContentLoaded', function(){ // Аналог $(document).ready(function(){
  	var elm = document.getElementsByClassName("field-qrcode")

    
    	for (var i = 0; i < elm.length; i++) {
        	const newDiv = document.createElement("div");
			newDiv.id = "qrcode" + i;
        	elm[i].after(newDiv)
    
    		const text = elm[i].textContent.replaceAll(' ', '')
        	const text_split = text.split(":")
            console.log(text_split)
        
        	if(text_split.length == 1) {
            	new QRCode("qrcode"+i, {
   	 				text: "https://cms.labauto.kz/store/qr/"+text_split[0],
    				width: 200,
                    height: 200,
    				colorDark : "#000000",
    				colorLight : "#ffffff",
    				correctLevel : QRCode.CorrectLevel.L
				})
            } else {
            	new QRCode("qrcode"+i, {
   	 			text: "https://cms.labauto.kz/store/qr/"+text_split[1].replaceAll('\n', ''),
    			width: 200,
    			height: 200,
    			colorDark : "#000000",
    			colorLight : "#ffffff",
    			correctLevel : QRCode.CorrectLevel.L
			})
            }
        
        }
// 		elm[0].after(newDiv)
    
//     	const text = elm[0].textContent.replaceAll(' ', '')
//         const text_split = text.split(":")
        
    
//     	var qrcode = new QRCode("qrcode", {
//    	 		text: "https://cms.labauto.kz/store/qr/"+text_split[1],
//     		width: 256,
//     		height: 256,
//     		colorDark : "#000000",
//     		colorLight : "#ffffff",
//     		correctLevel : QRCode.CorrectLevel.H
// 		})
   // }
	 
});