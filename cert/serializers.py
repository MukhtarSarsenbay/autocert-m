from rest_framework import serializers
from .models import Certificates

class CertModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificates
        fields = "__all__"

class ImageModelSerializer(serializers.ModelSerializer):
	class Meta:
		model = Certificates
		fields = ["signature"]
