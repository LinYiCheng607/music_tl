from django.contrib.auth.forms import UserCreationForm
from .models import MyUser
from django import forms


class MyUserCreationForm(UserCreationForm):
    # 重写初始化函数，设置自定义字段password1和password2的样式和属性
    def __init__(self, *args, **kwargs):
        super(MyUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'class': 'txt tabInput', 'placeholder': '请输入包含4-16位数字/字母/特殊符号（空格除外）的密码'})
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'class': 'txt tabInput', 'placeholder': '请重复输入密码'})

    class Meta(UserCreationForm.Meta):
        model = MyUser
        # 设置模型界面添加模型字段：手机号码和密码
        fields = UserCreationForm.Meta.fields + ('mobile',)
        # 设置模型字段的样式和属性
        widgets = {
            'mobile': forms.widgets.TextInput(attrs={'class': 'txt tabInput', 'placeholder': '请输入手机号'}),
            'username': forms.widgets.TextInput(attrs={'class': 'txt tabInput', 'placeholder': '请输入用户名'}),
        }


