(function($) {

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


function setRecognitionStatus(input, message, isError) {
    const id = input.id + '_recognition_status';
    let status = document.getElementById(id);
    if (!status) {
        status = document.createElement('div');
        status.id = id;
        status.setAttribute('role', 'status');
        input.insertAdjacentElement('afterend', status);
    }
    status.textContent = message;
    status.style.color = isError ? '#b91c1c' : '#475569';
}

function normalizeDateForInput(value) {
    const text = String(value || '').trim();
    const match = text.match(/^(\d{2})[.\/-](\d{2})[.\/-](\d{4})$/);
    return match ? `${match[3]}-${match[2]}-${match[1]}` : text;
}

async function handleDocumentSelection(input, kind) {
    // Cancel any previous upload, including when the new selection is invalid.
    if (input.recognitionController) input.recognitionController.abort();
    const controller = new AbortController();
    input.recognitionController = controller;
    const file = input.files && input.files[0];
    if (!file) {
        setRecognitionStatus(input, '', false);
        return;
    }
    if (!/^(application\/(x-)?pdf|image\/(jpeg|jpg|pjpeg))$/i.test(file.type || '')
        && !/\.(pdf|jpe?g)$/i.test(file.name || '')) {
        setRecognitionStatus(input, 'Поддерживаются только PDF и JPG', true);
        return;
    }
    const previewId = input.id + '_document_preview';
    let preview = document.getElementById(previewId);
    if (!preview) {
        preview = document.createElement('div');
        preview.id = previewId;
        input.insertAdjacentElement('afterend', preview);
    }
    if (preview.dataset.objectUrl) URL.revokeObjectURL(preview.dataset.objectUrl);
    const url = URL.createObjectURL(file);
    preview.dataset.objectUrl = url;
    const pdf = /pdf$/i.test(file.type || '') || /\.pdf$/i.test(file.name || '');
    const image = document.createElement(pdf ? 'embed' : 'img');
    image.src = url;
    image.style.cssText = 'max-width:100%;width:500px;max-height:500px;object-fit:contain;';
    if (pdf) {
        image.type = 'application/pdf';
        image.height = '500';
    }
    preview.replaceChildren(image);
    const fieldIds = kind === 'id'
        ? ['id_frln', 'id_personUid', 'id_personNumber', 'id_personPublic', 'id_address']
        : ['id_carVincode', 'id_carMarka', 'id_carYear'];
    const before = Object.fromEntries(fieldIds.map(id => [id, document.getElementById(id)?.value]));
    function fill(id, value) {
        const field = document.getElementById(id);
        if (field && value !== null && value !== undefined && String(value).trim()
            && field.value === before[id]) {
            field.value = String(value).trim();
        }
    }
    setRecognitionStatus(input, 'Распознавание документа…', false);
    const timer = setTimeout(() => controller.abort(), 90000);
    try {
        const body = new FormData();
        body.append('file', file);
        const response = await fetch(`/api/actus/documents/recognize/${kind}/`, {
            method: 'POST', body, credentials: 'same-origin',
            headers: {'X-CSRFToken': getCSRFToken() || ''}, signal: controller.signal
        });
        let result;
        try { result = await response.json(); }
        catch (_) { throw new Error('Сервер вернул некорректный ответ. Обновите страницу и повторите попытку.'); }
        if (!response.ok) throw new Error(result?.error || result?.detail || 'Не удалось распознать документ');
        if (!result || typeof result !== 'object' || Array.isArray(result)) throw new Error('Некорректный ответ сервиса');
        if (input.recognitionController !== controller) return;
        const values = kind === 'id'
            ? [result.flm, result.uid, result.id, normalizeDateForInput(result.date), result.address]
            : [String(result.vin_code || '').trim().toUpperCase(),
               result.marka || [result.name, result.model].filter(Boolean).join(' '), result.year];
        if (!values.some(value => value !== null && value !== undefined && String(value).trim())) {
            throw new Error('Сервис не смог распознать данные документа');
        }
        fieldIds.forEach((id, index) => fill(id, values[index]));
        setRecognitionStatus(input, 'Документ распознан. Проверьте заполненные поля.', false);
    } catch (error) {
        if (input.recognitionController !== controller) return;
        setRecognitionStatus(input, error.name === 'AbortError'
            ? 'Время ожидания истекло. Выберите файл повторно.' : error.message, true);
    } finally {
        clearTimeout(timer);
    }
}

$(document).ready(function() {
    // Match Django file widgets by name; their id may be app1 or id_app1.
    if (!document.getElementById('id_carVincode') || !document.getElementById('id_frln')) return;
    for (const [name, kind] of [['app1', 'id'], ['app2', 'vin']]) {
        const input = document.querySelector(`input[type="file"][name="${name}"]`);
        if (input) input.addEventListener('change', () => handleDocumentSelection(input, kind));
    }

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

	
});

})(django.jQuery);
