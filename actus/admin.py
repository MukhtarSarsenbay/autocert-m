from django.contrib import admin
from django.conf import settings
from .models import *
#from import_export.admin import ImportMixin, ExportMixin, ExportActionModelAdmin
from .resource import ButtonResource, ActusResourse, ActusReportResourse
from subuser.models import SubUser, Profile

from django.contrib.auth.models import User, Group

from docxtpl import DocxTemplate

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

import os

from .utils import convert_to

from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from django.utils.html import format_html

from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.admin import ExportActionModelAdmin


from unfold.contrib.filters.admin import (
    RangeDateFilter,
    RangeDateTimeFilter,
)

from rangefilter.filters import (
    DateRangeFilterBuilder,
    DateTimeRangeFilterBuilder,
    NumericRangeFilterBuilder,
    DateRangeQuickSelectListFilterBuilder,
)

from django.utils.translation import gettext_lazy as _
#from .filters import CreatedAtFilter

month_to_string = {
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
	12: "декабря"
}

DIRECTOR_FULL_NAME = "Сайдхакимов Бахтияр Абдухамидович"


def get_act_document_paths(obj):
	output_dir = Path(settings.MEDIA_ROOT) / "act"
	output_dir.mkdir(parents=True, exist_ok=True)

	# User-entered names must not create nested paths or exceed filesystem limits.
	details = f"{obj.frln} - {obj.carVincode}"
	details = " ".join(details.replace("/", "-").replace("\\", "-").split())
	act_name = f"Акт_{obj.number}){details}"[:70].rstrip(" .")
	contract_name = f"Договор_{obj.number}"

	return (
		output_dir / f"{act_name}.docx",
		output_dir / f"{contract_name}.docx",
	)


def get_default_subuser(user, create=False):
	if isinstance(user, SubUser):
		return user
	if isinstance(user, User):
		qs = SubUser.objects.filter(creator=user)
		subuser = qs.filter(is_active=True).order_by("id").first() or qs.order_by("id").first()
		if subuser or not create:
			return subuser

		profile = Profile.objects.filter(user=user).first()
		if not profile or not profile.sign:
			return None

		base_username = f"{user.username}_actus"[:140]
		username = base_username
		suffix = 1
		while SubUser.objects.filter(username=username).exists():
			suffix += 1
			username = f"{base_username}_{suffix}"[:150]

		return SubUser.objects.create_user(
			username=username,
			password=None,
			creator=user,
			is_active=True,
			first_name=user.first_name,
			last_name=user.last_name,
			email=user.email or "",
			sign=profile.sign,
		)
	return None

def get_actus_creator(request, obj, create=False):
	if obj.button_id and obj.button and obj.button.user_id:
		return obj.button.user
	if obj.creator_id:
		return obj.creator
	return get_default_subuser(request.user, create=create)

class ActusUserFilter(admin.SimpleListFilter):
	title = "Пользователь"
	parameter_name = "creator"

	def lookups(self, request, model_admin):
		if request.user.is_superuser:
			# users = Actus.objects.values("creator").annotate(count=models.Count('creator'))
			# buttons = Button.objects.values("user").annotate(count=models.Count('user'))
			# return [(user['creator'], f"{User.objects.get(id=user['creator']).username} ({user['count']}/)")for user in users]

			actus_users_counts = Actus.objects.values('creator').annotate(count=models.Count('creator'))
			# Получаем количество записей для каждого пользователя в таблице Button
			button_users_counts = Button.objects.values('user').annotate(count=models.Count('user'))

			result = []
			for actus_user_count in actus_users_counts:
				user_id = actus_user_count['creator']
				if not user_id:
					continue
				actus_count = actus_user_count['count']
				button_count = next((item['count'] for item in button_users_counts if item['user'] == user_id), 0)
				result.append([user_id, f"{SubUser.objects.get(id=user_id).username}:А{actus_count}/К{button_count}/О{button_count-actus_count}"])
			#print(result)
			return result

		return []

	def queryset(self, request, queryset):
		value = self.value()
		
		if value:
			return queryset.filter(creator=value)

		return queryset

