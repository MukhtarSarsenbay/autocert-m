from django.http import HttpResponse, FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import close_old_connections
from docxtpl import DocxTemplate
import logging
import re
import threading
from datetime import date
import calendar
from pathlib import Path
from .models import TestLog
from subuser.models import SubUser
from cert.utils import convert_to
from .services import get_or_create_testlog_creator



BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)
DEFAULT_TEMPLATE_PATH = BASE_DIR / "media" / "ref" / "main_doc.fixed6.docx"
TRAILER_TEMPLATE_DOCX_PATH = BASE_DIR / "media" / "ref" / "main_doc_trailer.docx"
FORM_TO_MODEL_ALIASES = {                                                                                                                                                                              
      "plate_pos_front_ok": "plate_pos_front",                                                                                                                                                           
      "plate_pos_rear_ok": "plate_pos_rear",                                                                                                                                                             
}                                                                                                                                                                                                      
MODEL_TO_FORM_ALIASES = {v: k for k, v in FORM_TO_MODEL_ALIASES.items()}  

MONTH_TO_STRING = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}


def _is_subuser(user):
    return isinstance(user, SubUser)

def _is_company_user(user):
    return isinstance(user, User) and not user.is_superuser

def _can_access_testlog(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if not (user.has_perm("testlog.change_testlog") or user.has_perm("testlog.view_testlog")):
        return False
    return _is_subuser(user) or _is_company_user(user)

def _filter_testlog_queryset_for_user(qs, user):
    if not user or not user.is_authenticated:                                                                                                                                                          
        return qs.none()                                                                                                                                                                               
    if user.is_superuser:                                                                                                                                                                              
        return qs                                                                                                                                                                                      
    if _is_subuser(user):                                                                                                                                                                              
        return qs.filter(creator=user)                                                                                                                                                                 
    if _is_company_user(user):                                                                                                                                                                         
        return qs.filter(creator__creator_id=user.id)                                                                                                                                                  
    return qs.none()   


def _is_obj_in_scope(user, obj):                                                                                                                                                                       
    if user.is_superuser:                                                                                                                                                                              
        return True                                                                                                                                                                                    
    if _is_subuser(user):                                                                                                                                                                              
        return obj.creator_id == user.id                                                                                                                                                               
    if _is_company_user(user):                                                                                                                                                                         
        return bool(obj.creator_id and obj.creator and obj.creator.creator_id == user.id)                                                                                                              
    return False

def _can_access_testlog_obj(user, obj):
    return _can_access_testlog(user) and _is_obj_in_scope(user, obj)

def _can_create_testlog(user):                                                                                                                                                                         
    if not _can_access_testlog(user):                                                                                                                                                                  
        return False                                                                                                                                                                                   
    return user.is_superuser or _is_subuser(user) 

def _can_edit_testlog_obj(user, obj):                                                                                                                                                                  
    if user.is_superuser:                                                                                                                                                                              
        return True                                                                                                                                                                                    
    return _is_subuser(user) and _is_obj_in_scope(user, obj)

def _can_delete_testlog_obj(user, obj):                                                                                                                                                                
    return _can_edit_testlog_obj(user, obj) 

def badge_callback_testlog(request):
    if not _can_access_testlog(request.user):                                                                                                                                                          
        return 0                                                                                                                                                                                       
    qs = _filter_testlog_queryset_for_user(TestLog.objects.all(), request.user)                                                                                                                        
    return qs.count()     


def _render_pdf(obj):
    placeholder_fields = [
        f.name
        for f in TestLog._meta.fields
        if f.name
        not in {
            "id",
            "test_date",
            "creator",
            "protocol",
            "isClose",
            "created_at",
        }
    ]
    model = {name: getattr(obj, name) for name in placeholder_fields}
    # Keep backward-compatible placeholder names used in DOCX template.
    for form_name, model_name in FORM_TO_MODEL_ALIASES.items():
        model[form_name] = getattr(obj, model_name, "")

    if obj.test_date:
        model["date_day"] = obj.test_date.day
        model["date_month"] = MONTH_TO_STRING.get(obj.test_date.month, "")
        model["date_year"] = obj.test_date.year

    template_path = TRAILER_TEMPLATE_DOCX_PATH if _is_trailer_category(obj.car_category) else DEFAULT_TEMPLATE_PATH

    if not template_path.exists():
        raise FileNotFoundError(str(template_path))

    number = obj.test_number or str(obj.id)
    suffix = "Trailer" if _is_trailer_category(obj.car_category) else "TestLog"
    out_docx = BASE_DIR / "media" / "testlog" / f"{suffix}_{number}.docx"
    out_docx.parent.mkdir(parents=True, exist_ok=True)

    tpl = DocxTemplate(template_path)
    tpl.render(model)
    tpl.save(out_docx)

    try:
        convert_to(out_docx)
    except (FileNotFoundError, OSError):
        # unoconv is not available (Windows). Keep DOCX only.
        obj.protocol = None
        obj.isClose = False
        obj.save(update_fields=["protocol", "isClose"])
        return False

    pdf_name = f"{suffix}_{number}.pdf"
    obj.protocol = f"testlog/{pdf_name}"
    obj.isClose = True
    obj.save(update_fields=["protocol", "isClose"])
    return True


def _render_pdf_worker(obj_id):
    close_old_connections()
    try:
        obj = TestLog.objects.get(id=obj_id)
        _render_pdf(obj)
    except Exception:
        logger.exception("Failed to render TestLog PDF for id=%s", obj_id)
    finally:
        close_old_connections()


def _queue_pdf_render(obj):
    obj.protocol = None
    obj.isClose = False
    obj.save(update_fields=["protocol", "isClose"])
    thread = threading.Thread(target=_render_pdf_worker, args=(obj.id,), daemon=True)
    thread.start()


FORM_TEMPLATE_NAME = "testlog/form_raw.html"
TRAILER_FORM_TEMPLATE_NAME = "testlog/o1o2o3.html"
FORM_PATH = BASE_DIR / "templates" / FORM_TEMPLATE_NAME
TRAILER_FORM_PATH = BASE_DIR / "templates" / TRAILER_FORM_TEMPLATE_NAME

TYPE_CATEGORY = {
    "M1",
    "M2",
    "M3",
    "N1",
    "N2",
    "N3",
    "O1",
    "O2",
    "O3",
    "O4",
}

MONTH_NAME_MAP = {
    "январь": 1,
    "января": 1,
    "февраль": 2,
    "февраля": 2,
    "март": 3,
    "марта": 3,
    "апрель": 4,
    "апреля": 4,
    "май": 5,
    "мая": 5,
    "июнь": 6,
    "июня": 6,
    "июль": 7,
    "июля": 7,
    "август": 8,
    "августа": 8,
    "сентябрь": 9,
    "сентября": 9,
    "октябрь": 10,
    "октября": 10,
    "ноябрь": 11,
    "ноября": 11,
    "декабрь": 12,
    "декабря": 12,
}

def _parse_number(value):
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None
    
def _is_trailer_category(value):                                                                                                                                                                       
    raw = str(value or "").strip().upper()                                                                                                                                                             
    if not raw:                                                                                                                                                                                        
        return False
    code = raw.split()[0]                                                                                                                                                                              
    return code in {"O1", "O2", "O3", "O4"} 


def _validate_form(post_data):
    errors = {}
    cleaned = {}

    temp = _parse_number(post_data.get("temp_air"))
    if temp is None or not (5 <= temp <= 35):
        errors["temp_air"] = "Температура должна быть от 5 до 35"

    humidity = _parse_number(post_data.get("humidity"))
    if humidity is None or not (0 <= humidity <= 85):
        errors["humidity"] = "Влажность должна быть от 0 до 85%"

    pressure = _parse_number(post_data.get("pressure"))
    if pressure is None or not (92 <= pressure <= 105):
        errors["pressure"] = "Давление должно быть от 92 до 105 кПа"

    plate_height = _parse_number(post_data.get("plate_height_up"))
    if plate_height is None or not (400 <= plate_height <= 1200):
        errors["plate_height_up"] = "Высота таблички должна быть от 400 до 1200"

    vin = (post_data.get("vin_last4") or "").strip().upper()
    if not vin or not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin):
        errors["vin_last4"] = "VIN должен быть 17 символов (A-Z/0-9), без I,O,Q"
    else:
        cleaned["vin_last4"] = vin

    car_category = (post_data.get("car_category") or "").strip().upper()
    if not car_category:
        errors["car_category"] = "Укажите категорию ТС"
    else:
        code = car_category.split()[0]
        if code not in TYPE_CATEGORY:
            errors["car_category"] = "Категория ТС должна быть из списка M1..O4"
        else:
            cleaned["car_category"] = code

    # Brake difference calculations
