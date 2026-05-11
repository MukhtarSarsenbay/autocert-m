from django import forms
#from unfold.widgets import UnfoldAdminPasswordInput
from .models import Certificates


class CertForm(forms.ModelForm):
    class Meta:
        model = Certificates
        fields = "__all__"
        widgets = {
            'personPassword': forms.PasswordInput(render_value=True),
        }