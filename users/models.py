from django.db import models
from django.contrib.auth.models import User
from PIL import Image


# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(blank=True, upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, **kwargs):
        super().save(**kwargs)
        if not self.image or not self.image.storage.exists(self.image.name):
            return
        with Image.open(self.image.path) as image:
            if max(image.size) > 300:
                image.thumbnail((300, 300))
                image.save(self.image.path)
