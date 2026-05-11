from django.contrib import admin
from .models import Store, StoreImage

from unfold.admin import ModelAdmin, StackedInline
from django.utils.html import format_html
from unfold.contrib.import_export.admin import ExportActionModelAdmin
from .resource import StoreResource

from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm


class StoreImageInline(StackedInline):
	model = StoreImage
	max_num = 10
	extra = 0
	#can_delete = False

@admin.register(Store)
class StoreAdminMenu(ModelAdmin, ImportExportModelAdmin):
	list_display = ("id", "name", "brand", "model", "serial", "invnumber", "creator","price", "year_check","entity","file_link")
	search_fields = ("name", "brand", "model", "serial", "price","entity", "creator")

	list_filter = (
    	'entity',
    )

	inlines = [StoreImageInline,]
	#autocomplete_fields = ["creator"]
	readonly_fields = ("qrcode", "counter")

	resource_class = StoreResource

	import_form_class = ImportForm
	export_form_class = ExportForm

	fieldsets = (
      ('Генерация QR KODE', {
          'fields': ("counter", 'qrcode','document','date',)
      }),
    
      ('Информация о ТМЦ', {
          'fields': ('typ', 'name', 'brand', 'model', 'serial', 'invnumber', 'recordType', 'amount', 'unitPrice', 'price')
      }),
    
      ('Местоположение ТМЦ', {
          'fields': ('entity', 'location',)
      }),
    
      ('Выберите пользователя', {
          'fields': ('creator',)
      }),
    )

	def file_link(self, obj):
		if obj.document:
			return format_html(f"<a href='https://cms.labauto.kz/media/{obj.document}' style='color: #3884ff;' target='_blank' rel='noopener'>Посмотреть</a>")
		return None

	
	def save_model(self, request, obj, form, change):
		if request.user.is_superuser: return
		#obj.creator = request.user
		super().save_model(request, obj, form, change)

	class Media:
		js = (
        	#"//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js",
        	'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js',
        	'https://cdn.jsdelivr.net/npm/qr-scanner@1.4.2/qr-scanner.min.js',
        	'js/store_script.js',
        )