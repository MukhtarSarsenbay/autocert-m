from django.contrib import admin
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from django.contrib.auth.models import User
from subuser.models import SubUser
from .models import TestLog

@admin.register(TestLog)
class TestLogAdmin(ModelAdmin):
    list_display = ("test_number", "test_date", "car_mark", "vin_last4", "download_pdf_link")
    search_fields = ("test_number", "car_mark", "vin_last4", "creator__username", "name_surname")
    readonly_fields = ("protocol", "isClose", "created_at")
    change_list_template = "admin/testlog/testlog/change_list.html"
    actions = ("clone_selected",)



    def download_pdf_link(self, obj):
        if obj.protocol:
            return format_html(
                '<a class="button" href="/app/testlog/download/{}/">Скачать</a>',
                obj.id
            )
        return "—"

    download_pdf_link.short_description = "PDF"

    FIELD_LABELS = {
        "test_number": "Номер записи",
        "test_date": "Дата",
        "name_surname": "Испытатель",
        "car_mark": "Марка ТС",
        "vin_last4": "VIN (последние 4)",
        "car_category": "Категория ТС",
        "temp_air": "Температура воздуха, °C",
        "humidity": "Влажность, %",
        "pressure": "Атм. давление, кПа",
        "date_day": "День",
        "date_month": "Месяц (текст)",
        "date_year": "Год",
    }

    TOKEN_MAP = {
        "yes": "Да",
        "no": "Нет",
        "na": "Не требуется",
        "ok": "Соот.",
        "bad": "Несоот.",
        "test": "Тест",
        "number": "номер",
        "date": "дата",
        "day": "день",
        "month": "месяц",
        "year": "год",
        "name": "ФИО",
        "surname": "ФИО",
        "car": "ТС",
        "mark": "марка",
        "category": "категория",
        "vin": "VIN",
        "last4": "последние 4",
        "temp": "температура",
        "air": "воздуха",
        "humidity": "влажность",
        "pressure": "давление",
        "abs": "АБС",
        "ax1": "ось 1",
        "ax2": "ось 2",
        "ax3": "ось 3",
        "ax4": "ось 4",
        "ax5": "ось 5",
        "ax": "ось",
        "spare": "запасная",
        "brake": "тормоз",
        "power": "сила",
        "specific": "удельная",
        "pedal": "усилие на органе",
        "diff": "разность",
        "mass": "масса",
        "total": "общая",
        "parking": "стояночная",
        "all": "все",
        "wheel": "колеса",
        "stops": "тормозит",
        "plate": "ГРЗ",
        "pos": "место",
        "front": "передний",
        "rear": "задний",
        "angle": "угол",
        "long": "продольный",
        "vert": "вертикальный",
        "height": "высота",
        "width": "ширина",
        "light": "подсветка",
        "vis": "видимость",
        "down": "вниз",
        "up": "вверх",
        "left": "влево",
        "right": "вправо",
        "nav": "навигация",
        "eCall": "СОС",
        "ring": "прозвонь",
        "tachograph": "тахограф",
        "fog": "ПТФ",
        "lowbeam": "ближний свет",
        "lamp": "сигналы",
        "pos_lamps": "габариты",
        "drl": "ДХО",
        "head": "фароочистка",
        "wash": "омыват.",
        "level": "уровень",
        "auto": "авто",
        "opt": "факульт.",
        "turn": "поворотники",
        "hazard": "аварийка",
        "flash": "мигающий",
        "no_damage": "без повреждений",
        "lamp_sym": "симметрия фар",
        "tyre": "шина",
        "tread": "протектор",
        "glass": "стекла",
        "trans": "светопропускание",
        "mirrors": "зеркала",
        "speedo": "спидометр",
        "seatbelt": "ремни",
        "seats": "сиденья",
        "ext": "наружн.",
        "danger": "опасные",
        "emblems": "эмблемы",
        "deflect": "дефлекторы",
        "bumper": "бамперы",
        "handles": "ручки",
        "jack": "домкрат",
        "bracket": "кронштейн",
        "exhaust": "выпуск",
        "pipe": "труба",
        "steer": "рулевое",
        "safe": "безопасн.",
        "interior": "внутреннее",
        "shelves": "полки",
        "hard": "жесткие элементы",
        "fire": "пожарная",
        "emission": "выбросы",
        "obd": "OBD",
        "eco": "эко",
        "fuel": "топливо",
        "co": "CO",
        "engine": "двигатель",
        "noise": "шум",
        "decel": "замедление",
        "coupling": "сцепное",
        "completeness": "комплектность",
        "state": "состояние",
        "table": "таблица",
    }


    def save_model(self, request, obj, form, change):
        if isinstance(request.user, SubUser):
            obj.creator = request.user
        elif not request.user.is_superuser:
            raise ValidationError("Создавать/изменять может только SubUser.")
        elif obj.creator_id is None:
            raise ValidationError("Для superuser обязательно укажите creator (SubUser).")
        super().save_model(request, obj, form, change)

    def add_view(self, request, form_url="", extra_context=None):
        return redirect("/app/testlog/form/")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return redirect(f"/app/testlog/form/{object_id}/")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if isinstance(request.user, SubUser):
            return qs.filter(creator=request.user)
        if isinstance(request.user, User):
            return qs.filter(creator__creator=request.user)
        return qs.none()

    def _is_obj_in_scope(self, request, obj):
        if request.user.is_superuser:
            return True
        if isinstance(request.user, SubUser):
            return obj.creator_id == request.user.id
        if isinstance(request.user, User):
            return bool(obj.creator_id and obj.creator and obj.creator.creator_id == request.user.id)
        return False

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not (request.user.has_perm("testlog.change_testlog") or request.user.has_perm("testlog.view_testlog")):
            return False
        if obj is None:
            return isinstance(request.user, (SubUser, User))
        return self._is_obj_in_scope(request, obj)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not isinstance(request.user, SubUser):
            return False
        if not request.user.has_perm("testlog.change_testlog"):
            return False
        if obj is None:
            return True
        return self._is_obj_in_scope(request, obj)

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return isinstance(request.user, SubUser) and request.user.has_perm("testlog.change_testlog")

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not isinstance(request.user, SubUser):
            return False
        if obj is None:
            return request.user.has_perm("testlog.change_testlog")
        return self._is_obj_in_scope(request, obj)

    def get_fields(self, request, obj=None):
        fields = [f.name for f in self.model._meta.fields if f.name != "id"]
        return fields

    def label_for_field(self, name):
        if name in self.FIELD_LABELS:
            return self.FIELD_LABELS[name]
        parts = name.split("_")
        translated = [self.TOKEN_MAP.get(p, p) for p in parts]
        return " ".join(translated)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        kwargs["label"] = self.label_for_field(db_field.name)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)
        extra_context = extra_context or {}
        extra_context.update(
            {
                "total_count": qs.count(),
                "pdf_count": qs.filter(isClose=True).count(),
                "docx_count": qs.filter(isClose=False).count(),
            }
        )
        return super().changelist_view(request, extra_context=extra_context)

    def get_fieldsets(self, request, obj=None):
        all_fields = [f.name for f in self.model._meta.fields if f.name != "id"]
        used = set()

        def take(names):
            picked = [n for n in names if n in all_fields]
            used.update(picked)
            return picked

        def take_prefix(prefixes):
            picked = [n for n in all_fields if any(n.startswith(p) for p in prefixes)]
            used.update(picked)
            return picked

        fieldsets = []

        fieldsets.append((
            "Запись",
            {"fields": take(["test_number", "test_date", "name_surname", "car_mark", "vin_last4", "car_category",
                             "creator", "isClose", "protocol", "created_at"])}
        ))

        fieldsets.append((
            "Окружающая среда",
            {"classes": ["tab"], "fields": take(["temp_air", "humidity", "pressure", "date_day", "date_month", "date_year"])}
        ))

        fieldsets.append((
            "Идентификация / ГРЗ",
            {"classes": ["tab"], "fields": take_prefix(["state_", "vin_match_", "plate_"])}
        ))

        fieldsets.append((
            "Тормозная система",
            {"classes": ["tab"], "fields": take_prefix(["abs_", "ax", "brake_", "parking_", "all_wheel_stops_", "effort_"])}
        ))

        fieldsets.append((
            "Освещение и сигнализация",
            {"classes": ["tab"], "fields": take_prefix([
                "lights_", "lamp_", "lowbeam_", "fog_", "rear_fog_", "pos_lamps_", "drl_", "plate_light_",
                "turn_freq_", "hazard_sync_", "flash_mode_", "no_red_front_", "no_white_back_",
                "wash_level_", "head_wash_", "auto_level_", "opt_turn_", "brake_lamp_"
            ])}
        ))

        fieldsets.append((
            "Кузов и травмобезопасность",
            {"classes": ["tab"], "fields": take_prefix([
                "bumper_", "handles_", "ext_", "deflect_", "emblems_", "jack_bracket_", "exhaust_pipe_",
                "hard_parts_", "shelves_", "no_danger_out_", "interior_safe_", "steer_safe_"
            ])}
        ))

        fieldsets.append((
            "Безопасность и оснащение",
            {"classes": ["tab"], "fields": take_prefix([
                "anti_theft_", "seatbelt_", "seats_", "mirrors_", "speedo_", "coupling_", "nav_", "eCall_", "ring_"
            ])}
        ))

        fieldsets.append((
            "Экология / OBD",
            {"classes": ["tab"], "fields": take_prefix([
                "emission_", "obd_", "obd_req_", "obd_ok_", "eco_dev_", "fuel_mod_",
                "co_", "engine_req_", "noise_req_"
            ]) + take(["car_year"])}
        ))

        fieldsets.append((
            "Прочее",
            {"classes": ["tab"], "fields": take_prefix([
                "heater_", "heater_exhaust_", "auto_cutoff_", "body_heat_", "comb_air_", "fire_safe_",
                "no_damage_opt_", "table_", "tyre_", "tread_", "glass_trans_", "date_"
            ])}
        ))

        remaining = [n for n in all_fields if n not in used]
        if remaining:
            fieldsets.append(("Не распределено", {"classes": ["tab"], "fields": remaining}))

        return fieldsets

    @admin.action(description="Клонировать выбранные")
    def clone_selected(self, request, queryset):
        if not request.user.has_perm("testlog.change_testlog"):
            self.message_user(request, "Нет прав для клонирования.", level="error")
            return

        created = 0
        for src in queryset:
            if not self._is_obj_in_scope(request, src):
                continue

            creator = request.user if isinstance(request.user, SubUser) else src.creator
            dst = TestLog.objects.create(creator=creator)

            skip = {"id", "creator", "protocol", "isClose", "created_at"}
            for f in TestLog._meta.fields:
                if f.name in skip:
                    continue
                setattr(dst, f.name, getattr(src, f.name))

            dst.protocol = None
            dst.isClose = False
            dst.save()
            created += 1

        self.message_user(request, f"Склонировано записей: {created}")
