if (!$) {
    $ = django.jQuery;
}


function getRandomFloat(min, max, decimals) {
  const str = (Math.random() * (max - min) + min).toFixed(
    decimals,
  );

  return parseFloat(str);
}

function getRandomInt(min, max) {
  min = Math.ceil(min);
  max = Math.floor(max);
  return Math.floor(Math.random() * (max - min) + min); // The maximum is exclusive and the minimum is inclusive
}

// Генерация случайного числа в диапазоне от 3 до 6 с двумя знаками после запятой
function getRandomNumber(a, b) {
  return (Math.random() * (b - a) + a).toFixed(2);
}

// Генерация случайного процентного значения в диапазоне от 6 до 16
function getRandomPercentage(a, b) {
  return (Math.random() * (b - a) + a).toFixed(0);
}

// Рассчитывает разницу в процентах между двумя значениями
function calculatePercentageDifference(value1, value2) {
  return (((value2 - value1) / value1) * 100);
}

function getCSRFToken() {
	const formToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
	if (formToken && formToken.value) {
		return formToken.value;
	}

    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
		const separator = cookie.indexOf('=');
		if (separator === -1) continue;

		const name = cookie.substring(0, separator);
		if (name === 'csrftoken' || name.endsWith('_csrftoken')) {
			return decodeURIComponent(cookie.substring(separator + 1));
		}
    }
	return null;
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

   	// Функция для загрузки файла по ссылке
function downloadFile(url) {
  fetch(url)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.blob();
    })
    .then(blob => {
      // Извлекаем имя файла и декодируем его
      let filename = url.split('/').pop().split('?')[0]; 
      filename = decodeURIComponent(filename); // Декодируем URL

      const fileUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = fileUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(fileUrl);
    })
    .catch(error => console.error('There has been a problem with your fetch operation:', error));
}


