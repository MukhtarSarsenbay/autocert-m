from django.contrib import admin
from .models import *
from django.contrib.auth.models import User

from rangefilter.filters import (
    DateRangeFilterBuilder,
    DateTimeRangeFilterBuilder,
    NumericRangeFilterBuilder,
    DateRangeQuickSelectListFilterBuilder,
)

from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.admin import ExportActionModelAdmin

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from unfold.decorators import action
from django.http import HttpRequest
from typing import Union

from .resource import CertResourse
from subuser.models import SubUser
from .forms import CertForm
from django.utils.html import format_html, format_html_join 

otts = [
	"DN8",
	"ASV50",
	"XV50",
	"ASV50L",
	"CN7",
	"IK","RG3","JK1","JX1",
	"GSU45","GSU55","XU5","US4","KA4",
	"HM","HM2", "DL3","TF","SP2",
	"MQ4","UM","NQ5","LX2",
	"J30","TM","LF","NX4", "J15", "J15T", "J150",
	"JF", "AXVA70", "JL6482D06", "JA", "TQ",
	"DM", "AD", "ADA",
]

class OttsFilter(admin.SimpleListFilter):
	title = "ОТТС"
	parameter_name = "otts"

	def lookups(self, request, model_admin):
		lookups = [('in', 'есть'), ('not_in', 'нет')]
		return lookups

	def queryset(self, request, queryset):
		value = self.value()
		if value == 'in':
			return queryset.filter(carType__in=otts)
		elif value == "not_in":
			return queryset.exclude(carType__in=otts)
	
		return queryset

class CarMarkaFilter(admin.SimpleListFilter):
    title = 'Марка'
    parameter_name = 'carMarka'

    def lookups(self, request, model_admin):
        # Возвращаем список категорий
        # categories = Certificates.objects.values_list('carMarka', flat=True).distinct()
        # return [(category, category) for category in categories]
        categories = model_admin.get_queryset(request).values('carMarka').annotate(count=models.Count('carMarka'))
        categories = reversed(sorted(categories, key=lambda d: d['count']))
        return [(category['carMarka'], f"{category['carMarka']} ({category['count']})") for category in categories]

    def queryset(self, request, queryset):
        # Фильтруем объекты по выбранной категории
        value = self.value()
        if value:
            return queryset.filter(carMarka=value)
        return queryset

class CarModelFilter(admin.SimpleListFilter):
    title = 'Модель'
    parameter_name = 'carModel'

    def lookups(self, request, model_admin):
        # Возвращаем список категорий
        # categories = Certificates.objects.values_list('carMarka', flat=True).distinct()
        # return [(category, category) for category in categories]
        categories = model_admin.get_queryset(request).values('carModel').annotate(count=models.Count('carModel'))
        categories = reversed(sorted(categories, key=lambda d: d['count']))
        return [(category['carModel'], f"{category['carModel']} ({category['count']})") for category in categories]

    def queryset(self, request, queryset):
        # Фильтруем объекты по выбранной категории
        value = self.value()
        if value:
            return queryset.filter(carModel=value)
        return queryset

class CarTypeFilter(admin.SimpleListFilter):
    title = 'Тип тс'
    parameter_name = 'carType'

    def lookups(self, request, model_admin):
        # Возвращаем список категорий
        # categories = Certificates.objects.values_list('carMarka', flat=True).distinct()
        # return [(category, category) for category in categories]
        categories = model_admin.get_queryset(request).values('carType').annotate(count=models.Count('carType'))
        categories = reversed(sorted(categories, key=lambda d: d['count']))
        return [(category['carType'], f"{category['carType'].upper()} ({category['count']})") for category in categories]

    def queryset(self, request, queryset):
        # Фильтруем объекты по выбранной категории
        value = self.value()
        if value:
            return queryset.filter(carType=value)
        return queryset

# class MyClassBasedView(UnfoldModelAdminViewMixin, TemplateView):
#     title = "Custom Title"  # required: custom page header title
#     permission_required = () # required: tuple of permissions
#     template_name = "cert/change_cert_form.html"