class ButtonUserFilter(admin.SimpleListFilter):
	title = "Пользователь"
	parameter_name = "user"

	def lookups(self, request, model_admin):
		if request.user.is_superuser:
			users = Button.objects.values("user").annotate(count=models.Count('user'))
			userList = []
			for user in users:
				try:
					userList.append((user['user'], f"{SubUser.objects.get(id=user['user']).username} ({user['count']})"))
				except:
					pass
				
			return userList # [(user['user'], f"{SubUser.objects.get(id=user['user']).username} ({user['count']})") for user in users]
		return []

	def queryset(self, request, queryset):
		value = self.value()
		
		if value:
			return queryset.filter(user=value)

		return queryset

class RegisterFilter(admin.SimpleListFilter):
	title = "Статус"
	parameter_name = "user"

	def lookups(self, request, model_admin):
		return (
			('empty', _('-')),
			('registred', _('Регистрация')),
			('called', _('Прозвон')),
		)

	def queryset(self, request, queryset):
		if self.value() == 'empty':
			return queryset.filter(
				isRegistred="-", 
            	isCalled="-"  # Добавьте свои поля, по которым нужно фильтровать
			)
		elif self.value() == 'registred':
			return queryset.filter(
            	isRegistred__lte=10,
			)
		elif self.value() == 'called':
			return queryset.exclude(
            	isRegistred=False, 
            	isCalled=False  # Добавьте свои поля, по которым нужно фильтровать
			)

