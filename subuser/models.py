from django.db import models
from django.contrib.auth.models import AbstractUser, User
from django.contrib.auth.hashers import make_password

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	vendor = models.CharField(verbose_name="Поставщик", max_length=200, blank=True)
	uid = models.CharField(verbose_name="БИН",max_length=200, blank=True)
	address = models.TextField(verbose_name="Адрес", max_length=500, blank=True)
	phone = models.CharField(verbose_name="Телефон", max_length=50, blank=True)
	iik = models.CharField(verbose_name="ИИК", max_length=100, blank=True)
	bik = models.CharField(verbose_name="БИК", max_length=100, blank=True)
	fil = models.CharField(verbose_name="Филиал", max_length=200, blank=True, default="")
	sign = models.FileField(upload_to="vendor_sign/", verbose_name="Подпись", null=True, blank=True)
	seal = models.FileField(upload_to="vendor_sign/", verbose_name="Печать", null=True, blank=True)

	def __str__(self):
		return ""
	
	class Meta:
		verbose_name="Профиль"
		verbose_name_plural="Профили"


class SubUser(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='subuser_group_set',
        related_query_name="subuser",
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='subuser_permission_set',
        related_query_name="subuser",
    )

    creator = models.ForeignKey(User, related_name="subuser_user", on_delete=models.CASCADE, verbose_name="Создатель", null=True)
    sign = models.FileField(upload_to="signs/", verbose_name="Подпись")

    # def save(self, *args, **kwargs):
    #     if not self.pk:
    #         self.set_password(self.password)
    #     super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Суб пользователь'
        verbose_name_plural = 'Суб пользователи'



