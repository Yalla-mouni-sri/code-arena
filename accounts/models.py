from django.db import models

# Admin Table
class Admin(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    class Meta:
        db_table = 'admin'

    def __str__(self):
        return self.name

class Coder(models.Model):
    email = models.EmailField(unique=True)
    rollno = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    confirm_password = models.CharField(max_length=255, blank=True, null=True)
    coins = models.IntegerField(default=0)
    is_approved = models.BooleanField(default=False)
    assigned_admin = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_coders')

    class Meta:
        db_table = 'coder'

    def __str__(self):
        return self.rollno