#     def _calc_brake_diff(left_name, right_name, out_name):
#         left = _parse_number(post_data.get(left_name))
#         right = _parse_number(post_data.get(right_name))
#         if left is None or right is None:
#             errors[out_name] = f"Заполните {left_name} и {right_name}"
#             return
#         max_val = max(left, right)
#         if max_val <= 0:
#             errors[out_name] = "Некорректные значения для расчета"
#             return
#         diff = abs(left - right) / max_val * 100.0
#         cleaned[out_name] = f"{diff:.2f}"

#         category_code = cleaned.get("car_category") or car_category.split()[0] if car_category else ""
#         limit = 20 if category_code in {"O1", "O2", "O3", "O4"} else 25
#         if diff > limit:
#             errors[out_name] = f"Превышение нормы: {diff:.2f}% (допустимо до {limit}%)"

#     _calc_brake_diff("ax1_brake_power_l", "ax1_brake_power_r", "brake_diff")
#     _calc_brake_diff("ax1_spare_brake_power_l", "ax1_spare_brake_power_r", "brake_diff_spare")

    day_raw = (post_data.get("date_day") or "").strip()
    month_raw = (post_data.get("date_month") or "").strip()
    year_raw = (post_data.get("date_year") or "").strip()
    if day_raw or month_raw or year_raw:
        if not (day_raw and month_raw and year_raw):
            if not day_raw:
                errors["date_day"] = "Укажите день"
            if not month_raw:
                errors["date_month"] = "Укажите месяц"
            if not year_raw:
                errors["date_year"] = "Укажите год"
        else:
            day = int(day_raw) if day_raw.isdigit() else None
            year = int(year_raw) if year_raw.isdigit() else None
            month = None
            if month_raw.isdigit():
                month = int(month_raw)
            else:
                month = MONTH_NAME_MAP.get(month_raw.lower())

            if day is None or not (1 <= day <= 31):
                errors["date_day"] = "День должен быть от 1 до 31"
            if month is None or not (1 <= month <= 12):
                errors["date_month"] = "Месяц должен быть от 1 до 12"
            if year is None or not (1900 <= year <= date.today().year):
                errors["date_year"] = "Год должен быть корректным"

            if not errors.get("date_day") and not errors.get("date_month") and not errors.get("date_year"):
                max_day = calendar.monthrange(year, month)[1]
                if day > max_day:
                    errors["date_day"] = "Такой даты не существует"
                else:
                    picked = date(year, month, day)
                    if picked > date.today():
                        errors["date_day"] = "Дата не может быть в будущем"

    return errors, cleaned


