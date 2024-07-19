from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager

# Create a custom user model
class User(AbstractBaseUser, PermissionsMixin):
    TITLE_CHOICES = (
        ('Prof.', 'Prof.'),
        ('Dr.', 'Dr.'),
        ('Mr.', 'Mr.'),
        ('Mrs.', 'Mrs.'),
    )
    
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female')
    )
    
    EXECUTIVE_POSITION_CHOICES = (
        ('President', 'President'),
        ('Vice President', 'Vice President'),
        ('Secretary', 'Secretary'),
        ('Treasurer', 'Treasurer'),
        ('Committee Member', 'Committee Member'),
    )

    title = models.CharField(max_length=5, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30)
    other_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    profile_pic = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=50, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # Executive-specific fields
    executive_image = models.ImageField(upload_to='executive_images/', blank=True, null=True)
    executive_position = models.CharField(max_length=30, choices=EXECUTIVE_POSITION_CHOICES, blank=True, null=True)
    fb_profile_url = models.URLField(blank=True, null=True)
    twitter_profile_url = models.URLField(blank=True, null=True)
    linkedin_profile_url = models.URLField(blank=True, null=True)
    date_appointed = models.DateField(null=True, blank=True)
    date_ended = models.DateField(null=True, blank=True)
    is_active_executive = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['title', 'first_name', 'last_name', 'gender']
    
    def get_full_name(self):
        if self.other_name:
            return f'{self.title} {self.first_name} {self.other_name} {self.last_name}'
        else:
            return f'{self.title} {self.first_name} {self.last_name}'
    
    def get_short_name(self):
        return self.first_name
    
    def get_profile_pic_url(self):
        return self.profile_pic.url if self.profile_pic else None
    
    def is_acting(self):
        return self.groups.filter(name__in=['President', 'Vice President', 'Secretary', 'Treasurer', 'Committee Member']).exists() and self.is_active_executive and self.date_ended is None

    def __str__(self):
        return self.get_full_name()
    
    class Meta:
        permissions = [
            ('view_dashboard', 'Can view dashboard'),
            ('view_admins', 'Can view admins'),
            ('view_members', 'Can view members'),
            ('view_executives', 'Can view executives'),
        ]