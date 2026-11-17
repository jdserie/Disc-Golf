from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CourseForm, ReviewForm
from .models import Course, Review


def posted_id(request, key='id'):
    value = request.POST.get(key, '')
    if not value.isascii() or not value.isdecimal() or len(value) > 19:
        raise Http404
    identifier = int(value)
    if identifier > 2**63 - 1:
        raise Http404
    return identifier


def home(request):
    if request.method == 'POST':
        if not request.user.is_staff:
            raise PermissionDenied
        value = request.POST.get('play')
        if value not in ('True', 'False'):
            return HttpResponseBadRequest('Invalid course status.')
        course = get_object_or_404(Course, pk=posted_id(request))
        course.play = value == 'True'
        course.save(update_fields=['play'])
        return redirect('courseHome')

    query = request.GET.get('q', '').strip()[:120]
    courses = Course.objects.filter(play=False).order_by('course_name', 'pk')
    if query:
        courses = courses.filter(Q(course_name__icontains=query) | Q(city__icontains=query))
    return render(request, 'course/course_list.html', {
        'course_list': courses,
        'play_course': Course.objects.filter(play=True).order_by('course_name') if request.user.is_staff else (),
        'query': query,
    })


@login_required
def add(request):
    form = CourseForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        course = form.save()
        return redirect('courseInfo', course.pk)
    return render(request, 'course/course_add.html', {'form': form})


@require_POST
def my_delete(request):
    if not request.user.is_staff:
        raise PermissionDenied
    get_object_or_404(Course, pk=posted_id(request), play=True).delete()
    return redirect('courseHome')


def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    return render_detail(request, course, ReviewForm())


def render_detail(request, course, form, status=200):
    reviews = course.review_set.select_related('author').order_by('-pk')
    return render(request, 'course/course_detail.html', {
        'ind_course': course,
        'review_list': Paginator(reviews, 5).get_page(request.GET.get('page')),
        'form': form,
    }, status=status)


def review(request):
    reviews = Review.objects.select_related('author', 'crse').order_by('-pk')
    return render(request, 'course/reviews.html', {
        'review_list': Paginator(reviews, 5).get_page(request.GET.get('page')),
    })


@login_required
@require_POST
def add_review(request):
    course = get_object_or_404(Course, pk=posted_id(request, 'crse'), play=False)
    form = ReviewForm(request.POST)
    if not form.is_valid():
        return render_detail(request, course, form, status=400)
    entry = form.save(commit=False)
    entry.crse = course
    entry.author = request.user
    entry.save()
    messages.success(request, 'Your review was posted.')
    return redirect('courseInfo', course.pk)


@login_required
@require_POST
def review_delete(request):
    entries = Review.objects.all()
    if not request.user.is_staff:
        entries = entries.filter(author=request.user)
    get_object_or_404(entries, pk=posted_id(request)).delete()
    return redirect('reviewCourse')
