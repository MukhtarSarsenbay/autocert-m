if (!$) {
    $ = django.jQuery;
}

function getCSRFToken() {
    let cookieValue = null;
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            cookieValue = cookie.substring('csrftoken='.length);
            break;
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    return /^(GET|HEAD|OPTIONS|TRACE)$/i.test(method || '');
}

function sameOrigin(url) {
    if (!url) {
        return true;
    }
    const origin = window.location.protocol + '//' + window.location.host;
    return (url.charAt(0) === '/' && url.charAt(1) !== '/') || url.indexOf(origin) === 0;
}

if ($ && $.ajaxSetup) {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type || settings.method) && sameOrigin(settings.url)) {
                const token = getCSRFToken();
                if (token) {
                    xhr.setRequestHeader('X-CSRFToken', token);
                }
            }
        }
    });
}

function decodeVIN(vin) {
    // Проверяем длину VIN-кода
    if (vin.length !== 17) {
        return "Неправильная длина VIN-кода";
    }

    // Создаем объект, соответствующий символы года году выпуска
    const yearCodes = {
        'A': 1980, 'B': 1981, 'C': 1982, 'D': 1983, 'E': 1984, 'F': 1985,
        'G': 1986, 'H': 1987, 'J': 1988, 'K': 1989, 'L': 1990, 'M': 1991,
        'N': 1992, 'P': 1993, 'R': 1994, 'S': 1995, 'T': 1996, 'V': 1997,
        'W': 1998, 'X': 1999, 'Y': 2000, '1': 2001, '2': 2002, '3': 2003,
        '4': 2004, '5': 2005, '6': 2006, '7': 2007, '8': 2008, '9': 2009,
        'A': 2010, 'B': 2011, 'C': 2012, 'D': 2013, 'E': 2014, 'F': 2015,
        'G': 2016, 'H': 2017, 'J': 2018, 'K': 2019, 'L': 2020, 'M': 2021,
        'N': 2022, 'P': 2023, 'R': 2024, 'S': 2025, 'T': 2026, 'V': 2027,
        'W': 2028, 'X': 2029, 'Y': 2030, '1': 2031, '2': 2032, '3': 2033,
        '4': 2034, '5': 2035
    };

    // Получаем символ, соответствующий году выпуска (символ с индексом 10)
    const yearSymbol = vin.charAt(9).toUpperCase();

    // Проверяем, есть ли символ года в объекте, и возвращаем соответствующий год
    if (yearSymbol in yearCodes) {
        return yearCodes[yearSymbol];
    } else {
        return "Год не найден";
    }
}

document.addEventListener('DOMContentLoaded', function() {
    var rows = document.querySelectorAll('#result_list tbody tr');
    rows.forEach(function(row) {
        var columnValueRegister = row.querySelector('.field-isRegistred').innerText; // замените '.your-column-class' на класс вашего столбца
    	var columnValueCall = row.querySelector('.field-isCalled').innerText; // замените '.your-column-class' на класс вашего столбца
        if (columnValueRegister.length == 10) {
        	row.querySelector(".action-checkbox").style.backgroundColor = "rgb(247, 231, 121)"
            //row.style.color = 'rgb(119, 106, 0)';
        }
    	if (columnValueCall.length == 10) {
        //row.style.color = 'rgb(0, 128, 0)';
        row.querySelector(".action-checkbox").style.backgroundColor = "rgb(179, 255, 179)"
        }
    });
});