@admin.register(Certificates)
class CertAdminMenu(ModelAdmin, ExportActionModelAdmin):
	#compressed_fields = True
	#warn_unsaved_form = True
	#list_filter_submit = True
	#list_horizontal_scrollbar_top = True

	list_display = ("sbkts", "certCreateDate", "carVin", "carMarka", "carModel", "carType", "frln", "creator", "isClose")
	readonly_fields = ("decision", "application", "contract", "protocol", "protocol_new","logbook", "testlog_records", "expert", "conclusion", "journal_c00395", "protocol_c00395", "isClose", "signature")
	search_fields  = ("sbkts", "carVin", "carMarka", "carModel", "carType","creator__username", "lastName", "firstName", "middleName", "personId",)
	list_filter = (("certCreateDate", DateRangeFilterBuilder()),
    				"testType", "isClose",
                   
                   #OttsFilter, CarMarkaFilter, CarModelFilter, CarTypeFilter,
    )
	autocomplete_fields = ["actus"]

	#form = CertForm

	actions = ['copy_selected']
	resource_classes = [CertResourse]

	#compressed_fields = True


	fieldsets = (
      ('Сертификат', {
          'fields': ('sbkts', 'certCreateDate', 'actus')
      }),
      (_("Applicant"), {
      	  "classes": ["tab"],
          'fields': [('lastName', 'firstName', 'middleName'), 'personId', 'personAddress', 'personPhone', 'personEmail', 'personPassword',]
      }),
      (_("Transport"), {
      	  "classes": ["tab"],
          'fields': ['carMarka', 'carModel', 
                     'carType', 'carVin',
                     'carYear', 'carCategory', 'carEco', 
                     'carManufacturer',
                     'carWF', 'carVLD', 'carEngLoc',
                     'сarCabin', 'carDLS',
                     'carBody', 'carNSFR',  'testMass', 'testMaxMass', 
                     ('carLength', 'carWidth', 'carHeight'), 'carBase',
                     'carWT', 'carEngine',
                     'carEngineCount', 'carEngineVolume', 'carEngineCR',
                     'carEnginePower', 'testFuelType', 'carPowerType', 'carIgnitionType',
                     'carEANS', 'carTransmission', 'carClutches',
                     'carGearbox', 'carSusFront', 'carSusRear', 'carSC',
                     'carBrakeWork', 'carBrakeSpear', 'carBrakeParking', 'testTM', 'carMarkRefPlL', 'carMarkRefPlH'
                    ]
      }),
      (_("Trailer"), {
      	  "classes": ["tab"],
          'fields': ["carSusTree","carSusFour", "carSusFive", "carSusSix", "carSusSeven", "carSusEight", "device",],
      }),
      (_("Tests"), {
          "classes": ["tab"],
          'fields': [
          'testType', 'testLocation', ('testTemp', 'testHum', 'testPress'),
          ('testLTLG', 'testLTWG', 'testLTRG'),
          #  'testBWD', 'testSPB', 'testCBDR', 'testCBDP', 'testNNCF',
          # 'testNNCR', 'testFLW', 'testFRW', 'testRLW', 'testRRW',
          # 'testMass', 'testMaxMass', 'testFAW', 'testRAW', 'testEF',
          # 'testCoMin', 'testCoMax', 'testEN', 'testLNR', 'testLNL',
          # 'testMPLA', 'testFPM', 'testTSP', 'testLT', 'testTH', 'testTM',
          # 'testASR', 'testBD', 'testSD', 'testBSAT'
          'testBWD',
          'testSPB',
           'testCBDR',
          'testCBDP',
          ('testCoMin', 'testCoMax'),
           'testEN',
           'testEF',
           'testBD',
           'testSD',
           'testBSAT',
           # 'testFAW',
           # 'testRAW',
          ('testFW', 'testSW'),
          ('testTW', 'testFOW', 'testFIW'),
          #('testNNCR', 'testNNCF'),
          'testALN',
          ('testLNR', 'testLNL'),
          ('testMPLAR', 'testMPLAL', 'testMPLA'),
          'testFPM',
          # 'testASR',
          # 'testTM',
          'testTH',
          'testTSP',
          # 'testLT',
          'testMAUP',
          'testMALEFT',
          'testMARIGHT',
		  #'testUsilie',
		  #'test_depth',
		  #'test_noise',
		  #'carBase',
		  #('testWheelFront', 'testWheelBack'),
          ]
      }),
    
      # (_("Video"), {
      # 	  "classes": ["tab"],
      #     'fields': ['linkVideo',]
      # }),
    
      (_("Appendices"), {
      	  "classes": ["tab"],
          'fields': ['app1', 'app2', 'app3', 'app4', 'app5', 'app6', 'app7', 'app8', 'app9', 'app10']
      }),
    	
    
      (_("Documents"), {
          "classes": ["tab"],
          'fields': ['decision', 'application', 'contract', 'protocol','protocol_new', 'logbook','testlog_records', 'expert', 'conclusion', 'journal_c00395', 'protocol_c00395', 'signature', 'isClose']
      }),
    
    )
	
	# def get_urls(self):
	# 	# IMPORTANT: model_admin is required
	# 	custom_view = self.admin_site.admin_view(
	# 		MyClassBasedView.as_view(model_admin=self)
	# 	)
	# 	return super().get_urls() + [
	# 		path(
	# 			"custom-url-path", custom_view, name="custom_name"
	# 		),
	# 	]

	#change_form_before_template = "cert/change_cert_form.html"


	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return self._filter_queryset_for_user(qs, request.user).order_by("-id")
		# qs = super().get_queryset(request)
		# if request.user.is_superuser:
		# 	return qs
		# if isinstance(request.user, User):
		# 	susers = SubUser.objects.filter(creator=request.user)
		# 	return qs.filter(creator__in=susers)
		# return qs.filter(creator=request.user)

	def _filter_queryset_for_user(self, qs, user):                                                                                                                                                                           
		if not user or not user.is_authenticated:                                                                                                                                                                            
			return qs.none()                                                                                                                                                                                                 
																																																							
		if user.is_superuser:                                                                                                                                                                                                
			return qs                                                                                                                                                                                                        
																																																							
		# Manager (SubUser): see all certs in same company (same creator)                                                                                                                                                    
		if isinstance(user, SubUser):                                                                                                                                                                                        
			if not user.creator_id:                                                                                                                                                                                          
				return qs.none()                                                                                                                                                                                             
			return qs.filter(creator__creator_id=user.creator_id)                                                                                                                                                            
																																																							
		# Company account (auth.User): see all certs of its managers                                                                                                                                                         
		if isinstance(user, User):                                                                                                                                                                                           
			return qs.filter(creator__creator_id=user.id)                                                                                                                                                                    
																																																							
		return qs.none()                                                                                                                                                                                                     
                                                                                                                                                                                                                           
	def _is_obj_in_scope(self, request, obj):                                                                                                                                                                                
		if obj is None:                                                                                                                                                                                                      
			return True                                                                                                                                                                                                      
		if request.user.is_superuser:                                                                                                                                                                                        
			return True                                                                                                                                                                                                      
																																																							
		if not obj.creator_id or not obj.creator:                                                                                                                                                                            
			return False                                                                                                                                                                                                     
																																																							
		if isinstance(request.user, SubUser):                                                                                                                                                                                
			return bool(request.user.creator_id and obj.creator.creator_id == request.user.creator_id)                                                                                                                       
																																																							
		if isinstance(request.user, User):                                                                                                                                                                                   
			return obj.creator.creator_id == request.user.id                                                                                                                                                                 
																																																							
		return False    
                                                                                                                                                           
	def testlog_records(self, obj):
		vin = (obj.carVin or "").strip().upper()
		if not vin:
			return "VIN не указан"

		try:
			from testlog.models import TestLog
		except Exception:
			return "Модуль 'Записи об испытаниях' недоступен"

		records = TestLog.objects.filter(vin_last4__iexact=vin).order_by("-id")[:10]
		if not records:
			return "По VIN записи не найдены"

		rows = []
		for rec in records:
			label = rec.test_number or f"ID {rec.id}"
			if rec.protocol:
				rows.append((format_html('<a href="{}" target="_blank">{}</a>', rec.protocol.url, label),))
			else:
				rows.append((f"{label} (PDF не сформирован)",))

		return format_html_join(format_html("<br/>"), "{}", rows)

	testlog_records.short_description = "Записи об испытаниях (по VIN)"
                                                                                                                                                                                                        

