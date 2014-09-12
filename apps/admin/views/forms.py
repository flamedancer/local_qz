#-*- coding:utf-8 -*-
from django import forms

from apps.admin import admin_configuration
import apps.admin.auth

class ModeratorCreationForm(forms.Form):
    """
        新建管理员表单
    """
    username = forms.CharField(label="帐号",max_length=30,help_text = r"必须,30个字符以内")
    email = forms.EmailField(label="邮箱",help_text=u"请输入管理员联系邮箱地址")
    password1 = forms.CharField(label=u"密码", widget=forms.PasswordInput)
    password2 = forms.CharField(label=u"确认密码", widget=forms.PasswordInput,
        help_text = "请输入与上面密码一致的密码。")

    #（角色，描述）
    permissions = forms.MultipleChoiceField(choices=[(perm["code"], perm["description"]) for key,perm in admin_configuration.all_permissions.items()])

    def clean_username(self):
        username = self.cleaned_data['username']

        if apps.admin.auth.get_mid_by_username(username) is not None:
            raise forms.ValidationError("该帐号已存在，请重新选择.")
        else:
            return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError("确认密码与密码不符，请重新输入.")
        return password2

class ModeratorManageForm(forms.Form):
    """
    管理员管理表单
    """
    password1 = forms.CharField(label=u"密码", required=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label=u"确认密码", required=False, widget=forms.PasswordInput,
            help_text = u"请输入与上面密码一致的密码。")

    permissions = forms.MultipleChoiceField(choices = [(perm["code"],perm["description"]) for key,perm in admin_configuration.all_permissions.items()])


    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(u"确认密码与密码不符，请重新输入.")
        return password2

class ModeratorResetPasswordForm(forms.Form):
    """
        管理员自己修改密码表单
    """
    password1 = forms.CharField(label=u"密码", widget=forms.PasswordInput)
    password2 = forms.CharField(label=u"确认密码", widget=forms.PasswordInput,
            help_text = u"请输入与上面密码一致的密码。")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(u"确认密码与密码不符，请重新输入.")
        return password2


