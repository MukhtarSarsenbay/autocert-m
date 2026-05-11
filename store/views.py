from django.shortcuts import render
from .models import Store, StoreImage
from datetime import datetime

def getStoreQR(request, code):
	result = Store.objects.filter(qrcode=code)
	if len(result) > 0:
		images = StoreImage.objects.filter(store=result[0]).values()
		result[0].counter = result[0].counter + 1
		result[0].save()

		check = False

		if datetime.now().date() > result[0].date:
			check = True

		return render(request, 'qr/index.html', {"res": result[0].__dict__, "images": images, "check": check})
	return render(request, 'qr/index.html', {})