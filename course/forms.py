from django import forms

from .models import Course, Review


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('course_name', 'city', 'holes', 'tee_type')


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('thoughts',)
        widgets = {'thoughts': forms.Textarea(attrs={'rows': 4})}
