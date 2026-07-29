from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import BaseUserManager
# from cloudinary.models import CloudinaryField



class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        #Role implemneted
        extra_fields.setdefault("role", User.Role.SUPER_ADMIN)  # or "ADMIN"
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
     # Login info
    
    username = models.CharField(max_length=50,unique=True)  
    
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)

    is_approved = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)



    class Role(models.TextChoices):
        USER = "USER", "User"
        FINANCE = "FINANCE", "Finance Admin"
        SUPPORT = "SUPPORT", "Support"
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=200, blank=True, null=True)
    home_address = models.CharField(max_length=200, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    last_active = models.DateTimeField(null=True, blank=True)
    # avatar =CloudinaryField('image', null=True, blank=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    # gender


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email