$( document ).ready(function() {
	let style = "style='border: 2px solid; margin-left: 3px; margin-top: 3px; width:220px; padding: 5px'"

    let txt1 = `<a id='generator' ${style}>Генерировать данные</a>`;
  	$("#id_testBWD").after(txt1);
	txt1 = `<a id='gettestlog' ${style}>Взять данные с Записей</a>`;
  	$("#generator").after(txt1);

	txt1 = `<a id='getclimat' ${style}>Получить данные о погоде</a>`;
  	$("#id_testLocation").after(txt1);

	txt1 = `<a id='newpage' ${style}>Создать ссылку для подписи</a>`;
  	$(".deletelink-box").after(txt1);

	txt1 = `<a id='download' ${style}>Скачать все документы</a>`;
  	$(".field-signature").after(txt1);

    txt1 = `<a id='getuser' ${style}>Получить данные с ЕКТРМ</a>`;
  	$("#id_personId").after(txt1);

	txt1 = `<a id='getcar' ${style}>Получить данные с ЕКТРМ</a>`;
  	$("#id_carVin").after(txt1);

	// var txt1 = `
	// <div id="toolbar">
	// <form id="changelist-search" method="get">
	// 	<div><!-- DIV needed for valid HTML -->
	// 		<label for="searchbar"><img src="/static/admin/img/search.svg" alt="Search"></label>
	// 		<input type="text" size="40" name="q" value="" id="searchbar">
	// 		<input type="submit" value="Найти">
	// 	</div>
	// </form>
	// </div>
	// `
    //$("#content").before(txt1);

	// var txt1 = "<a id='getAll' style='border: 2px solid; margin-left: 5px'>Получить все документы</a>";
	// $(".submit-row").after(txt1);

	//var des = $(".field-decision").find(".readonly")[0].children[0];
    //var app = $(".field-application").find(".readonly")[0].children[0];
    //var cont = $(".field-contract").find(".readonly")[0].children[0]
    //var pro = $(".field-protocol").find(".readonly")[0].children[0];
    
    //des.setAttribute("download", "");
    //app.setAttribute("download", "");
    //cont.setAttribute("download", "");
    //pro.setAttribute("download", "");

	if ($('#id_testType').attr('checked')) {
        $('#id_testBD').show();
		$('#id_testSD').show();
		$('#id_testBSAT').show();
        
        $('#id_testSPB').hide();
        $('#id_testBWD').hide();
        $('#id_testNNCR').hide();
        $('#id_testNNCF').hide();
        $('#id_testFLW').hide();
    	$('#id_testFRW').hide();
    	$('#id_testRLW').hide();
    	$('#id_testRRW').hide();
        //$('#id_testMaxMass').hide();
        //$('#id_testMass').hide();
        $('#id_testFAW').hide();
        $('#id_testRAW').hide();
	} else {
        $('#id_testBD').hide();
		$('#id_testSD').hide();
		$('#id_testBSAT').hide();
        
        $('#id_testSPB').show();
        $('#id_testBWD').show();
        $('#id_testNNCR').show();
        $('#id_testNNCF').show();
        $('#id_testFLW').show();
    	$('#id_testFRW').show();
    	$('#id_testRLW').show();
    	$('#id_testRRW').show();
       
        //$('#id_testMaxMass').show();
        //$('#id_testMass').show();
        $('#id_testFAW').show();
        $('#id_testRAW').show();
    }

	var fileLinks = [
    	$(".field-application a").attr("href"),
    	$(".field-decision a").attr("href"),
    	$(".field-contract a").attr("href"),
    	$(".field-protocol a").attr("href"),
    ]
    

	$('#download').click(function() {
    	for (var i = 0; i < fileLinks.length; i++) {
        	downloadFile(fileLinks[i]);
        }
    })
	


	//$('#id_testBD').hide();
	//$('#id_testSD').hide();
	//$('#id_testBSAT').hide();
	//$('#id_test').hide();
	$('#id_testType').hide()

	$('#id_testType').click(function() {
    	if (this.checked) {
        	$('#id_testBD').show();
			$('#id_testSD').show();
			$('#id_testBSAT').show();
        
        	$('#id_testSPB').hide();
        	$('#id_testBWD').hide();
        	$('#id_testNNCR').hide();
        	$('#id_testNNCF').hide();
        	$('#id_testFLW').hide();
    		$('#id_testFRW').hide();
    		$('#id_testRLW').hide();
    		$('#id_testRRW').hide();
        	//$('#id_testMaxMass').hide();
        	//$('#id_testMass').hide();
        	$('#id_testFAW').hide();
        	$('#id_testRAW').hide();
        } else {
        	$('#id_testBD').hide();
			$('#id_testSD').hide();
			$('#id_testBSAT').hide();
        
        	$('#id_testSPB').show();
        	$('#id_testBWD').show();
        	$('#id_testNNCR').show();
        	$('#id_testNNCF').show();
        	$('#id_testFLW').show();
    		$('#id_testFRW').show();
    		$('#id_testRLW').show();
    		$('#id_testRRW').show();
       
        	//$('#id_testMaxMass').show();
        	//$('#id_testMass').show();
        	$('#id_testFAW').show();
        	$('#id_testRAW').show();
        }
	});


	$("#generator").on( "click", function() {
    	
    	// Генерация случайных значений
// 		const firstValueF = parseFloat(getRandomNumber(3, 6));
    
// 		const percentageDifferenceF = getRandomPercentage(6, 16);
    
// 		const secondValueF = (firstValueF + (firstValueF * percentageDifferenceF) / 100).toFixed(2);
    
//     	const firstValueR = parseFloat(getRandomNumber(3, 6));
    
// 		const percentageDifferenceR = getRandomPercentage(6, 16);
    
// 		const secondValueR = (firstValueR + (firstValueR * percentageDifferenceR) / 100).toFixed(2);
    
//     	const BWD = ((parseFloat(firstValueF) + parseFloat(firstValueR) + 
//                       parseFloat(secondValueF) + parseFloat(secondValueR)) * 1000) / (parseInt($('#id_testMass').val()) * 9.8)
        
//         const SPB = ((parseFloat(secondValueF) + parseFloat(secondValueR)) * 1000) / (parseInt($('#id_testMaxMass').val()) * 9.8)
        
        
        const MaxMass = (parseInt($('#id_testMaxMass').val()) * 9.81)
        const Ffcd = getRandomInt(200, 400);
    	const Afact = getRandomFloat(0.60, 0.90, 2) // Коф удельная тормозная сила рабочей тормозной системы
        
        const Kfcd = (Afact * MaxMass * 9.81) / Ffcd;
    
    	const FfcdNormal = (Afact * MaxMass * 9.81) / Kfcd; // Нютон орган управления
    
    	
    	const Kfmmin = (Afact * MaxMass * 9.81) / 589;
    	const Kfmmax = (Afact * MaxMass * 9.81) / 200;
    
    	
    	const Kfpmin = (Afact * MaxMass * 9.81) / 688;
    	const Kfpmax = (Afact * MaxMass * 9.81) / 250;
    
    	
       	const Fbm = (Afact * MaxMass * 9.81) / getRandomInt(Kfmmax, Kfmmin) // Нютон ручного 
        const Fbp = (Afact * MaxMass * 9.81) / getRandomInt(Kfpmax, Kfpmin) // Нютон ножного
                
        
        
		const firstValueL = parseFloat(getRandomNumber(689, 2231));
		const percentageDifferenceL = getRandomPercentage(3, 5);
		const secondValueL = (firstValueL + (firstValueL * percentageDifferenceL) / 100).toFixed(2);
        
        $('#id_testFAW').val(parseInt($('#id_testMass').val()) * 0.6)
    	$('#id_testRAW').val(parseInt($('#id_testMass').val()) * 0.4)
    
    	$('#id_testFW').val(parseInt($('#id_testMass').val()) * 0.6)
    	$('#id_testSW').val(parseInt($('#id_testMass').val()) * 0.4)
    
    	$('#id_testTH').val(getRandomFloat(2.0, 6.0, 2))
    	$('#id_testASR').val(getRandomInt(29, 31))
    	$('#id_testBD').val(getRandomFloat(9.9, 15.2, 1))
    	$('#id_testSD').val(getRandomFloat(5.5, 8.6, 1))
    	$('#id_testBSAT').val(getRandomFloat(0.3, 0.5, 1))
    
    	//$('#id_testFLW').val(firstValueF);
    	//$('#id_testFRW').val(secondValueF);
    	//$('#id_testRLW').val(firstValueR);
    	//$('#id_testRRW').val(secondValueR);
        
  		$('#id_testCoMin').val(getRandomFloat(0.11, 0.14, 2));
    	$('#id_testCoMax').val(getRandomFloat(0.08, 0.10, 2));
    	$('#id_testEN').val(getRandomInt(60, 90));
    	$('#id_testBWD').val(FfcdNormal.toFixed(0));
    	$('#id_testSPB').val(Afact);
    	
    	$('#id_testCBDR').val(Fbm.toFixed(0));
    	$('#id_testCBDP').val(Fbp.toFixed(0));
    
    	//$('#id_testNNCF').val(percentageDifferenceF);
    	//$('#id_testNNCR').val(percentageDifferenceR);
    	
    	$('#id_testBDF').val(getRandomInt(1600, 5000));
    	$('#id_testBDR').val(getRandomInt(1600, 5000));
    
    	$('#id_testNNC').val(getRandomInt(16, 19));
    
    	$('#id_testEF').val(getRandomFloat(0.10, 1.39, 2));
    
    	$('#id_testALN').val(getRandomFloat(0.12, 0.14, 2));
    	$('#id_testLNR').val(parseInt(firstValueL));  // 689,2231
    	$('#id_testLNL').val(parseInt(secondValueL)); // 691,2315
    
    	const MPLAR = parseFloat(getRandomInt(110000, 130000));	
    	const MPLAL = parseFloat(getRandomInt(110000, 130000));	
    
    	$('#id_testMPLAR').val(MPLAR);
    	$('#id_testMPLAL').val(MPLAL);
    	$('#id_testMPLA').val(MPLAR + MPLAL);
    	$('#id_testFPM').val(getRandomInt(80, 105));
    	$('#id_testTSP').val(getRandomInt(2, 7));
    	$('#id_testLT').val(getRandomInt(75, 95));
    
    	$('#id_testLTWG').val(getRandomInt(80, 93));
    	$('#id_testLTLG').val(getRandomInt(79, 85));
    	$('#id_testLTRG').val(getRandomInt(79, 85));
    
    	$('#id_testMAUP').val(getRandomInt(16, 30));
    	$('#id_testMALEFT').val(getRandomInt(31, 45));
    	$('#id_testMARIGHT').val(getRandomInt(31, 45));
    	//alert("Успешно генерирован")
	});

	$("#gettestlog").on("click", function() {
		const vin = ($("#id_carVin").val() || "").trim();
		if (!vin) {
			alert("Укажите VIN в поле 'Вин-Код'");
			return;
		}

		$.ajax({
			url: `/api/gettestlog/?vin=${encodeURIComponent(vin)}`,
			headers: {
				"X-CSRFToken": getCSRFToken()
			},
			method: "get",
			success: function(result){
				const fields = result && result.fields ? result.fields : {};
				let updated = 0;

				Object.keys(fields).forEach(function(name) {
					const el = $(`#id_${name}`);
					if (el.length) {
						el.val(fields[name] || "");
						updated += 1;
					}
				});

				const num = result && result.testlog_number ? result.testlog_number : "-";
				alert(`Данные подтянуты из Записей об испытаниях: ${num}. Обновлено полей: ${updated}`);
			},
			error: function(xhr) {
				const msg = (xhr.responseJSON && xhr.responseJSON.error)
					? xhr.responseJSON.error
					: "Не удалось получить данные из Записей";
				alert(msg);
			}
		});
	});

	$("#getclimat").on( "click", function() {
    	$.ajax({
        	url: "https://api.weatherapi.com/v1/current.json?key=c7fcb09158e34ac5941104316231309%20&q=shymkent&aqi=no",
        	corsDomain:true,
        	success: function(result){
    			$("#id_testTemp").val(result.current.temp_c);
        		$("#id_testHum").val(result.current.humidity);
        		$("#id_testPress").val(result.current.pressure_mb / 10);
  			}
        });
    
  		//alert("Данные о погоде успешно получено")
	});

	$("#getuser").on( "click", function(event) {
		event.preventDefault();
		const button = $(this);
		const username = $("#id_personEmail").val().trim();
		const password = $("#id_personPassword").val();
		if (!username || !password) {
			alert("Введите почту и пароль для входа в ЕКТРМ");
			return;
		}

		button.css("pointer-events", "none");
    	$.ajax(
        	{
            	url: "/api/getuser/",
				// beforeSend: function (xhr) {
				// xhr.setRequestHeader ("Authorization", "Basic " + btoa($("#id_personEmail").val() + ":" + $("#id_personPassword").val()));
				// },
            
            	headers: {
        			"X-CSRFToken": getCSRFToken()
    			},
            	method: "post",
            	data: {	
					"username": username,
					"password": password
                },
            	success: function(result){
    				$("#id_lastName").val(result.lastname);
        			$("#id_firstName").val(result.firstname);
                	$("#id_middleName").val(result.patronymic);
                	$("#id_personId").val(result.code.replace("IIN", ""));
					alert("Данные из ЕКТРМ получены");
				},
				error: function(xhr) {
					const message = xhr.responseJSON && xhr.responseJSON.error
						? xhr.responseJSON.error
						: "Не удалось получить данные из ЕКТРМ";
					alert(message);
				},
				complete: function() {
					button.css("pointer-events", "");
				}
  		});
    
  		//alert("Данные о погоде успешно получено")
	});

	$("#getcar").on("click", function() {
    	$.ajax(
        	{
            	url: `/api/getcar/?search=${$("#id_carVin").val()}`,
            
            	headers: {
        			"X-CSRFToken": getCSRFToken()
    			},
            	method: "get",
            	success: function(result){
                	alert("Успешно найдено транспорт")
                
                	$("#id_carYear").val(result.fieldValue.textbox_year);
                
                	$("#id_carMarka").val(result.fieldValue.textbox_stamp);
                
                	$("#id_carNSFR").val(result.fieldValue.textbox_number_of_seats);
                
                	$("#id_testMass").val(result.fieldValue.textbox_min);
                	$("#id_testMaxMass").val(result.fieldValue.textbox_min_2);
                    
                    $("#id_testTM").val(result.fieldValue.textbox_size_tires);
                
                	$("#id_carEngLoc").val(result.fieldValue.textarea_description_engine_location);
                    
                    $("#id_carSusFront").val(result.fieldValue.textarea_front_suspension);
                	$("#id_carSusRear").val(result.fieldValue.textarea_back_suspension);
                
    				$("#id_carIgnitionType").val(result.fieldValue.textarea_ignition);
                
                	$("#id_carLength").val(result.fieldValue.textbox_length);
                	$("#id_carWidth").val(result.fieldValue.textbox_width);
                	$("#id_carHeight").val(result.fieldValue.textbox_height);
                
                
                	$("#id_carTransmission").val(result.fieldValue.textarea_transmission);
                
                    $("#id_carEngineCR").val(result.fieldValue.numericinput_engine_compression_ratio);
                
                	$("#id_carEnginePower").val(result.fieldValue.numericinput_maximum_power);
                
                    $("#id_carEngineVolume").val(result.fieldValue.numericinput_engine_cylinder_displacement);
                
                    $("#id_carEngineCount").val(result.fieldValue.numericinput_number_of_engine_cylinders);
                
                	$("#id_carEngine").val(result.fieldValue.textbox_engine_brand);
                
                	$('#id_carCategory').val(result.fieldValue.listbox_category);
                
                	$('#id_carSC').val(result.fieldValue.textbox_mark_steering);
                
                	$('#id_carBody').val(result.fieldValue.listbox_type_body+"/"+result.fieldValue.textbox_body_type);
                
                	$('#id_carManufacturer').val(result.fieldValue.textbox_address_assembly_plant);
                
                	$('#id_carEngLoc').val(result.fieldValue.textarea_description_engine_location);
                	
                	$('#id_carWF').val(result.fieldValue.textbox_vehicle_layout_diagram + "/" + result.fieldValue.listbox_type_body)
                	$('#id_carBase').val(result.fieldValue.textbox_base)
                	$('#id_carWT').val(result.fieldValue.textbox_track_front_rear_wheels)
                
                	//$('#id_carVLD').val()
                
                	$('#id_carBrakeWork').val(result.fieldValue.textbox_br_work)
                	$('#id_carBrakeSpear').val(result.fieldValue.textbox_br_spare)
                	$('#id_carBrakeParking').val(result.fieldValue.textbox_br_parking)
                
                	let track_wheels = result.fieldValue.textbox_track_front_rear_wheels
                    if (track_wheels.split("/").length > 0) {
                    	$("#id_carFWT").val(track_wheels.split("/")[0]);
                		$("#id_carRWT").val(track_wheels.split("/")[1]);
                    }
                
                    $("#id_carPowerType").val(result.fieldValue.textarea_power_system_description);
                
                	$("#id_carEANS").val(result.fieldValue.textarea_exhaust);
                
                	$("#id_carGearbox").val(result.fieldValue.textbox_cp_type);
                },
            	error: function() {
                	alert("Не удалость найти марку из базы ЕКТРМ")
                }
  		});
    })

	$("#newpage").on( "click", function() {
    	var height = 500
        var width = 500
        
        var vin = $('#id_carVin').val()
    	
    	var top = parseInt((screen.availHeight) - height - 100);
    	var left = parseInt((screen.availWidth) - (width / 2));
    	var features = "location=1, status=1, scrollbars=1, width=" + width + ", height=" + height + ", top=" + top + ", left=" + left;
        console.log(vin);
    	window.open(`/api/signature/?vin=${vin}`, "kad", features);
	});

// 	$("#getAll").on("click", function() {
    	
//     })
	
});
