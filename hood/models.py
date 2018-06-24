from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.dispatch import receiver

# Create your models here.
class Profile(models.Model):
    """
    Profile class that defines objects of each profile
    """
    profile_photo = models.ImageField(
        upload_to='profiles/', verbose_name='Pick Profile Pic', null=True)
    profile_owner = models.OneToOneField(User)
    profile_id = models.CharField(max_length=8, verbose_name="Id Number",
                                  validators=[
                                      RegexValidator(
                                          regex=r'^(\d{7}|\d{8})$',
                                          message='ID number must have eight numeric characters'
                                      ),
                                  ])
    profile_hood = models.ForeignKey('Hood', null=True)
    email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return str(self.profile_owner)

    def save_profile(self):
        self.save()

    def delete_profile(self):
        self.delete()

    def delete(self):
        """
        this method prevents a user from deleting their own profile & overrides the other default delete methods
        """
        self.email_confirmed = False
        self.save()

    @classmethod
    def update_profile_photo(cls, user_id, value):
        """
        method that updates a user's profile photo
        """
        cls.objects.filter(profile_owner=user_id).update(profile_photo=value)

    @classmethod
    def update_profile_hood(cls, user_id, value):
        """
        method that updates a user's neighbourhood
        """
        cls.objects.filter(profile_owner=user_id).update(profile_hood=value)

    @classmethod
    def find_profile_by_name(cls, username):
        """
        method that returns a user's profile by name
        """
        profile = cls.objects.get(profile_owner__username=username)
        return profile

    @classmethod
    def find_profile_by_userid(cls, user_id):
        """
        method that returns a user's details 
        """
        user_details = cls.objects.get(profile_owner=user_id)
        return user_details


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    """
    method that let's a user update their profile
    """
    if created:
        Profile.objects.create(profile_owner=instance)
    instance.profile.save()


class Hood(models.Model):
    """
    Hood class that defines objects of each neighbourhood
    """
    hood_name = models.CharField(max_length=150)
    hood_location = models.ForeignKey('Location')
    hood_admin = models.ForeignKey('Profile')

    def __str__(self):
        return str(self.hood_name)

    class Meta:
        ordering = ['hood_name']

    def create_hood(self):
        """
        Method that creates a new hood object
        """
        self.save()

    def delete_hood(self):
        """
        Method that deletes a hood object
        """
        self.delete()

    @classmethod
    def find_hood(cls, hood_id):
        """
        Class method that returns a hood instance
        Args:
            hood_id
        """
        found_hood = cls.objects.get(id=hood_id)
        return found_hood


class Location(models.Model):
    """
    Location class that defines objects of each location
    """
    loc_name = models.CharField(max_length=255, verbose_name="Pick your Location")

    def __str__(self):
        return str(self.loc_name)


class Business(models.Model):
    """
    Business class that defines objects of each business
    """
    BUSINESS_CHOICES = (
        ('B', 'Boutique & Cosmetics Shop'),
        ('BT', 'Butchery'),
        ('C', 'Cobblers'),
        ('E', 'Education'),
        ('H', 'Hardware'),
        ('HC', 'HealthCare'),
        ('K', 'Kiosks'),
        ('M', 'Supermarkets'),
        ('V', 'Mpesa Airtel vendors'),
        ('S', 'Salon'),
    )
    business_name = models.CharField(max_length=50)
    business_category = models.CharField(max_length=2, choices=BUSINESS_CHOICES)
    business_owner = models.ForeignKey('Profile')
    business_hood = models.ForeignKey('Hood')
    business_description = models.CharField(max_length=100, null=True, blank=True)
    business_email = models.EmailField()

    def create_business(self):
        """
        method that creates business
        """
        self.save()

    def delete_business(self):
        """
        Delete method to delete an instance of class Business
        """
        self.delete()

    @classmethod
    def find_business(cls, business_id):
        """
        method to return a specific instance of class business
        """
        found_business = cls.objects.get(id=business_id)
        return found_business


class News(models.Model):
    """
    News class that defines objects of each news
    """
    news_footage = models.ImageField(
        upload_to='footages/', verbose_name="Attach Footage", null=True, blank=True)
    news_details = models.TextField()
    news_created_by = models.ForeignKey('Profile', verbose_name='Created By', related_name='owner')
    news_hood = models.ForeignKey('Hood')
    # news_comments = models.ManyToManyField('Profile', default=False, through='Comment', through_fields=(
    #     'comment_image', 'comment_owner'))
    news_pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.news_details[:50])

    class Meta:
        """
        Ordering of posts with the most recent showing from the top most
        """
        ordering = ['-news_pub_date']
        verbose_name_plural = 'news'

    def save_news(self):
        """
        method that creates news
        """
        self.save()

    def delete_news(self):
        """
        methods that deletes an instance of news
        """
        self.delete()