$( document ).ready(function() {
	txt1 = `<div id='id_container'></div>`;
	$("div.form-row.block.field-frln").after(txt1);

	txt1 = `<div id='pdfContainer'></div>`;
	$("#id_personPhone").after(txt1);

	const pdfInput = document.getElementById('app1');
    const pdfContainer = document.getElementById('pdfContainer');
	pdfContainer.setAttribute('style', 'float:right');

	txt1 = `<div id='idblock'></div>`;
	$("#id_container").append(txt1)

	const idBlock = document.getElementById('idblock');
	idBlock.setAttribute('style', 'float:left;width:50%;');
	
	$("#idblock").append($(".field-frln"));
	$("#idblock").append($(".field-personUid"));
	$("#idblock").append($(".field-personNumber"));
	$("#idblock").append($(".field-personPhone"));
	$("#idblock").append($(".field-personPublic"));
	$("#idblock").append($(".field-address"));
	$("#id_container").append($("#pdfContainer"))

    pdfInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file && file.type === 'application/pdf') {
            // Создаем URL для загруженного файла
            //const fileURL = URL.createObjectURL(file);
        	const fileURL = URL.createObjectURL(file) + '#page=1&scrollbar=0&navpanes=0&toolbar=0';
            
            // Создаем embed элемент
            const embed = document.createElement('embed');
            embed.setAttribute('src', fileURL);
            embed.setAttribute('width', '500px');
            embed.setAttribute('height', '500px');
        	//embed.setAttribute('style', 'float:right');
            embed.setAttribute('type', 'application/pdf');
            
            // Очищаем контейнер и добавляем embed
            pdfContainer.innerHTML = '';
            pdfContainer.appendChild(embed);
        
        
			formdata = new FormData();
        	formdata.append("file", file);
        	$.ajax({
    			url: "/dev/f4ac48ee-e171-45ca-be84-b1c16efbe474/detectID/",
    			type: "POST",
    			data: formdata,
    			processData: false,
    			contentType: false,
    			success: function (result) {
                	$("#id_frln").val(result.flm);
                	$("#id_personUid").val(result.uid);
                	$("#id_personUid").val(result.uid);
                	$("#id_personNumber").val(result.id);
                	$("#id_personPublic").val(result.date);
                	$("#id_address").val(result.address);
    			},
            	error: function() {
                	alert("Ошибка при распознование УД")
            	}
			});
        
        } else if (file && file.type === 'image/jpeg') {
        	const reader = new FileReader();
        
        	if (file) {
    			reader.readAsDataURL(file);
  			}
        
        	reader.addEventListener(
    			"load",
    			() => {
      				// convert image file to base64 string
                
                	const embed = document.createElement('img');
            		embed.setAttribute('src', reader.result);
            		embed.setAttribute('width', '500px');
            		embed.setAttribute('height', '500px');
        			//embed.setAttribute('style', 'float:right');
            
            		// Очищаем контейнер и добавляем embed
            		pdfContainer.innerHTML = '';
            		pdfContainer.appendChild(embed);
      				//preview.src = reader.result;
    			},
   	 			false,
  			);
        
        	formdata = new FormData();
        	formdata.append("file", file);
        	$.ajax({
    			url: "/dev/f4ac48ee-e171-45ca-be84-b1c16efbe474/detectID/",
    			type: "POST",
    			data: formdata,
    			processData: false,
    			contentType: false,
    			success: function (result) {
                	$("#id_frln").val(result.flm);
                	$("#id_personUid").val(result.uid);
                	$("#id_personUid").val(result.uid);
                	$("#id_personNumber").val(result.id);
                	$("#id_personPublic").val(result.date);
                	$("#id_address").val(result.address);
    			},
            	error: function() {
                	alert("Ошибка при распознование УД")
            	}
			});
        }
    	else {
            alert('Пожалуйста, выберите PDF или JPG файл');
        }
    });


	txt1 = `<div id='id_container_vin'></div>`;
	$(".field-carMarka").after(txt1);

	txt1 = `<div id='pdfContainerVIN'></div>`;
	$("#id_carColor").after(txt1);

	const pdfContainerVIN = document.getElementById('pdfContainerVIN');
	pdfContainerVIN.setAttribute('style', 'float:right');

	txt1 = `<div id='idblockVIN'></div>`;
	$("#id_container_vin").append(txt1)

	const idBlockVIN = document.getElementById('idblockVIN');
	idBlockVIN.setAttribute('style', 'float:left;width:40%;');
	
	$("#idblockVIN").append($(".field-carMarka"));
	$("#idblockVIN").append($(".field-carVincode"));
	$("#idblockVIN").append($(".field-carYear"));
	$("#idblockVIN").append($(".field-carColor"));
	$("#id_container_vin").append($("#pdfContainerVIN"))

	const pdfInputVIN = document.getElementById('app2');

	pdfInputVIN.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file && file.type === 'application/pdf') {
            // Создаем URL для загруженного файла
            //const fileURL = URL.createObjectURL(file);
        	const fileURL = URL.createObjectURL(file) + '#page=1&scrollbar=0&navpanes=0&toolbar=0';
            
            // Создаем embed элемент
            const embed = document.createElement('embed');
            embed.setAttribute('src', fileURL);
            embed.setAttribute('width', '300px');
            embed.setAttribute('height', '300px');
        	//embed.setAttribute('style', 'float:right');
            embed.setAttribute('type', 'application/pdf');
            
            // Очищаем контейнер и добавляем embed
            pdfContainerVIN.innerHTML = '';
            pdfContainerVIN.appendChild(embed);
        
        
			formdata = new FormData();
        	formdata.append("file", file);
        	$.ajax({
    			url: "/dev/f4ac48ee-e171-45ca-be84-b1c16efbe474/detectVIN/",
    			type: "POST",
    			data: formdata,
    			processData: false,
    			contentType: false,
    			success: function (result) {
                	$("#id_carVincode").val(result.vin_code);
                	$("#id_carMarka").val(result.marka);
                	$("#id_carYear").val(result.year);
    			},
            	error: function() {
                	alert("Ошибка при распознование УД")
            	}
			});
        
        } else if (file && file.type === 'image/jpeg') {
        	const reader = new FileReader();
        
        	if (file) {
    			reader.readAsDataURL(file);
  			}
        
        	reader.addEventListener(
    			"load",
    			() => {
      				// convert image file to base64 string
                
                	const embed = document.createElement('img');
            		embed.setAttribute('src', reader.result);
            		embed.setAttribute('width', '300px');
            		embed.setAttribute('height', '300px');
        			//embed.setAttribute('style', 'float:right');
            
            		// Очищаем контейнер и добавляем embed
            		pdfContainerVIN.innerHTML = '';
            		pdfContainerVIN.appendChild(embed);
      				//preview.src = reader.result;
    			},
   	 			false,
  			);
        
        	formdata = new FormData();
        	formdata.append("file", file);
        	$.ajax({
    			url: "/dev/f4ac48ee-e171-45ca-be84-b1c16efbe474/detectVIN/",
    			type: "POST",
    			data: formdata,
    			processData: false,
    			contentType: false,
    			success: function (result) {
                	$("#id_carVincode").val(result.vin_code);
                	$("#id_carMarka").val(result.marka);
                	$("#id_carYear").val(result.year);
    			},
            	error: function() {
                	alert("Ошибка при распознование УД")
            	}
			});
        }
    	else {
            alert('Пожалуйста, выберите PDF или JPG файл');
        }
    });


	$('#id_carVincode').keyup(function (e) {
		$(".field-carVincode").removeClass( "errors" );
    	$(".field-carVincode").find(".errorlist").remove();
    	
  		const text = $("#id_carVincode").val();
    
        if (text.includes("O") || text.includes("o")) {
            e.preventDefault();
            $(".field-carVincode").addClass( "errors" );
    		$(".field-carVincode").prepend( `<ul class='errorlist'><li>Вин коде встречается символ "O"!</li></ul>` );	
            return false;
        }
        
        if (text.includes("I") ||  text.includes("i")) {
            e.preventDefault();
            
            $(".field-carVincode").addClass( "errors" );
    		$(".field-carVincode").prepend( `<ul class='errorlist'><li>Вин коде встречается символ "I"!</li></ul>` );	
            return false;
        }

    
    	var regexp = /[а-яё]/i;
  	 	if(regexp.test(text)) {
       		e.preventDefault();
        
       		$(".field-carVincode").addClass( "errors" );
    		$(".field-carVincode").prepend( `<ul class='errorlist'><li>Вин коде встречается кирилица!</li></ul>` );	
       		return false;
   		}

    	if (text.length < 17) {
        	e.preventDefault();
        	$(".field-carVincode").addClass( "errors" );
    		$(".field-carVincode").prepend( `<ul class='errorlist'><li>Вин код меньше 17 символов (${text.length}/17)</li></ul>` );	
        	return false;
        } else if (text.length > 17) {
        	e.preventDefault();
			$(".field-carVincode").addClass( "errors" );
    		$(".field-carVincode").prepend( `<ul class='errorlist'><li>Вин код больше 17 символов (${text.length}/17)</li></ul>` );	
        	return false;
        }
    	
    	$('#id_carYear').val(decodeVIN(text))
	});

	$('#id_carVincode').on("change", function (e) {
  		const text = $("#id_carVincode").val();
    
    	$(".field-carVincode").removeClass( "errors" );
    	$(".field-carVincode").find(".errorlist").remove();
    	
    	var regexp = /[а-яё]/i;
  	 	if(regexp.test(text)) {
       		e.preventDefault();
        
       		$(".field-carVincode").addClass( "errors" );
    		$(".field-carVincode").prepend( `<ul class='errorlist'><li>Вин код встечается кирилица!</li></ul>` );	
       		return false;
   		}

    	if (text.length < 17) {
        	e.preventDefault();
        	$(".field-carVincode").addClass( "errors" );
    		$(".field-carVincode").prepend( `<ul class='errorlist'><li>Вин код меньше 17 символов (${text.length}/17)</li></ul>` );	
        	return false;
        } else if (text.length > 17) {
        	e.preventDefault();
			$(".field-carVincode").addClass( "errors" );
    		$(".field-carVincode").prepend( `<ul class='errorlist'><li>Вин код больше 17 символов (${text.length}/17)</li></ul>` );	
        	return false;
        }
    
    	$('#id_carYear').val(decodeVIN(text))
	});

	
})