@ensure_csrf_cookie
@login_required
def form_page(request, pk):
    if not _can_access_testlog(request.user):
        return HttpResponse("forbidden", status=403)

    obj = get_object_or_404(TestLog, id=pk)
    if not _can_access_testlog_obj(request.user, obj):                                                                                                                                                     
        return HttpResponse("forbidden", status=403) 
    
    if request.method == "POST":
        if not _can_edit_testlog_obj(request.user, obj):                                                                                                                                                       
            return HttpResponse("forbidden", status=403) 
        errors, cleaned = _validate_form(request.POST)
        if errors:
            return JsonResponse({"errors": errors}, status=400)
        for f in TestLog._meta.fields:
            if f.name in {"id", "test_date", "creator", "protocol", "isClose", "created_at"}:
                continue
            post_name = MODEL_TO_FORM_ALIASES.get(f.name, f.name)
            if f.name.endswith(("_yes", "_no", "_na", "_ok", "_bad")):
                value = "[✓]" if (post_name in request.POST or f.name in request.POST) else ""
            else:
                value = cleaned.get(f.name, request.POST.get(post_name, request.POST.get(f.name, "")))
                if f.name in {"plate_pos_front", "plate_pos_rear"} and value == "on":
                    value = "[✓]"
            setattr(obj, f.name, value)
        
        day_raw = (request.POST.get("date_day") or "").strip()                                                         
        month_raw = (request.POST.get("date_month") or "").strip()                                                     
        year_raw = (request.POST.get("date_year") or "").strip()                                                       
                                                                                                                        
        if day_raw and month_raw and year_raw:                                                                         
            month = int(month_raw) if month_raw.isdigit() else MONTH_NAME_MAP.get(month_raw.lower())                   
            obj.test_date = date(int(year_raw), month, int(day_raw))                                                   
        else:                                                                                                          
            obj.test_date = None 
        obj.save()
        _queue_pdf_render(obj)
        return HttpResponse("pdf queued", status=202)

    form_path = TRAILER_FORM_PATH if _is_trailer_category(obj.car_category) else FORM_PATH
    if not form_path.exists():
        return HttpResponse("form not found", status=500)
    template_name = TRAILER_FORM_TEMPLATE_NAME if _is_trailer_category(obj.car_category) else FORM_TEMPLATE_NAME
    return render(request, template_name)