@admin.register(Actus)
class ActusAdminMenu(ModelAdmin, ExportActionModelAdmin):
	list_display = ("get_number", "get_button", "frln", "carVincode","get_marka", "get_date", "isClose", "isRegistred", "isCalled", "creator")

	list_filter_submit = True  # Submit button at the bottom of the filter
	list_filter = (
    	("createDate", RangeDateFilter),           
    	RegisterFilter, 
    	ActusUserFilter
    )

	search_fields = ("number", "button__iccid", "button__imei", "button__serial", "frln", "carMarka", "carVincode")
	readonly_fields = ("creator", "isClose", "act", "contract",)
	autocomplete_fields = ["button", "creator"]
	resource_classes = [ActusResourse]

	fieldsets = (
      ('Акт', {
          'fields': ('number', 'cost', 'creator')
      }),
    
      ('Кнопка', {
          'fields': ('button',)
      }),
    
      ('Транспорт', {
          'fields': ('carMarka', 'carVincode', 'carYear', 'carColor')
      }),
    
      ('Клиент', {
          'fields': ('frln', 'personUid', 'personNumber', 'personPublic', 'personPhone', 'address')
      }),
    
      ('Файлы', {
          'fields': ('act', 'contract', "app1", "app2", "app3",)
      }),
    )

	@admin.display(ordering='number', description='№')
	def get_number(self, obj):
		return obj.number

	@admin.display(ordering='button__iccid', description='Кнопка')
	def get_button(self, obj):
		return format_html('%s<br/>%s<br/>%s<br/>%s' % (
            obj.button.iccid, obj.button.imei, obj.button.serial, obj.button.hwname))   #"{obj.button.iccid}\n{obj.button.imei}\n{obj.button.serial}"

	@admin.display(ordering='carMarka', description='Марка/Модель машины')
	def get_marka(self, obj):
		return obj.carMarka

	@admin.display(ordering='createDate', description='Дата')
	def get_date(self, obj):
		delta = timedelta(hours=5, minutes=0)
		crt = obj.createDate + delta
		return format_html('%s<br/>%s' % (
           	crt.strftime("%d.%m.%Y"), crt.strftime("%H:%M:%S"))) #obj.createDate.strftime("%d.%m.%Y")

	def get_queryset(self, request):
		qs = super().get_queryset(request)

		if request.user.is_superuser:
			return qs.order_by("-id")
		else:
			if isinstance(request.user, User):
				susers = SubUser.objects.filter(creator=request.user)
				return qs.filter(creator__in=susers)
			else:
				if "autocomplete" in request.path and request.user.has_perm("cert.change_certificates"):
					return qs

				return qs.filter(creator=request.user).order_by("-id")

	def get_readonly_fields(self, request, obj=None):
		if request.user.is_superuser:
			if obj:
				return ['creator', 'isClose', 'act', 'contract']
			return ['isClose', 'act', 'contract']

		# if request.user.username == "qaztehna":
		# 	return ["frln", "personUid", "personNumber", "personPublic", "personPhone", 
		# "address", "app1", "app2", "app3", "act", "contract"]
		

		if obj and obj.isClose:
			return ['number', 'cost', 'button', 
                    'creator', 'isClose', 'act', 'contract', 'app1', 'app2', 'app3']

		return ['creator', 'isClose', 'act', 'contract']

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
		if db_field.name == "creator" and request.user.is_superuser:
			formfield.required = False
			default_user = get_default_subuser(request.user)
			if default_user:
				formfield.initial = default_user.pk
		return formfield

	def save_model(self, request, obj, form, change):
		now = datetime.now()

		creator = get_actus_creator(request, obj, create=True)
		if creator:
			obj.creator = creator
		else:
			raise ValueError("Не найден SubUser для создания акта. Выберите создателя, назначьте кнопку пользователю или заполните подпись в профиле главного admin.")

		try:
			last_object = Actus.objects.filter(creator=obj.creator).latest('number')
			obj.number = obj.number if obj.number else last_object.number + 1
		except:
			obj.number = obj.number if obj.number else 1

		model = obj.__dict__
		model["first_name"] = obj.creator.first_name
		model["last_name"] = obj.creator.last_name
		model["day"] = now.day
		model["month"] = month_to_string.get(now.month)
		model["year"] = now.year
		company_user = obj.creator.creator
		if not company_user and isinstance(request.user, User):
			company_user = request.user
		if not company_user:
			raise ValueError("У создателя акта не указан главный пользователь.")
		profile, _ = Profile.objects.get_or_create(user=company_user)
		model["vendor_phone"] = profile.phone
		model["vendor"] = profile.vendor
		model["vendor_address"] = profile.address
		model["vendor_email"] = company_user.email
		model["vendor_iik"] = profile.iik
		model["vendor_uid"] = profile.uid
		model["vendor_fil"] = profile.fil
		model["vendor_bik"] = profile.bik
		model["vendor_frln"] = DIRECTOR_FULL_NAME
		
		#model["personPublic"] = model["personPublic"].strftime("%d.%m.%Y")
		model = {**model, **obj.button.__dict__}
		if model.get("personPublic"):
			model["personPublic"] = model["personPublic"].strftime("%d.%m.%Y")

		if obj.button.imei == None:
			model["imei"] = ""
		if obj.button.serial == None:
			model["serial"] = ""

		act_path, contract_path = get_act_document_paths(obj)
		act = DocxTemplate(BASE_DIR / "media/ref/act.docx")

		act.render(model)
		act.save(act_path)
		act_pdf_path = convert_to(act_path)


		if request.user.username == "qaztehna":
			act_contract = DocxTemplate(BASE_DIR / f"media/ref/act_contract_qaz.docx")
		else:
			act_contract = DocxTemplate(BASE_DIR / f"media/ref/act_contract.docx")

		act_contract.render(model)
		act_contract.save(contract_path)
		contract_pdf_path = convert_to(contract_path)

		

		obj.act = act_pdf_path.relative_to(settings.MEDIA_ROOT).as_posix()
		obj.contract = contract_pdf_path.relative_to(settings.MEDIA_ROOT).as_posix()
		obj.isClose = True

		super().save_model(request, obj, form, change)

	class Media:
		js = (
			'admin/js/jquery.init.js',
			'js/custom_list_color.js',
		)