# 	def has_view_permission(self, request, obj=None):
# 		# if request.user.is_superuser:
# 		# 	return True
# 		# return True
# 		# if obj is None:
# 		# 	return True
# 		# if isinstance(request.user, User):
# 		# 	return obj.creator and obj.creator.creator_id == request.user.id
# 		# return obj.creator_id == request.user.id
		

# 	def has_change_permission(self, request, obj=None):
# 		if request.user.is_superuser:
# 			return True
# 		return True
# 		# if obj is None:
# 		# 	return True
# 		# if isinstance(request.user, User):
# 		# 	return obj.creator and obj.creator.creator_id == request.user.id
# 		# return obj.creator_id == request.user.id
	def has_view_permission(self, request, obj=None):                                                                                                                                                                        
		if request.user.is_superuser:                                                                                                                                                                                        
			return True                                                                                                                                                                                                      
																																																							
		# Keep compatibility with existing permission setup                                                                                                                                                                  
		if not (                                                                                                                                                                                                             
			request.user.has_perm("cert.view_certificates")                                                                                                                                                                  
			or request.user.has_perm("cert.change_certificates")                                                                                                                                                             
		):                                                                                                                                                                                                                   
			return False                                                                                                                                                                                                     
																																																							
		if obj is None:                                                                                                                                                                                                      
			return isinstance(request.user, (SubUser, User))                                                                                                                                                                 
																																																							
		return self._is_obj_in_scope(request, obj)                                                                                                                                                                           
																																																							
	def has_change_permission(self, request, obj=None):                                                                                                                                                                      
		if request.user.is_superuser:                                                                                                                                                                                        
			return True                                                                                                                                                                                                      
																																																							
		if not request.user.has_perm("cert.change_certificates"):                                                                                                                                                            
			return False                                                                                                                                                                                                     
																																																							
		if obj is None:                                                                                                                                                                                                      
			return isinstance(request.user, (SubUser, User))                                                                                                                                                                 
																																																							
		return self._is_obj_in_scope(request, obj)

	def has_delete_permission(self, request, obj=None):                                                                                                                                                                      
		if request.user.is_superuser:                                                                                                                                                                                        
			return True                                                                                                                                                                                                      
																																																							
		if not request.user.has_perm("cert.delete_certificates"):                                                                                                                                                            
			return False                                                                                                                                                                                                     
																																																							
		if obj is None:                                                                                                                                                                                                      
			return isinstance(request.user, (SubUser, User))                                                                                                                                                                 
																																																							
		return self._is_obj_in_scope(request, obj)  

	def copy_selected(self, request, queryset):
		for obj in queryset:
			# Создаем копию объекта, исключая поле с первичным ключом
			obj.pk = None
			obj.actus = None
			obj.app1 = None
			obj.app2 = None
			obj.app3 = None
			obj.app4 = None
			obj.app5 = None
			obj.app6 = None
			obj.app7 = None
			obj.app8 = None
			obj.app9 = None
			obj.app10 = None
			obj.save()
	copy_selected.short_description = "Клонировать модель"

	def save_model(self, request, obj, form, change):                                                                                                                                                                                                                                                          
		if not change and isinstance(request.user, SubUser):                                                                                                                                                                 
			obj.creator = request.user  																																																		                                                                                                                																																																					
		super().save_model(request, obj, form, change)  

	def frln(self, obj):
		middleName = ""
		if obj.middleName is not None:
			middleName = obj.middleName
		return f"{obj.lastName}, {obj.firstName} {middleName}"	

	frln.short_description = 'ФИО'
    #get_author.admin_order_field = 'book__author'

	class Media:
		js = (
        	"//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js",
        	"js/custom_script.js",
        )