@ensure_csrf_cookie
@login_required                                                                                                                                                                                        
def form_create(request):                                                                                                                                                                              
    if not _can_access_testlog(request.user):                                                                                                                                                          
        return HttpResponse("forbidden", status=403)                                                                                                                                                   
    
    kind = (request.GET.get("kind") or "").strip().lower()

    if request.method == "POST":                                                                                                                                                                       
        if not _can_create_testlog(request.user):                                                                                                                                                      
            return HttpResponse("forbidden", status=403)                                                                                                                                               
                                                                                                                                                                                                        
        errors, cleaned = _validate_form(request.POST)                                                                                                                                                 
        if errors:                                                                                                                                                                                     
            return JsonResponse({"errors": errors}, status=400)                                                                                                                                        
                                                                                                                                                                                                        
        if _is_subuser(request.user):                                                                                                                                                                  
            obj = TestLog.objects.create(creator=request.user)                                                                                                                                         
        elif request.user.is_superuser:                                                                                                                                                                
            creator_id = request.POST.get("creator_id")                                                                                                                                                
            creator, _ = get_or_create_testlog_creator(request.user, creator_id)
            if creator is None:                                                                                                                                                                        
                return HttpResponse("No active SubUser found for superuser", status=400)                                                                                                               
            obj = TestLog.objects.create(creator=creator)                                                                                                                                              
        else:                                                                                                                                                                                          
            return HttpResponse("forbidden", status=403)                                                                                                                                               
                                                                                                                                                                                                        
        for f in TestLog._meta.fields:                                                                                                                                                                 
            if f.name in {"id", "test_date", "creator", "protocol", "isClose", "created_at"}:                                                                                                          
                continue                                                                                                                                                                               
            post_name = MODEL_TO_FORM_ALIASES.get(f.name, f.name)
            if f.name.endswith(("_yes", "_no", "_na", "_ok", "_bad")):                                                                                                                                 
                value = "[✓]" if (post_name in request.POST or f.name in request.POST) else ""                                                                                                                                        
            else:                                                                                                                                                                                      
                value = cleaned.get(f.name, request.POST.get(post_name, request.POST.get(f.name, "")))                                                                                                                              
                if f.name in {"plate_pos_front", "plate_pos_rear"} and value == "on":
                    value = "[✓]"
            setattr(obj, f.name, value)                                                                                                                                                                
        day_raw = (request.POST.get("date_day") or "").strip()                                                         
        month_raw = (request.POST.get("date_month") or "").strip()                                                     
        year_raw = (request.POST.get("date_year") or "").strip()                                                       
                                                                                                                        
        if day_raw and month_raw and year_raw:                                                                         
            month = int(month_raw) if month_raw.isdigit() else MONTH_NAME_MAP.get(month_raw.lower())                   
            obj.test_date = date(int(year_raw), month, int(day_raw))                                                   
        else:                                                                                                          
            obj.test_date = None                                                                                                                                                                                  
        obj.save()                                                                                                                                                                                     
        _queue_pdf_render(obj)
        return HttpResponse("pdf queued", status=202)

    if kind == "trailer":
        if not TRAILER_FORM_PATH.exists():
            return HttpResponse("trailer form not found", status=500)
        return render(request, TRAILER_FORM_TEMPLATE_NAME)

    if kind == "default":
        if not FORM_PATH.exists():
            return HttpResponse("form not found", status=500)
        return render(request, FORM_TEMPLATE_NAME)

    return render(request, "testlog/form_choice.html")
                                                                                                                                                                                                        
    if not FORM_PATH.exists():                                                                                                                                                                         
        return HttpResponse("form not found", status=500)                                                                                                                                              
    return render(request, FORM_TEMPLATE_NAME)

    