@admin.register(ActusPending)
class ActusReportMenu(ModelAdmin, ExportActionModelAdmin):
	list_display = ("get_number", "get_button", "frln", "carVincode","get_marka", "get_date", "isClose", "isRegistred", "isCalled", "creator")
	list_filter_submit = True  # Submit button at the bottom of the filter

	list_filter = (
    	("createDate", RangeDateFilter),           
    	RegisterFilter, 
    	ActusUserFilter
    )

	search_fields = ("number", "button__iccid", "button__imei", "button__serial", "frln", "carMarka", "carVincode")
	readonly_fields = ("creator", "isClose", "act", "contract",)
	#raw_id_fields = ["button"]
	autocomplete_fields = ["button", "creator"]
	resource_classes = [ActusReportResourse]

	fieldsets = (
      ('Акт', {
          'fields': ('number', 'cost', 'creator')
      }),
    
      ('Кнопка', {
          'fields': ('button',)
      }),
    
      ('Транспорт', {
          'fields': ('carMarka', 'carVincode', 'carYear', 'carColor')
      }),
    
      ('Клиент', {
          'fields': ('frln', 'personUid', 'personNumber', 'personPublic', 'personPhone', 'address')
      }),
    
      ('Файлы', {
          'fields': ('act', 'contract', "app1", "app2", "app3",)
      }),
    
    )

	@admin.display(ordering='number', description='№')
	def get_number(self, obj):
		return obj.number

	@admin.display(ordering='button__iccid', description='Кнопка')
	def get_button(self, obj):
		return format_html('%s<br/>%s<br/>%s<br/>%s' % (
            obj.button.iccid, obj.button.imei, obj.button.serial, obj.button.hwname))   #"{obj.button.iccid}\n{obj.button.imei}\n{obj.button.serial}"

	@admin.display(ordering='carMarka', description='Марка/Модель машины')
	def get_marka(self, obj):
		return obj.carMarka

	@admin.display(ordering='createDate', description='Дата')
	def get_date(self, obj):
		delta = timedelta(hours=5, minutes=0)
		crt = obj.createDate + delta
		return format_html('%s<br/>%s' % (
           	crt.strftime("%d.%m.%Y"), crt.strftime("%H:%M:%S"))) #obj.createDate.strftime("%d.%m.%Y")

	def get_queryset(self, request):
		qs = super().get_queryset(request)


		if request.user.is_superuser:
			return qs.order_by("-id")
		else:
			if isinstance(request.user, User):
				susers = SubUser.objects.filter(creator=request.user)
				return qs.filter(creator__in=susers)
			else:
				return qs.filter(creator=request.user).order_by("-id")

	def get_readonly_fields(self, request, obj=None):
		if request.user.is_superuser:
			if obj:
				return ['creator', 'isClose', 'act', 'contract']
			return ['isClose', 'act', 'contract']

		if obj and obj.isClose:
			return ['number', 'cost', 'button', 
                    'creator', 'isClose', 'act', 'contract', 'app1', 'app2', 'app3']

		return ['creator', 'isClose', 'act', 'contract']

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
		if db_field.name == "creator" and request.user.is_superuser:
			formfield.required = False
			default_user = get_default_subuser(request.user)
			if default_user:
				formfield.initial = default_user.pk
		return formfield



@admin.register(Button)
class ButtonAdminMenu(ModelAdmin, ImportExportModelAdmin):
	import_form_class = ImportForm
	export_form_class = ExportForm
	list_display = ("iccid","imei", "serial", "hwname", "user", "createDate")
	list_filter_submit = True
	list_filter = ("hwname", ("createDate", RangeDateFilter), ButtonUserFilter,)
	search_fields = ("iccid", "imei", "serial", "hwname")
	ordering = ["iccid"]
	readonly_fields = ("user",)
	autocomplete_fields = ["user"]
	resource_class = ButtonResource

	def get_queryset(self, request):
		qs = super().get_queryset(request)

		if "autocomplete" in request.path:
			qs = qs.filter(actus__isnull=True)
			if request.user.is_superuser:
				return qs
			if isinstance(request.user, User):
				return qs.filter(user__creator=request.user)
			return qs.filter(user=request.user)

		if request.user.is_superuser:
			return qs
		if isinstance(request.user, User):
			return qs.filter(user__creator=request.user)
		return qs.filter(user=request.user)

	def get_readonly_fields(self, request, obj=None):
		if request.user.is_superuser:
			return ()
		return ("user",)

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
		if db_field.name == "user" and request.user.is_superuser:
			formfield.required = False
			default_user = get_default_subuser(request.user)
			if default_user:
				formfield.initial = default_user.pk
		return formfield

	# def get_import_resource_kwargs(self, request, *args, **kwargs):
	# 	kwargs = super().get_resource_kwargs(request, *args, **kwargs)
	# 	kwargs.update({"user": request.user})
	# 	return kwargs

	def save_model(self, request, obj, form, change):
		if isinstance(request.user, SubUser):
			obj.user = request.user
		elif isinstance(request.user, User):
			default_user = get_default_subuser(request.user, create=True)
			if default_user and not obj.user_id:
				obj.user = default_user
		super().save_model(request, obj, form, change)
