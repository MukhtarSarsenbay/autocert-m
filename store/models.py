from django.db import models
from subuser.models import SubUser
import uuid
from django.utils.html import format_html
from datetime import datetime
from datetime import timedelta

class StoreImage(models.Model):
  image = models.ImageField(upload_to='store/') # здесь укажите куда сохранять изображения
  store = models.ForeignKey('Store', on_delete=models.CASCADE, related_name="images")

class Store(models.Model):
	RECORD_TYPE_CHOICES = (
    	("ONE", "Единичное ТМЦ"),
    	("MORE", "Количественное ТМЦ"),
	)
	
	# Данные для товара
	typ = models.CharField(max_length=255, verbose_name="Тип ТМЦ")
	name = models.CharField(max_length=255, verbose_name="Название ТМЦ/Инструмента", default="")
	brand = models.CharField(max_length=255, verbose_name="Бренд", default="")
	model = models.CharField(max_length=255, verbose_name="Модель", default="")
	serial = models.CharField(max_length=255, verbose_name="Серейний номер", default="")
	invnumber = models.CharField(max_length=8, default="00000000", verbose_name="Инвертарный номер")

	# Цена и тип
	recordType = models.CharField(max_length=4, verbose_name="Тип учета", choices=RECORD_TYPE_CHOICES, default="one")
	amount = models.IntegerField(verbose_name="Количество", blank=True, default=1)
	unitPrice = models.DecimalField(verbose_name="Цена за ед.", 
                                    max_digits = 10, 
                                    decimal_places=2, 
                                    blank=True, 
                                    default=1) 
	price = models.DecimalField(verbose_name="Цена", max_digits = 10, decimal_places=2, default=1) 

	# Местоположение
	entity = models.CharField(max_length=255, verbose_name="Объект")
	location = models.CharField(max_length=255, verbose_name="Локация")

	document = models.FileField(verbose_name="Документ", upload_to='store/', default="")

	# Создатель и Ответсвтенный
	#creator = models.ForeignKey(SubUser, on_delete=models.CASCADE, verbose_name="Ответсвтенный")
	creator = models.CharField(max_length=255, verbose_name="Ответсвтенный", default="Асылхан")
	date = models.DateField(verbose_name="Срок действия поверки СИ", null=True)

	qrcode =  models.UUIDField(default=uuid.uuid4, editable=False)#models.TextField(default=uuid.uuid4(),blank=True, editable=False, verbose_name="QR CODE GENERATOR")
	counter = models.IntegerField(verbose_name="Счетчик",default=0)

	def year_check(self):
		if self.date is None: return self.date
		#month = 1 if self.date.month - 1 <= 0 else self.date.month - 1

		prev_month_date = self.date.replace(day=1) - timedelta(days=1)

		#low = self.date.replace(month=month)
		if datetime.now().date() > prev_month_date:
			return format_html('<span style="color: red">{}</span>',prev_month_date)
		return prev_month_date

	def __str__(self):
		return f"{self.name}"
	
	class Meta:
		verbose_name = "Склад"
		verbose_name_plural=verbose_name
	