@login_required
def data_page(request, pk):
    if not _can_access_testlog(request.user):
        return HttpResponse("forbidden", status=403)
    obj = get_object_or_404(TestLog, id=pk)
    if not _can_access_testlog_obj(request.user, obj):                                                                                                                                                     
        return HttpResponse("forbidden", status=403) 
    data = {}
    for f in TestLog._meta.fields:
        if f.name in {"id", "test_date", "creator", "protocol", "isClose", "created_at"}:
            continue
        val = getattr(obj, f.name)
        out_name = MODEL_TO_FORM_ALIASES.get(f.name, f.name)
        data[out_name] = "" if val is None else val
    return JsonResponse(data)


@login_required
def list_page(request):
    if not _can_access_testlog(request.user):
        return HttpResponse("forbidden", status=403)
    qs = TestLog.objects.all().order_by("-id")
    if not request.user.is_superuser:
        qs = _filter_testlog_queryset_for_user(qs, request.user) 
    total_count = qs.count()
    pdf_count = qs.filter(isClose=True).count()
    docx_count = qs.filter(isClose=False).count()
    return render(
        request,
        "testlog/list.html",
        {
            "items": qs,
            "total_count": total_count,
            "pdf_count": pdf_count,
            "docx_count": docx_count,
        },
    )


@login_required
def delete_page(request, pk):
    if not _can_access_testlog(request.user):
        return HttpResponse("forbidden", status=403)
    obj = get_object_or_404(TestLog, id=pk)
    if not _can_delete_testlog_obj(request.user, obj):                                                                                                                                                     
        return HttpResponse("forbidden", status=403) 
    obj.delete()
    return HttpResponse("deleted")


@login_required
def download_pdf(request, pk):
    if not _can_access_testlog(request.user):
        return HttpResponse("forbidden", status=403)

    obj = get_object_or_404(TestLog, id=pk)
    if not _can_access_testlog_obj(request.user, obj):                                                                                                                                                     
        return HttpResponse("forbidden", status=403) 

    if not obj.protocol:
        return HttpResponse("file not found", status=404)

    try:
        fh = obj.protocol.open("rb")
    except FileNotFoundError:
        return HttpResponse("file not found", status=404)

    filename = Path(obj.protocol.name).name
    return FileResponse(
        fh,
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )
